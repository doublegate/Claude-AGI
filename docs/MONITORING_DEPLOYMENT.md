# Claude-AGI Monitoring Stack Deployment Guide

## Overview

This document describes the deployment of a comprehensive monitoring stack for Claude-AGI, providing real-time visibility into system performance, consciousness activity, memory operations, and overall health.

## Architecture

The monitoring stack consists of:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Node Exporter**: System-level metrics
- **cAdvisor**: Container metrics
- **Claude-AGI App**: Application with built-in metrics endpoint

## Prerequisites

### Required Software

- Docker (version 20.0+)
- Docker Compose (version 2.0+)
- 4GB+ available RAM
- 10GB+ available disk space

### System Requirements

- Linux, macOS, or Windows with Docker Desktop
- Network access to pull Docker images
- Ports 3000, 8080, 9090, 9093, 9100 available

## Quick Start

### 1. Automated Deployment

```bash
cd /var/home/parobek/Code/Claude-AGI/monitoring
./deploy.sh
```

The deployment script will:
- Validate prerequisites
- Create necessary directories
- Configure permissions
- Deploy all monitoring services
- Verify service health
- Display access URLs

### 2. Manual Deployment

If you prefer manual deployment:

```bash
cd /var/home/parobek/Code/Claude-AGI/monitoring

# Create data directories
mkdir -p data/{prometheus,grafana,alertmanager}

# Set permissions (Linux/macOS)
sudo chown 472:472 data/grafana
sudo chown 65534:65534 data/prometheus

# Deploy stack
docker-compose up -d

# Check status
docker-compose ps
```

## Service Access

Once deployed, access the monitoring services:

| Service | URL | Description |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | Primary dashboard interface |
| **Prometheus** | http://localhost:9090 | Metrics database and query interface |
| **Alertmanager** | http://localhost:9093 | Alert management interface |
| **Node Exporter** | http://localhost:9100 | System metrics endpoint |
| **cAdvisor** | http://localhost:8080 | Container metrics interface |

### Default Credentials

- **Grafana**: admin / admin (change on first login)

## Configuration

### Grafana Setup

1. **Initial Login**
   ```
   URL: http://localhost:3000
   Username: admin
   Password: admin
   ```

2. **Change Default Password**
   - Login and follow the password change prompt
   - Choose a strong password for production use

3. **Verify Data Source**
   - Navigate to Configuration → Data Sources
   - Prometheus should be automatically configured
   - Test connection to ensure it's working

4. **Import Dashboards**
   - The Claude-AGI overview dashboard should be automatically loaded
   - If not, manually import from `monitoring/grafana/dashboards/`

### Prometheus Configuration

The Prometheus configuration (`monitoring/prometheus.yml`) defines:

- **Scrape Intervals**: 5-30 seconds depending on service
- **Targets**: All monitoring endpoints
- **Alert Rules**: Located in `monitoring/rules/`

Key scrape jobs:
```yaml
scrape_configs:
  - job_name: 'claude-agi-app'
    static_configs:
      - targets: ['claude-agi:8001']
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
```

### Alertmanager Configuration

Configure notifications in `monitoring/alertmanager.yml`:

#### Email Notifications
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'your-email@gmail.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
```

#### Slack Notifications
```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#claude-agi-alerts'
    username: 'Claude-AGI Monitor'
```

After configuration changes:
```bash
docker-compose restart alertmanager
```

## Claude-AGI Application Integration

### Enable Metrics in Your Application

1. **Environment Variables**
   ```bash
   export PROMETHEUS_METRICS_PORT=8001
   export METRICS_ENABLED=true
   ```

2. **Configuration File**
   ```yaml
   # configs/development.yaml
   monitoring:
     metrics_enabled: true
     metrics_port: 8001
     prometheus_endpoint: '/metrics'
   ```

3. **Start Application**
   ```bash
   python claude-agi.py  # Refactored implementation with monitoring
   ```

### Verify Metrics Endpoint

Test the metrics endpoint:
```bash
curl http://localhost:8001/metrics
```

You should see Prometheus-formatted metrics including:
- `claude_agi_thoughts_generated_total`
- `claude_agi_memory_operations_total`
- `claude_agi_api_request_duration_seconds`
- Standard process metrics

## Monitoring Features

### Key Dashboards

#### 1. System Overview
- Application health status
- Consciousness activity levels
- Memory usage and operations
- API performance metrics
- Safety system status

#### 2. Performance Metrics
- CPU and memory utilization
- Database connection health
- Query performance statistics
- Request latency distributions

#### 3. Consciousness Monitoring
- Thought generation rates by stream
- Consciousness quality scores
- Stream buffer utilization
- Attention weight distributions

#### 4. Safety Dashboard
- Safety violations count
- Security check frequency
- Threat detection rates
- Anomaly detection alerts

### Alert Rules

The system includes comprehensive alerting for:

#### Critical Alerts
- **Application Down**: Service unavailable
- **Safety Violations**: Security incidents detected
- **Database Connection Loss**: Data access failure

#### Warning Alerts
- **High CPU/Memory**: Resource utilization > 90%
- **Slow Queries**: Database performance degradation
- **API Latency**: Response times > 2 seconds
- **Consciousness Stalled**: No thoughts generated > 5 minutes

### Custom Metrics

#### Consciousness Metrics
```python
# Example custom metrics in your application
consciousness_quality_score = Gauge('claude_agi_consciousness_quality_score', 'Quality score of consciousness')
thoughts_generated = Counter('claude_agi_thoughts_generated_total', 'Total thoughts generated', ['stream_type'])
```

#### Memory System Metrics
```python
memory_usage = Gauge('claude_agi_memory_usage_bytes', 'Memory usage in bytes')
memory_operations = Counter('claude_agi_memory_operations_total', 'Memory operations', ['operation'])
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check logs
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Check disk space
df -h

# Check port conflicts
netstat -tulpn | grep :3000
```

#### 2. Permission Errors
```bash
# Fix Grafana permissions
sudo chown -R 472:472 monitoring/data/grafana

# Fix Prometheus permissions  
sudo chown -R 65534:65534 monitoring/data/prometheus
```

#### 3. No Metrics Data
```bash
# Check Claude-AGI metrics endpoint
curl http://localhost:8001/metrics

# Check Prometheus targets
open http://localhost:9090/targets

# Verify network connectivity
docker network ls
docker network inspect claude-agi-monitoring
```

#### 4. Grafana Dashboard Issues
```bash
# Reload dashboards
docker-compose restart grafana

# Check dashboard JSON
cat monitoring/grafana/dashboards/claude-agi-overview.json

# Import manually
# Go to Grafana → Dashboards → Import
```

### Log Analysis

#### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f alertmanager
```

#### Debug Prometheus Configuration
```bash
# Validate config
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check rules
docker-compose exec prometheus promtool check rules /etc/prometheus/rules/*.yml
```

### Performance Optimization

#### Reduce Metrics Retention
```yaml
# In prometheus.yml command section
- '--storage.tsdb.retention.time=7d'  # Reduce from 200h to 7 days
```

#### Optimize Scrape Intervals
```yaml
# Increase intervals for less critical services
- job_name: 'node-exporter'
  scrape_interval: 30s  # Increased from 15s
```

#### Limit Resource Usage
```yaml
# In docker-compose.yml
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## Security Considerations

### Network Security
- Services are isolated in the `claude-agi-monitoring` Docker network
- Only necessary ports are exposed to the host
- No external access by default (localhost only)

### Authentication
- Change default Grafana credentials immediately
- Configure Grafana user roles and permissions
- Enable Grafana audit logging for production

### Data Protection
- Metrics data is stored in Docker volumes
- Consider encryption for sensitive metrics
- Implement backup strategy for dashboard configs

### Production Hardening
```yaml
# Additional security for production
services:
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_SECURITY_COOKIE_SECURE=true
```

## Maintenance

### Regular Tasks

#### 1. Update Images
```bash
cd monitoring
docker-compose pull
docker-compose up -d
```

#### 2. Clean Up Old Data
```bash
# Remove old metrics data (Prometheus will recreate)
docker-compose down
docker volume rm monitoring_prometheus_data
docker-compose up -d
```

#### 3. Backup Configuration
```bash
# Backup important configs
tar -czf monitoring-backup-$(date +%Y%m%d).tar.gz \
  prometheus.yml \
  alertmanager.yml \
  grafana/provisioning/ \
  grafana/dashboards/
```

### Scaling Considerations

For high-load production environments:

#### 1. External Prometheus
- Use external Prometheus cluster
- Configure remote storage
- Implement federation for multiple instances

#### 2. Load Balancing
- Use nginx/traefik for Grafana
- Implement high availability setup
- Configure external authentication

#### 3. Advanced Alerting
- Integrate with PagerDuty/OpsGenie
- Configure escalation policies
- Implement alert suppression rules

## Integration Examples

### CI/CD Integration
```yaml
# .github/workflows/monitoring.yml
- name: Deploy Monitoring Stack
  run: |
    cd monitoring
    ./deploy.sh
    
- name: Wait for Services
  run: |
    timeout 60 bash -c 'until curl -f http://localhost:3000/api/health; do sleep 2; done'
```

### Kubernetes Deployment
```yaml
# For Kubernetes environments
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    # Your Prometheus config here
```

### API Integration
```python
# Query metrics programmatically
import requests

def get_consciousness_metrics():
    response = requests.get('http://localhost:9090/api/v1/query', params={
        'query': 'claude_agi_thoughts_generated_total'
    })
    return response.json()
```

## Conclusion

The Claude-AGI monitoring stack provides comprehensive observability into your AI system's performance, health, and behavior. Regular monitoring of consciousness activity, memory operations, and safety metrics ensures optimal performance and early detection of issues.

For production deployments, consider implementing additional security measures, backup strategies, and scaling configurations based on your specific requirements.