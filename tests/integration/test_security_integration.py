"""
Integration tests for security features (Options C)
Tests authentication, rate limiting, and validation working together
"""

import pytest
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import time

from src.security.auth import (
    AuthenticationManager,
    UserRole,
    get_current_user,
    require_role
)
from src.security.rate_limiter import (
    RateLimiter,
    create_rate_limit_dependency,
    RateLimitExceeded
)
from src.security.validation import (
    SecureThoughtRequest,
    SecureMemoryQuery,
    validate_input,
    get_security_headers
)


class TestAuthenticationIntegration:
    """Test authentication flow integration"""

    @pytest.fixture
    def auth_manager(self):
        return AuthenticationManager()

    @pytest.fixture
    def app(self, auth_manager):
        """Create test FastAPI app"""
        app = FastAPI()

        @app.get("/public")
        async def public_endpoint():
            return {"message": "public"}

        @app.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"message": "protected", "user": user["username"]}

        @app.get("/admin")
        async def admin_endpoint(user: dict = Depends(require_role(UserRole.ADMIN))):
            return {"message": "admin", "user": user["username"]}

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_public_endpoint_no_auth(self, client):
        """Test public endpoint doesn't require auth"""
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json()["message"] == "public"

    def test_protected_endpoint_no_auth(self, client):
        """Test protected endpoint requires auth"""
        response = client.get("/protected")
        assert response.status_code == 401

    def test_protected_endpoint_with_api_key(self, client, auth_manager):
        """Test protected endpoint with valid API key"""
        # Generate API key
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Access protected endpoint
        response = client.get("/protected", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        assert response.json()["user"] == "testuser"

    def test_protected_endpoint_with_jwt(self, client, auth_manager):
        """Test protected endpoint with valid JWT token"""
        # Generate JWT token
        token = auth_manager.create_access_token("testuser", UserRole.USER)

        # Access protected endpoint
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["user"] == "testuser"

    def test_admin_endpoint_user_role_denied(self, client, auth_manager):
        """Test admin endpoint denies USER role"""
        # Generate user token
        token = auth_manager.create_access_token("testuser", UserRole.USER)

        # Try to access admin endpoint
        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_admin_endpoint_admin_role_allowed(self, client, auth_manager):
        """Test admin endpoint allows ADMIN role"""
        # Generate admin token
        token = auth_manager.create_access_token("admin", UserRole.ADMIN)

        # Access admin endpoint
        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["user"] == "admin"

    def test_revoked_key_denied(self, client, auth_manager):
        """Test revoked API key is denied"""
        # Generate and revoke key
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)
        auth_manager.revoke_api_key(key_id)

        # Try to use revoked key
        response = client.get("/protected", headers={"X-API-Key": api_key})
        assert response.status_code == 401


class TestRateLimitingIntegration:
    """Test rate limiting integration"""

    @pytest.fixture
    async def rate_limiter(self):
        """Create rate limiter with mock Redis"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True
        return limiter

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting"""
        app = FastAPI()

        # Mock rate limiter
        async def mock_rate_limit(request):
            # Simple in-memory rate limiting for testing
            if not hasattr(mock_rate_limit, 'counts'):
                mock_rate_limit.counts = {}

            key = request.client.host
            current_time = time.time()
            window_start = int(current_time / 60) * 60

            if key not in mock_rate_limit.counts:
                mock_rate_limit.counts[key] = {}

            if window_start not in mock_rate_limit.counts[key]:
                mock_rate_limit.counts[key] = {window_start: 0}

            mock_rate_limit.counts[key][window_start] += 1

            if mock_rate_limit.counts[key][window_start] > 5:  # 5 requests per minute
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

        @app.get("/limited", dependencies=[Depends(mock_rate_limit)])
        async def limited_endpoint():
            return {"message": "success"}

        return app

    @pytest.fixture
    def client(self, app_with_rate_limit):
        return TestClient(app_with_rate_limit)

    def test_rate_limit_allows_within_limit(self, client):
        """Test requests within limit are allowed"""
        # Make 5 requests (within limit)
        for i in range(5):
            response = client.get("/limited")
            assert response.status_code == 200

    def test_rate_limit_blocks_over_limit(self, client):
        """Test requests over limit are blocked"""
        # Make 6 requests (over limit of 5)
        for i in range(6):
            response = client.get("/limited")

        # Last request should be rate limited
        assert response.status_code == 429


class TestValidationIntegration:
    """Test input validation integration"""

    @pytest.fixture
    def app(self):
        """Create app with validation"""
        app = FastAPI()

        @app.post("/thought")
        async def create_thought(request: SecureThoughtRequest):
            return {"status": "created", "stream": request.stream_type}

        @app.post("/memory")
        async def query_memory(request: SecureMemoryQuery):
            return {"status": "queried", "query": request.query}

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_valid_thought_request(self, client):
        """Test valid thought request is accepted"""
        response = client.post("/thought", json={
            "stream_type": "PRIMARY",
            "context": {"key": "value"}
        })
        assert response.status_code == 200
        assert response.json()["stream"] == "PRIMARY"

    def test_invalid_stream_type_rejected(self, client):
        """Test invalid stream type is rejected"""
        response = client.post("/thought", json={
            "stream_type": "INVALID",
            "context": {}
        })
        assert response.status_code == 422  # Validation error

    def test_sql_injection_blocked(self, client):
        """Test SQL injection in context is blocked"""
        response = client.post("/thought", json={
            "stream_type": "PRIMARY",
            "context": {"query": "1' OR '1'='1"}
        })
        # Should be blocked by validator
        assert response.status_code in [400, 422]

    def test_valid_memory_query(self, client):
        """Test valid memory query is accepted"""
        response = client.post("/memory", json={
            "query": "search term",
            "limit": 10
        })
        assert response.status_code == 200

    def test_memory_query_limit_validation(self, client):
        """Test memory query limit is validated"""
        response = client.post("/memory", json={
            "query": "test",
            "limit": 1000  # Over limit
        })
        assert response.status_code == 422


class TestFullSecurityStack:
    """Test complete security stack working together"""

    @pytest.fixture
    def auth_manager(self):
        return AuthenticationManager()

    @pytest.fixture
    def app(self, auth_manager):
        """Create app with full security stack"""
        app = FastAPI()

        # Add security headers middleware
        @app.middleware("http")
        async def add_security_headers(request, call_next):
            response = await call_next(request)
            for header, value in get_security_headers().items():
                response.headers[header] = value
            return response

        @app.post("/secure/thought")
        async def secure_thought(
            request: SecureThoughtRequest,
            user: dict = Depends(get_current_user)
        ):
            return {
                "status": "created",
                "user": user["username"],
                "stream": request.stream_type
            }

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_full_stack_authenticated_valid_request(self, client, auth_manager):
        """Test complete flow: auth + validation"""
        # Generate token
        token = auth_manager.create_access_token("testuser", UserRole.USER)

        # Make valid request
        response = client.post(
            "/secure/thought",
            json={
                "stream_type": "PRIMARY",
                "context": {"key": "value"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["user"] == "testuser"
        assert response.json()["stream"] == "PRIMARY"

        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_full_stack_no_auth(self, client):
        """Test request without auth is rejected"""
        response = client.post(
            "/secure/thought",
            json={
                "stream_type": "PRIMARY",
                "context": {}
            }
        )
        assert response.status_code == 401

    def test_full_stack_invalid_input(self, client, auth_manager):
        """Test authenticated request with invalid input"""
        # Generate token
        token = auth_manager.create_access_token("testuser", UserRole.USER)

        # Make invalid request
        response = client.post(
            "/secure/thought",
            json={
                "stream_type": "INVALID_TYPE",
                "context": {}
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422


class TestPerformanceBaselines:
    """Test performance characteristics of security features"""

    @pytest.fixture
    def auth_manager(self):
        return AuthenticationManager()

    def test_api_key_validation_performance(self, auth_manager):
        """Test API key validation is fast (< 1ms)"""
        # Generate key
        key_id, api_key = auth_manager.generate_api_key("testuser", UserRole.USER)

        # Measure validation time
        start = time.time()
        for _ in range(100):
            auth_manager.validate_api_key(api_key)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        assert avg_time < 0.001  # Less than 1ms per validation

    def test_jwt_generation_performance(self, auth_manager):
        """Test JWT generation is fast (< 2ms)"""
        start = time.time()
        for _ in range(100):
            auth_manager.create_access_token("testuser", UserRole.USER)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        assert avg_time < 0.002  # Less than 2ms per token

    def test_input_validation_performance(self):
        """Test input validation is fast (< 1ms)"""
        test_string = "normal user input with some content"

        start = time.time()
        for _ in range(100):
            validate_input(test_string)
        elapsed = time.time() - start

        avg_time = elapsed / 100
        assert avg_time < 0.001  # Less than 1ms per validation
