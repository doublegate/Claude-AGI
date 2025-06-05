"""
Connection Pool Manager for Memory System

Manages connection pools for Redis and PostgreSQL with automatic
reconnection, health monitoring, and connection recycling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncpg
import redis.asyncio as redis
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from ..core.service_registry import ServiceRegistry
from ..core.event_bus import EventBus


class ConnectionHealth(Enum):
    """Connection health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


@dataclass
class ConnectionStats:
    """Statistics for a connection pool"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    health_checks_passed: int = 0
    health_checks_failed: int = 0


@dataclass
class PoolConfig:
    """Configuration for connection pools"""
    # PostgreSQL settings
    postgres_min_size: int = 10
    postgres_max_size: int = 20
    postgres_max_queries: int = 50000
    postgres_max_inactive_connection_lifetime: float = 300.0
    postgres_timeout: float = 60.0
    postgres_command_timeout: float = 60.0
    postgres_statement_cache_size: int = 1024
    
    # Redis settings
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_socket_connect_timeout: float = 5.0
    redis_socket_keepalive: bool = True
    redis_socket_keepalive_options: Dict[int, int] = field(default_factory=dict)
    redis_health_check_interval: int = 30
    
    # General settings
    reconnect_interval: float = 5.0
    max_reconnect_attempts: int = 10
    health_check_interval: float = 30.0
    connection_retry_backoff: float = 2.0


class ConnectionPoolManager:
    """
    Manages database connection pools with health monitoring and auto-reconnection.
    """
    
    def __init__(
        self,
        postgres_dsn: Optional[str] = None,
        redis_url: Optional[str] = None,
        config: Optional[PoolConfig] = None,
        service_registry: Optional[ServiceRegistry] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.postgres_dsn = postgres_dsn
        self.redis_url = redis_url
        self.config = config or PoolConfig()
        self.service_registry = service_registry
        self.event_bus = event_bus
        
        self.logger = logging.getLogger(__name__)
        
        # Connection pools
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._redis_client: Optional[redis.Redis] = None
        
        # Health monitoring
        self._postgres_health = ConnectionHealth.DISCONNECTED
        self._redis_health = ConnectionHealth.DISCONNECTED
        self._postgres_stats = ConnectionStats()
        self._redis_stats = ConnectionStats()
        
        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        
        # Locks
        self._postgres_lock = asyncio.Lock()
        self._redis_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection pools and start monitoring"""
        self.logger.info("Initializing Connection Pool Manager")
        
        # Create initial connections
        await self._create_postgres_pool()
        await self._create_redis_pool()
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "connection_pool_manager",
                self,
                {
                    "postgres_health": self._postgres_health.value,
                    "redis_health": self._redis_health.value
                }
            )
    
    async def shutdown(self):
        """Shutdown all connection pools gracefully"""
        self.logger.info("Shutting down Connection Pool Manager")
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()
        
        # Close connections
        await self._close_postgres_pool()
        await self._close_redis_pool()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("connection_pool_manager")
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """
        Get a PostgreSQL connection from the pool.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if not self._postgres_pool:
            raise ConnectionError("PostgreSQL pool not initialized")
        
        if self._postgres_health == ConnectionHealth.UNHEALTHY:
            raise ConnectionError("PostgreSQL connection unhealthy")
        
        start_time = datetime.now()
        connection = None
        
        try:
            async with self._postgres_lock:
                self._postgres_stats.active_connections += 1
            
            connection = await self._postgres_pool.acquire()
            yield connection
            
            # Update statistics
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            self._postgres_stats.total_queries += 1
            self._update_avg_query_time(self._postgres_stats, query_time)
            
        except Exception as e:
            self._postgres_stats.failed_queries += 1
            self._postgres_stats.last_error = str(e)
            self._postgres_stats.last_error_time = datetime.now()
            self.logger.error(f"PostgreSQL query failed: {e}")
            raise
            
        finally:
            if connection:
                await self._postgres_pool.release(connection)
            
            async with self._postgres_lock:
                self._postgres_stats.active_connections -= 1
    
    def get_redis_client(self) -> redis.Redis:
        """
        Get Redis client instance.
        
        Returns:
            redis.Redis: Redis client
        """
        if not self._redis_client:
            raise ConnectionError("Redis client not initialized")
        
        if self._redis_health == ConnectionHealth.UNHEALTHY:
            raise ConnectionError("Redis connection unhealthy")
        
        return self._redis_client
    
    async def execute_postgres_query(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """
        Execute a PostgreSQL query with connection management.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            List of query results
        """
        timeout = timeout or self.config.postgres_command_timeout
        
        async with self.get_postgres_connection() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def execute_redis_command(self, command: str, *args, **kwargs) -> Any:
        """
        Execute a Redis command with error handling.
        
        Args:
            command: Redis command name
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            Command result
        """
        client = self.get_redis_client()
        start_time = datetime.now()
        
        try:
            # Get command method
            cmd = getattr(client, command)
            result = await cmd(*args, **kwargs)
            
            # Update statistics
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            self._redis_stats.total_queries += 1
            self._update_avg_query_time(self._redis_stats, query_time)
            
            return result
            
        except Exception as e:
            self._redis_stats.failed_queries += 1
            self._redis_stats.last_error = str(e)
            self._redis_stats.last_error_time = datetime.now()
            self.logger.error(f"Redis command '{command}' failed: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all connection pools.
        
        Returns:
            Dict with health information
        """
        return {
            "postgres": {
                "health": self._postgres_health.value,
                "stats": {
                    "total_connections": self._postgres_stats.total_connections,
                    "active_connections": self._postgres_stats.active_connections,
                    "idle_connections": self._postgres_stats.idle_connections,
                    "failed_connections": self._postgres_stats.failed_connections,
                    "total_queries": self._postgres_stats.total_queries,
                    "failed_queries": self._postgres_stats.failed_queries,
                    "avg_query_time_ms": round(self._postgres_stats.avg_query_time_ms, 2),
                    "last_error": self._postgres_stats.last_error,
                    "health_check_ratio": self._calculate_health_ratio(self._postgres_stats)
                }
            },
            "redis": {
                "health": self._redis_health.value,
                "stats": {
                    "total_queries": self._redis_stats.total_queries,
                    "failed_queries": self._redis_stats.failed_queries,
                    "avg_query_time_ms": round(self._redis_stats.avg_query_time_ms, 2),
                    "last_error": self._redis_stats.last_error,
                    "health_check_ratio": self._calculate_health_ratio(self._redis_stats)
                }
            }
        }
    
    # Private helper methods
    
    async def _create_postgres_pool(self):
        """Create PostgreSQL connection pool"""
        if not self.postgres_dsn:
            self.logger.warning("PostgreSQL DSN not provided, skipping pool creation")
            return
        
        try:
            self.logger.info("Creating PostgreSQL connection pool")
            
            self._postgres_pool = await asyncpg.create_pool(
                self.postgres_dsn,
                min_size=self.config.postgres_min_size,
                max_size=self.config.postgres_max_size,
                max_queries=self.config.postgres_max_queries,
                max_inactive_connection_lifetime=self.config.postgres_max_inactive_connection_lifetime,
                timeout=self.config.postgres_timeout,
                command_timeout=self.config.postgres_command_timeout,
                statement_cache_size=self.config.postgres_statement_cache_size
            )
            
            # Test connection
            async with self._postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            self._postgres_health = ConnectionHealth.HEALTHY
            self._postgres_stats.total_connections = self._postgres_pool.get_size()
            self._postgres_stats.idle_connections = self._postgres_pool.get_idle_size()
            
            self.logger.info("PostgreSQL pool created successfully")
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish(
                    "database.postgres.connected",
                    {"pool_size": self._postgres_pool.get_size()}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL pool: {e}")
            self._postgres_health = ConnectionHealth.UNHEALTHY
            self._postgres_stats.failed_connections += 1
            raise
    
    async def _create_redis_pool(self):
        """Create Redis connection pool"""
        if not self.redis_url:
            self.logger.warning("Redis URL not provided, skipping pool creation")
            return
        
        try:
            self.logger.info("Creating Redis connection pool")
            
            # Create connection pool
            self._redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.config.redis_max_connections,
                socket_timeout=self.config.redis_socket_timeout,
                socket_connect_timeout=self.config.redis_socket_connect_timeout,
                socket_keepalive=self.config.redis_socket_keepalive,
                socket_keepalive_options=self.config.redis_socket_keepalive_options,
                health_check_interval=self.config.redis_health_check_interval
            )
            
            # Create client
            self._redis_client = redis.Redis(connection_pool=self._redis_pool)
            
            # Test connection
            await self._redis_client.ping()
            
            self._redis_health = ConnectionHealth.HEALTHY
            
            self.logger.info("Redis pool created successfully")
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish(
                    "database.redis.connected",
                    {"max_connections": self.config.redis_max_connections}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to create Redis pool: {e}")
            self._redis_health = ConnectionHealth.UNHEALTHY
            self._redis_stats.failed_connections += 1
            raise
    
    async def _close_postgres_pool(self):
        """Close PostgreSQL connection pool"""
        if self._postgres_pool:
            try:
                await self._postgres_pool.close()
                self._postgres_pool = None
                self._postgres_health = ConnectionHealth.DISCONNECTED
                self.logger.info("PostgreSQL pool closed")
            except Exception as e:
                self.logger.error(f"Error closing PostgreSQL pool: {e}")
    
    async def _close_redis_pool(self):
        """Close Redis connection pool"""
        if self._redis_client:
            try:
                await self._redis_client.close()
                self._redis_client = None
                self._redis_pool = None
                self._redis_health = ConnectionHealth.DISCONNECTED
                self.logger.info("Redis pool closed")
            except Exception as e:
                self.logger.error(f"Error closing Redis pool: {e}")
    
    async def _health_check_loop(self):
        """Background task for health checking"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Check PostgreSQL health
                if self._postgres_pool:
                    await self._check_postgres_health()
                
                # Check Redis health
                if self._redis_client:
                    await self._check_redis_health()
                
                # Update service registry
                if self.service_registry:
                    await self.service_registry.update_service_metadata(
                        "connection_pool_manager",
                        {
                            "postgres_health": self._postgres_health.value,
                            "redis_health": self._redis_health.value
                        }
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
    
    async def _check_postgres_health(self):
        """Check PostgreSQL connection health"""
        try:
            async with self._postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1", timeout=5.0)
            
            self._postgres_stats.health_checks_passed += 1
            
            # Update health status based on recent failures
            failure_rate = self._calculate_failure_rate(self._postgres_stats)
            if failure_rate < 0.1:
                self._postgres_health = ConnectionHealth.HEALTHY
            elif failure_rate < 0.3:
                self._postgres_health = ConnectionHealth.DEGRADED
            else:
                self._postgres_health = ConnectionHealth.UNHEALTHY
                
        except Exception as e:
            self._postgres_stats.health_checks_failed += 1
            self._postgres_health = ConnectionHealth.UNHEALTHY
            self.logger.warning(f"PostgreSQL health check failed: {e}")
    
    async def _check_redis_health(self):
        """Check Redis connection health"""
        try:
            await self._redis_client.ping()
            
            self._redis_stats.health_checks_passed += 1
            
            # Update health status based on recent failures
            failure_rate = self._calculate_failure_rate(self._redis_stats)
            if failure_rate < 0.1:
                self._redis_health = ConnectionHealth.HEALTHY
            elif failure_rate < 0.3:
                self._redis_health = ConnectionHealth.DEGRADED
            else:
                self._redis_health = ConnectionHealth.UNHEALTHY
                
        except Exception as e:
            self._redis_stats.health_checks_failed += 1
            self._redis_health = ConnectionHealth.UNHEALTHY
            self.logger.warning(f"Redis health check failed: {e}")
    
    async def _reconnect_loop(self):
        """Background task for reconnecting failed connections"""
        while True:
            try:
                await asyncio.sleep(self.config.reconnect_interval)
                
                # Reconnect PostgreSQL if needed
                if self._postgres_health == ConnectionHealth.UNHEALTHY and self.postgres_dsn:
                    await self._reconnect_postgres()
                
                # Reconnect Redis if needed
                if self._redis_health == ConnectionHealth.UNHEALTHY and self.redis_url:
                    await self._reconnect_redis()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Reconnect loop error: {e}")
    
    async def _reconnect_postgres(self):
        """Attempt to reconnect PostgreSQL"""
        self.logger.info("Attempting to reconnect PostgreSQL")
        
        try:
            # Close existing pool
            await self._close_postgres_pool()
            
            # Create new pool
            await self._create_postgres_pool()
            
            self.logger.info("PostgreSQL reconnected successfully")
            
        except Exception as e:
            self.logger.error(f"PostgreSQL reconnection failed: {e}")
    
    async def _reconnect_redis(self):
        """Attempt to reconnect Redis"""
        self.logger.info("Attempting to reconnect Redis")
        
        try:
            # Close existing connection
            await self._close_redis_pool()
            
            # Create new connection
            await self._create_redis_pool()
            
            self.logger.info("Redis reconnected successfully")
            
        except Exception as e:
            self.logger.error(f"Redis reconnection failed: {e}")
    
    def _update_avg_query_time(self, stats: ConnectionStats, query_time: float):
        """Update average query time"""
        total_queries = stats.total_queries
        if total_queries == 1:
            stats.avg_query_time_ms = query_time
        else:
            # Calculate running average
            stats.avg_query_time_ms = (
                (stats.avg_query_time_ms * (total_queries - 1) + query_time) / 
                total_queries
            )
    
    def _calculate_failure_rate(self, stats: ConnectionStats) -> float:
        """Calculate failure rate for health assessment"""
        total_checks = stats.health_checks_passed + stats.health_checks_failed
        if total_checks == 0:
            return 0.0
        
        # Consider recent checks more heavily
        recent_window = min(10, total_checks)
        recent_failures = min(stats.health_checks_failed, recent_window // 2)
        
        return recent_failures / recent_window
    
    def _calculate_health_ratio(self, stats: ConnectionStats) -> float:
        """Calculate health check success ratio"""
        total = stats.health_checks_passed + stats.health_checks_failed
        if total == 0:
            return 0.0
        return round(stats.health_checks_passed / total, 2)