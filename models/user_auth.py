"""
User authentication models for GreenPlateAI.

This module contains SQLAlchemy models for user management,
authentication, and role-based access control.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
import re

Base = declarative_base()


class UserRole(str, Enum):
    """User roles for the application."""
    ADMIN = "admin"
    KITCHEN_STAFF = "kitchen_staff"
    STUDENT = "student"


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.STUDENT, nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    department = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format."""
        if username and not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            raise ValueError("Username must be 3-30 characters, alphanumeric and underscores only")
        return username
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_kitchen_staff(self) -> bool:
        """Check if user is kitchen staff."""
        return self.role == UserRole.KITCHEN_STAFF
    
    @property
    def is_student(self) -> bool:
        """Check if user is student."""
        return self.role == UserRole.STUDENT
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role == UserRole.ADMIN
    
    @property
    def can_manage_kitchen(self) -> bool:
        """Check if user can manage kitchen operations."""
        return self.role in [UserRole.ADMIN, UserRole.KITCHEN_STAFF]
    
    @property
    def can_view_reports(self) -> bool:
        """Check if user can view reports."""
        return self.role in [UserRole.ADMIN, UserRole.KITCHEN_STAFF]
    
    @property
    def can_manage_inventory(self) -> bool:
        """Check if user can manage inventory."""
        return self.role in [UserRole.ADMIN, UserRole.KITCHEN_STAFF]
    
    @property
    def can_view_dashboard(self) -> bool:
        """Check if user can view dashboard."""
        return self.role in [UserRole.ADMIN, UserRole.KITCHEN_STAFF, UserRole.STUDENT]
    
    def lock_account(self, hours: int = 24) -> None:
        """Lock user account for specified hours."""
        self.locked_until = datetime.utcnow() + timedelta(hours=hours)
        self.failed_login_attempts = 0
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def reset_failed_login(self) -> None:
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
    
    def get_permissions(self) -> List[str]:
        """Get user permissions based on role."""
        permissions = {
            UserRole.ADMIN: [
                "manage_users", "manage_system", "view_all_reports", 
                "manage_inventory", "manage_kitchen", "view_dashboard"
            ],
            UserRole.KITCHEN_STAFF: [
                "manage_inventory", "manage_kitchen", "view_reports", 
                "view_dashboard"
            ],
            UserRole.STUDENT: [
                "view_dashboard"
            ]
        }
        return permissions.get(self.role, [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.get_permissions()
    
    def to_dict(self, exclude_sensitive: bool = True) -> dict:
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'department': self.department,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if not exclude_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_locked,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        return data


class UserSession(Base):
    """User session model for authentication tracking."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired
    
    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def invalidate(self) -> None:
        """Invalidate session."""
        self.is_active = False
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()


class PasswordReset(Base):
    """Password reset model for password recovery."""
    
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")
    
    @property
    def is_expired(self) -> bool:
        """Check if reset token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if reset token is valid."""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self) -> None:
        """Mark reset token as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()


class AuditLog(Base):
    """Audit log for tracking user actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(Text)  # JSON string for additional details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


# Database helper functions
def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")


def drop_tables(engine):
    """Drop all database tables."""
    Base.metadata.drop_all(engine)
    print("Database tables dropped successfully!")
