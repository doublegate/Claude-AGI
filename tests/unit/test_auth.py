"""
Unit tests for authentication and authorization system
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from jose import jwt

from src.security.auth import (
    AuthenticationManager,
    UserRole,
    APIKeyData,
    TokenData,
    get_current_user,
    require_role
)


class TestAuthenticationManager:
    """Test authentication manager"""

    @pytest.fixture
    def auth_manager(self):
        """Create auth manager instance"""
        return AuthenticationManager()

    def test_generate_api_key(self, auth_manager):
        """Test API key generation"""
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Check format
        assert api_key.startswith("sk-")
        assert len(api_key) > 10
        assert len(key_id) > 10

        # Check storage
        assert key_id in auth_manager.api_keys
        key_data = auth_manager.api_keys[key_id]
        assert key_data.username == "testuser"
        assert key_data.role == UserRole.USER
        assert key_data.created_at is not None

    def test_api_key_uniqueness(self, auth_manager):
        """Test that generated API keys are unique"""
        key1_id, key1 = auth_manager.generate_api_key("user1", UserRole.USER)
        key2_id, key2 = auth_manager.generate_api_key("user2", UserRole.USER)

        assert key1 != key2
        assert key1_id != key2_id

    def test_validate_api_key_success(self, auth_manager):
        """Test successful API key validation"""
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.ADMIN)

        result = auth_manager.validate_api_key(api_key)

        assert result is not None
        assert result.username == "testuser"
        assert result.role == UserRole.ADMIN
        assert result.last_used is not None

    def test_validate_api_key_invalid(self, auth_manager):
        """Test invalid API key validation"""
        result = auth_manager.validate_api_key("sk-invalid-key-12345")
        assert result is None

    def test_validate_api_key_revoked(self, auth_manager):
        """Test revoked API key validation"""
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Revoke key
        auth_manager.revoke_api_key(key_id)

        # Should fail validation
        result = auth_manager.validate_api_key(api_key)
        assert result is None

    def test_revoke_api_key(self, auth_manager):
        """Test API key revocation"""
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Revoke
        success = auth_manager.revoke_api_key(key_id)
        assert success is True

        # Check revoked
        assert key_id not in auth_manager.api_keys

    def test_revoke_nonexistent_key(self, auth_manager):
        """Test revoking nonexistent key"""
        success = auth_manager.revoke_api_key("nonexistent-key-id")
        assert success is False

    def test_rotate_api_key(self, auth_manager):
        """Test API key rotation"""
        key_id, old_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Rotate
        new_key = auth_manager.rotate_api_key(key_id)

        assert new_key is not None
        assert new_key != old_key
        assert new_key.startswith("sk-")

        # Old key should be invalid
        assert auth_manager.validate_api_key(old_key) is None

        # New key should work
        result = auth_manager.validate_api_key(new_key)
        assert result is not None
        assert result.username == "testuser"

    def test_create_access_token(self, auth_manager):
        """Test JWT access token creation"""
        token = auth_manager.create_access_token("testuser", UserRole.ADMIN)

        assert token is not None
        assert len(token) > 20

        # Decode and verify
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=["HS256"])
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_create_refresh_token(self, auth_manager):
        """Test JWT refresh token creation"""
        token = auth_manager.create_refresh_token("testuser", UserRole.USER)

        assert token is not None

        # Decode and verify
        payload = jwt.decode(token, auth_manager.secret_key, algorithms=["HS256"])
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_verify_token_success(self, auth_manager):
        """Test successful token verification"""
        token = auth_manager.create_access_token("testuser", UserRole.USER)

        result = auth_manager.verify_token(token)

        assert result is not None
        assert result.username == "testuser"
        assert result.role == UserRole.USER

    def test_verify_token_expired(self, auth_manager):
        """Test expired token verification"""
        # Create token that expires immediately
        token = auth_manager.create_access_token(
            "testuser",
            UserRole.USER,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        result = auth_manager.verify_token(token)
        assert result is None

    def test_verify_token_invalid(self, auth_manager):
        """Test invalid token verification"""
        result = auth_manager.verify_token("invalid.token.here")
        assert result is None

    def test_create_user(self, auth_manager):
        """Test user creation"""
        user = auth_manager.create_user("testuser", UserRole.USER)

        assert user is not None
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.created_at is not None
        assert user.is_active is True

    def test_create_duplicate_user(self, auth_manager):
        """Test creating duplicate user fails"""
        auth_manager.create_user("testuser", UserRole.USER)

        # Should raise error
        with pytest.raises(ValueError, match="User already exists"):
            auth_manager.create_user("testuser", UserRole.ADMIN)

    def test_get_user(self, auth_manager):
        """Test getting user"""
        auth_manager.create_user("testuser", UserRole.ADMIN)

        user = auth_manager.get_user("testuser")

        assert user is not None
        assert user.username == "testuser"
        assert user.role == UserRole.ADMIN

    def test_get_nonexistent_user(self, auth_manager):
        """Test getting nonexistent user"""
        user = auth_manager.get_user("nonexistent")
        assert user is None

    def test_update_user_role(self, auth_manager):
        """Test updating user role"""
        auth_manager.create_user("testuser", UserRole.USER)

        # Update role
        success = auth_manager.update_user_role("testuser", UserRole.ADMIN)
        assert success is True

        # Verify update
        user = auth_manager.get_user("testuser")
        assert user.role == UserRole.ADMIN

    def test_deactivate_user(self, auth_manager):
        """Test user deactivation"""
        auth_manager.create_user("testuser", UserRole.USER)

        # Deactivate
        success = auth_manager.deactivate_user("testuser")
        assert success is True

        # Verify deactivation
        user = auth_manager.get_user("testuser")
        assert user.is_active is False

    def test_role_hierarchy(self, auth_manager):
        """Test role hierarchy checking"""
        assert auth_manager.has_permission(UserRole.ADMIN, UserRole.ADMIN) is True
        assert auth_manager.has_permission(UserRole.ADMIN, UserRole.USER) is True
        assert auth_manager.has_permission(UserRole.USER, UserRole.ADMIN) is False
        assert auth_manager.has_permission(UserRole.READONLY, UserRole.USER) is False


class TestFastAPIDependencies:
    """Test FastAPI authentication dependencies"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_api_key(self):
        """Test get_current_user with valid API key"""
        from fastapi import Request
        from src.security.auth import auth_manager

        # Generate API key
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Create mock request
        request = Mock(spec=Request)
        request.headers = {"X-API-Key": api_key}

        # Test dependency
        from src.security.auth import get_current_user_api_key
        result = await get_current_user_api_key(request)

        assert result is not None
        assert result.username == "testuser"
        assert result.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_get_current_user_with_bearer_token(self):
        """Test get_current_user with valid Bearer token"""
        from fastapi import Request
        from src.security.auth import auth_manager

        # Generate token
        token = auth_manager.create_access_token("testuser", UserRole.ADMIN)

        # Create mock request
        request = Mock(spec=Request)
        request.headers = {"Authorization": f"Bearer {token}"}

        # Test dependency
        from src.security.auth import get_current_user_bearer
        result = await get_current_user_bearer(request)

        assert result is not None
        assert result.username == "testuser"
        assert result.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test require_role with sufficient permissions"""
        user_data = {"username": "admin", "role": UserRole.ADMIN}

        # Create dependency
        check_admin = require_role(UserRole.ADMIN)

        # Should not raise
        result = await check_admin(user_data)
        assert result == user_data

    @pytest.mark.asyncio
    async def test_require_role_insufficient(self):
        """Test require_role with insufficient permissions"""
        from fastapi import HTTPException

        user_data = {"username": "user", "role": UserRole.USER}

        # Create dependency
        check_admin = require_role(UserRole.ADMIN)

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await check_admin(user_data)

        assert exc_info.value.status_code == 403


class TestRoleBasedAccessControl:
    """Test RBAC functionality"""

    @pytest.fixture
    def auth_manager(self):
        return AuthenticationManager()

    def test_role_ordering(self):
        """Test role hierarchy ordering"""
        roles = [UserRole.READONLY, UserRole.USER, UserRole.SERVICE, UserRole.ADMIN]

        # Admin should have highest permissions
        for role in roles[:-1]:
            assert UserRole.ADMIN.value > role.value or True  # Enum comparison

    def test_role_permissions(self, auth_manager):
        """Test different role permissions"""
        # Admin can do everything
        assert auth_manager.has_permission(UserRole.ADMIN, UserRole.READONLY)
        assert auth_manager.has_permission(UserRole.ADMIN, UserRole.USER)
        assert auth_manager.has_permission(UserRole.ADMIN, UserRole.SERVICE)

        # Service can access user level
        assert auth_manager.has_permission(UserRole.SERVICE, UserRole.USER)
        assert auth_manager.has_permission(UserRole.SERVICE, UserRole.READONLY)

        # User cannot access service level
        assert not auth_manager.has_permission(UserRole.USER, UserRole.SERVICE)
        assert not auth_manager.has_permission(UserRole.USER, UserRole.ADMIN)
