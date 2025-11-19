"""
Unit tests for rate limiting system
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException

from src.security.rate_limiter import (
    RateLimiter,
    RateLimitStrategy,
    RateLimitExceeded,
    create_rate_limit_dependency
)


class TestRateLimiter:
    """Test rate limiter functionality"""

    @pytest.fixture
    async def redis_mock(self):
        """Create mock Redis client"""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock(return_value=True)
        redis.incr = AsyncMock(return_value=1)
        redis.expire = AsyncMock(return_value=True)
        redis.zremrangebyscore = AsyncMock(return_value=0)
        redis.zcard = AsyncMock(return_value=0)
        redis.zadd = AsyncMock(return_value=1)
        redis.pipeline = MagicMock()

        # Mock pipeline
        pipe_mock = MagicMock()
        pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
        pipe_mock.zcard = MagicMock(return_value=pipe_mock)
        pipe_mock.zadd = MagicMock(return_value=pipe_mock)
        pipe_mock.expire = MagicMock(return_value=pipe_mock)
        pipe_mock.execute = AsyncMock(return_value=[0, 0, 1, True])
        redis.pipeline.return_value = pipe_mock

        return redis

    @pytest.fixture
    async def rate_limiter(self, redis_mock):
        """Create rate limiter instance with mock Redis"""
        limiter = RateLimiter()
        limiter.redis_client = redis_mock
        limiter.enabled = True
        return limiter

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert limiter.default_strategy == RateLimitStrategy.SLIDING_WINDOW
        assert limiter.enabled is True

    @pytest.mark.asyncio
    async def test_fixed_window_strategy_success(self, rate_limiter, redis_mock):
        """Test fixed window strategy allows requests within limit"""
        redis_mock.get.return_value = b"5"  # 5 requests so far
        redis_mock.incr.return_value = 6  # Now 6 requests

        # Should not raise (limit is typically 100)
        result = await rate_limiter._fixed_window("test_key", limit=10, window_seconds=60)

        assert result["allowed"] is True
        assert result["remaining"] == 4  # 10 - 6
        redis_mock.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_fixed_window_strategy_exceeded(self, rate_limiter, redis_mock):
        """Test fixed window strategy blocks when limit exceeded"""
        redis_mock.get.return_value = b"10"  # Already at limit
        redis_mock.incr.return_value = 11  # Would exceed

        # Should raise
        with pytest.raises(RateLimitExceeded) as exc_info:
            await rate_limiter._fixed_window("test_key", limit=10, window_seconds=60)

        assert exc_info.value.limit == 10
        assert exc_info.value.window_seconds == 60

    @pytest.mark.asyncio
    async def test_sliding_window_strategy_success(self, rate_limiter, redis_mock):
        """Test sliding window strategy allows requests within limit"""
        # Mock pipeline execution - returns current count of 5
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 5, 1, True]  # 5 current requests

        result = await rate_limiter._sliding_window("test_key", limit=10, window_seconds=60)

        assert result["allowed"] is True
        assert result["remaining"] == 4  # 10 - 6 (5 + new request)

    @pytest.mark.asyncio
    async def test_sliding_window_strategy_exceeded(self, rate_limiter, redis_mock):
        """Test sliding window strategy blocks when limit exceeded"""
        # Mock pipeline execution - returns current count of 10
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 10, 1, True]  # 10 current requests

        # Should raise
        with pytest.raises(RateLimitExceeded):
            await rate_limiter._sliding_window("test_key", limit=10, window_seconds=60)

    @pytest.mark.asyncio
    async def test_token_bucket_strategy_success(self, rate_limiter, redis_mock):
        """Test token bucket strategy allows bursts"""
        redis_mock.get.return_value = b'{"tokens": 5, "last_refill": %f}' % time.time()

        result = await rate_limiter._token_bucket("test_key", limit=10, window_seconds=60)

        assert result["allowed"] is True
        redis_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_bucket_strategy_empty(self, rate_limiter, redis_mock):
        """Test token bucket strategy blocks when no tokens"""
        redis_mock.get.return_value = b'{"tokens": 0, "last_refill": %f}' % time.time()

        with pytest.raises(RateLimitExceeded):
            await rate_limiter._token_bucket("test_key", limit=10, window_seconds=60)

    @pytest.mark.asyncio
    async def test_token_bucket_refill(self, rate_limiter, redis_mock):
        """Test token bucket refills over time"""
        # Set last refill to 30 seconds ago
        past_time = time.time() - 30
        redis_mock.get.return_value = b'{"tokens": 0, "last_refill": %f}' % past_time

        # Should refill some tokens
        result = await rate_limiter._token_bucket("test_key", limit=10, window_seconds=60)

        # Should have refilled and allowed request
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_success(self, rate_limiter, redis_mock):
        """Test check_rate_limit with valid request"""
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 5, 1, True]

        # Should not raise
        await rate_limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, redis_mock):
        """Test check_rate_limit when limit exceeded"""
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 10, 1, True]

        with pytest.raises(RateLimitExceeded) as exc_info:
            await rate_limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

        error = exc_info.value
        assert error.limit == 10
        assert error.window_seconds == 60
        assert error.retry_after > 0

    @pytest.mark.asyncio
    async def test_get_client_identifier_from_api_key(self, rate_limiter):
        """Test extracting client ID from API key"""
        request = Mock(spec=Request)
        request.headers = {"X-API-Key": "sk-test-key-12345"}

        client_id = await rate_limiter.get_client_identifier(request)

        assert client_id == "apikey:sk-test-key-12345"

    @pytest.mark.asyncio
    async def test_get_client_identifier_from_ip(self, rate_limiter):
        """Test extracting client ID from IP address"""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_id = await rate_limiter.get_client_identifier(request)

        assert client_id == "ip:192.168.1.1"

    @pytest.mark.asyncio
    async def test_reset_limit(self, rate_limiter, redis_mock):
        """Test resetting rate limit for a key"""
        redis_mock.delete = AsyncMock(return_value=1)

        await rate_limiter.reset_limit("test_key")

        redis_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_limit_status(self, rate_limiter, redis_mock):
        """Test getting current limit status"""
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 7, 1, True]

        status = await rate_limiter.get_limit_status("test_key", limit=10, window_seconds=60)

        assert status["current"] == 8  # 7 + 1 new
        assert status["limit"] == 10
        assert status["remaining"] == 2
        assert status["window_seconds"] == 60

    @pytest.mark.asyncio
    async def test_disabled_rate_limiter(self, redis_mock):
        """Test rate limiter when disabled"""
        limiter = RateLimiter()
        limiter.redis_client = redis_mock
        limiter.enabled = False

        # Should always allow when disabled
        result = await limiter._fixed_window("test_key", limit=1, window_seconds=60)

        assert result["allowed"] is True
        # Should not call Redis
        redis_mock.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_strategy_selection(self, rate_limiter, redis_mock):
        """Test different strategy selection"""
        pipe_mock = redis_mock.pipeline.return_value
        pipe_mock.execute.return_value = [0, 5, 1, True]

        # Test with different strategies
        for strategy in RateLimitStrategy:
            rate_limiter.default_strategy = strategy
            await rate_limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter, redis_mock):
        """Test handling concurrent requests"""
        pipe_mock = redis_mock.pipeline.return_value

        # Simulate multiple concurrent requests
        async def make_request(request_num):
            pipe_mock.execute.return_value = [0, request_num, 1, True]
            return await rate_limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

        # Make 5 concurrent requests
        results = await asyncio.gather(
            *[make_request(i) for i in range(5)],
            return_exceptions=False
        )

        assert len(results) == 5


class TestRateLimitDependency:
    """Test FastAPI rate limit dependency"""

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_success(self):
        """Test rate limit dependency allows valid request"""
        with patch('src.security.rate_limiter.rate_limiter') as mock_limiter:
            mock_limiter.enabled = True
            mock_limiter.get_client_identifier = AsyncMock(return_value="test_client")
            mock_limiter.check_rate_limit = AsyncMock(return_value=None)

            # Create dependency
            rate_limit_checker = create_rate_limit_dependency(limit=10, window=60)

            # Create mock request
            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/test"

            # Should not raise
            await rate_limit_checker(request)

            mock_limiter.check_rate_limit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_dependency_exceeded(self):
        """Test rate limit dependency blocks exceeded request"""
        with patch('src.security.rate_limiter.rate_limiter') as mock_limiter:
            mock_limiter.enabled = True
            mock_limiter.get_client_identifier = AsyncMock(return_value="test_client")
            mock_limiter.check_rate_limit = AsyncMock(
                side_effect=RateLimitExceeded(10, 60, 30)
            )

            # Create dependency
            rate_limit_checker = create_rate_limit_dependency(limit=10, window=60)

            # Create mock request
            request = Mock(spec=Request)
            request.method = "GET"
            request.url.path = "/test"

            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_checker(request)

            assert exc_info.value.status_code == 429
            assert "rate limit exceeded" in exc_info.value.detail.lower()


class TestRateLimitException:
    """Test RateLimitExceeded exception"""

    def test_exception_creation(self):
        """Test creating RateLimitExceeded exception"""
        exc = RateLimitExceeded(limit=100, window_seconds=60, retry_after=45)

        assert exc.limit == 100
        assert exc.window_seconds == 60
        assert exc.retry_after == 45
        assert "100" in str(exc)
        assert "60" in str(exc)

    def test_exception_message(self):
        """Test exception message format"""
        exc = RateLimitExceeded(limit=50, window_seconds=30, retry_after=15)

        message = str(exc)
        assert "50" in message
        assert "30" in message
        assert "rate limit" in message.lower()
