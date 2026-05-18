"""
Access control decorators for GreenPlateAI authentication.
This module provides decorators for protecting pages and functions
with role-based access control and authentication requirements.
"""
import functools
import streamlit as st
from typing import Callable, Optional, List, Union
import logging
from auth.auth_utils import auth_manager
from models.user_auth import UserRole

logger = logging.getLogger(__name__)

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a function.
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check authentication
        user_info = check_authentication()
        
        if not user_info:
            st.error("🔐 Authentication required. Please log in to access this page.")
            st.info("Please log in to continue.")
            
            # Show login form
            from auth.pages.login import show_login_form_simple
            show_login_form_simple()
            
            st.stop()
        
        return func(*args, **kwargs)
    
    return wrapper


def require_role(required_role: Union[UserRole, List[UserRole]]) -> Callable:
    """
    Decorator to require specific user role(s).
    
    Args:
        required_role: Required role(s) - can be single role or list of roles
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check authentication first
            user_info = check_authentication()
            
            if not user_info:
                st.error("🔐 Authentication required. Please log in to access this page.")
                st.info("Please log in to continue.")
                
                # Show login form
                from auth.pages.login import show_login_form_simple
                show_login_form_simple()
                
                st.stop()
            
            # Check role requirements
            user_role = UserRole(user_info.get('role', 'student'))
            
            # Convert single role to list for uniform handling
            roles_to_check = [required_role] if isinstance(required_role, UserRole) else required_role
            
            if user_role not in roles_to_check:
                # Get role hierarchy for better error message
                role_hierarchy = {
                    UserRole.STUDENT: 1,
                    UserRole.KITCHEN_STAFF: 2,
                    UserRole.ADMIN: 3
                }
                
                user_level = role_hierarchy.get(user_role, 0)
                required_levels = [role_hierarchy.get(role, 0) for role in roles_to_check]
                max_required_level = max(required_levels)
                
                if user_level < max_required_level:
                    st.error(f"🚫 Access denied. This page requires {', '.join([role.title() for role in roles_to_check])} privileges.")
                    st.info(f"Your current role: {user_role.title()}")
                    
                    # Show upgrade path if applicable
                    if user_role == UserRole.STUDENT and max_required_level > 1:
                        st.info("💡 To access this feature, please contact your administrator for role upgrade.")
                    
                    st.stop()
                else:
                    st.error(f"🚫 Access denied. Your role ({user_role.title()}) is not authorized for this page.")
                    st.stop()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role only.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    return require_role(UserRole.ADMIN)(func)


def require_kitchen_staff(func: Callable) -> Callable:
    """
    Decorator to require kitchen staff role or higher.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    return require_role([UserRole.KITCHEN_STAFF, UserRole.ADMIN])(func)


def require_permission(permission: str) -> Callable:
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check authentication
            user_info = check_authentication()
            
            if not user_info:
                st.error("🔐 Authentication required. Please log in to access this page.")
                st.info("Please log in to continue.")
                
                # Show login form
                from auth.pages.login import show_login_form_simple
                show_login_form_simple()
                
                st.stop()
            
            # Check permission
            user_role = UserRole(user_info.get('role', 'student'))
            
            # Create temporary user object to check permissions
            from models.user_auth import User
            temp_user = User()
            temp_user.role = user_role
            
            if not temp_user.has_permission(permission):
                st.error(f"🚫 Access denied. You don't have permission to: {permission}")
                st.info(f"Your current role: {user_role.title()}")
                st.stop()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def optional_auth(func: Callable) -> Callable:
    """
    Decorator that makes authentication optional.
    The function will receive the user info as first argument if authenticated,
    or None if not authenticated.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_info = check_authentication()
        return func(user_info, *args, **kwargs)
    
    return wrapper


def check_session_timeout(timeout_minutes: int = 60) -> Callable:
    """
    Decorator to check for session timeout.
    
    Args:
        timeout_minutes: Session timeout in minutes
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if login time exists
            if 'login_time' not in st.session_state:
                st.error("🔐 Session expired. Please log in again.")
                st.info("Please log in to continue.")
                
                # Clear session
                if 'session_token' in st.session_state:
                    del st.session_state.session_token
                if 'user' in st.session_state:
                    del st.session_state.user
                if 'login_time' in st.session_state:
                    del st.session_state.login_time
                
                # Show login form
                from auth.pages.login import show_login_form_simple
                show_login_form_simple()
                
                st.stop()
            
            # Check session timeout
            import time
            current_time = time.time()
            login_time = st.session_state.login_time
            timeout_seconds = timeout_minutes * 60
            
            if current_time - login_time > timeout_seconds:
                st.error("🔐 Session expired due to inactivity. Please log in again.")
                st.info("Please log in to continue.")
                
                # Clear session
                if 'session_token' in st.session_state:
                    del st.session_state.session_token
                if 'user' in st.session_state:
                    del st.session_state.user
                if 'login_time' in st.session_state:
                    del st.session_state.login_time
                
                # Show login form
                from auth.pages.login import show_login_form_simple
                show_login_form_simple()
                
                st.stop()
            
            # Update login time (extend session)
            st.session_state.login_time = current_time
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(max_attempts: int = 5, window_minutes: int = 15) -> Callable:
    """
    Decorator to implement rate limiting for sensitive operations.
    
    Args:
        max_attempts: Maximum number of attempts allowed
        window_minutes: Time window in minutes
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get user info
            user_info = check_authentication()
            
            if user_info:
                user_id = user_info.get('id')
                rate_limit_key = f"rate_limit_{user_id}_{func.__name__}"
            else:
                rate_limit_key = f"rate_limit_anonymous_{func.__name__}"
            
            current_time = st.session_state.get(rate_limit_key + '_time', 0)
            attempt_count = st.session_state.get(rate_limit_key + '_count', 0)
            
            # Check if we're in the same window
            import time
            now = time.time()
            window_seconds = window_minutes * 60
            
            if now - current_time < window_seconds:
                if attempt_count >= max_attempts:
                    remaining_time = int((window_seconds - (now - current_time)) / 60)
                    st.error(f"🚫 Rate limit exceeded. Please wait {remaining_time} minutes before trying again.")
                    st.stop()
                else:
                    # Increment attempt count
                    st.session_state[rate_limit_key + '_count'] = attempt_count + 1
            else:
                # Reset window
                st.session_state[rate_limit_key + '_time'] = now
                st.session_state[rate_limit_key + '_count'] = 1
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_access(action: str = "page_access") -> Callable:
    """
    Decorator to log user access to pages or functions.
    
    Args:
        action: Action description for logging
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user_info = check_authentication()
            
            if user_info:
                # Log the access
                logger.info(f"Access: {action} by user {user_info.get('email')} ({user_info.get('role')})")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_authentication() -> Optional[dict]:
    """
    Check if user is authenticated and return user info.
    
    Returns:
        dict: User information if authenticated, None otherwise
    """
    session_token = st.session_state.get('session_token')
    
    if not session_token:
        return None
    
    user = auth_manager.get_current_user(session_token)
    
    if not user:
        # Clear invalid session
        if 'session_token' in st.session_state:
            del st.session_state.session_token
        if 'user' in st.session_state:
            del st.session_state.user
        if 'login_time' in st.session_state:
            del st.session_state.login_time
        return None
    
    # Update user info in session state
    st.session_state.user = user.to_dict()
    
    return user.to_dict()


def get_current_user() -> Optional[dict]:
    """
    Get current authenticated user information.
    
    Returns:
        dict: User information if authenticated, None otherwise
    """
    return check_authentication()


def is_authenticated() -> bool:
    """
    Check if current user is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return check_authentication() is not None


def get_user_role() -> Optional[UserRole]:
    """
    Get current user's role.
    
    Returns:
        UserRole: User role if authenticated, None otherwise
    """
    user_info = check_authentication()
    if user_info:
        return UserRole(user_info.get('role', 'student'))
    return None


def has_permission(permission: str) -> bool:
    """
    Check if current user has specific permission.
    
    Args:
        permission: Permission to check
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    user_info = check_authentication()
    
    if not user_info:
        return False
    
    user_role = UserRole(user_info.get('role', 'student'))
    
    # Create temporary user object to check permissions
    from models.user_auth import User
    temp_user = User()
    temp_user.role = user_role
    
    return temp_user.has_permission(permission)


def require_page_auth(required_role: Union[UserRole, List[UserRole]] = None, 
                    required_permission: str = None,
                    timeout_minutes: int = 60,
                    log_access: bool = True) -> Callable:
    """
    Comprehensive page authentication decorator.
    
    Args:
        required_role: Required role(s) for the page
        required_permission: Required permission for the page
        timeout_minutes: Session timeout in minutes
        log_access: Whether to log page access
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check authentication
            user_info = check_authentication()
            
            if not user_info:
                st.error("🔐 Authentication required. Please log in to access this page.")
                st.info("Please log in to continue.")
                
                # Show login form
                from auth.pages.login import show_login_form_simple
                show_login_form_simple()
                
                st.stop()
            
            # Check session timeout
            import time
            if 'login_time' in st.session_state:
                current_time = time.time()
                login_time = st.session_state.login_time
                timeout_seconds = timeout_minutes * 60
                
                if current_time - login_time > timeout_seconds:
                    st.error("🔐 Session expired due to inactivity. Please log in again.")
                    st.info("Please log in to continue.")
                    
                    # Clear session
                    if 'session_token' in st.session_state:
                        del st.session_state.session_token
                    if 'user' in st.session_state:
                        del st.session_state.user
                    if 'login_time' in st.session_state:
                        del st.session_state.login_time
                    
                    # Show login form
                    from auth.pages.login import show_login_form_simple
                    show_login_form_simple()
                    
                    st.stop()
            
            # Check role requirements
            if required_role:
                user_role = UserRole(user_info.get('role', 'student'))
                roles_to_check = [required_role] if isinstance(required_role, UserRole) else required_role
                
                if user_role not in roles_to_check:
                    st.error(f"🚫 Access denied. This page requires {', '.join([role.title() for role in roles_to_check])} privileges.")
                    st.info(f"Your current role: {user_role.title()}")
                    st.stop()
            
            # Check permission requirements
            if required_permission:
                user_role = UserRole(user_info.get('role', 'student'))
                from models.user_auth import User
                temp_user = User()
                temp_user.role = user_role
                
                if not temp_user.has_permission(required_permission):
                    st.error(f"🚫 Access denied. You don't have permission to: {required_permission}")
                    st.info(f"Your current role: {user_role.title()}")
                    st.stop()
            
            # Log access if requested
            if log_access:
                logger.info(f"Page access: {func.__name__} by user {user_info.get('email')} ({user_info.get('role')})")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Streamlit-specific page decorators
def authenticated_page(func: Callable) -> Callable:
    """
    Decorator for Streamlit pages requiring authentication.
    
    Args:
        func: Page function to protect
        
    Returns:
        Callable: Protected page function
    """
    return require_auth(func)


def admin_page(func: Callable) -> Callable:
    """
    Decorator for admin-only pages.
    
    Args:
        func: Page function to protect
        
    Returns:
        Callable: Protected page function
    """
    return require_admin(func)


def kitchen_staff_page(func: Callable) -> Callable:
    """
    Decorator for kitchen staff pages.
    
    Args:
        func: Page function to protect
        
    Returns:
        Callable: Protected page function
    """
    return require_kitchen_staff(func)


def student_page(func: Callable) -> Callable:
    """
    Decorator for student pages (minimum authentication).
    
    Args:
        func: Page function to protect
        
    Returns:
        Callable: Protected page function
    """
    return require_auth(func)
