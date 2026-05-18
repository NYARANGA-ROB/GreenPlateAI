"""
Authentication logic for GreenPlateAI.
This module provides core authentication functionality including
user login/logout, session management, and password handling.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import secrets

from utils.helpers import generate_token, verify_token, hash_password, verify_password
from utils.config import get_config
from database.connection import get_session
from models.user import User, Session, UserRole

logger = logging.getLogger(__name__)


def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User: Authenticated user or None if authentication fails
    """
    try:
        db = get_session()
        
        # Find user by email
        user = db.query(User).filter(
            User.email == email.lower(),
            User.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return None
        
        # Check if account is locked
        if user.is_locked:
            logger.warning(f"Login attempt on locked account: {email}")
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            user.increment_failed_login()
            db.commit()
            logger.warning(f"Failed login attempt for email: {email}")
            return None
        
        # Reset failed login attempts
        user.reset_failed_login()
        user.update_last_login()
        
        # Create session
        session_token = generate_token(str(user.id))
        user_session = Session(
            user_id=str(user.id),
            session_token=session_token,
            ip_address=st.context.headers.get('x-forwarded-for', 'unknown'),
            user_agent=st.context.headers.get('user-agent', 'unknown'),
            expires_at=datetime.utcnow() + timedelta(hours=get_config().session_timeout_hours)
        )
        
        db.add(user_session)
        db.commit()
        
        # Store session in Streamlit session state
        st.session_state.session_token = session_token
        st.session_state.user_id = str(user.id)
        
        logger.info(f"User authenticated successfully: {email}")
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()


def logout_user() -> bool:
    """
    Logout current user and invalidate session.
    
    Returns:
        bool: True if logout successful
    """
    try:
        # Get session token from session state
        session_token = st.session_state.get('session_token')
        
        if session_token:
            db = get_session()
            
            # Invalidate session in database
            user_session = db.query(Session).filter(
                Session.session_token == session_token,
                Session.is_active == True
            ).first()
            
            if user_session:
                user_session.invalidate()
                db.commit()
            
            db.close()
        
        # Clear Streamlit session state
        if 'session_token' in st.session_state:
            del st.session_state.session_token
        if 'user_id' in st.session_state:
            del st.session_state.user_id
        if 'user' in st.session_state:
            del st.session_state.user
        
        logger.info("User logged out successfully")
        return True
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return False


def get_current_user() -> Optional[User]:
    """
    Get current authenticated user from session.
    
    Returns:
        User: Current user or None if not authenticated
    """
    try:
        # Check if user is cached in session state
        if 'user' in st.session_state and st.session_state.user:
            return st.session_state.user
        
        # Get session token
        session_token = st.session_state.get('session_token')
        if not session_token:
            return None
        
        # Verify token
        payload = verify_token(session_token)
        if not payload:
            # Token is invalid, clear session
            logout_user()
            return None
        
        # Get user from database
        db = get_session()
        user = db.query(User).filter(
            User.id == payload.get('user_id'),
            User.is_active == True
        ).first()
        
        if not user:
            logout_user()
            return None
        
        # Check if session is still valid
        user_session = db.query(Session).filter(
            Session.session_token == session_token,
            Session.is_active == True,
            Session.expires_at > datetime.utcnow()
        ).first()
        
        if not user_session:
            logout_user()
            return None
        
        # Update session activity
        user_session.update_activity()
        db.commit()
        
        # Cache user in session state
        st.session_state.user = user
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()


def create_user(
    email: str,
    username: str,
    password: str,
    role: UserRole = UserRole.VIEWER,
    full_name: str = None,
    department: str = None,
    phone: str = None
) -> Optional[User]:
    """
    Create a new user account.
    
    Args:
        email: User email
        username: Username
        password: Password
        role: User role
        full_name: Full name
        department: Department
        phone: Phone number
        
    Returns:
        User: Created user or None if creation fails
    """
    try:
        db = get_session()
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email.lower()) | (User.username == username)
        ).first()
        
        if existing_user:
            logger.warning(f"Attempt to create duplicate user: {email}/{username}")
            return None
        
        # Create new user
        user = User(
            email=email.lower(),
            username=username,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name,
            department=department,
            phone=phone,
            is_email_verified=False,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        
        logger.info(f"New user created: {email}")
        return user
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()


def update_user(
    user_id: str,
    email: str = None,
    username: str = None,
    full_name: str = None,
    department: str = None,
    phone: str = None,
    role: UserRole = None
) -> Optional[User]:
    """
    Update user information.
    
    Args:
        user_id: User ID
        email: New email
        username: New username
        full_name: New full name
        department: New department
        phone: New phone
        role: New role
        
    Returns:
        User: Updated user or None if update fails
    """
    try:
        db = get_session()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Update fields if provided
        if email and email != user.email:
            # Check if email is already taken
            existing = db.query(User).filter(
                User.email == email.lower(),
                User.id != user_id
            ).first()
            if existing:
                return None
            user.email = email.lower()
        
        if username and username != user.username:
            # Check if username is already taken
            existing = db.query(User).filter(
                User.username == username,
                User.id != user_id
            ).first()
            if existing:
                return None
            user.username = username
        
        if full_name is not None:
            user.full_name = full_name
        
        if department is not None:
            user.department = department
        
        if phone is not None:
            user.phone = phone
        
        if role is not None:
            user.role = role
        
        db.commit()
        
        logger.info(f"User updated: {user.email}")
        return user
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return None
    finally:
        if 'db' in locals():
            db.close()


def delete_user(user_id: str) -> bool:
    """
    Delete user account (soft delete).
    
    Args:
        user_id: User ID
        
    Returns:
        bool: True if deletion successful
    """
    try:
        db = get_session()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Soft delete user
        user.soft_delete()
        
        # Invalidate all user sessions
        db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True
        ).update({'is_active': False})
        
        db.commit()
        
        logger.info(f"User deleted: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """
    Change user password.
    
    Args:
        user_id: User ID
        current_password: Current password
        new_password: New password
        
    Returns:
        bool: True if password change successful
    """
    try:
        db = get_session()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Invalidate all sessions except current one
        current_session_token = st.session_state.get('session_token')
        db.query(Session).filter(
            Session.user_id == user_id,
            Session.session_token != current_session_token,
            Session.is_active == True
        ).update({'is_active': False})
        
        db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def reset_password_request(email: str) -> bool:
    """
    Request password reset (sends reset token).
    
    Args:
        email: User email
        
    Returns:
        bool: True if reset request processed
    """
    try:
        db = get_session()
        
        user = db.query(User).filter(
            User.email == email.lower(),
            User.is_active == True
        ).first()
        
        if not user:
            # Don't reveal if email exists or not
            return True
        
        # Generate reset token (valid for 1 hour)
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token (in a real app, you'd store this in a separate table)
        user.preferences = f'{{"reset_token": "{reset_token}", "reset_expires": "{(datetime.utcnow() + timedelta(hours=1)).isoformat()}"}}'
        
        db.commit()
        
        # In a real app, you'd send an email with the reset link
        logger.info(f"Password reset requested for: {email}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def reset_password(token: str, new_password: str) -> bool:
    """
    Reset password with token.
    
    Args:
        token: Reset token
        new_password: New password
        
    Returns:
        bool: True if password reset successful
    """
    try:
        db = get_session()
        
        # Find user with valid reset token
        users = db.query(User).filter(User.is_active == True).all()
        
        target_user = None
        for user in users:
            try:
                import json
                prefs = json.loads(user.preferences or '{}')
                if prefs.get('reset_token') == token:
                    # Check if token is still valid
                    expires = datetime.fromisoformat(prefs.get('reset_expires', '1970-01-01'))
                    if expires > datetime.utcnow():
                        target_user = user
                        break
            except:
                continue
        
        if not target_user:
            return False
        
        # Update password
        target_user.password_hash = hash_password(new_password)
        target_user.password_changed_at = datetime.utcnow()
        
        # Clear reset token
        target_user.preferences = '{}'
        
        # Invalidate all sessions
        db.query(Session).filter(
            Session.user_id == target_user.id,
            Session.is_active == True
        ).update({'is_active': False})
        
        db.commit()
        
        logger.info(f"Password reset completed for: {target_user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def is_authenticated() -> bool:
    """
    Check if current user is authenticated.
    
    Returns:
        bool: True if authenticated
    """
    return get_current_user() is not None


def get_active_sessions(user_id: str = None) -> list:
    """
    Get active user sessions.
    
    Args:
        user_id: User ID (None for current user)
        
    Returns:
        list: Active sessions
    """
    try:
        db = get_session()
        
        if user_id is None:
            current_user = get_current_user()
            if not current_user:
                return []
            user_id = current_user.id
        
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True,
            Session.expires_at > datetime.utcnow()
        ).order_by(Session.last_activity.desc()).all()
        
        session_list = []
        for session in sessions:
            session_list.append({
                'session_token': session.session_token[:8] + '...',  # Show only first 8 chars
                'ip_address': session.ip_address,
                'user_agent': session.user_agent[:50] + '...' if len(session.user_agent) > 50 else session.user_agent,
                'last_activity': session.last_activity,
                'expires_at': session.expires_at
            })
        
        return session_list
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return []
    finally:
        if 'db' in locals():
            db.close()


def revoke_session(session_token: str) -> bool:
    """
    Revoke a specific session.
    
    Args:
        session_token: Session token to revoke
        
    Returns:
        bool: True if session revoked
    """
    try:
        db = get_session()
        
        session = db.query(Session).filter(
            Session.session_token == session_token,
            Session.is_active == True
        ).first()
        
        if session:
            session.invalidate()
            db.commit()
            logger.info(f"Session revoked: {session_token[:8]}...")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error revoking session: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


def revoke_all_sessions(user_id: str = None) -> bool:
    """
    Revoke all sessions for a user.
    
    Args:
        user_id: User ID (None for current user)
        
    Returns:
        bool: True if sessions revoked
    """
    try:
        db = get_session()
        
        if user_id is None:
            current_user = get_current_user()
            if not current_user:
                return False
            user_id = current_user.id
        
        # Revoke all sessions
        db.query(Session).filter(
            Session.user_id == user_id,
            Session.is_active == True
        ).update({'is_active': False})
        
        db.commit()
        
        logger.info(f"All sessions revoked for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
