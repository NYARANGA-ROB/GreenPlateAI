"""
Authentication and authorization module for GreenPlateAI.

This module provides user authentication, session management,
and role-based access control functionality.
"""

# Core authentication utilities
from .auth_utils import auth_manager, PasswordManager, SessionManager, AuthenticationManager

# Page components
from .pages.login import show_login_page, check_authentication, logout_user
from .pages.register import show_registration_page
from .pages.reset_password import show_reset_password_page, show_change_password_form

# Access control
from .access_control import (
    require_auth, require_role, require_admin, require_kitchen_staff,
    require_permission, optional_auth, check_session_timeout,
    rate_limit, log_access, get_current_user, is_authenticated,
    get_user_role, has_permission, authenticated_page,
    admin_page, kitchen_staff_page, student_page
)

# Navigation
from .sidebar_navigation import (
    show_authenticated_sidebar, show_unauthenticated_sidebar,
    render_sidebar, show_mobile_navigation
)

# Models
from models.user_auth import User, UserSession, PasswordReset, AuditLog, UserRole

__all__ = [
    # Core authentication
    'auth_manager',
    'PasswordManager', 
    'SessionManager',
    'AuthenticationManager',
    
    # Page functions
    'show_login_page',
    'show_registration_page', 
    'show_reset_password_page',
    'show_change_password_form',
    
    # Authentication helpers
    'check_authentication',
    'logout_user',
    'get_current_user',
    'is_authenticated',
    
    # Access control decorators
    'require_auth',
    'require_role',
    'require_admin',
    'require_kitchen_staff',
    'require_permission',
    'optional_auth',
    'check_session_timeout',
    'rate_limit',
    'log_access',
    
    # Page decorators
    'authenticated_page',
    'admin_page',
    'kitchen_staff_page', 
    'student_page',
    
    # User helpers
    'get_user_role',
    'has_permission',
    
    # Navigation
    'show_authenticated_sidebar',
    'show_unauthenticated_sidebar',
    'render_sidebar',
    'show_mobile_navigation',
    
    # Models
    'User',
    'UserSession',
    'PasswordReset', 
    'AuditLog',
    'UserRole'
]
