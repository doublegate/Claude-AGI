"""
Role-Based Access Control (RBAC) System for Claude-AGI
======================================================

Implements a comprehensive RBAC system with:
- Hierarchical roles
- Fine-grained permissions
- Resource-based access control
- Permission inheritance
- Dynamic permission checking
"""

import logging
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions"""
    
    # System Administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"
    
    # Consciousness Management
    CONSCIOUSNESS_VIEW = "consciousness:view"
    CONSCIOUSNESS_CONTROL = "consciousness:control"
    CONSCIOUSNESS_DEBUG = "consciousness:debug"
    CONSCIOUSNESS_MODIFY = "consciousness:modify"
    
    # Memory System
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    MEMORY_EXPORT = "memory:export"
    MEMORY_IMPORT = "memory:import"
    
    # User Management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_MODIFY = "user:modify"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"
    
    # API Access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # Safety & Security
    SAFETY_VIEW = "safety:view"
    SAFETY_CONFIGURE = "safety:configure"
    SAFETY_OVERRIDE = "safety:override"
    
    # Exploration & Discovery
    EXPLORE_WEB = "explore:web"
    EXPLORE_INTERNAL = "explore:internal"
    EXPLORE_ADMIN = "explore:admin"
    
    # Dreams & Creativity
    DREAM_VIEW = "dream:view"
    DREAM_CREATE = "dream:create"
    DREAM_ANALYZE = "dream:analyze"
    
    # Goals & Planning
    GOALS_VIEW = "goals:view"
    GOALS_CREATE = "goals:create"
    GOALS_MODIFY = "goals:modify"
    GOALS_DELETE = "goals:delete"


@dataclass
class Role:
    """Role definition with permissions and metadata"""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: Optional[str] = None
    is_system_role: bool = False
    created_at: Optional[str] = None
    
    def add_permission(self, permission: Permission):
        """Add permission to role"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission):
        """Remove permission from role"""
        self.permissions.discard(permission)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions


class RBACManager:
    """
    Role-Based Access Control Manager
    
    Manages roles, permissions, and access control for the Claude-AGI system.
    Supports hierarchical roles, permission inheritance, and dynamic access control.
    """
    
    def __init__(self):
        """Initialize RBAC manager with default roles"""
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> set of role names
        
        # Initialize default roles
        self._create_default_roles()
        
        logger.info("RBAC Manager initialized with %d default roles", len(self.roles))
    
    def _create_default_roles(self):
        """Create default system roles"""
        
        # Super Administrator - Full system access
        super_admin = Role(
            name="super_admin",
            description="Super Administrator with full system access",
            is_system_role=True
        )
        # Add all permissions
        for permission in Permission:
            super_admin.add_permission(permission)
        self.roles["super_admin"] = super_admin
        
        # System Administrator - System management without safety override
        admin = Role(
            name="admin",
            description="System Administrator",
            is_system_role=True
        )
        admin_permissions = [
            Permission.SYSTEM_ADMIN,
            Permission.SYSTEM_CONFIG,
            Permission.SYSTEM_MONITOR,
            Permission.SYSTEM_BACKUP,
            Permission.USER_VIEW,
            Permission.USER_CREATE,
            Permission.USER_MODIFY,
            Permission.USER_DELETE,
            Permission.USER_ADMIN,
            Permission.API_ADMIN,
            Permission.CONSCIOUSNESS_VIEW,
            Permission.CONSCIOUSNESS_CONTROL,
            Permission.CONSCIOUSNESS_DEBUG,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.MEMORY_EXPORT,
            Permission.MEMORY_IMPORT,
            Permission.SAFETY_VIEW,
            Permission.SAFETY_CONFIGURE,
        ]
        for perm in admin_permissions:
            admin.add_permission(perm)
        self.roles["admin"] = admin
        
        # Researcher - Consciousness and memory research access
        researcher = Role(
            name="researcher",
            description="Researcher with consciousness and memory access",
            is_system_role=True
        )
        researcher_permissions = [
            Permission.CONSCIOUSNESS_VIEW,
            Permission.CONSCIOUSNESS_DEBUG,
            Permission.MEMORY_READ,
            Permission.MEMORY_EXPORT,
            Permission.DREAM_VIEW,
            Permission.DREAM_ANALYZE,
            Permission.GOALS_VIEW,
            Permission.API_READ,
            Permission.EXPLORE_INTERNAL,
            Permission.SAFETY_VIEW,
        ]
        for perm in researcher_permissions:
            researcher.add_permission(perm)
        self.roles["researcher"] = researcher
        
        # Operator - Day-to-day operations
        operator = Role(
            name="operator",
            description="System Operator for day-to-day operations",
            is_system_role=True
        )
        operator_permissions = [
            Permission.CONSCIOUSNESS_VIEW,
            Permission.CONSCIOUSNESS_CONTROL,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.DREAM_VIEW,
            Permission.DREAM_CREATE,
            Permission.GOALS_VIEW,
            Permission.GOALS_CREATE,
            Permission.GOALS_MODIFY,
            Permission.API_READ,
            Permission.API_WRITE,
            Permission.EXPLORE_WEB,
            Permission.EXPLORE_INTERNAL,
        ]
        for perm in operator_permissions:
            operator.add_permission(perm)
        self.roles["operator"] = operator
        
        # Viewer - Read-only access
        viewer = Role(
            name="viewer",
            description="Read-only access to system information",
            is_system_role=True
        )
        viewer_permissions = [
            Permission.CONSCIOUSNESS_VIEW,
            Permission.MEMORY_READ,
            Permission.DREAM_VIEW,
            Permission.GOALS_VIEW,
            Permission.API_READ,
            Permission.SAFETY_VIEW,
        ]
        for perm in viewer_permissions:
            viewer.add_permission(perm)
        self.roles["viewer"] = viewer
        
        # Guest - Minimal access for demonstration
        guest = Role(
            name="guest",
            description="Guest access with minimal permissions",
            is_system_role=True
        )
        guest_permissions = [
            Permission.CONSCIOUSNESS_VIEW,
            Permission.DREAM_VIEW,
            Permission.API_READ,
        ]
        for perm in guest_permissions:
            guest.add_permission(perm)
        self.roles["guest"] = guest
    
    def create_role(self, role: Role) -> bool:
        """
        Create a new role
        
        Args:
            role: Role to create
            
        Returns:
            True if created successfully
        """
        if role.name in self.roles:
            logger.warning("Role %s already exists", role.name)
            return False
        
        # Validate inheritance
        if role.inherits_from and role.inherits_from not in self.roles:
            logger.error("Cannot create role %s: parent role %s not found", 
                        role.name, role.inherits_from)
            return False
        
        self.roles[role.name] = role
        logger.info("Created role: %s", role.name)
        return True
    
    def delete_role(self, role_name: str) -> bool:
        """
        Delete a role
        
        Args:
            role_name: Name of role to delete
            
        Returns:
            True if deleted successfully
        """
        if role_name not in self.roles:
            logger.warning("Role %s not found", role_name)
            return False
        
        role = self.roles[role_name]
        if role.is_system_role:
            logger.error("Cannot delete system role: %s", role_name)
            return False
        
        # Remove role from all users
        for user_id in list(self.user_roles.keys()):
            self.user_roles[user_id].discard(role_name)
        
        del self.roles[role_name]
        logger.info("Deleted role: %s", role_name)
        return True
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """
        Assign role to user
        
        Args:
            user_id: User identifier
            role_name: Role name to assign
            
        Returns:
            True if assigned successfully
        """
        if role_name not in self.roles:
            logger.error("Role %s not found", role_name)
            return False
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        
        self.user_roles[user_id].add(role_name)
        logger.info("Assigned role %s to user %s", role_name, user_id)
        return True
    
    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """
        Remove role from user
        
        Args:
            user_id: User identifier
            role_name: Role name to remove
            
        Returns:
            True if removed successfully
        """
        if user_id not in self.user_roles:
            return False
        
        self.user_roles[user_id].discard(role_name)
        logger.info("Removed role %s from user %s", role_name, user_id)
        return True
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all roles for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of role names
        """
        return list(self.user_roles.get(user_id, set()))
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all effective permissions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of permissions
        """
        permissions = set()
        
        user_role_names = self.user_roles.get(user_id, set())
        
        for role_name in user_role_names:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
                
                # Handle role inheritance
                if role.inherits_from:
                    parent_role = self.roles.get(role.inherits_from)
                    if parent_role:
                        permissions.update(parent_role.permissions)
        
        return permissions
    
    def user_has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user_id: User identifier
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
    
    def user_has_role(self, user_id: str, role_name: str) -> bool:
        """
        Check if user has specific role
        
        Args:
            user_id: User identifier
            role_name: Role name to check
            
        Returns:
            True if user has role
        """
        user_role_names = self.user_roles.get(user_id, set())
        return role_name in user_role_names
    
    def user_has_any_role(self, user_id: str, role_names: List[str]) -> bool:
        """
        Check if user has any of the specified roles
        
        Args:
            user_id: User identifier
            role_names: List of role names to check
            
        Returns:
            True if user has at least one role
        """
        user_role_names = self.user_roles.get(user_id, set())
        return bool(user_role_names.intersection(set(role_names)))
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """
        Get role by name
        
        Args:
            role_name: Role name
            
        Returns:
            Role object if found
        """
        return self.roles.get(role_name)
    
    def list_roles(self, include_system: bool = True) -> List[Role]:
        """
        List all roles
        
        Args:
            include_system: Whether to include system roles
            
        Returns:
            List of roles
        """
        if include_system:
            return list(self.roles.values())
        else:
            return [role for role in self.roles.values() if not role.is_system_role]
    
    def get_role_hierarchy(self) -> Dict[str, List[str]]:
        """
        Get role hierarchy mapping
        
        Returns:
            Dictionary mapping parent roles to child roles
        """
        hierarchy = {}
        
        for role_name, role in self.roles.items():
            if role.inherits_from:
                if role.inherits_from not in hierarchy:
                    hierarchy[role.inherits_from] = []
                hierarchy[role.inherits_from].append(role_name)
        
        return hierarchy
    
    def validate_permission_set(self, permissions: List[str]) -> List[Permission]:
        """
        Validate and convert permission strings to Permission enums
        
        Args:
            permissions: List of permission strings
            
        Returns:
            List of valid Permission enums
        """
        valid_permissions = []
        
        for perm_str in permissions:
            try:
                perm = Permission(perm_str)
                valid_permissions.append(perm)
            except ValueError:
                logger.warning("Invalid permission: %s", perm_str)
        
        return valid_permissions
    
    def check_resource_access(self, user_id: str, resource: str, 
                            action: str) -> bool:
        """
        Check resource-specific access (extensible for future use)
        
        Args:
            user_id: User identifier
            resource: Resource name
            action: Action to perform
            
        Returns:
            True if access is allowed
        """
        # For now, map resource:action to permissions
        resource_permission_map = {
            'consciousness:view': Permission.CONSCIOUSNESS_VIEW,
            'consciousness:control': Permission.CONSCIOUSNESS_CONTROL,
            'consciousness:debug': Permission.CONSCIOUSNESS_DEBUG,
            'consciousness:modify': Permission.CONSCIOUSNESS_MODIFY,
            'memory:read': Permission.MEMORY_READ,
            'memory:write': Permission.MEMORY_WRITE,
            'memory:delete': Permission.MEMORY_DELETE,
            'system:admin': Permission.SYSTEM_ADMIN,
            'system:config': Permission.SYSTEM_CONFIG,
            'api:read': Permission.API_READ,
            'api:write': Permission.API_WRITE,
            'user:admin': Permission.USER_ADMIN,
        }
        
        resource_key = f"{resource}:{action}"
        required_permission = resource_permission_map.get(resource_key)
        
        if required_permission:
            return self.user_has_permission(user_id, required_permission)
        
        logger.warning("No permission mapping for resource:action %s", resource_key)
        return False
    
    def get_user_count_by_role(self) -> Dict[str, int]:
        """
        Get count of users per role
        
        Returns:
            Dictionary mapping role names to user counts
        """
        role_counts = {role_name: 0 for role_name in self.roles}
        
        for user_roles in self.user_roles.values():
            for role_name in user_roles:
                if role_name in role_counts:
                    role_counts[role_name] += 1
        
        return role_counts
    
    def export_rbac_config(self) -> Dict[str, Any]:
        """
        Export RBAC configuration for backup/import
        
        Returns:
            RBAC configuration dictionary
        """
        config = {
            'roles': {},
            'user_roles': {}
        }
        
        # Export roles (excluding system roles for security)
        for role_name, role in self.roles.items():
            if not role.is_system_role:
                config['roles'][role_name] = {
                    'description': role.description,
                    'permissions': [p.value for p in role.permissions],
                    'inherits_from': role.inherits_from
                }
        
        # Export user role assignments
        config['user_roles'] = {
            user_id: list(roles) 
            for user_id, roles in self.user_roles.items()
        }
        
        return config
    
    def import_rbac_config(self, config: Dict[str, Any]) -> bool:
        """
        Import RBAC configuration
        
        Args:
            config: RBAC configuration dictionary
            
        Returns:
            True if imported successfully
        """
        try:
            # Import custom roles
            for role_name, role_data in config.get('roles', {}).items():
                if role_name not in self.roles:  # Don't overwrite existing roles
                    permissions = self.validate_permission_set(role_data['permissions'])
                    role = Role(
                        name=role_name,
                        description=role_data['description'],
                        permissions=set(permissions),
                        inherits_from=role_data.get('inherits_from')
                    )
                    self.create_role(role)
            
            # Import user role assignments
            for user_id, role_names in config.get('user_roles', {}).items():
                self.user_roles[user_id] = set(role_names)
            
            logger.info("Successfully imported RBAC configuration")
            return True
            
        except Exception as e:
            logger.error("Failed to import RBAC configuration: %s", e)
            return False