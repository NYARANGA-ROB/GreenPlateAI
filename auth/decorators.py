"""
Authentication decorators for GreenPlateAI.
This module provides decorators for protecting routes and functions
with authentication and authorization requirements.
"""

import functools
import streamlit as st
from typing import Callable, Optional, List
import logging
from .authenticator import get_current_user
from .permissions import check_permission
from models.user import UserRole

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
        user = get_current_user()
        if not user:
            st.error("Authentication required. Please log in.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_role(required_role: UserRole) -> Callable:
    """
    Decorator to require specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            # Check role hierarchy
            role_hierarchy = {
                UserRole.VIEWER: 0,
                UserRole.STAFF: 1,
                UserRole.MANAGER: 2,
                UserRole.ADMIN: 3
            }
            
            user_level = role_hierarchy.get(user.role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                st.error(f"Access denied. Required role: {required_role.value}")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


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
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            if not check_permission(user, permission):
                st.error(f"Access denied. Required permission: {permission}")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]) -> Callable:
    """
    Decorator to require any of the specified permissions.
    
    Args:
        permissions: List of required permissions
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            has_permission = any(check_permission(user, perm) for perm in permissions)
            
            if not has_permission:
                st.error(f"Access denied. Required one of: {', '.join(permissions)}")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]) -> Callable:
    """
    Decorator to require all specified permissions.
    
    Args:
        permissions: List of required permissions
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            missing_permissions = []
            for permission in permissions:
                if not check_permission(user, permission):
                    missing_permissions.append(permission)
            
            if missing_permissions:
                st.error(f"Access denied. Missing permissions: {', '.join(missing_permissions)}")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def admin_only(func: Callable) -> Callable:
    """
    Decorator to require admin role only.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    return require_role(UserRole.ADMIN)(func)


def manager_or_admin(func: Callable) -> Callable:
    """
    Decorator to require manager or admin role.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            if not user.is_manager:
                st.error("Access denied. Manager or admin role required.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def staff_or_above(func: Callable) -> Callable:
    """
    Decorator to require staff role or higher.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required. Please log in.")
                st.stop()
            
            if user.role not in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]:
                st.error("Access denied. Staff role or higher required.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def optional_auth(func: Callable) -> Callable:
    """
    Decorator that makes authentication optional.
    The function will receive the user as first argument if authenticated,
    or None if not authenticated.
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        return func(user, *args, **kwargs)
    return wrapper


def rate_limit(max_calls: int = 10, window_seconds: int = 60) -> Callable:
    """
    Decorator for rate limiting function calls.
    
    Args:
        max_calls: Maximum number of calls allowed
        window_seconds: Time window in seconds
        
    Returns:
        Callable: Rate-limited function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user for rate limiting
            user = get_current_user()
            user_id = user.id if user else st.session_state.get('session_token', 'anonymous')
            
            # Initialize rate limit tracking in session state
            if 'rate_limits' not in st.session_state:
                st.session_state.rate_limits = {}
            
            key = f"{func.__name__}_{user_id}"
            now = datetime.utcnow().timestamp()
            
            # Get or initialize rate limit info
            if key not in st.session_state.rate_limits:
                st.session_state.rate_limits[key] = {
                    'calls': [],
                    'blocked_until': 0
                }
            
            rate_info = st.session_state.rate_limits[key]
            
            # Check if currently blocked
            if now < rate_info['blocked_until']:
                remaining_time = int(rate_info['blocked_until'] - now)
                st.error(f"Rate limit exceeded. Please wait {remaining_time} seconds.")
                st.stop()
            
            # Clean old calls outside window
            window_start = now - window_seconds
            rate_info['calls'] = [call_time for call_time in rate_info['calls'] if call_time > window_start]
            
            # Check if limit exceeded
            if len(rate_info['calls']) >= max_calls:
                # Block for the window duration
                rate_info['blocked_until'] = now + window_seconds
                st.error(f"Rate limit exceeded. Please wait {window_seconds} seconds.")
                st.stop()
            
            # Add current call
            rate_info['calls'].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_access(func: Callable) -> Callable:
    """
    Decorator to log function access.
    
    Args:
        func: Function to log
        
    Returns:
        Callable: Logged function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        user_info = f"{user.email} ({user.role})" if user else "Anonymous"
        
        logger.info(f"Access: {func.__name__} by {user_info}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"Success: {func.__name__} by {user_info}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__} by {user_info}: {e}")
            raise
    
    return wrapper


def validate_csrf(func: Callable) -> Callable:
    """
    Decorator to validate CSRF token (simplified for Streamlit).
    
    Args:
        func: Function to protect
        
    Returns:
        Callable: Protected function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # In Streamlit, CSRF protection is simplified
        # We can use session state for basic protection
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = secrets.token_urlsafe(16)
        
        # For POST-like operations, we'd validate the token
        # This is a simplified implementation
        return func(*args, **kwargs)
    
    return wrapper


def cache_result(ttl_seconds: int = 300) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live in seconds
        
    Returns:
        Callable: Cached function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Initialize cache in session state
            if 'function_cache' not in st.session_state:
                st.session_state.function_cache = {}
            
            cache = st.session_state.function_cache
            
            # Check if cached result exists and is valid
            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]
                if (datetime.utcnow().timestamp() - cached_time) < ttl_seconds:
                    return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, datetime.utcnow().timestamp())
            
            return result
        return wrapper
    return decorator


# Streamlit-specific decorators
def streamlit_page(func: Callable) -> Callable:
    """
    Decorator for Streamlit pages with authentication check.
    
    Args:
        func: Page function
        
    Returns:
        Callable: Protected page function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check authentication
        user = get_current_user()
        if not user:
            st.error("Please log in to access this page.")
            st.stop()
        
        # Set page context
        if 'page_title' in kwargs:
            st.set_page_config(page_title=kwargs['page_title'])
        
        return func(*args, **kwargs)
    return wrapper


def admin_page(func: Callable) -> Callable:
    """
    Decorator for admin-only pages.
    
    Args:
        func: Page function
        
    Returns:
        Callable: Protected page function
    """
    @streamlit_page
    @admin_only
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def manager_page(func: Callable) -> Callable:
    """
    Decorator for manager-only pages.
    
    Args:
        func: Page function
        
    Returns:
        Callable: Protected page function
    """
    @streamlit_page
    @manager_or_admin
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
