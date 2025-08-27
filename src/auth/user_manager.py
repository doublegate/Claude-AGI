"""
User Management System for Claude-AGI Authentication
===================================================

Provides user account management with secure password handling:
- User creation and authentication
- Password hashing with bcrypt
- Profile management
- Account status tracking
- Integration with RBAC system
"""

import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class User:
    """User account representation"""
    user_id: str
    username: str
    email: str
    password_hash: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.status == UserStatus.LOCKED:
            if self.locked_until and datetime.utcnow() > self.locked_until:
                # Lock expired, reset status
                self.status = UserStatus.ACTIVE
                self.locked_until = None
                self.failed_attempts = 0
                return False
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password)"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_attempts': self.failed_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'metadata': self.metadata
        }


class UserManager:
    """
    User account management system
    
    Provides secure user management with password hashing, account locking,
    and integration with the RBAC system for role-based access control.
    """
    
    def __init__(self, rbac_manager, max_failed_attempts: int = 5, 
                 lockout_duration_minutes: int = 30):
        """
        Initialize user manager
        
        Args:
            rbac_manager: RBAC manager instance
            max_failed_attempts: Max login attempts before lockout
            lockout_duration_minutes: Account lockout duration
        """
        self.rbac_manager = rbac_manager
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)
        
        # In-memory user storage (in production, use database)
        self.users: Dict[str, User] = {}
        self.username_to_id: Dict[str, str] = {}
        self.email_to_id: Dict[str, str] = {}
        
        # Create default admin user
        self._create_default_admin()
        
        logger.info("User Manager initialized with lockout policy: %d attempts, %d minutes",
                   max_failed_attempts, lockout_duration_minutes)
    
    def _create_default_admin(self):
        """Create default admin user if none exists"""
        admin_username = "admin"
        admin_email = "admin@claude-agi.local"
        admin_password = "admin123"  # Change in production!
        
        if admin_username not in self.username_to_id:
            admin_user = self.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                status=UserStatus.ACTIVE
            )
            
            if admin_user:
                # Assign super_admin role
                self.rbac_manager.assign_role_to_user(admin_user.user_id, "super_admin")
                logger.info("Created default admin user: %s", admin_username)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        import uuid
        return str(uuid.uuid4())
    
    def create_user(self, username: str, email: str, password: str,
                   status: UserStatus = UserStatus.ACTIVE,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[User]:
        """
        Create new user account
        
        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
            status: Initial account status
            metadata: Additional user metadata
            
        Returns:
            User object if created successfully
        """
        # Validate inputs
        if not username or not email or not password:
            logger.error("Missing required user fields")
            return None
        
        if username in self.username_to_id:
            logger.error("Username already exists: %s", username)
            return None
        
        if email in self.email_to_id:
            logger.error("Email already exists: %s", email)
            return None
        
        # Create user
        user_id = self._generate_user_id()
        password_hash = self._hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            status=status,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store user
        self.users[user_id] = user
        self.username_to_id[username] = user_id
        self.email_to_id[email] = user_id
        
        logger.info("Created user: %s (ID: %s)", username, user_id)
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User object if authentication successful
        """
        # Find user by username or email
        user_id = self.username_to_id.get(username) or self.email_to_id.get(username)
        if not user_id:
            logger.warning("Authentication failed: user not found: %s", username)
            return None
        
        user = self.users.get(user_id)
        if not user:
            logger.error("User data inconsistency for ID: %s", user_id)
            return None
        
        # Check if account is locked
        if user.is_locked():
            logger.warning("Authentication failed: account locked: %s", username)
            return None
        
        # Check account status
        if user.status != UserStatus.ACTIVE:
            logger.warning("Authentication failed: account inactive: %s", username)
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_attempts >= self.max_failed_attempts:
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.utcnow() + self.lockout_duration
                logger.warning("Account locked due to failed attempts: %s", username)
            
            logger.warning("Authentication failed: invalid password for %s (attempt %d)",
                          username, user.failed_attempts)
            return None
        
        # Successful authentication
        user.failed_attempts = 0
        user.last_login = datetime.utcnow()
        
        logger.info("User authenticated successfully: %s", username)
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_id = self.username_to_id.get(username)
        return self.users.get(user_id) if user_id else None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self.email_to_id.get(email)
        return self.users.get(user_id) if user_id else None
    
    def update_user(self, user_id: str, **updates) -> bool:
        """
        Update user information
        
        Args:
            user_id: User ID
            **updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        user = self.users.get(user_id)
        if not user:
            logger.error("User not found for update: %s", user_id)
            return False
        
        # Handle username changes
        if 'username' in updates:
            new_username = updates['username']
            if new_username != user.username:
                if new_username in self.username_to_id:
                    logger.error("Username already exists: %s", new_username)
                    return False
                
                # Update username mapping
                del self.username_to_id[user.username]
                self.username_to_id[new_username] = user_id
                user.username = new_username
        
        # Handle email changes
        if 'email' in updates:
            new_email = updates['email']
            if new_email != user.email:
                if new_email in self.email_to_id:
                    logger.error("Email already exists: %s", new_email)
                    return False
                
                # Update email mapping
                del self.email_to_id[user.email]
                self.email_to_id[new_email] = user_id
                user.email = new_email
        
        # Handle password changes
        if 'password' in updates:
            user.password_hash = self._hash_password(updates['password'])
        
        # Handle other fields
        for field, value in updates.items():
            if field not in ['username', 'email', 'password'] and hasattr(user, field):
                setattr(user, field, value)
        
        logger.info("Updated user: %s", user.username)
        return True
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if changed successfully
        """
        user = self.users.get(user_id)
        if not user:
            logger.error("User not found for password change: %s", user_id)
            return False
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            logger.warning("Password change failed: invalid old password for %s", user.username)
            return False
        
        # Update password
        user.password_hash = self._hash_password(new_password)
        logger.info("Password changed for user: %s", user.username)
        return True
    
    def unlock_user(self, user_id: str) -> bool:
        """
        Unlock user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if unlocked successfully
        """
        user = self.users.get(user_id)
        if not user:
            logger.error("User not found for unlock: %s", user_id)
            return False
        
        user.status = UserStatus.ACTIVE
        user.failed_attempts = 0
        user.locked_until = None
        
        logger.info("Unlocked user account: %s", user.username)
        return True
    
    def suspend_user(self, user_id: str, reason: str = "") -> bool:
        """
        Suspend user account
        
        Args:
            user_id: User ID
            reason: Suspension reason
            
        Returns:
            True if suspended successfully
        """
        user = self.users.get(user_id)
        if not user:
            logger.error("User not found for suspension: %s", user_id)
            return False
        
        user.status = UserStatus.SUSPENDED
        if reason:
            user.metadata['suspension_reason'] = reason
            user.metadata['suspended_at'] = datetime.utcnow().isoformat()
        
        logger.info("Suspended user account: %s (reason: %s)", user.username, reason)
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        user = self.users.get(user_id)
        if not user:
            logger.error("User not found for deletion: %s", user_id)
            return False
        
        # Remove from RBAC
        user_roles = self.rbac_manager.get_user_roles(user_id)
        for role in user_roles:
            self.rbac_manager.remove_role_from_user(user_id, role)
        
        # Remove user data
        username = user.username
        email = user.email
        
        del self.users[user_id]
        del self.username_to_id[username]
        del self.email_to_id[email]
        
        logger.info("Deleted user account: %s", username)
        return True
    
    def list_users(self, status_filter: Optional[UserStatus] = None) -> List[User]:
        """
        List users with optional status filter
        
        Args:
            status_filter: Filter by user status
            
        Returns:
            List of users
        """
        users = list(self.users.values())
        
        if status_filter:
            users = [u for u in users if u.status == status_filter]
        
        return sorted(users, key=lambda u: u.created_at or datetime.min)
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics
        
        Returns:
            Statistics dictionary
        """
        total_users = len(self.users)
        status_counts = {}
        
        for status in UserStatus:
            status_counts[status.value] = len([
                u for u in self.users.values() 
                if u.status == status
            ])
        
        locked_users = len([
            u for u in self.users.values() 
            if u.is_locked()
        ])
        
        return {
            'total_users': total_users,
            'status_distribution': status_counts,
            'locked_users': locked_users,
            'users_with_roles': len([
                u for u in self.users.values()
                if self.rbac_manager.get_user_roles(u.user_id)
            ])
        }
    
    def export_users(self) -> Dict[str, Any]:
        """
        Export users for backup/migration
        
        Returns:
            Users data dictionary
        """
        return {
            'users': [user.to_dict() for user in self.users.values()],
            'exported_at': datetime.utcnow().isoformat()
        }