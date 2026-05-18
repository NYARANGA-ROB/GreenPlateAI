"""
Authentication utilities for GreenPlateAI.

This module provides password hashing, session management,
and authentication helper functions.
"""

import secrets
import hashlib
import re
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    import bcrypt
except ImportError:
    bcrypt = None

from models.user_auth import User, UserSession, PasswordReset, AuditLog, UserRole
from database.connection import get_db

class PasswordManager:
    """Password hashing and verification utilities."""
    PBKDF2_ITERATIONS = 390000
    PBKDF2_PREFIX = "pbkdf2_sha256"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt when available, otherwise PBKDF2."""
        if not password:
            raise ValueError("Password cannot be empty")
        if bcrypt is not None:
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')

        # Fallback for environments without bcrypt installed.
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PasswordManager.PBKDF2_ITERATIONS,
        )
        salt_b64 = base64.b64encode(salt).decode("utf-8")
        digest_b64 = base64.b64encode(digest).decode("utf-8")
        return f"{PasswordManager.PBKDF2_PREFIX}${PasswordManager.PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        if not password or not hashed_password:
            return False
        
        try:
            if hashed_password.startswith(f"{PasswordManager.PBKDF2_PREFIX}$"):
                _, iterations, salt_b64, digest_b64 = hashed_password.split("$", 3)
                iterations_int = int(iterations)
                salt = base64.b64decode(salt_b64.encode("utf-8"))
                expected_digest = base64.b64decode(digest_b64.encode("utf-8"))
                candidate_digest = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt,
                    iterations_int,
                )
                return secrets.compare_digest(candidate_digest, expected_digest)

            if bcrypt is None:
                # Can't validate existing bcrypt hashes without bcrypt installed.
                return False

            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return feedback."""
        if not password:
            return {
                "valid": False,
                "score": 0,
                "errors": ["Password cannot be empty"],
                "suggestions": ["Please enter a password"]
            }
        
        errors = []
        suggestions = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
            suggestions.append("Use a longer password")
        else:
            score += 20
        
        # Uppercase check
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            suggestions.append("Add uppercase letters")
        else:
            score += 20
        
        # Lowercase check
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            suggestions.append("Add lowercase letters")
        else:
            score += 20
        
        # Digit check
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
            suggestions.append("Add numbers")
        else:
            score += 20
        
        # Special character check
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
            suggestions.append("Add special characters")
        else:
            score += 20
        
        # Common patterns check
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123', r'111111'
        ]
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append("Password contains common patterns")
                suggestions.append("Avoid common patterns")
                score -= 10
                break
        
        return {
            "valid": len(errors) == 0,
            "score": max(0, min(100, score)),
            "errors": errors,
            "suggestions": suggestions
        }


class SessionManager:
    """Session management utilities."""
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_session(user: User, ip_address: str = None, user_agent: str = None, hours: int = 24) -> UserSession:
        """Create a new user session."""
        db = next(get_db())
        try:
            # Deactivate existing sessions for this user
            existing_sessions = db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).all()
            
            for session in existing_sessions:
                session.is_active = False
            
            # Create new session
            session_token = SessionManager.generate_session_token()
            expires_at = datetime.utcnow() + timedelta(hours=hours)
            
            new_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            return new_session
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @staticmethod
    def get_user_from_session(session_token: str) -> Optional[User]:
        """Get user from session token."""
        if not session_token:
            return None
        
        db = next(get_db())
        try:
            # Find active session
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            ).first()
            
            if not session or session.is_expired:
                return None
            
            # Update last activity
            session.update_activity()
            db.commit()
            
            # Get user
            user = db.query(User).filter(
                User.id == session.user_id,
                User.is_active == True
            ).first()
            
            return user
            
        except Exception:
            return None
        finally:
            db.close()
    
    @staticmethod
    def invalidate_session(session_token: str) -> bool:
        """Invalidate a user session."""
        if not session_token:
            return False
        
        db = next(get_db())
        try:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                return True
            
            return False
            
        except Exception:
            return False
        finally:
            db.close()
    
    @staticmethod
    def invalidate_all_user_sessions(user_id: int) -> bool:
        """Invalidate all sessions for a user."""
        db = next(get_db())
        try:
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).all()
            
            for session in sessions:
                session.is_active = False
            
            db.commit()
            return True
            
        except Exception:
            return False
        finally:
            db.close()
    
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """Clean up expired sessions."""
        db = next(get_db())
        try:
            expired_sessions = db.query(UserSession).filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_sessions)
            for session in expired_sessions:
                db.delete(session)
            
            db.commit()
            return count
            
        except Exception:
            return 0
        finally:
            db.close()


class AuthenticationManager:
    """Main authentication manager."""
    
    def __init__(self):
        self.password_manager = PasswordManager()
        self.session_manager = SessionManager()
    
    def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = None,
        phone: str = None,
        department: str = None,
        role: UserRole = UserRole.STUDENT,
        auto_verify: bool = False
    ) -> Tuple[bool, str, Optional[User]]:
        """Register a new user."""
        try:
            # Validate password strength
            password_validation = self.password_manager.validate_password_strength(password)
            if not password_validation["valid"]:
                return False, "Password does not meet security requirements", None
            
            db = next(get_db())
            
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return False, "Email already registered", None
                else:
                    return False, "Username already taken", None
            
            # Hash password
            password_hash = self.password_manager.hash_password(password)
            
            # Create user
            new_user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                phone=phone,
                department=department,
                role=role,
                is_verified=auto_verify
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Log registration
            self._log_action(new_user.id, "user_registered", "user", str(new_user.id))
            
            return True, "Registration successful", new_user
            
        except IntegrityError:
            return False, "User already exists", None
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
        finally:
            if 'db' in locals():
                db.close()
    
    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, str, Optional[User], Optional[str]]:
        """Authenticate user and create session."""
        try:
            db = next(get_db())
            
            # Find user
            user = db.query(User).filter(
                User.email == email,
                User.is_active == True
            ).first()
            
            if not user:
                return False, "Invalid email or password", None, None
            
            # Check if account is locked
            if user.is_locked:
                return False, "Account is temporarily locked", None, None
            
            # Verify password
            if not self.password_manager.verify_password(password, user.password_hash):
                user.increment_failed_login()
                db.commit()
                
                if user.is_locked:
                    return False, "Account locked due to multiple failed attempts", None, None
                
                return False, "Invalid email or password", None, None
            
            # Reset failed login attempts
            user.reset_failed_login()
            
            # Update last login
            user.update_last_login()
            db.commit()
            
            # Create session
            session = self.session_manager.create_session(
                user, ip_address, user_agent
            )
            
            # Log successful login
            self._log_action(user.id, "user_login", "session", str(session.id))
            
            return True, "Login successful", user, session.session_token
            
        except Exception as e:
            return False, f"Authentication failed: {str(e)}", None, None
        finally:
            if 'db' in locals():
                db.close()
    
    def logout_user(self, session_token: str) -> bool:
        """Logout user and invalidate session."""
        try:
            user = self.session_manager.get_user_from_session(session_token)
            
            if user:
                # Invalidate session
                success = self.session_manager.invalidate_session(session_token)
                
                if success:
                    # Log logout
                    self._log_action(user.id, "user_logout", "session", session_token)
                    return True
            
            return False
            
        except Exception:
            return False
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        """Change user password."""
        try:
            db = next(get_db())
            
            user = db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
            
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not self.password_manager.verify_password(current_password, user.password_hash):
                return False, "Current password is incorrect"
            
            # Validate new password
            password_validation = self.password_manager.validate_password_strength(new_password)
            if not password_validation["valid"]:
                return False, "New password does not meet security requirements"
            
            # Check if new password is same as current
            if self.password_manager.verify_password(new_password, user.password_hash):
                return False, "New password must be different from current password"
            
            # Update password
            user.password_hash = self.password_manager.hash_password(new_password)
            user.password_changed_at = datetime.utcnow()
            
            # Invalidate all sessions (force re-login)
            self.session_manager.invalidate_all_user_sessions(user_id)
            
            db.commit()
            
            # Log password change
            self._log_action(user_id, "password_changed", "user", str(user_id))
            
            return True, "Password changed successfully"
            
        except Exception as e:
            return False, f"Password change failed: {str(e)}"
        finally:
            if 'db' in locals():
                db.close()
    
    def reset_password_request(self, email: str) -> Tuple[bool, str]:
        """Request password reset."""
        try:
            db = next(get_db())
            
            user = db.query(User).filter(
                User.email == email,
                User.is_active == True
            ).first()
            
            if not user:
                return False, "Email not found"
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Create password reset record
            password_reset = PasswordReset(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            
            db.add(password_reset)
            db.commit()
            
            # Log password reset request
            self._log_action(user.id, "password_reset_requested", "user", str(user.id))
            
            # In a real application, you would send an email here
            # For now, we'll just return success
            return True, "Password reset link sent to your email"
            
        except Exception as e:
            return False, f"Password reset request failed: {str(e)}"
        finally:
            if 'db' in locals():
                db.close()
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password using token."""
        try:
            db = next(get_db())
            
            # Find valid reset token
            password_reset = db.query(PasswordReset).filter(
                PasswordReset.token == token,
                PasswordReset.is_used == False
            ).first()
            
            if not password_reset or password_reset.is_expired:
                return False, "Invalid or expired reset token"
            
            # Validate new password
            password_validation = self.password_manager.validate_password_strength(new_password)
            if not password_validation["valid"]:
                return False, "Password does not meet security requirements"
            
            # Get user
            user = db.query(User).filter(
                User.id == password_reset.user_id,
                User.is_active == True
            ).first()
            
            if not user:
                return False, "User not found"
            
            # Update password
            user.password_hash = self.password_manager.hash_password(new_password)
            user.password_changed_at = datetime.utcnow()
            
            # Mark token as used
            password_reset.mark_as_used()
            
            # Invalidate all sessions
            self.session_manager.invalidate_all_user_sessions(user.id)
            
            db.commit()
            
            # Log password reset
            self._log_action(user.id, "password_reset_completed", "user", str(user.id))
            
            return True, "Password reset successful"
            
        except Exception as e:
            return False, f"Password reset failed: {str(e)}"
        finally:
            if 'db' in locals():
                db.close()
    
    def get_current_user(self, session_token: str) -> Optional[User]:
        """Get current authenticated user."""
        return self.session_manager.get_user_from_session(session_token)
    
    def _log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: str = None
    ):
        """Log user action."""
        try:
            db = next(get_db())
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception:
            pass  # Don't fail if logging fails
        finally:
            if 'db' in locals():
                db.close()


# Global authentication manager instance
auth_manager = AuthenticationManager()
