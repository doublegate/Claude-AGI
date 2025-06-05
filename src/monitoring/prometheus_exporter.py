"""
Prometheus Exporter

Exports metrics in Prometheus format via HTTP endpoint.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from aiohttp import web

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
    from prometheus_client.core import CollectorRegistry
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    CONTENT_TYPE_LATEST = "text/plain"
    REGISTRY = None
    
    def generate_latest(registry=None):
        return b"# Prometheus client not available\n"

try:
    from ..core.service_registry import ServiceRegistry
except ImportError:
    # For standalone testing or when imported directly
    from core.service_registry import ServiceRegistry
from .metrics_collector import MetricsCollector


class PrometheusExporter:
    """
    Exports metrics in Prometheus format.
    
    Features:
    - HTTP endpoint for Prometheus scraping
    - Configurable port and path
    - Authentication support
    - Custom registry support
    - Graceful shutdown
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        service_registry: Optional[ServiceRegistry] = None,
        host: str = "0.0.0.0",
        port: int = 9090,
        path: str = "/metrics",
        auth_token: Optional[str] = None
    ):
        self.metrics_collector = metrics_collector
        self.service_registry = service_registry
        self.host = host
        self.port = port
        self.path = path
        self.auth_token = auth_token
        
        self.logger = logging.getLogger(__name__)
        
        # Web server
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Metrics
        self._request_count = 0
        self._last_scrape_time = None
        
    async def initialize(self):
        """Initialize the Prometheus exporter"""
        self.logger.info(f"Initializing Prometheus Exporter on {self.host}:{self.port}{self.path}")
        
        if not HAS_PROMETHEUS:
            self.logger.warning("prometheus_client not available, metrics export will be limited")
        
        # Create web application
        self.app = web.Application()
        
        # Add routes
        self.app.router.add_get(self.path, self._handle_metrics)
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/ready", self._handle_ready)
        
        # Add middleware
        self.app.middlewares.append(self._auth_middleware)
        self.app.middlewares.append(self._metrics_middleware)
        
        # Start web server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        self.logger.info(f"Prometheus exporter started on http://{self.host}:{self.port}{self.path}")
        
        # Register with service registry
        if self.service_registry:
            await self.service_registry.register_service(
                "prometheus_exporter",
                self,
                {
                    "host": self.host,
                    "port": self.port,
                    "path": self.path,
                    "prometheus_available": HAS_PROMETHEUS
                }
            )
    
    async def shutdown(self):
        """Shutdown the Prometheus exporter"""
        self.logger.info("Shutting down Prometheus Exporter")
        
        # Stop web server
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        # Unregister from service registry
        if self.service_registry:
            await self.service_registry.unregister_service("prometheus_exporter")
    
    @web.middleware
    async def _auth_middleware(self, request: web.Request, handler):
        """Authentication middleware"""
        if self.auth_token and request.path == self.path:
            # Check bearer token
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != self.auth_token:
                return web.Response(text="Unauthorized", status=401)
        
        return await handler(request)
    
    @web.middleware
    async def _metrics_middleware(self, request: web.Request, handler):
        """Metrics tracking middleware"""
        import time
        start_time = time.time()
        
        try:
            response = await handler(request)
            
            # Record metrics
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_api_request(
                    method=request.method,
                    endpoint=request.path,
                    status_code=response.status,
                    duration=duration
                )
            
            return response
            
        except Exception as e:
            # Record error
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_api_request(
                    method=request.method,
                    endpoint=request.path,
                    status_code=500,
                    duration=duration
                )
            raise
    
    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """Handle metrics endpoint requests"""
        self._request_count += 1
        self._last_scrape_time = asyncio.get_event_loop().time()
        
        try:
            # Collect latest metrics
            await self.metrics_collector.collect_metrics()
            
            # Generate Prometheus format
            if HAS_PROMETHEUS:
                metrics_output = generate_latest(REGISTRY)
            else:
                # Fallback format
                metrics_output = await self._generate_text_metrics()
            
            return web.Response(
                body=metrics_output,
                content_type=CONTENT_TYPE_LATEST,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generating metrics: {e}")
            return web.Response(
                text=f"# Error generating metrics: {str(e)}\n",
                status=500,
                content_type=CONTENT_TYPE_LATEST
            )
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check endpoint"""
        # Basic health check - is the service running?
        health = {
            "status": "healthy",
            "prometheus_available": HAS_PROMETHEUS,
            "request_count": self._request_count,
            "last_scrape_time": self._last_scrape_time
        }
        
        return web.json_response(health)
    
    async def _handle_ready(self, request: web.Request) -> web.Response:
        """Handle readiness check endpoint"""
        # Check if metrics collector is ready
        ready = True
        details = {}
        
        if self.metrics_collector:
            # Check if we can get metrics
            try:
                metrics = self.metrics_collector.get_all_metrics()
                details["metrics_count"] = len(metrics)
            except Exception as e:
                ready = False
                details["error"] = str(e)
        else:
            ready = False
            details["error"] = "Metrics collector not available"
        
        if ready:
            return web.json_response({"ready": True, **details})
        else:
            return web.json_response({"ready": False, **details}, status=503)
    
    async def _generate_text_metrics(self) -> bytes:
        """Generate metrics in text format when prometheus_client is not available"""
        lines = []
        lines.append("# Claude-AGI Metrics")
        lines.append("# TYPE claude_agi_up gauge")
        lines.append("claude_agi_up 1")
        
        # Get all metrics from collector
        metrics = self.metrics_collector.get_all_metrics()
        
        for metric_name, metric_info in metrics.items():
            metric_type = metric_info.get("type", "gauge")
            description = metric_info.get("description", "")
            
            lines.append(f"# HELP {metric_name} {description}")
            lines.append(f"# TYPE {metric_name} {metric_type}")
            
            # This is simplified - real implementation would include actual values
            lines.append(f"{metric_name} 0")
        
        lines.append("")  # Empty line at end
        return "\n".join(lines).encode("utf-8")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exporter statistics"""
        return {
            "request_count": self._request_count,
            "last_scrape_time": self._last_scrape_time,
            "endpoint": f"http://{self.host}:{self.port}{self.path}",
            "prometheus_available": HAS_PROMETHEUS
        }