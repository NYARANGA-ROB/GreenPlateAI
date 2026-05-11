"""
User authentication and authorization models.

This module contains models for user management, authentication,
and role-based access control.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import BaseModel


class UserRole(str, Enum):
    """User roles for the application."""
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.VIEWER, nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    department = Column(String(100))
    is_email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    login_count = Column(String(50), default="0")
    failed_login_attempts = Column(String(50), default="0")
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    preferences = Column(Text)  # JSON string for user preferences
    profile_image_url = Column(String(500))
    bio = Column(Text)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
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
    def is_manager(self) -> bool:
        """Check if user is manager or higher."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @property
    def can_view_reports(self) -> bool:
        """Check if user can view reports."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF]
    
    @property
    def can_manage_data(self) -> bool:
        """Check if user can manage data."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF]
    
    def lock_account(self, hours: int = 24) -> None:
        """Lock user account for specified hours."""
        self.locked_until = datetime.utcnow() + timedelta(hours=hours)
        self.failed_login_attempts = "0"
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = "0"
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts."""
        current = int(self.failed_login_attempts or "0")
        self.failed_login_attempts = str(current + 1)
        
        # Lock account after 5 failed attempts
        if current >= 4:
            self.lock_account()
    
    def reset_failed_login(self) -> None:
        """Reset failed login attempts."""
        self.failed_login_attempts = "0"
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        current = int(self.login_count or "0")
        self.login_count = str(current + 1)
    
    def get_permissions(self) -> list:
        """Get user permissions based on role."""
        permissions = {
            UserRole.ADMIN: [
                "manage_users", "manage_system", "view_all_reports",
                "manage_data", "manage_predictions", "manage_settings"
            ],
            UserRole.MANAGER: [
                "view_reports", "manage_data", "manage_predictions",
                "manage_team", "export_data"
            ],
            UserRole.STAFF: [
                "view_reports", "manage_data", "create_predictions",
                "export_data"
            ],
            UserRole.VIEWER: [
                "view_reports", "view_data"
            ]
        }
        return permissions.get(self.role, [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.get_permissions()
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """Convert user to dictionary, excluding sensitive fields."""
        exclude_fields = exclude_fields or []
        sensitive_fields = ["password_hash", "two_factor_secret"]
        exclude_fields.extend(sensitive_fields)
        return super().to_dict(exclude_fields=exclude_fields)


class Session(BaseModel):
    """User session model for authentication tracking."""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
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
