"""
Authentication and Authorization System for Claude-AGI
======================================================

Provides JWT-based authentication and role-based access control (RBAC)
for the Claude-AGI system.

Components:
- JWT token management
- User authentication
- Role-based permissions
- Session management
- API endpoint protection
"""

from .jwt_manager import JWTManager, TokenPayload
from .user_manager import UserManager, User, UserStatus
from .rbac import RBACManager, Role, Permission
from .decorators import (
    require_auth, require_permission, require_role, require_admin, 
    require_super_admin, audit_log, rate_limit, optional_auth,
    get_current_user, get_current_user_id, get_current_username,
    get_user_roles, get_user_permissions, has_permission, has_role, has_any_role
)
from .middleware import (
    AuthMiddleware, SecurityMiddleware, RequestContextMiddleware,
    create_middleware_stack
)

__all__ = [
    # JWT Management
    'JWTManager',
    'TokenPayload',
    
    # User Management
    'UserManager', 
    'User',
    'UserStatus',
    
    # RBAC System
    'RBACManager',
    'Role',
    'Permission',
    
    # Authentication Decorators
    'require_auth',
    'require_permission',
    'require_role',
    'require_admin',
    'require_super_admin',
    'audit_log',
    'rate_limit',
    'optional_auth',
    
    # Context Utilities
    'get_current_user',
    'get_current_user_id', 
    'get_current_username',
    'get_user_roles',
    'get_user_permissions',
    'has_permission',
    'has_role',
    'has_any_role',
    
    # Middleware
    'AuthMiddleware',
    'SecurityMiddleware',
    'RequestContextMiddleware',
    'create_middleware_stack'
]