"""
Permission management for GreenPlateAI.

This module provides role-based permission checking and
access control utilities.
"""

from typing import List, Dict, Set
from models.user import User, UserRole

# Permission definitions
PERMISSIONS = {
    # User management
    "manage_users": "Create, update, and delete user accounts",
    "view_users": "View user information and lists",
    "manage_team": "Manage team members and assignments",
    
    # System management
    "manage_system": "Access system configuration and settings",
    "view_system": "View system information and logs",
    "manage_settings": "Modify application settings",
    
    # Data management
    "manage_data": "Create, update, and delete data records",
    "view_data": "View data records and information",
    "import_data": "Import data from external sources",
    "export_data": "Export data to external formats",
    "delete_data": "Permanently delete data records",
    
    # Analytics and reports
    "view_reports": "View analytics reports and dashboards",
    "create_reports": "Create and generate custom reports",
    "manage_reports": "Manage report configurations",
    "view_all_reports": "Access all reports across organization",
    
    # Predictions and ML
    "manage_predictions": "Create and manage ML predictions",
    "view_predictions": "View prediction results and forecasts",
    "train_models": "Train and update ML models",
    "manage_models": "Manage model configurations",
    
    # Recommendations
    "view_recommendations": "View AI recommendations",
    "manage_recommendations": "Manage recommendation settings",
    "implement_recommendations": "Mark recommendations as implemented",
    
    # Inventory management
    "manage_inventory": "Create, update, and delete inventory records",
    "view_inventory": "View inventory information",
    "adjust_inventory": "Adjust inventory quantities",
    
    # Waste tracking
    "manage_waste": "Create, update, and delete waste records",
    "view_waste": "View waste tracking information",
    "verify_waste": "Verify and approve waste records",
    
    # Audit and compliance
    "view_audit": "View audit logs and compliance information",
    "manage_audit": "Manage audit configurations",
    
    # Notifications
    "manage_notifications": "Configure system notifications",
    "send_notifications": "Send notifications to users",
    
    # Backup and recovery
    "manage_backups": "Create and manage system backups",
    "restore_data": "Restore data from backups"
}

# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(PERMISSIONS.keys()),  # Admin has all permissions
    
    UserRole.MANAGER: [
        # User management (limited)
        "view_users",
        "manage_team",
        
        # System management (limited)
        "view_system",
        
        # Data management
        "manage_data",
        "view_data",
        "import_data",
        "export_data",
        
        # Analytics and reports
        "view_reports",
        "create_reports",
        "manage_reports",
        "view_all_reports",
        
        # Predictions and ML
        "manage_predictions",
        "view_predictions",
        
        # Recommendations
        "view_recommendations",
        "manage_recommendations",
        "implement_recommendations",
        
        # Inventory management
        "manage_inventory",
        "view_inventory",
        "adjust_inventory",
        
        # Waste tracking
        "manage_waste",
        "view_waste",
        "verify_waste",
        
        # Notifications
        "manage_notifications",
        "send_notifications"
    ],
    
    UserRole.STAFF: [
        # Data management
        "view_data",
        "import_data",
        "export_data",
        
        # Analytics and reports
        "view_reports",
        "create_reports",
        
        # Predictions and ML
        "view_predictions",
        
        # Recommendations
        "view_recommendations",
        "implement_recommendations",
        
        # Inventory management
        "view_inventory",
        "adjust_inventory",
        
        # Waste tracking
        "manage_waste",
        "view_waste"
    ],
    
    UserRole.VIEWER: [
        # View-only permissions
        "view_data",
        "view_reports",
        "view_predictions",
        "view_recommendations",
        "view_inventory",
        "view_waste"
    ]
}

# Permission categories for organization
PERMISSION_CATEGORIES = {
    "User Management": ["manage_users", "view_users", "manage_team"],
    "System Administration": ["manage_system", "view_system", "manage_settings"],
    "Data Management": ["manage_data", "view_data", "import_data", "export_data", "delete_data"],
    "Analytics & Reporting": ["view_reports", "create_reports", "manage_reports", "view_all_reports"],
    "Machine Learning": ["manage_predictions", "view_predictions", "train_models", "manage_models"],
    "Recommendations": ["view_recommendations", "manage_recommendations", "implement_recommendations"],
    "Inventory": ["manage_inventory", "view_inventory", "adjust_inventory"],
    "Waste Tracking": ["manage_waste", "view_waste", "verify_waste"],
    "Audit & Compliance": ["view_audit", "manage_audit"],
    "Notifications": ["manage_notifications", "send_notifications"],
    "Backup & Recovery": ["manage_backups", "restore_data"]
}


def get_user_permissions(user: User) -> Set[str]:
    """
    Get all permissions for a user based on their role.
    
    Args:
        user: User object
        
    Returns:
        set: Set of permission names
    """
    if not user or not user.role:
        return set()
    
    # Get base permissions for role
    base_permissions = set(ROLE_PERMISSIONS.get(user.role, []))
    
    # In a more complex system, you might add role-specific logic
    # or additional permission assignments here
    
    return base_permissions


def check_permission(user: User, permission: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: User object
        permission: Permission name to check
        
    Returns:
        bool: True if user has permission
    """
    if not user or not permission:
        return False
    
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def check_permissions(user: User, permissions: List[str]) -> Dict[str, bool]:
    """
    Check multiple permissions for a user.
    
    Args:
        user: User object
        permissions: List of permission names to check
        
    Returns:
        dict: Dictionary mapping permission names to boolean results
    """
    results = {}
    user_permissions = get_user_permissions(user)
    
    for permission in permissions:
        results[permission] = permission in user_permissions
    
    return results


def has_any_permission(user: User, permissions: List[str]) -> bool:
    """
    Check if user has any of the specified permissions.
    
    Args:
        user: User object
        permissions: List of permission names
        
    Returns:
        bool: True if user has any permission
    """
    user_permissions = get_user_permissions(user)
    return any(permission in user_permissions for permission in permissions)


def has_all_permissions(user: User, permissions: List[str]) -> bool:
    """
    Check if user has all of the specified permissions.
    
    Args:
        user: User object
        permissions: List of permission names
        
    Returns:
        bool: True if user has all permissions
    """
    user_permissions = get_user_permissions(user)
    return all(permission in user_permissions for permission in permissions)


def get_permission_description(permission: str) -> str:
    """
    Get description for a permission.
    
    Args:
        permission: Permission name
        
    Returns:
        str: Permission description
    """
    return PERMISSIONS.get(permission, "Unknown permission")


def get_permissions_by_category(category: str) -> List[str]:
    """
    Get all permissions in a specific category.
    
    Args:
        category: Category name
        
    Returns:
        list: List of permission names
    """
    return PERMISSION_CATEGORIES.get(category, [])


def get_all_permission_categories() -> Dict[str, List[str]]:
    """
    Get all permission categories and their permissions.
    
    Returns:
        dict: Dictionary mapping category names to permission lists
    """
    return PERMISSION_CATEGORIES.copy()


def filter_permissions_by_role(role: UserRole, category: str = None) -> List[str]:
    """
    Get permissions for a specific role, optionally filtered by category.
    
    Args:
        role: User role
        category: Optional category filter
        
    Returns:
        list: List of permission names
    """
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    if category:
        category_permissions = PERMISSION_CATEGORIES.get(category, [])
        permissions = [p for p in permissions if p in category_permissions]
    
    return permissions


def can_access_resource(user: User, resource_type: str, action: str) -> bool:
    """
    Check if user can access a specific resource type with an action.
    
    Args:
        user: User object
        resource_type: Type of resource (e.g., 'users', 'reports', 'predictions')
        action: Action to perform (e.g., 'view', 'create', 'delete')
        
    Returns:
        bool: True if access is allowed
    """
    # Map resource types and actions to permissions
    resource_permission_map = {
        'users': {
            'view': 'view_users',
            'create': 'manage_users',
            'update': 'manage_users',
            'delete': 'manage_users'
        },
        'reports': {
            'view': 'view_reports',
            'create': 'create_reports',
            'update': 'manage_reports',
            'delete': 'manage_reports'
        },
        'predictions': {
            'view': 'view_predictions',
            'create': 'manage_predictions',
            'update': 'manage_predictions',
            'delete': 'manage_predictions'
        },
        'recommendations': {
            'view': 'view_recommendations',
            'create': 'manage_recommendations',
            'update': 'manage_recommendations',
            'delete': 'manage_recommendations'
        },
        'inventory': {
            'view': 'view_inventory',
            'create': 'manage_inventory',
            'update': 'adjust_inventory',
            'delete': 'manage_inventory'
        },
        'waste': {
            'view': 'view_waste',
            'create': 'manage_waste',
            'update': 'manage_waste',
            'delete': 'manage_waste',
            'verify': 'verify_waste'
        },
        'data': {
            'view': 'view_data',
            'create': 'manage_data',
            'update': 'manage_data',
            'delete': 'delete_data',
            'import': 'import_data',
            'export': 'export_data'
        },
        'system': {
            'view': 'view_system',
            'update': 'manage_system',
            'configure': 'manage_settings'
        }
    }
    
    # Get the required permission
    resource_permissions = resource_permission_map.get(resource_type, {})
    required_permission = resource_permissions.get(action)
    
    if not required_permission:
        # Default to deny if mapping doesn't exist
        return False
    
    return check_permission(user, required_permission)


def get_role_hierarchy() -> List[UserRole]:
    """
    Get roles ordered by hierarchy (lowest to highest).
    
    Returns:
        list: List of roles in hierarchical order
    """
    return [UserRole.VIEWER, UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]


def can_manage_role(user: User, target_role: UserRole) -> bool:
    """
    Check if user can manage accounts with target role.
    
    Args:
        user: User attempting to manage
        target_role: Role of target user
        
    Returns:
        bool: True if user can manage target role
    """
    if not user:
        return False
    
    # Admin can manage any role
    if user.role == UserRole.ADMIN:
        return True
    
    # Manager can manage staff and viewer roles
    if user.role == UserRole.MANAGER:
        return target_role in [UserRole.STAFF, UserRole.VIEWER]
    
    # Staff and viewer cannot manage other roles
    return False


def get_permission_summary(user: User) -> Dict[str, any]:
    """
    Get a summary of user's permissions.
    
    Args:
        user: User object
        
    Returns:
        dict: Permission summary
    """
    permissions = get_user_permissions(user)
    
    summary = {
        'user_id': user.id,
        'user_email': user.email,
        'user_role': user.role,
        'total_permissions': len(permissions),
        'permissions_by_category': {},
        'can_manage_users': check_permission(user, 'manage_users'),
        'can_view_reports': check_permission(user, 'view_reports'),
        'can_manage_data': check_permission(user, 'manage_data'),
        'can_manage_predictions': check_permission(user, 'manage_predictions'),
        'role_level': get_role_hierarchy().index(user.role) if user.role in get_role_hierarchy() else -1
    }
    
    # Group permissions by category
    for category, category_permissions in PERMISSION_CATEGORIES.items():
        category_perms = [p for p in category_permissions if p in permissions]
        summary['permissions_by_category'][category] = {
            'count': len(category_perms),
            'permissions': category_perms
        }
    
    return summary


def validate_permission_assignment(role: UserRole, permissions: List[str]) -> Dict[str, any]:
    """
    Validate if permissions can be assigned to a role.
    
    Args:
        role: User role
        permissions: List of permissions to assign
        
    Returns:
        dict: Validation result
    """
    result = {
        'valid': True,
        'invalid_permissions': [],
        'missing_permissions': [],
        'warnings': []
    }
    
    # Check if all permissions exist
    for permission in permissions:
        if permission not in PERMISSIONS:
            result['invalid_permissions'].append(permission)
            result['valid'] = False
    
    # For non-admin roles, check if permissions exceed role capabilities
    if role != UserRole.ADMIN:
        role_base_permissions = set(ROLE_PERMISSIONS.get(role, []))
        requested_permissions = set(permissions)
        
        # Find permissions that exceed role capabilities
        excess_permissions = requested_permissions - role_base_permissions
        if excess_permissions:
            result['warnings'].append(f"Permissions exceed role capabilities: {', '.join(excess_permissions)}")
    
    return result


def get_permission_audit_log(user: User, action: str, resource: str = None) -> Dict[str, any]:
    """
    Create an audit log entry for permission-based actions.
    
    Args:
        user: User performing the action
        action: Action being performed
        resource: Resource being acted upon
        
    Returns:
        dict: Audit log entry
    """
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user.id,
        'user_email': user.email,
        'user_role': user.role,
        'action': action,
        'resource': resource,
        'permissions': list(get_user_permissions(user)),
        'ip_address': st.context.headers.get('x-forwarded-for', 'unknown') if 'st' in globals() else 'unknown',
        'user_agent': st.context.headers.get('user-agent', 'unknown') if 'st' in globals() else 'unknown'
    }
