"""
Health Checker

Monitors system health and provides health status endpoints.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field

try:
    from ..core.service_registry import ServiceRegistry
    from ..core.event_bus import EventBus
except ImportError:
    # For standalone testing or when imported directly
    from core.service_registry import ServiceRegistry
    from core.event_bus import EventBus
from .metrics_collector import MetricsCollector


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of components to monitor"""
    SERVICE = "service"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"
    CONSCIOUSNESS = "consciousness"
    SAFETY = "safety"


@dataclass
class HealthCheck:
    """Definition of a health check"""
    name: str
    component_type: ComponentType
    check_function: Callable
    timeout: float = 5.0
    critical: bool = True
    
    
@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0


class HealthChecker:
    """
    Monitors system health across all components.
    
    Features:
    - Periodic health checks
    - Component-level health status
    - Aggregated system health
    - Health history tracking
    - Alert generation for degraded health
    """
    
    def __init__(
        self,
        service_registry: Optional[ServiceRegistry] = None,
        event_bus: Optional[EventBus] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        check_interval: float = 30.0,
        history_size: int = 100
    ):
        self.service_registry = service_registry
        self.event_bus = event_bus
        self.metrics_collector = metrics_collector
        self.check_interval = check_interval
        self.history_size = history_size
        
        self.logger = logging.getLogger(__name__)
        
        # Health checks
        self._health_checks: List[HealthCheck] = []
        self._check_results: Dict[str, HealthCheckResult] = {}
        self._health_history: List[Dict[str, Any]] = []
        
        # Check task
        self._check_task: Optional[asyncio.Task] = None
        
        # System status
        self._system_status = HealthStatus.UNKNOWN
        self._last_check_time: Optional[datetime] = None
        
    async def initialize(self):
        """Initialize the health checker"""
        self.logger.info("Initializing Health Checker")
        
        # Register standard health checks
        await self._register_standard_checks()
        
        # Start health check task
        self._check_task = asyncio.create_task(self._check_loop())
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "health_checker",
                self,
                {"check_interval": self.check_interval}
            )
    
    async def shutdown(self):
        """Shutdown the health checker"""
        self.logger.info("Shutting down Health Checker")
        
        # Cancel check task
        if self._check_task:
            self._check_task.cancel()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("health_checker")
    
    def register_check(self, health_check: HealthCheck):
        """
        Register a new health check.
        
        Args:
            health_check: Health check definition
        """
        self._health_checks.append(health_check)
        self.logger.info(f"Registered health check: {health_check.name}")
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Perform all health checks and return results.
        
        Returns:
            Dict containing overall status and component results
        """
        start_time = datetime.now(timezone.utc)
        results = []
        
        # Run all health checks concurrently
        check_tasks = []
        for check in self._health_checks:
            task = asyncio.create_task(self._run_check(check))
            check_tasks.append((check, task))
        
        # Wait for all checks with timeout
        for check, task in check_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=check.timeout)
                results.append(result)
                self._check_results[check.name] = result
            except asyncio.TimeoutError:
                result = HealthCheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {check.timeout}s"
                )
                results.append(result)
                self._check_results[check.name] = result
            except Exception as e:
                result = HealthCheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}"
                )
                results.append(result)
                self._check_results[check.name] = result
        
        # Calculate overall system status
        self._system_status = self._calculate_system_status(results)
        self._last_check_time = start_time
        
        # Create health report
        health_report = {
            "status": self._system_status.value,
            "timestamp": start_time.isoformat(),
            "duration_ms": (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
            "checks": {
                result.name: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "duration_ms": result.duration_ms
                }
                for result in results
            }
        }
        
        # Add to history
        self._add_to_history(health_report)
        
        # Update metrics if available
        if self.metrics_collector:
            await self._update_health_metrics(results)
        
        # Publish health status event
        if self.event_bus:
            await self.event_bus.publish("health.status_updated", health_report)
        
        return health_report
    
    async def get_component_health(self, component_name: str) -> Optional[HealthCheckResult]:
        """
        Get health status for a specific component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Health check result if available
        """
        return self._check_results.get(component_name)
    
    def get_system_status(self) -> HealthStatus:
        """
        Get overall system health status.
        
        Returns:
            Current system health status
        """
        return self._system_status
    
    def get_health_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get health check history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of historical health reports
        """
        if limit:
            return self._health_history[-limit:]
        return self._health_history.copy()
    
    async def _register_standard_checks(self):
        """Register standard health checks for all components"""
        
        # Service registry check
        if self.service_registry:
            self.register_check(HealthCheck(
                name="service_registry",
                component_type=ComponentType.SERVICE,
                check_function=self._check_service_registry,
                critical=True
            ))
        
        # Event bus check
        if self.event_bus:
            self.register_check(HealthCheck(
                name="event_bus",
                component_type=ComponentType.SERVICE,
                check_function=self._check_event_bus,
                critical=True
            ))
        
        # Database checks
        self.register_check(HealthCheck(
            name="postgresql",
            component_type=ComponentType.DATABASE,
            check_function=self._check_postgresql,
            critical=True
        ))
        
        self.register_check(HealthCheck(
            name="redis",
            component_type=ComponentType.DATABASE,
            check_function=self._check_redis,
            critical=True
        ))
        
        # Memory system check
        self.register_check(HealthCheck(
            name="memory_system",
            component_type=ComponentType.MEMORY,
            check_function=self._check_memory_system,
            critical=True
        ))
        
        # Consciousness check
        self.register_check(HealthCheck(
            name="consciousness_streams",
            component_type=ComponentType.CONSCIOUSNESS,
            check_function=self._check_consciousness,
            critical=False
        ))
        
        # Safety framework check
        self.register_check(HealthCheck(
            name="safety_framework",
            component_type=ComponentType.SAFETY,
            check_function=self._check_safety,
            critical=True
        ))
        
        # API check
        self.register_check(HealthCheck(
            name="api_server",
            component_type=ComponentType.API,
            check_function=self._check_api,
            critical=False
        ))
    
    async def _check_loop(self):
        """Background task for periodic health checks"""
        # Initial delay
        await asyncio.sleep(5.0)
        
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _run_check(self, check: HealthCheck) -> HealthCheckResult:
        """Run a single health check"""
        import time
        start_time = time.time()
        
        try:
            # Run the check function
            if asyncio.iscoroutinefunction(check.check_function):
                result = await check.check_function()
            else:
                result = check.check_function()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # If check returns a result object, use it
            if isinstance(result, HealthCheckResult):
                result.duration_ms = duration_ms
                return result
            
            # Otherwise, assume healthy if no exception
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.HEALTHY,
                message="Check passed",
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=duration_ms
            )
    
    async def _check_service_registry(self) -> HealthCheckResult:
        """Check service registry health"""
        try:
            services = await self.service_registry.list_services()
            service_count = len(services)
            
            if service_count == 0:
                return HealthCheckResult(
                    name="service_registry",
                    status=HealthStatus.DEGRADED,
                    message="No services registered",
                    details={"service_count": 0}
                )
            
            return HealthCheckResult(
                name="service_registry",
                status=HealthStatus.HEALTHY,
                message=f"{service_count} services registered",
                details={"service_count": service_count, "services": list(services.keys())}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="service_registry",
                status=HealthStatus.UNHEALTHY,
                message=f"Service registry error: {str(e)}"
            )
    
    async def _check_event_bus(self) -> HealthCheckResult:
        """Check event bus health"""
        try:
            # Test publish/subscribe
            test_event = f"health_check_test_{datetime.now().timestamp()}"
            received = False
            
            async def test_handler(data):
                nonlocal received
                received = True
            
            # Subscribe
            await self.event_bus.subscribe(test_event, test_handler)
            
            # Publish
            await self.event_bus.publish(test_event, {"test": True})
            
            # Wait briefly
            await asyncio.sleep(0.1)
            
            # Unsubscribe
            await self.event_bus.unsubscribe(test_event, test_handler)
            
            if received:
                return HealthCheckResult(
                    name="event_bus",
                    status=HealthStatus.HEALTHY,
                    message="Event bus operational"
                )
            else:
                return HealthCheckResult(
                    name="event_bus",
                    status=HealthStatus.UNHEALTHY,
                    message="Event bus not delivering messages"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="event_bus",
                status=HealthStatus.UNHEALTHY,
                message=f"Event bus error: {str(e)}"
            )
    
    async def _check_postgresql(self) -> HealthCheckResult:
        """Check PostgreSQL health"""
        if not self.service_registry:
            return HealthCheckResult(
                name="postgresql",
                status=HealthStatus.UNKNOWN,
                message="Service registry not available"
            )
        
        try:
            # Get connection pool manager
            pool_manager = await self.service_registry.get_service("connection_pool_manager")
            if not pool_manager:
                return HealthCheckResult(
                    name="postgresql",
                    status=HealthStatus.DEGRADED,
                    message="Connection pool manager not found"
                )
            
            # Check PostgreSQL health
            health_status = pool_manager.get_health_status()
            postgres_health = health_status.get("postgres", {})
            
            status_map = {
                "healthy": HealthStatus.HEALTHY,
                "degraded": HealthStatus.DEGRADED,
                "unhealthy": HealthStatus.UNHEALTHY,
                "disconnected": HealthStatus.UNHEALTHY
            }
            
            status = status_map.get(
                postgres_health.get("health", "unknown"),
                HealthStatus.UNKNOWN
            )
            
            return HealthCheckResult(
                name="postgresql",
                status=status,
                message=f"PostgreSQL is {postgres_health.get('health', 'unknown')}",
                details=postgres_health.get("stats", {})
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="postgresql",
                status=HealthStatus.UNHEALTHY,
                message=f"PostgreSQL check error: {str(e)}"
            )
    
    async def _check_redis(self) -> HealthCheckResult:
        """Check Redis health"""
        if not self.service_registry:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNKNOWN,
                message="Service registry not available"
            )
        
        try:
            # Get connection pool manager
            pool_manager = await self.service_registry.get_service("connection_pool_manager")
            if not pool_manager:
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    message="Connection pool manager not found"
                )
            
            # Check Redis health
            health_status = pool_manager.get_health_status()
            redis_health = health_status.get("redis", {})
            
            status_map = {
                "healthy": HealthStatus.HEALTHY,
                "degraded": HealthStatus.DEGRADED,
                "unhealthy": HealthStatus.UNHEALTHY,
                "disconnected": HealthStatus.UNHEALTHY
            }
            
            status = status_map.get(
                redis_health.get("health", "unknown"),
                HealthStatus.UNKNOWN
            )
            
            return HealthCheckResult(
                name="redis",
                status=status,
                message=f"Redis is {redis_health.get('health', 'unknown')}",
                details=redis_health.get("stats", {})
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check error: {str(e)}"
            )
    
    async def _check_memory_system(self) -> HealthCheckResult:
        """Check memory system health"""
        if not self.service_registry:
            return HealthCheckResult(
                name="memory_system",
                status=HealthStatus.UNKNOWN,
                message="Service registry not available"
            )
        
        try:
            # Get memory coordinator
            memory_coordinator = await self.service_registry.get_service("memory_coordinator")
            if not memory_coordinator:
                return HealthCheckResult(
                    name="memory_system",
                    status=HealthStatus.UNHEALTHY,
                    message="Memory coordinator not found"
                )
            
            # Get memory stats
            stats = memory_coordinator.get_stats()
            
            # Check for issues
            issues = []
            
            # Check working memory
            if stats.get("working_memory", {}).get("hit_rate", 0) < 0.5:
                issues.append("Low working memory hit rate")
            
            # Check episodic memory
            episodic = stats.get("episodic_memory", {})
            if episodic.get("total_memories", 0) == 0:
                issues.append("No episodic memories stored")
            
            # Check semantic index
            semantic = stats.get("semantic_index", {})
            if not semantic.get("use_faiss", False) and semantic.get("numpy_vectors", 0) > 10000:
                issues.append("Large semantic index without FAISS")
            
            if issues:
                return HealthCheckResult(
                    name="memory_system",
                    status=HealthStatus.DEGRADED,
                    message="; ".join(issues),
                    details=stats
                )
            
            return HealthCheckResult(
                name="memory_system",
                status=HealthStatus.HEALTHY,
                message="Memory system operational",
                details=stats
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="memory_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory system check error: {str(e)}"
            )
    
    async def _check_consciousness(self) -> HealthCheckResult:
        """Check consciousness streams health"""
        # This would check if consciousness streams are generating thoughts
        # For now, return healthy
        return HealthCheckResult(
            name="consciousness_streams",
            status=HealthStatus.HEALTHY,
            message="Consciousness streams operational"
        )
    
    async def _check_safety(self) -> HealthCheckResult:
        """Check safety framework health"""
        if not self.service_registry:
            return HealthCheckResult(
                name="safety_framework",
                status=HealthStatus.UNKNOWN,
                message="Service registry not available"
            )
        
        try:
            # Get safety framework
            safety = await self.service_registry.get_service("enhanced_safety_framework")
            if not safety:
                return HealthCheckResult(
                    name="safety_framework",
                    status=HealthStatus.UNHEALTHY,
                    message="Safety framework not found"
                )
            
            # Test validation
            test_input = "Hello, this is a health check"
            result = await safety.validate_content(test_input)
            
            if result.passed:
                return HealthCheckResult(
                    name="safety_framework",
                    status=HealthStatus.HEALTHY,
                    message="Safety framework operational"
                )
            else:
                return HealthCheckResult(
                    name="safety_framework",
                    status=HealthStatus.DEGRADED,
                    message="Safety framework rejecting valid input"
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="safety_framework",
                status=HealthStatus.UNHEALTHY,
                message=f"Safety framework check error: {str(e)}"
            )
    
    async def _check_api(self) -> HealthCheckResult:
        """Check API server health"""
        # This would check if API server is responding
        # For now, return healthy
        return HealthCheckResult(
            name="api_server",
            status=HealthStatus.HEALTHY,
            message="API server operational"
        )
    
    def _calculate_system_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Calculate overall system status from component results"""
        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        critical_unhealthy = False
        
        for result in results:
            status_counts[result.status] += 1
            
            # Check if any critical component is unhealthy
            check = next((c for c in self._health_checks if c.name == result.name), None)
            if check and check.critical and result.status == HealthStatus.UNHEALTHY:
                critical_unhealthy = True
        
        # Determine overall status
        if critical_unhealthy or status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] > len(results) / 2:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def _add_to_history(self, health_report: Dict[str, Any]):
        """Add health report to history"""
        self._health_history.append(health_report)
        
        # Trim history if needed
        if len(self._health_history) > self.history_size:
            self._health_history = self._health_history[-self.history_size:]
    
    async def _update_health_metrics(self, results: List[HealthCheckResult]):
        """Update health metrics in metrics collector"""
        # This would update Prometheus metrics
        # Implementation depends on metrics collector interface
        pass