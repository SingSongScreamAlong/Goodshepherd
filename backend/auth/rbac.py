"""Role-based access control (RBAC) for route protection."""

from enum import Enum
from typing import Callable, Optional
from functools import wraps
from fastapi import HTTPException, Depends, status
from backend.auth.jwt_handler import get_current_user, TokenData


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"


# Role hierarchy - higher roles include permissions of lower roles
ROLE_HIERARCHY = {
    Role.ADMIN: [Role.ADMIN, Role.ANALYST, Role.OPERATOR, Role.VIEWER],
    Role.ANALYST: [Role.ANALYST, Role.OPERATOR, Role.VIEWER],
    Role.OPERATOR: [Role.OPERATOR, Role.VIEWER],
    Role.VIEWER: [Role.VIEWER],
}


class Permission(str, Enum):
    """Granular permissions for specific actions."""
    # Event permissions
    EVENTS_READ = "events:read"
    EVENTS_CREATE = "events:create"
    EVENTS_UPDATE = "events:update"
    EVENTS_DELETE = "events:delete"
    
    # Alert permissions
    ALERTS_READ = "alerts:read"
    ALERTS_CREATE = "alerts:create"
    ALERTS_UPDATE = "alerts:update"
    ALERTS_DELETE = "alerts:delete"
    ALERTS_ACKNOWLEDGE = "alerts:acknowledge"
    
    # Report permissions
    REPORTS_READ = "reports:read"
    REPORTS_CREATE = "reports:create"
    REPORTS_EXPORT = "reports:export"
    
    # User management permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_AUDIT = "system:audit"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.EVENTS_READ, Permission.EVENTS_CREATE, Permission.EVENTS_UPDATE, Permission.EVENTS_DELETE,
        Permission.ALERTS_READ, Permission.ALERTS_CREATE, Permission.ALERTS_UPDATE, Permission.ALERTS_DELETE, Permission.ALERTS_ACKNOWLEDGE,
        Permission.REPORTS_READ, Permission.REPORTS_CREATE, Permission.REPORTS_EXPORT,
        Permission.USERS_READ, Permission.USERS_CREATE, Permission.USERS_UPDATE, Permission.USERS_DELETE,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_AUDIT,
    ],
    Role.ANALYST: [
        Permission.EVENTS_READ, Permission.EVENTS_CREATE, Permission.EVENTS_UPDATE,
        Permission.ALERTS_READ, Permission.ALERTS_CREATE, Permission.ALERTS_UPDATE, Permission.ALERTS_ACKNOWLEDGE,
        Permission.REPORTS_READ, Permission.REPORTS_CREATE, Permission.REPORTS_EXPORT,
        Permission.USERS_READ,
    ],
    Role.OPERATOR: [
        Permission.EVENTS_READ, Permission.EVENTS_CREATE,
        Permission.ALERTS_READ, Permission.ALERTS_ACKNOWLEDGE,
        Permission.REPORTS_READ,
    ],
    Role.VIEWER: [
        Permission.EVENTS_READ,
        Permission.ALERTS_READ,
        Permission.REPORTS_READ,
    ],
}


def get_user_permissions(roles: list[str]) -> set[Permission]:
    """Get all permissions for a user based on their roles."""
    permissions = set()
    for role_str in roles:
        try:
            role = Role(role_str)
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        except ValueError:
            # Unknown role, skip
            continue
    return permissions


def has_role(user_roles: list[str], required_role: Role) -> bool:
    """Check if user has the required role (considering hierarchy)."""
    for role_str in user_roles:
        try:
            user_role = Role(role_str)
            if required_role in ROLE_HIERARCHY.get(user_role, []):
                return True
        except ValueError:
            continue
    return False


def has_permission(user_roles: list[str], required_permission: Permission) -> bool:
    """Check if user has the required permission."""
    user_permissions = get_user_permissions(user_roles)
    return required_permission in user_permissions


def has_any_permission(user_roles: list[str], required_permissions: list[Permission]) -> bool:
    """Check if user has any of the required permissions."""
    user_permissions = get_user_permissions(user_roles)
    return bool(user_permissions.intersection(required_permissions))


def has_all_permissions(user_roles: list[str], required_permissions: list[Permission]) -> bool:
    """Check if user has all of the required permissions."""
    user_permissions = get_user_permissions(user_roles)
    return all(p in user_permissions for p in required_permissions)


class RoleChecker:
    """Dependency for checking user roles."""
    
    def __init__(self, required_roles: list[Role]):
        self.required_roles = required_roles
    
    async def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        user_roles = current_user.roles or []
        
        for required_role in self.required_roles:
            if has_role(user_roles, required_role):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {', '.join(r.value for r in self.required_roles)}",
        )


class PermissionChecker:
    """Dependency for checking user permissions."""
    
    def __init__(self, required_permissions: list[Permission], require_all: bool = False):
        self.required_permissions = required_permissions
        self.require_all = require_all
    
    async def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        user_roles = current_user.roles or []
        
        if self.require_all:
            if has_all_permissions(user_roles, self.required_permissions):
                return current_user
        else:
            if has_any_permission(user_roles, self.required_permissions):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {', '.join(p.value for p in self.required_permissions)}",
        )


# Convenience dependencies
def require_admin():
    """Require admin role."""
    return RoleChecker([Role.ADMIN])


def require_analyst():
    """Require analyst role or higher."""
    return RoleChecker([Role.ADMIN, Role.ANALYST])


def require_operator():
    """Require operator role or higher."""
    return RoleChecker([Role.ADMIN, Role.ANALYST, Role.OPERATOR])


def require_viewer():
    """Require viewer role or higher (any authenticated user with a role)."""
    return RoleChecker([Role.ADMIN, Role.ANALYST, Role.OPERATOR, Role.VIEWER])


def require_permission(permission: Permission):
    """Require a specific permission."""
    return PermissionChecker([permission])


def require_permissions(*permissions: Permission, require_all: bool = False):
    """Require multiple permissions."""
    return PermissionChecker(list(permissions), require_all=require_all)


# Example usage in routes:
# @app.get("/api/admin/users", dependencies=[Depends(require_admin())])
# @app.get("/api/events", dependencies=[Depends(require_permission(Permission.EVENTS_READ))])
