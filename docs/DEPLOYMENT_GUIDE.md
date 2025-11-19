# Claude-AGI Deployment Guide

**Version**: 1.6.2
**Last Updated**: November 19, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Backup & Restore](#backup--restore)
5. [Monitoring Setup](#monitoring-setup)
6. [Production Configuration](#production-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (20.10+)
- 4GB RAM minimum, 8GB recommended
- 20GB disk space
- Anthropic API key

### 5-Minute Deploy

```bash
# 1. Clone repository
git clone https://github.com/doublegate/Claude-AGI.git
cd Claude-AGI

# 2. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start all services
docker-compose up -d

# 4. Verify deployment
curl http://localhost:8000/health

# 5. Access services
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9091
```

---

## Docker Compose Deployment

### Architecture Overview

The Docker Compose setup includes:

```
┌─────────────────────────────────────────────────┐
│              Claude-AGI Stack                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   API    │  │PostgreSQL│  │  Redis   │     │
│  │ Server   │──│ Database │──│  Cache   │     │
│  └────┬─────┘  └──────────┘  └──────────┘     │
│       │                                         │
│  ┌────┴─────┐  ┌──────────┐  ┌──────────┐     │
│  │Prometheus│──│ Grafana  │  │  Nginx   │     │
│  │Monitoring│  │Dashboards│  │  Proxy   │     │
│  └──────────┘  └──────────┘  └──────────┘     │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Configuration

#### Environment Variables

Edit `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Database (auto-configured for Docker)
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password

# Optional: Monitoring credentials
GRAFANA_PASSWORD=admin
```

#### Service Customization

```yaml
# docker-compose.override.yml (optional)
version: '3.8'

services:
  api:
    environment:
      LOG_LEVEL: DEBUG
      WORKERS: 8
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d api postgres redis

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart a service
docker-compose restart api

# View service status
docker-compose ps

# Execute command in container
docker-compose exec api python -m src.cli status
```

### Production Profile

For production deployment with Nginx reverse proxy:

```bash
docker-compose --profile production up -d
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- 8GB RAM per node recommended
- Storage class for persistent volumes

### Deployment Steps

#### 1. Create Namespace

```bash
kubectl create namespace claude-agi
kubectl config set-context --current --namespace=claude-agi
```

#### 2. Configure Secrets

```bash
# Create API key secret
kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=sk-ant-your-key-here

# Create database secrets
kubectl create secret generic database-secrets \
  --from-literal=postgres-password=your_secure_password \
  --from-literal=redis-password=your_secure_password
```

#### 3. Deploy Services

```bash
# Deploy in order
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/postgres-statefulset.yaml
kubectl apply -f deployment/kubernetes/redis-statefulset.yaml

# Wait for database readiness
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Deploy application
kubectl apply -f deployment/kubernetes/api-deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml

# Deploy ingress (optional)
kubectl apply -f deployment/kubernetes/ingress.yaml
```

#### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods

# Check services
kubectl get svc

# View logs
kubectl logs -f deployment/claude-agi-api

# Test API
kubectl port-forward svc/claude-agi-api 8000:8000
curl http://localhost:8000/health
```

### Scaling

```bash
# Horizontal scaling
kubectl scale deployment claude-agi-api --replicas=3

# Vertical scaling (edit deployment)
kubectl edit deployment claude-agi-api
```

### Updates

```bash
# Rolling update
kubectl set image deployment/claude-agi-api \
  api=claude-agi:v1.6.2

# Check rollout status
kubectl rollout status deployment/claude-agi-api

# Rollback if needed
kubectl rollout undo deployment/claude-agi-api
```

---

## Backup & Restore

### Automated Backups

#### Setup Cron Job

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/Claude-AGI/deployment/scripts/backup.sh --s3 --retention 30

# Weekly backup to S3
0 3 * * 0 /path/to/Claude-AGI/deployment/scripts/backup.sh --s3 --retention 90
```

#### Manual Backup

```bash
# Local backup
./deployment/scripts/backup.sh

# Backup to S3
./deployment/scripts/backup.sh --s3

# Custom retention (7 days)
./deployment/scripts/backup.sh --retention 7
```

### Restore from Backup

#### Local Restore

```bash
./deployment/scripts/restore.sh /path/to/backup.tar.gz
```

#### S3 Restore

```bash
./deployment/scripts/restore.sh --s3 s3://bucket/backup.tar.gz
```

### Backup Verification

```bash
# List backups
ls -lh backups/

# Verify backup integrity
cd backups/claude-agi-backup-YYYYMMDD_HHMMSS/
sha256sum -c SHA256SUMS
```

---

## Monitoring Setup

### Access Dashboards

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9091 | N/A |
| API Metrics | http://localhost:9090/metrics | N/A |

### Grafana Setup

#### 1. Initial Login

1. Navigate to http://localhost:3000
2. Login with admin/admin
3. Change password when prompted

#### 2. Import Dashboard

1. Click "+" → "Import"
2. Upload `deployment/monitoring/grafana/dashboards/claude-agi.json`
3. Select Prometheus datasource
4. Click "Import"

### Prometheus Metrics

Claude-AGI exposes these metric types:

```
# Counters
claude_agi_thoughts_total{stream="PRIMARY"}
claude_agi_api_requests_total{endpoint="/health"}

# Gauges
claude_agi_active_streams
claude_agi_memory_count

# Histograms
claude_agi_thought_generation_duration_seconds
claude_agi_api_request_duration_seconds
```

### Alerts Configuration

Create alert rules in `deployment/monitoring/prometheus/rules/`:

```yaml
# alerts.yml
groups:
  - name: claude-agi
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(claude_agi_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: ServiceDown
        expr: up{job="claude-agi-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Claude-AGI API is down"
```

---

## Production Configuration

### Security Hardening

#### 1. Environment Variables

Never commit `.env` to version control:

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

#### 2. Database Security

```yaml
# docker-compose.prod.yml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Password required}
    networks:
      - backend  # Internal network only
```

#### 3. API Security (Future)

```python
# Enable authentication
API_KEY_REQUIRED=true
JWT_SECRET_KEY=your-secret-key-here
RATE_LIMIT_ENABLED=true
```

### Performance Tuning

#### Database Optimization

```sql
-- PostgreSQL configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

#### API Server Tuning

```yaml
# docker-compose.prod.yml
services:
  api:
    environment:
      WORKERS: 4  # 2 × CPU cores
      WORKER_CONNECTIONS: 1000
      KEEPALIVE_TIMEOUT: 5
```

#### Redis Optimization

```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

### SSL/TLS Configuration

```nginx
# deployment/nginx/conf.d/default.conf
server {
    listen 443 ssl http2;
    server_name api.claude-agi.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. API Won't Start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing ANTHROPIC_API_KEY
# - Database not ready
# - Port already in use

# Solutions:
docker-compose down
# Fix .env configuration
docker-compose up -d
```

#### 2. Database Connection Errors

```bash
# Check database health
docker-compose exec postgres pg_isready

# Check connection string
docker-compose exec api env | grep DATABASE_URL

# Reset database
docker-compose down postgres
docker volume rm claude-agi_postgres_data
docker-compose up -d postgres
```

#### 3. Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits
docker-compose down
# Edit docker-compose.yml, add memory limits
docker-compose up -d

# Or increase system swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. Slow Performance

```bash
# Check system resources
docker stats

# Optimize PostgreSQL
docker-compose exec postgres psql -U claude -d claude_agi -c "VACUUM ANALYZE;"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB

# Restart services
docker-compose restart
```

### Debug Mode

```bash
# Enable debug logging
docker-compose down
# Edit .env: LOG_LEVEL=DEBUG
docker-compose up

# Or temporarily
docker-compose exec api env LOG_LEVEL=DEBUG uvicorn src.api.server:app --reload
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping

# Full system status
curl http://localhost:8000/status | jq
```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Developer Guide**: [API_DEVELOPER_GUIDE.md](API_DEVELOPER_GUIDE.md)
- **Architecture**: [ARCHITECTURE_REFACTORING_PROGRESS.md](ARCHITECTURE_REFACTORING_PROGRESS.md)
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/doublegate/Claude-AGI/issues
- Discussions: https://github.com/doublegate/Claude-AGI/discussions

---

**Happy Deploying! 🚀**
