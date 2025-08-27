"""
JWT Token Management for Claude-AGI Authentication
==================================================

Handles JWT token creation, validation, and management with security features:
- Token signing and verification
- Expiration handling
- Refresh token support
- Token blacklisting
- Secure key management
"""

import jwt
import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    user_id: str
    username: str
    roles: list
    permissions: list
    iat: int  # Issued at
    exp: int  # Expires at
    aud: str = "claude-agi"  # Audience
    iss: str = "claude-agi-auth"  # Issuer
    jti: Optional[str] = None  # JWT ID for blacklisting


class JWTManager:
    """
    JWT token manager with security features
    
    Provides secure JWT token creation, validation, and management
    with support for token refresh, blacklisting, and role-based claims.
    """
    
    def __init__(self, secret_key: Optional[str] = None, 
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        """
        Initialize JWT manager
        
        Args:
            secret_key: JWT signing secret (auto-generated if None)
            algorithm: JWT signing algorithm
            access_token_expire_minutes: Access token expiration time
            refresh_token_expire_days: Refresh token expiration time
        """
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Initialize secret key
        self.secret_key = secret_key or self._get_secret_key()
        
        # Token blacklist (in production, use Redis or database)
        self._blacklisted_tokens: Set[str] = set()
        
        # Refresh token storage (in production, use database)
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
        logger.info("JWT Manager initialized with algorithm %s", algorithm)
    
    def _get_secret_key(self) -> str:
        """Get or generate JWT secret key"""
        # Try to get from environment first
        secret = os.getenv('JWT_SECRET_KEY')
        if secret:
            return secret
        
        # Generate a secure random key
        key = secrets.token_urlsafe(32)
        logger.warning("Generated new JWT secret key. Set JWT_SECRET_KEY environment variable for production.")
        return key
    
    def create_access_token(self, user_id: str, username: str, 
                          roles: list, permissions: list,
                          expires_delta: Optional[timedelta] = None) -> str:
        """
        Create access token
        
        Args:
            user_id: User identifier
            username: Username
            roles: User roles
            permissions: User permissions
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        # Create token payload
        payload = TokenPayload(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
            iat=int(now.timestamp()),
            exp=int(expire.timestamp()),
            jti=secrets.token_hex(16)  # Unique token ID
        )
        
        # Sign and return token
        token = jwt.encode(asdict(payload), self.secret_key, algorithm=self.algorithm)
        
        logger.debug("Created access token for user %s (expires: %s)", username, expire)
        return token
    
    def create_refresh_token(self, user_id: str, username: str) -> str:
        """
        Create refresh token
        
        Args:
            user_id: User identifier
            username: Username
            
        Returns:
            Refresh token string
        """
        token_id = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Store refresh token info
        self._refresh_tokens[token_id] = {
            'user_id': user_id,
            'username': username,
            'expires': expires,
            'created': datetime.utcnow()
        }
        
        logger.debug("Created refresh token for user %s", username)
        return token_id
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="claude-agi",
                issuer="claude-agi-auth"
            )
            
            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti and jti in self._blacklisted_tokens:
                logger.warning("Attempted use of blacklisted token: %s", jti)
                return None
            
            logger.debug("Verified token for user %s", payload.get('username'))
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", e)
            return None
    
    def refresh_access_token(self, refresh_token: str, 
                           new_roles: Optional[list] = None,
                           new_permissions: Optional[list] = None) -> Optional[str]:
        """
        Create new access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            new_roles: Updated roles (if any)
            new_permissions: Updated permissions (if any)
            
        Returns:
            New access token if refresh token is valid
        """
        # Validate refresh token
        refresh_info = self._refresh_tokens.get(refresh_token)
        if not refresh_info:
            logger.warning("Invalid refresh token used")
            return None
        
        # Check expiration
        if datetime.utcnow() > refresh_info['expires']:
            logger.debug("Refresh token expired for user %s", refresh_info['username'])
            del self._refresh_tokens[refresh_token]
            return None
        
        # Get current user info (in production, fetch from database)
        user_id = refresh_info['user_id']
        username = refresh_info['username']
        
        # Use provided roles/permissions or defaults
        roles = new_roles or []
        permissions = new_permissions or []
        
        # Create new access token
        new_token = self.create_access_token(user_id, username, roles, permissions)
        
        logger.debug("Refreshed access token for user %s", username)
        return new_token
    
    def blacklist_token(self, token: str) -> bool:
        """
        Blacklist a token (logout)
        
        Args:
            token: Token to blacklist
            
        Returns:
            True if successfully blacklisted
        """
        try:
            # Decode to get JTI
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Don't check expiration for blacklisting
            )
            
            jti = payload.get('jti')
            if jti:
                self._blacklisted_tokens.add(jti)
                logger.debug("Blacklisted token with JTI: %s", jti)
                return True
                
        except jwt.InvalidTokenError:
            logger.warning("Attempted to blacklist invalid token")
        
        return False
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke refresh token
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if successfully revoked
        """
        if refresh_token in self._refresh_tokens:
            del self._refresh_tokens[refresh_token]
            logger.debug("Revoked refresh token")
            return True
        
        return False
    
    def cleanup_expired_tokens(self):
        """Clean up expired refresh tokens and blacklisted tokens"""
        now = datetime.utcnow()
        
        # Clean up expired refresh tokens
        expired_refresh = [
            token for token, info in self._refresh_tokens.items()
            if now > info['expires']
        ]
        
        for token in expired_refresh:
            del self._refresh_tokens[token]
        
        if expired_refresh:
            logger.debug("Cleaned up %d expired refresh tokens", len(expired_refresh))
        
        # In production, implement blacklist cleanup based on token expiration
        # For now, blacklist grows indefinitely (acceptable for development)
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed token information without verification
        
        Args:
            token: JWT token
            
        Returns:
            Token information if decodable
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False, "verify_aud": False, "verify_iss": False}
            )
            
            return {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'roles': payload.get('roles', []),
                'permissions': payload.get('permissions', []),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                'is_expired': datetime.utcnow() > datetime.fromtimestamp(payload.get('exp', 0)),
                'jti': payload.get('jti')
            }
            
        except jwt.InvalidTokenError:
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """
        Quick token validity check
        
        Args:
            token: JWT token
            
        Returns:
            True if token is valid and not blacklisted
        """
        return self.verify_token(token) is not None
    
    def get_blacklisted_count(self) -> int:
        """Get number of blacklisted tokens"""
        return len(self._blacklisted_tokens)
    
    def get_refresh_token_count(self) -> int:
        """Get number of active refresh tokens"""
        return len(self._refresh_tokens)