"""
Authentication and Authorization System for Claude-AGI
======================================================

Implements multi-tier authentication:
- API Key authentication for service-to-service
- JWT Bearer tokens for user authentication
- Role-based access control (RBAC)
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import hashlib
import hmac

import logging

logger = logging.getLogger(__name__)


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
API_KEY_HEADER_NAME = "X-API-Key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Security schemes
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    SERVICE = "service"


class User(BaseModel):
    """User model"""
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.USER
    disabled: bool = False
    api_keys: List[str] = []


class TokenData(BaseModel):
    """JWT token payload"""
    username: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


class APIKeyData(BaseModel):
    """API key information"""
    key_id: str
    key_hash: str
    username: str
    role: UserRole
    created_at: datetime
    last_used: Optional[datetime] = None
    enabled: bool = True
    rate_limit: int = 100  # requests per minute


class AuthenticationManager:
    """
    Manages authentication and authorization

    Supports:
    - API key validation
    - JWT token generation and validation
    - Role-based access control
    - User management
    """

    def __init__(self):
        # In-memory stores (in production, use database)
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKeyData] = {}  # key_hash -> APIKeyData

        # Initialize with default admin user
        self._initialize_default_users()

    def _initialize_default_users(self):
        """Create default users for development"""
        # Admin user
        admin = User(
            username="admin",
            email="admin@claude-agi.local",
            role=UserRole.ADMIN
        )
        self.users["admin"] = admin

        # Service account
        service = User(
            username="service",
            role=UserRole.SERVICE
        )
        self.users["service"] = service

        logger.info("Initialized default users")

    # API Key Methods

    def generate_api_key(
        self,
        username: str,
        role: UserRole = UserRole.USER,
        rate_limit: int = 100
    ) -> tuple[str, str]:
        """
        Generate a new API key

        Returns:
            (key_id, api_key) tuple - save api_key securely, only shown once
        """
        # Generate random key
        key_id = secrets.token_urlsafe(16)
        api_key = f"sk-{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = self._hash_api_key(api_key)

        # Store API key data
        api_key_data = APIKeyData(
            key_id=key_id,
            key_hash=key_hash,
            username=username,
            role=role,
            created_at=datetime.now(),
            rate_limit=rate_limit
        )

        self.api_keys[key_hash] = api_key_data

        # Add to user's keys
        if username in self.users:
            self.users[username].api_keys.append(key_id)

        logger.info(f"Generated API key {key_id} for {username}")
        return key_id, api_key

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def validate_api_key(self, api_key: str) -> Optional[APIKeyData]:
        """
        Validate API key

        Returns:
            APIKeyData if valid, None otherwise
        """
        if not api_key:
            return None

        key_hash = self._hash_api_key(api_key)
        api_key_data = self.api_keys.get(key_hash)

        if not api_key_data or not api_key_data.enabled:
            return None

        # Update last used
        api_key_data.last_used = datetime.now()

        logger.debug(f"Validated API key {api_key_data.key_id}")
        return api_key_data

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        for api_key_data in self.api_keys.values():
            if api_key_data.key_id == key_id:
                api_key_data.enabled = False
                logger.info(f"Revoked API key {key_id}")
                return True
        return False

    # JWT Methods

    def create_access_token(
        self,
        username: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": username,
            "role": role.value,
            "exp": expire,
            "type": "access"
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, username: str, role: UserRole) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": username,
            "role": role.value,
            "exp": expire,
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def validate_token(self, token: str) -> Optional[TokenData]:
        """
        Validate JWT token

        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role_str: str = payload.get("role")
            exp_timestamp: int = payload.get("exp")

            if username is None or role_str is None:
                return None

            role = UserRole(role_str)
            exp = datetime.fromtimestamp(exp_timestamp)

            return TokenData(username=username, role=role, exp=exp)

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None

    # User Management

    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user"""
        if username in self.users:
            raise ValueError(f"User {username} already exists")

        user = User(
            username=username,
            email=email,
            role=role
        )

        self.users[username] = user
        logger.info(f"Created user {username} with role {role}")
        return user

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)

    def disable_user(self, username: str) -> bool:
        """Disable a user"""
        user = self.users.get(username)
        if user:
            user.disabled = True
            logger.info(f"Disabled user {username}")
            return True
        return False

    # RBAC

    def check_permission(
        self,
        user_role: UserRole,
        required_role: UserRole
    ) -> bool:
        """
        Check if user role has permission

        Role hierarchy: ADMIN > SERVICE > USER > READONLY
        """
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.SERVICE: 3,
            UserRole.USER: 2,
            UserRole.READONLY: 1
        }

        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


# Global authentication manager
auth_manager = AuthenticationManager()


# FastAPI Dependencies

async def get_current_user_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[APIKeyData]:
    """
    Dependency to validate API key

    Use in routes:
        @app.get("/protected")
        async def protected(api_key_data: APIKeyData = Depends(get_current_user_api_key)):
    """
    if not api_key:
        return None

    api_key_data = auth_manager.validate_api_key(api_key)
    if not api_key_data:
        return None

    return api_key_data


async def get_current_user_bearer(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[TokenData]:
    """
    Dependency to validate Bearer token

    Use in routes:
        @app.get("/protected")
        async def protected(token_data: TokenData = Depends(get_current_user_bearer)):
    """
    if not credentials:
        return None

    token_data = auth_manager.validate_token(credentials.credentials)
    if not token_data:
        return None

    return token_data


async def get_current_user(
    api_key_data: Optional[APIKeyData] = Depends(get_current_user_api_key),
    token_data: Optional[TokenData] = Depends(get_current_user_bearer)
) -> Dict[str, Any]:
    """
    Dependency to get current user from either API key or Bearer token

    Returns user info dict or raises 401
    """
    # Try API key first
    if api_key_data:
        return {
            "username": api_key_data.username,
            "role": api_key_data.role,
            "auth_method": "api_key",
            "key_id": api_key_data.key_id
        }

    # Try Bearer token
    if token_data:
        return {
            "username": token_data.username,
            "role": token_data.role,
            "auth_method": "bearer",
            "exp": token_data.exp
        }

    # No valid authentication
    raise HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control

    Use in routes:
        @app.get("/admin")
        async def admin_only(user: dict = Depends(require_role(UserRole.ADMIN))):
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if not auth_manager.check_permission(user["role"], required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {required_role.value}"
            )
        return user

    return role_checker


# Utility Functions

def hash_password(password: str) -> str:
    """Hash password for storage"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
