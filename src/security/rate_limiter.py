"""
Rate Limiting System for Claude-AGI
====================================

Implements Redis-based rate limiting with multiple strategies:
- Fixed window
- Sliding window
- Token bucket
- Per-user/IP/endpoint limits
"""

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis

import logging

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""

    def __init__(
        self,
        limit: int,
        window: int,
        retry_after: int,
        detail: str = "Rate limit exceeded"
    ):
        super().__init__(
            status_code=429,
            detail=detail,
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window),
                "Retry-After": str(retry_after)
            }
        )


class RateLimiter:
    """
    Redis-based distributed rate limiter

    Supports multiple strategies and scopes (user, IP, endpoint, global)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    ):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL
            strategy: Rate limiting strategy to use
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/1"  # Use DB 1 for rate limiting
        )
        self.strategy = strategy
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Rate limiting disabled.")
            self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """
        Check rate limit for a given key

        Args:
            key: Unique identifier (user, IP, etc.)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Dict with rate limit info

        Raises:
            RateLimitExceeded if limit exceeded
        """
        if not self.redis_client:
            # Rate limiting disabled
            return {
                "allowed": True,
                "remaining": limit,
                "reset": int(time.time()) + window_seconds
            }

        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window(key, limit, window_seconds)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window(key, limit, window_seconds)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket(key, limit, window_seconds)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    async def _fixed_window(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """
        Fixed window rate limiting

        Simple counter that resets at fixed intervals
        """
        # Get current window
        now = int(time.time())
        window_start = (now // window_seconds) * window_seconds
        rate_key = f"rate_limit:fixed:{key}:{window_start}"

        # Increment counter
        count = await self.redis_client.incr(rate_key)

        # Set expiration on first request
        if count == 1:
            await self.redis_client.expire(rate_key, window_seconds)

        # Calculate reset time
        reset = window_start + window_seconds
        remaining = max(0, limit - count)

        if count > limit:
            retry_after = reset - now
            raise RateLimitExceeded(
                limit=limit,
                window=window_seconds,
                retry_after=retry_after,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
            )

        return {
            "allowed": True,
            "remaining": remaining,
            "reset": reset,
            "current": count
        }

    async def _sliding_window(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """
        Sliding window rate limiting

        More accurate than fixed window, prevents bursts at window boundaries
        """
        now = time.time()
        rate_key = f"rate_limit:sliding:{key}"

        # Use sorted set with timestamps as scores
        pipe = self.redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(rate_key, 0, now - window_seconds)

        # Count current requests in window
        pipe.zcard(rate_key)

        # Add current request
        pipe.zadd(rate_key, {str(now): now})

        # Set expiration
        pipe.expire(rate_key, window_seconds)

        results = await pipe.execute()
        count = results[1] + 1  # +1 for current request

        remaining = max(0, limit - count)
        reset = int(now + window_seconds)

        if count > limit:
            # Remove the request we just added since it's denied
            await self.redis_client.zrem(rate_key, str(now))

            retry_after = window_seconds
            raise RateLimitExceeded(
                limit=limit,
                window=window_seconds,
                retry_after=retry_after,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
            )

        return {
            "allowed": True,
            "remaining": remaining,
            "reset": reset,
            "current": count
        }

    async def _token_bucket(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """
        Token bucket rate limiting

        Allows bursts while maintaining average rate
        """
        now = time.time()
        rate_key = f"rate_limit:bucket:{key}"

        # Lua script for atomic token bucket
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1]) or limit
        local last_update = tonumber(bucket[2]) or now

        -- Refill tokens based on time passed
        local time_passed = now - last_update
        local refill = (time_passed / window) * limit
        tokens = math.min(limit, tokens + refill)

        -- Try to consume a token
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, window * 2)
            return {1, tokens}
        else
            return {0, tokens}
        end
        """

        result = await self.redis_client.eval(
            lua_script,
            1,
            rate_key,
            limit,
            window_seconds,
            now
        )

        allowed = result[0] == 1
        tokens_remaining = result[1]

        reset = int(now + window_seconds)

        if not allowed:
            retry_after = int((1 - tokens_remaining) * window_seconds / limit)
            raise RateLimitExceeded(
                limit=limit,
                window=window_seconds,
                retry_after=retry_after,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
            )

        return {
            "allowed": True,
            "remaining": int(tokens_remaining),
            "reset": reset,
            "tokens": tokens_remaining
        }

    async def get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting

        Priority: User ID > API Key > IP Address
        """
        # Check for authenticated user
        if hasattr(request.state, "user"):
            user = request.state.user
            if isinstance(user, dict) and "username" in user:
                return f"user:{user['username']}"

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Use hash of API key
            import hashlib
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"apikey:{key_hash}"

        # Fall back to IP address
        # Handle proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"


# Global rate limiter instance
rate_limiter = RateLimiter()


# FastAPI Middleware & Dependencies

async def rate_limit_dependency(
    request: Request,
    limit: int = 100,
    window: int = 60  # 60 seconds = 1 minute
):
    """
    FastAPI dependency for rate limiting

    Use in routes:
        @app.get("/api/endpoint")
        async def endpoint(rate_limit=Depends(rate_limit_dependency)):
    """
    if not rate_limiter.redis_client:
        # Rate limiting disabled
        return

    # Get client identifier
    client_id = await rate_limiter.get_client_identifier(request)

    # Get endpoint
    endpoint = f"{request.method}:{request.url.path}"
    key = f"{client_id}:{endpoint}"

    # Check rate limit
    try:
        result = await rate_limiter.check_rate_limit(key, limit, window)

        # Add headers to response
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(result["remaining"]),
            "X-RateLimit-Reset": str(result["reset"])
        }

    except RateLimitExceeded as e:
        # Add rate limit headers
        raise e


def create_rate_limit_dependency(limit: int, window: int = 60):
    """
    Factory for creating rate limit dependencies with custom limits

    Use in routes:
        strict_limit = create_rate_limit_dependency(limit=10, window=60)

        @app.post("/expensive-operation")
        async def expensive(rate_limit=Depends(strict_limit)):
    """
    async def rate_limit_checker(request: Request):
        return await rate_limit_dependency(request, limit, window)

    return rate_limit_checker


# Endpoint-specific limits
EndpointLimits = {
    "health_check": create_rate_limit_dependency(limit=1000, window=60),
    "thought_generation": create_rate_limit_dependency(limit=20, window=60),
    "memory_query": create_rate_limit_dependency(limit=100, window=60),
    "conversation": create_rate_limit_dependency(limit=50, window=60),
    "memory_consolidation": create_rate_limit_dependency(limit=10, window=60),
}
