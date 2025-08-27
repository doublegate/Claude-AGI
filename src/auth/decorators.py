"""
Authentication and Authorization Decorators for Claude-AGI
==========================================================

Provides decorators for securing API endpoints and functions:
- JWT token validation
- Role-based access control
- Permission checking
- Rate limiting integration
- Audit logging
"""

import functools
import logging
from typing import List, Optional, Callable, Any, Union
from flask import request, jsonify, g, current_app
from werkzeug.exceptions import Unauthorized, Forbidden

from .jwt_manager import JWTManager
from .rbac import Permission, RBACManager
from .user_manager import UserManager

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication failed"""
    pass


class AuthorizationError(Exception):
    """Authorization failed"""
    pass


def get_auth_managers():
    """Get authentication managers from Flask app context"""
    if not hasattr(current_app, 'jwt_manager'):
        raise RuntimeError("JWT manager not configured")
    if not hasattr(current_app, 'rbac_manager'):
        raise RuntimeError("RBAC manager not configured")
    if not hasattr(current_app, 'user_manager'):
        raise RuntimeError("User manager not configured")
    
    return (current_app.jwt_manager, 
            current_app.rbac_manager, 
            current_app.user_manager)


def extract_token() -> Optional[str]:
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    try:
        # Expected format: "Bearer <token>"
        scheme, token = auth_header.split(' ', 1)
        if scheme.lower() != 'bearer':
            return None
        return token
    except ValueError:
        return None


def require_auth(f: Callable) -> Callable:
    """
    Decorator requiring valid JWT authentication
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_endpoint():
            return {"user": g.current_user}
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        jwt_manager, rbac_manager, user_manager = get_auth_managers()
        
        # Extract token
        token = extract_token()
        if not token:
            logger.warning("Missing authentication token for %s", request.endpoint)
            return jsonify({"error": "Authentication required"}), 401
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        if not payload:
            logger.warning("Invalid token for %s", request.endpoint)
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get user info
        user_id = payload.get('user_id')
        username = payload.get('username')
        
        if not user_id or not username:
            logger.error("Invalid token payload: missing user info")
            return jsonify({"error": "Invalid token"}), 401
        
        # Verify user still exists and is active
        user = user_manager.get_user(user_id)
        if not user or user.status.value != 'active':
            logger.warning("Token for inactive user: %s", username)
            return jsonify({"error": "User account inactive"}), 401
        
        # Store user context
        g.current_user = user
        g.current_user_id = user_id
        g.current_username = username
        g.user_roles = payload.get('roles', [])
        g.user_permissions = payload.get('permissions', [])
        g.token_payload = payload
        
        logger.debug("Authenticated user: %s for %s", username, request.endpoint)
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission: Union[Permission, str], 
                      resource: Optional[str] = None,
                      action: Optional[str] = None) -> Callable:
    """
    Decorator requiring specific permission
    
    Args:
        permission: Required permission
        resource: Optional resource name
        action: Optional action name
        
    Usage:
        @app.route('/admin/users')
        @require_auth
        @require_permission(Permission.USER_VIEW)
        def list_users():
            return {"users": [...]}
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user is authenticated first
            if not hasattr(g, 'current_user_id'):
                return jsonify({"error": "Authentication required"}), 401
            
            jwt_manager, rbac_manager, user_manager = get_auth_managers()
            
            # Convert string to Permission enum if needed
            required_permission = permission
            if isinstance(permission, str):
                try:
                    required_permission = Permission(permission)
                except ValueError:
                    logger.error("Invalid permission string: %s", permission)
                    return jsonify({"error": "Invalid permission"}), 500
            
            # Check permission
            has_permission = False
            
            if resource and action:
                # Resource-based check
                has_permission = rbac_manager.check_resource_access(
                    g.current_user_id, resource, action
                )
            else:
                # Direct permission check
                has_permission = rbac_manager.user_has_permission(
                    g.current_user_id, required_permission
                )
            
            if not has_permission:
                logger.warning("Permission denied for user %s: %s", 
                             g.current_username, required_permission.value)
                return jsonify({
                    "error": "Insufficient permissions",
                    "required": required_permission.value
                }), 403
            
            logger.debug("Permission granted for user %s: %s", 
                        g.current_username, required_permission.value)
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(role: Union[str, List[str]], require_all: bool = False) -> Callable:
    """
    Decorator requiring specific role(s)
    
    Args:
        role: Required role name(s)
        require_all: If True, user must have ALL roles; if False, ANY role
        
    Usage:
        @app.route('/admin')
        @require_auth
        @require_role('admin')
        def admin_panel():
            return {"status": "admin access granted"}
            
        @app.route('/super-admin')
        @require_auth  
        @require_role(['admin', 'super_admin'], require_all=False)
        def super_admin_only():
            return {"status": "super admin access"}
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user is authenticated first
            if not hasattr(g, 'current_user_id'):
                return jsonify({"error": "Authentication required"}), 401
            
            jwt_manager, rbac_manager, user_manager = get_auth_managers()
            
            # Normalize role to list
            required_roles = role if isinstance(role, list) else [role]
            
            # Check roles
            has_access = False
            
            if require_all:
                # User must have ALL roles
                has_access = all(
                    rbac_manager.user_has_role(g.current_user_id, r) 
                    for r in required_roles
                )
            else:
                # User must have ANY role
                has_access = rbac_manager.user_has_any_role(
                    g.current_user_id, required_roles
                )
            
            if not has_access:
                logger.warning("Role check failed for user %s. Required: %s (all=%s)", 
                             g.current_username, required_roles, require_all)
                return jsonify({
                    "error": "Insufficient role privileges",
                    "required_roles": required_roles,
                    "require_all": require_all
                }), 403
            
            logger.debug("Role check passed for user %s: %s", 
                        g.current_username, required_roles)
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(f: Callable) -> Callable:
    """
    Decorator requiring admin role
    
    Shorthand for @require_role(['admin', 'super_admin'])
    """
    return require_role(['admin', 'super_admin'])(f)


def require_super_admin(f: Callable) -> Callable:
    """
    Decorator requiring super admin role
    
    Shorthand for @require_role('super_admin')
    """
    return require_role('super_admin')(f)


def audit_log(action: str, resource_type: str = "unknown") -> Callable:
    """
    Decorator for audit logging
    
    Args:
        action: Action being performed
        resource_type: Type of resource being accessed
        
    Usage:
        @app.route('/users/<user_id>', methods=['DELETE'])
        @require_auth
        @require_permission(Permission.USER_DELETE)
        @audit_log("delete_user", "user")
        def delete_user(user_id):
            return {"deleted": user_id}
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request info
            user_id = getattr(g, 'current_user_id', 'anonymous')
            username = getattr(g, 'current_username', 'anonymous')
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            # Log the action
            logger.info(
                "AUDIT: user=%s (%s) action=%s resource=%s endpoint=%s "
                "method=%s ip=%s user_agent=%s",
                username, user_id, action, resource_type,
                request.endpoint, request.method, ip_address, user_agent
            )
            
            try:
                # Execute the function
                result = f(*args, **kwargs)
                
                # Log success
                logger.info(
                    "AUDIT SUCCESS: user=%s action=%s resource=%s",
                    username, action, resource_type
                )
                
                return result
                
            except Exception as e:
                # Log failure
                logger.error(
                    "AUDIT FAILURE: user=%s action=%s resource=%s error=%s",
                    username, action, resource_type, str(e)
                )
                raise
        
        return decorated_function
    return decorator


def rate_limit(max_requests: int = 100, window_minutes: int = 60) -> Callable:
    """
    Rate limiting decorator (basic in-memory implementation)
    
    Args:
        max_requests: Maximum requests allowed
        window_minutes: Time window in minutes
        
    Usage:
        @app.route('/api/expensive')
        @require_auth
        @rate_limit(max_requests=10, window_minutes=1)
        def expensive_operation():
            return {"result": "computed"}
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # In-memory storage (use Redis in production)
    request_counts = defaultdict(list)
    
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user identifier
            user_id = getattr(g, 'current_user_id', request.remote_addr)
            
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=window_minutes)
            
            # Clean old requests
            request_counts[user_id] = [
                req_time for req_time in request_counts[user_id]
                if req_time > window_start
            ]
            
            # Check rate limit
            if len(request_counts[user_id]) >= max_requests:
                logger.warning(
                    "Rate limit exceeded for user %s: %d requests in %d minutes",
                    getattr(g, 'current_username', user_id),
                    len(request_counts[user_id]),
                    window_minutes
                )
                return jsonify({
                    "error": "Rate limit exceeded",
                    "max_requests": max_requests,
                    "window_minutes": window_minutes
                }), 429
            
            # Add current request
            request_counts[user_id].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication
    
    Sets user context if valid token provided, but doesn't require it.
    
    Usage:
        @app.route('/public-but-personalized')
        @optional_auth
        def public_endpoint():
            if hasattr(g, 'current_user'):
                return {"message": f"Hello {g.current_username}!"}
            else:
                return {"message": "Hello anonymous user!"}
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            jwt_manager, rbac_manager, user_manager = get_auth_managers()
            
            # Try to extract and verify token
            token = extract_token()
            if token:
                payload = jwt_manager.verify_token(token)
                if payload:
                    user_id = payload.get('user_id')
                    username = payload.get('username')
                    
                    if user_id and username:
                        user = user_manager.get_user(user_id)
                        if user and user.status.value == 'active':
                            # Set optional context
                            g.current_user = user
                            g.current_user_id = user_id
                            g.current_username = username
                            g.user_roles = payload.get('roles', [])
                            g.user_permissions = payload.get('permissions', [])
                            g.token_payload = payload
        except Exception:
            # Ignore auth errors for optional auth
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function


# Utility functions for use within decorated functions

def get_current_user():
    """Get current authenticated user"""
    return getattr(g, 'current_user', None)


def get_current_user_id():
    """Get current user ID"""
    return getattr(g, 'current_user_id', None)


def get_current_username():
    """Get current username"""
    return getattr(g, 'current_username', None)


def get_user_roles():
    """Get current user roles"""
    return getattr(g, 'user_roles', [])


def get_user_permissions():
    """Get current user permissions"""
    return getattr(g, 'user_permissions', [])


def has_permission(permission: Union[Permission, str]) -> bool:
    """Check if current user has permission"""
    if not hasattr(g, 'current_user_id'):
        return False
    
    try:
        _, rbac_manager, _ = get_auth_managers()
        
        if isinstance(permission, str):
            permission = Permission(permission)
            
        return rbac_manager.user_has_permission(g.current_user_id, permission)
    except:
        return False


def has_role(role: str) -> bool:
    """Check if current user has role"""
    if not hasattr(g, 'current_user_id'):
        return False
    
    try:
        _, rbac_manager, _ = get_auth_managers()
        return rbac_manager.user_has_role(g.current_user_id, role)
    except:
        return False


def has_any_role(roles: List[str]) -> bool:
    """Check if current user has any of the specified roles"""
    if not hasattr(g, 'current_user_id'):
        return False
    
    try:
        _, rbac_manager, _ = get_auth_managers()
        return rbac_manager.user_has_any_role(g.current_user_id, roles)
    except:
        return False