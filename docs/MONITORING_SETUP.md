# Monitoring Setup Guide

This guide explains how to set up and use the monitoring system in the Claude-AGI project.

## Overview

The monitoring system provides comprehensive observability for the Claude-AGI platform, including:
- Prometheus metrics collection
- Health check endpoints
- Performance tracking
- Resource usage monitoring
- Service status tracking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Applications                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Orchestrator│  │   Memory    │  │   Services  │   │
│  │             │  │   Manager   │  │             │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                 │           │
│         └────────────────┴─────────────────┘           │
│                          │                              │
│                    ┌─────▼─────┐                       │
│                    │Monitoring │                       │
│                    │Integration│                       │
│                    └─────┬─────┘                       │
│                          │                              │
│         ┌────────────────┴─────────────────┐           │
│         │                                  │           │
│    ┌────▼────┐                      ┌─────▼─────┐     │
│    │ Metrics │                      │  Health   │     │
│    │Collector│                      │  Checker  │     │
│    └────┬────┘                      └─────┬─────┘     │
│         │                                  │           │
│    ┌────▼────┐                      ┌─────▼─────┐     │
│    │Prometheus│                      │    API    │     │
│    │ Exporter│                      │ Endpoints │     │
│    └─────────┘                      └───────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Monitoring Integration (`src/monitoring/monitoring_integration.py`)
- Central integration point for all monitoring features
- Manages metrics collection and health checks
- Provides hooks for services to report metrics

### 2. Metrics Collector (`src/monitoring/metrics_collector.py`)
- Collects application metrics (requests, latency, errors)
- Tracks resource usage (CPU, memory, disk)
- Provides counter, gauge, and histogram metrics

### 3. Health Checker (`src/monitoring/health_checker.py`)
- Monitors service health status
- Tracks dependencies (Redis, PostgreSQL, external APIs)
- Provides liveness and readiness endpoints

### 4. Prometheus Exporter (`src/monitoring/prometheus_exporter.py`)
- Exports metrics in Prometheus format
- HTTP endpoint at `/metrics`
- Compatible with Prometheus scrapers

## Setup Instructions

### 1. Install Dependencies

```bash
pip install prometheus-client psutil aiohttp
```

### 2. Enable Monitoring in Configuration

Add to `configs/monitoring.yaml`:

```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
  health_check:
    enabled: true
    interval: 30  # seconds
  metrics:
    collect_interval: 10  # seconds
    include_system_metrics: true
```

### 3. Initialize Monitoring in Your Application

```python
from src.monitoring.monitoring_integration import MonitoringIntegration

# Create monitoring instance
monitoring = MonitoringIntegration(config)

# Start monitoring
await monitoring.start()

# Register your service
monitoring.register_service("my_service", health_check_func)

# Record metrics
monitoring.record_request("my_endpoint", duration=0.1, status=200)

# Shutdown
await monitoring.stop()
```

### 4. Configure Prometheus

Add to `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'claude-agi'
    static_configs:
      - targets: ['localhost:9090']
```

### 5. Run Prometheus

```bash
docker run -d \
  -p 9091:9090 \
  -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  --name prometheus \
  prom/prometheus
```

## Available Metrics

### Application Metrics
- `claude_agi_requests_total`: Total number of requests
- `claude_agi_request_duration_seconds`: Request duration histogram
- `claude_agi_errors_total`: Total number of errors
- `claude_agi_active_connections`: Current active connections

### Service Metrics
- `claude_agi_service_up`: Service health status (1=up, 0=down)
- `claude_agi_service_response_time`: Service response time
- `claude_agi_service_error_rate`: Service error rate

### System Metrics
- `claude_agi_cpu_usage_percent`: CPU usage percentage
- `claude_agi_memory_usage_bytes`: Memory usage in bytes
- `claude_agi_disk_usage_percent`: Disk usage percentage

## Health Check Endpoints

### Liveness Probe
```
GET /health/live
```

Returns 200 if the service is running.

### Readiness Probe
```
GET /health/ready
```

Returns 200 if the service is ready to accept traffic.

### Detailed Health Status
```
GET /health/status
```

Returns detailed health information:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-05T10:00:00Z",
  "services": {
    "orchestrator": "up",
    "memory_manager": "up",
    "redis": "up",
    "postgresql": "up"
  },
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 1024000000,
    "uptime": 3600
  }
}
```

## Testing the Monitoring System

Use the provided test script:

```bash
python scripts/test_monitoring.py
```

This will:
1. Start the monitoring system
2. Generate sample metrics
3. Verify Prometheus endpoint
4. Check health endpoints
5. Display collected metrics

## Integration with Grafana

1. Install Grafana:
```bash
docker run -d \
  -p 3000:3000 \
  --name grafana \
  grafana/grafana
```

2. Add Prometheus data source:
   - URL: `http://localhost:9091`
   - Access: Server (default)

3. Import the dashboard:
   - Use `monitoring/grafana/dashboards/claude-agi-overview.json`

## Alerting

Configure alerts in `monitoring/prometheus/alerts/claude-agi-alerts.yml`:

```yaml
groups:
  - name: claude-agi
    rules:
      - alert: HighErrorRate
        expr: rate(claude_agi_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected
          
      - alert: ServiceDown
        expr: claude_agi_service_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Service {{ $labels.service }} is down
```

## Troubleshooting

### Prometheus Not Scraping Metrics
- Check that the exporter is running on the configured port
- Verify Prometheus can reach the metrics endpoint
- Check logs for any errors

### Missing Metrics
- Ensure monitoring is enabled in configuration
- Verify services are registering with monitoring
- Check that metrics are being recorded

### High Memory Usage
- Adjust metrics retention period
- Reduce collection frequency
- Disable system metrics if not needed

## Best Practices

1. **Use appropriate metric types**:
   - Counters for totals (requests, errors)
   - Gauges for current values (connections, queue size)
   - Histograms for distributions (latency, size)

2. **Label metrics appropriately**:
   - Keep cardinality low
   - Use consistent label names
   - Avoid high-cardinality labels (user IDs, session IDs)

3. **Set reasonable collection intervals**:
   - Balance between granularity and resource usage
   - Use longer intervals for stable metrics
   - Shorter intervals for critical metrics

4. **Monitor the monitors**:
   - Track monitoring system resource usage
   - Alert on monitoring failures
   - Have fallback monitoring

## Next Steps

- Set up production Prometheus/Grafana stack
- Configure alerting rules
- Create custom dashboards
- Implement distributed tracing
- Add log aggregation