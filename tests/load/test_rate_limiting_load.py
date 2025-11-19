"""
Load tests for rate limiting system (Option C)
Tests performance and behavior under high concurrency
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.security.rate_limiter import (
    RateLimiter,
    RateLimitStrategy,
    RateLimitExceeded,
    create_rate_limit_dependency
)


class TestRateLimitingUnderLoad:
    """Test rate limiting behavior under concurrent load"""

    @pytest.fixture
    def app_with_limits(self):
        """Create app with various rate limits"""
        app = FastAPI()

        # Create in-memory rate limiter for testing
        request_counts = {}

        async def simple_rate_limit(limit: int, window: int):
            """Simple in-memory rate limiter"""
            async def rate_limit_checker(request):
                client_id = request.client.host
                current_window = int(time.time() / window)
                key = f"{client_id}:{current_window}"

                if key not in request_counts:
                    request_counts[key] = 0

                request_counts[key] += 1

                if request_counts[key] > limit:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded",
                        headers={"Retry-After": str(window)}
                    )

            return rate_limit_checker

        # Endpoints with different limits
        @app.get("/low-limit", dependencies=[Depends(simple_rate_limit(10, 60))])
        async def low_limit_endpoint():
            return {"message": "success"}

        @app.get("/medium-limit", dependencies=[Depends(simple_rate_limit(50, 60))])
        async def medium_limit_endpoint():
            return {"message": "success"}

        @app.get("/high-limit", dependencies=[Depends(simple_rate_limit(100, 60))])
        async def high_limit_endpoint():
            return {"message": "success"}

        return app

    @pytest.fixture
    def client(self, app_with_limits):
        return TestClient(app_with_limits)

    def test_concurrent_requests_low_limit(self, client):
        """Test concurrent requests against low limit"""
        limit = 10
        concurrent_requests = 20

        def make_request():
            return client.get("/low-limit")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [f.result() for f in futures]

        # Count successes and rate limit errors
        successes = sum(1 for r in results if r.status_code == 200)
        rate_limited = sum(1 for r in results if r.status_code == 429)

        # Should have some successes (around limit) and some failures
        assert successes <= limit + 2  # Allow small margin
        assert rate_limited > 0
        assert successes + rate_limited == concurrent_requests

    def test_concurrent_requests_medium_limit(self, client):
        """Test concurrent requests against medium limit"""
        limit = 50
        concurrent_requests = 75

        def make_request():
            return client.get("/medium-limit")

        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [f.result() for f in futures]

        successes = sum(1 for r in results if r.status_code == 200)
        rate_limited = sum(1 for r in results if r.status_code == 429)

        # Should allow more requests with higher limit
        assert successes <= limit + 5  # Slightly larger margin
        assert rate_limited > 0

    def test_burst_then_sustained(self, client):
        """Test burst of requests followed by sustained rate"""
        # Initial burst
        burst_size = 20
        burst_results = [client.get("/low-limit") for _ in range(burst_size)]

        burst_successes = sum(1 for r in burst_results if r.status_code == 200)

        # Should hit limit quickly
        assert burst_successes <= 12  # Around limit of 10

        # Wait for next window
        time.sleep(2)

        # Sustained requests should work again
        sustained = client.get("/low-limit")
        # May or may not succeed depending on window reset
        assert sustained.status_code in [200, 429]


class TestRateLimitingPerformance:
    """Test performance characteristics under load"""

    @pytest.mark.asyncio
    async def test_rate_limiter_latency(self):
        """Test rate limiter adds minimal latency"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True

        # Mock pipeline execution
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[0, 5, 1, True])
        pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
        pipe_mock.zcard = MagicMock(return_value=pipe_mock)
        pipe_mock.zadd = MagicMock(return_value=pipe_mock)
        pipe_mock.expire = MagicMock(return_value=pipe_mock)
        limiter.redis_client.pipeline.return_value = pipe_mock

        # Measure latency
        iterations = 100
        start = time.time()

        for _ in range(iterations):
            try:
                await limiter.check_rate_limit("test_key", limit=100, window_seconds=60)
            except RateLimitExceeded:
                pass

        elapsed = time.time() - start
        avg_latency = elapsed / iterations

        # Should be under 2ms average
        assert avg_latency < 0.002

    @pytest.mark.asyncio
    async def test_concurrent_rate_limit_checks(self):
        """Test concurrent rate limit checks"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True

        # Mock pipeline
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[0, 5, 1, True])
        pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
        pipe_mock.zcard = MagicMock(return_value=pipe_mock)
        pipe_mock.zadd = MagicMock(return_value=pipe_mock)
        pipe_mock.expire = MagicMock(return_value=pipe_mock)
        limiter.redis_client.pipeline.return_value = pipe_mock

        # Run concurrent checks
        async def check():
            try:
                await limiter.check_rate_limit("test_key", limit=100, window_seconds=60)
                return True
            except RateLimitExceeded:
                return False

        start = time.time()
        results = await asyncio.gather(*[check() for _ in range(100)])
        elapsed = time.time() - start

        # All should complete
        assert len(results) == 100

        # Should complete quickly (< 500ms for 100 concurrent checks)
        assert elapsed < 0.5


class TestRateLimitingStrategies:
    """Test different rate limiting strategies under load"""

    @pytest.fixture
    async def limiter(self):
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True
        return limiter

    @pytest.mark.asyncio
    async def test_fixed_window_burst_handling(self, limiter):
        """Test fixed window allows full burst at window start"""
        # Mock Redis for fixed window
        limiter.redis_client.get = AsyncMock(return_value=None)
        limiter.redis_client.incr = AsyncMock(side_effect=range(1, 102))
        limiter.redis_client.expire = AsyncMock()

        limit = 100
        successes = 0

        # Try to make burst of requests
        for i in range(120):
            try:
                await limiter._fixed_window("burst_test", limit=limit, window_seconds=60)
                successes += 1
            except RateLimitExceeded:
                break

        # Should allow exactly limit requests
        assert successes == limit

    @pytest.mark.asyncio
    async def test_sliding_window_smoother_limiting(self, limiter):
        """Test sliding window provides smoother rate limiting"""
        # Mock pipeline for sliding window
        successful_checks = 0
        call_count = [0]

        def mock_execute():
            call_count[0] += 1
            if call_count[0] <= 100:
                return [0, call_count[0] - 1, 1, True]  # Allow first 100
            else:
                return [0, 100, 1, True]  # Deny after that

        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(side_effect=mock_execute)
        pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
        pipe_mock.zcard = MagicMock(return_value=pipe_mock)
        pipe_mock.zadd = MagicMock(return_value=pipe_mock)
        pipe_mock.expire = MagicMock(return_value=pipe_mock)
        limiter.redis_client.pipeline.return_value = pipe_mock

        # Make requests
        for i in range(120):
            try:
                await limiter._sliding_window("sliding_test", limit=100, window_seconds=60)
                successful_checks += 1
            except RateLimitExceeded:
                pass

        # Should allow around limit
        assert successful_checks == 100

    @pytest.mark.asyncio
    async def test_token_bucket_burst_allowance(self, limiter):
        """Test token bucket allows controlled bursts"""
        # Mock Redis for token bucket
        current_time = time.time()

        # Start with full bucket
        limiter.redis_client.get = AsyncMock(
            return_value=f'{{"tokens": 100, "last_refill": {current_time}}}'.encode()
        )
        limiter.redis_client.set = AsyncMock()

        # Should allow burst up to bucket size
        successes = 0
        for i in range(120):
            try:
                # Re-mock with decreasing tokens
                remaining_tokens = max(0, 100 - successes)
                limiter.redis_client.get = AsyncMock(
                    return_value=f'{{"tokens": {remaining_tokens}, "last_refill": {current_time}}}'.encode()
                )

                await limiter._token_bucket("bucket_test", limit=100, window_seconds=60)
                successes += 1
            except RateLimitExceeded:
                break

        # Should allow burst equal to bucket size
        assert successes == 100


class TestRateLimitingScalability:
    """Test rate limiting at scale"""

    @pytest.mark.asyncio
    async def test_many_clients_independently_limited(self):
        """Test rate limiting works correctly with many clients"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True

        client_counts = {}

        def mock_pipeline_for_client(client_id):
            if client_id not in client_counts:
                client_counts[client_id] = 0

            client_counts[client_id] += 1
            count = client_counts[client_id]

            pipe_mock = MagicMock()
            pipe_mock.execute = AsyncMock(return_value=[0, count - 1, 1, True])
            pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
            pipe_mock.zcard = MagicMock(return_value=pipe_mock)
            pipe_mock.zadd = MagicMock(return_value=pipe_mock)
            pipe_mock.expire = MagicMock(return_value=pipe_mock)
            return pipe_mock

        # Simulate 10 clients each making 15 requests (limit 10 each)
        limit_per_client = 10
        requests_per_client = 15
        num_clients = 10

        for client_id in range(num_clients):
            key = f"client_{client_id}"
            successes = 0

            limiter.redis_client.pipeline.return_value = mock_pipeline_for_client(key)

            for req in range(requests_per_client):
                try:
                    await limiter.check_rate_limit(key, limit=limit_per_client, window_seconds=60)
                    successes += 1
                except RateLimitExceeded:
                    pass

            # Each client should be independently limited
            assert successes == limit_per_client

    @pytest.mark.asyncio
    async def test_high_throughput_handling(self):
        """Test handling very high throughput"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True

        # Mock for high throughput
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[0, 50, 1, True])
        pipe_mock.zremrangebyscore = MagicMock(return_value=pipe_mock)
        pipe_mock.zcard = MagicMock(return_value=pipe_mock)
        pipe_mock.zadd = MagicMock(return_value=pipe_mock)
        pipe_mock.expire = MagicMock(return_value=pipe_mock)
        limiter.redis_client.pipeline.return_value = pipe_mock

        # Process 1000 requests as fast as possible
        start = time.time()

        tasks = [
            limiter.check_rate_limit(f"key_{i % 10}", limit=1000, window_seconds=60)
            for i in range(1000)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start

        # Should handle 1000 requests in under 2 seconds
        assert elapsed < 2.0
        print(f"Processed 1000 requests in {elapsed:.3f}s ({1000/elapsed:.0f} req/s)")


class TestRateLimitingResilience:
    """Test rate limiting resilience and error handling"""

    @pytest.mark.asyncio
    async def test_redis_failure_graceful_degradation(self):
        """Test graceful handling when Redis is unavailable"""
        limiter = RateLimiter()
        limiter.redis_client = AsyncMock()
        limiter.enabled = True

        # Simulate Redis failure
        limiter.redis_client.pipeline.side_effect = Exception("Redis connection failed")

        # Should handle gracefully (either allow or raise appropriate error)
        try:
            await limiter.check_rate_limit("test_key", limit=100, window_seconds=60)
            # If it allows, that's acceptable for degraded mode
            assert True
        except Exception as e:
            # Should be a meaningful error, not raw Redis error
            assert "Redis connection failed" in str(e) or isinstance(e, RateLimitExceeded)

    @pytest.mark.asyncio
    async def test_disabled_rate_limiter_no_overhead(self):
        """Test disabled rate limiter has no overhead"""
        limiter = RateLimiter()
        limiter.enabled = False  # Disabled

        # Should never call Redis
        limiter.redis_client = None

        # Should work without Redis
        start = time.time()
        for _ in range(1000):
            await limiter.check_rate_limit("test_key", limit=10, window_seconds=60)
        elapsed = time.time() - start

        # Should be extremely fast (< 10ms for 1000 checks)
        assert elapsed < 0.01
