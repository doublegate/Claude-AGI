# Claude-AGI Disaster Recovery Runbook

**Version**: 1.0
**Last Updated**: November 2025
**Maintainer**: DevOps Team

---

## Table of Contents

1. [Overview](#overview)
2. [Emergency Contacts](#emergency-contacts)
3. [Incident Classification](#incident-classification)
4. [Recovery Procedures](#recovery-procedures)
5. [Backup & Restore](#backup--restore)
6. [Failover Procedures](#failover-procedures)
7. [Post-Incident](#post-incident)

---

## Overview

This runbook provides step-by-step procedures for recovering Claude-AGI from various disaster scenarios. Follow these procedures in order and escalate as needed.

### Recovery Time Objectives (RTO)

| Component | RTO | RPO |
|-----------|-----|-----|
| API Service | 15 minutes | 5 minutes |
| PostgreSQL Database | 30 minutes | 15 minutes |
| Redis Cache | 5 minutes | Acceptable loss |
| Full System | 1 hour | 15 minutes |

---

## Emergency Contacts

### On-Call Rotation
- **Primary**: DevOps Team (pagerduty.com/claude-agi)
- **Secondary**: Platform Engineering
- **Escalation**: CTO

### External Contacts
- **Cloud Provider**: AWS Support (Premium)
- **Anthropic API**: api-support@anthropic.com
- **Database Support**: PostgreSQL Enterprise Support

---

## Incident Classification

### Severity Levels

**SEV-1 (Critical)**: Complete service outage
- Full API unavailability
- Data loss or corruption
- Security breach

**SEV-2 (Major)**: Partial service degradation
- API latency > 5s (p99)
- Database connection issues
- Authentication failures

**SEV-3 (Minor)**: Limited impact
- Single pod failures
- Non-critical component issues
- Performance degradation < 20%

---

## Recovery Procedures

### SEV-1: Complete API Outage

#### Symptoms
- All health checks failing
- No API responses
- Zero successful requests

#### Immediate Actions (First 5 minutes)

```bash
# 1. Check pod status
kubectl get pods -n claude-agi-prod

# 2. Check recent events
kubectl get events -n claude-agi-prod --sort-by='.lastTimestamp'

# 3. Check logs
kubectl logs -n claude-agi-prod -l app=claude-agi --tail=100

# 4. Check service status
kubectl get svc -n claude-agi-prod

# 5. Check ingress
kubectl get ingress -n claude-agi-prod
```

#### Recovery Steps

**Step 1: Assess Scope** (5 min)
```bash
# Check all components
kubectl get all -n claude-agi-prod

# Check persistent volumes
kubectl get pv,pvc -n claude-agi-prod

# Check secrets and configmaps
kubectl get secrets,configmaps -n claude-agi-prod
```

**Step 2: Restart Services** (10 min)
```bash
# Rollout restart (zero downtime)
kubectl rollout restart deployment/claude-agi-api -n claude-agi-prod

# Monitor rollout status
kubectl rollout status deployment/claude-agi-api -n claude-agi-prod

# If restart fails, scale down and up
kubectl scale deployment/claude-agi-api --replicas=0 -n claude-agi-prod
kubectl scale deployment/claude-agi-api --replicas=3 -n claude-agi-prod
```

**Step 3: Verify Recovery**
```bash
# Check pod health
kubectl get pods -n claude-agi-prod -w

# Test API health endpoint
curl https://api.claude-agi.com/health

# Check metrics
curl https://api.claude-agi.com/metrics | grep http_requests_total
```

---

### SEV-1: Database Failure

#### Symptoms
- Database connection errors
- Data corruption
- Disk full
- Replication lag

#### Recovery Steps

**Step 1: Identify Issue**
```bash
# Check PostgreSQL pods
kubectl get pods -n claude-agi-prod -l app=postgresql

# Check logs
kubectl logs -n claude-agi-prod postgresql-0 --tail=200

# Check disk usage
kubectl exec -n claude-agi-prod postgresql-0 -- df -h

# Check replication status
kubectl exec -n claude-agi-prod postgresql-0 -- psql -U claude_agi -c "SELECT * FROM pg_stat_replication;"
```

**Step 2: Failover to Replica** (if available)
```bash
# Promote standby to primary
kubectl exec -n claude-agi-prod postgresql-1 -- pg_ctl promote

# Update service to point to new primary
kubectl patch svc postgresql -n claude-agi-prod \
  -p '{"spec":{"selector":{"statefulset.kubernetes.io/pod-name":"postgresql-1"}}}'

# Restart API pods to reconnect
kubectl rollout restart deployment/claude-agi-api -n claude-agi-prod
```

**Step 3: Restore from Backup** (if failover not possible)
```bash
# Get latest backup
aws s3 ls s3://claude-agi-backups/postgres/ --recursive | sort | tail -n 1

# Download backup
aws s3 cp s3://claude-agi-backups/postgres/backup-YYYYMMDD.sql.gz /tmp/

# Restore database
kubectl exec -n claude-agi-prod postgresql-0 -- dropdb claude_agi_prod
kubectl exec -n claude-agi-prod postgresql-0 -- createdb claude_agi_prod

gunzip < /tmp/backup-YYYYMMDD.sql.gz | \
  kubectl exec -i -n claude-agi-prod postgresql-0 -- \
  psql -U claude_agi claude_agi_prod
```

---

### SEV-1: Redis Cluster Failure

#### Recovery Steps

```bash
# Check cluster status
kubectl exec -n claude-agi-prod redis-cluster-0 -- redis-cli cluster info

# Check individual nodes
for i in {0..5}; do
  echo "Node $i:"
  kubectl exec -n claude-agi-prod redis-cluster-$i -- redis-cli ping
done

# Restart failed nodes
kubectl delete pod redis-cluster-X -n claude-agi-prod

# Rebuild cluster (if completely broken)
kubectl delete job redis-cluster-init -n claude-agi-prod
kubectl apply -f deployment/kubernetes/production/redis-cluster.yaml

# Verify cluster
kubectl exec -n claude-agi-prod redis-cluster-0 -- redis-cli cluster nodes
```

---

## Backup & Restore

### Automated Backups

**Schedule**:
- PostgreSQL: Every 6 hours + transaction logs
- Configuration: Daily
- Secrets: Weekly (encrypted)

**Retention**:
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

### Manual Backup

```bash
# Database backup
kubectl exec -n claude-agi-prod postgresql-0 -- \
  pg_dump -U claude_agi claude_agi_prod | \
  gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Upload to S3
aws s3 cp backup-*.sql.gz s3://claude-agi-backups/postgres/manual/

# Redis backup
kubectl exec -n claude-agi-prod redis-cluster-0 -- redis-cli --rdb - | \
  gzip > redis-backup-$(date +%Y%m%d-%H%M%S).rdb.gz

# Configuration backup
kubectl get all,configmaps,secrets -n claude-agi-prod -o yaml > \
  k8s-config-$(date +%Y%m%d).yaml
```

### Restore Process

```bash
# 1. Scale down API pods
kubectl scale deployment/claude-agi-api --replicas=0 -n claude-agi-prod

# 2. Restore database (see database failure section)

# 3. Restore Redis (if needed)
gunzip < redis-backup-YYYYMMDD.rdb.gz | \
  kubectl exec -i -n claude-agi-prod redis-cluster-0 -- redis-cli --pipe

# 4. Scale up API pods
kubectl scale deployment/claude-agi-api --replicas=3 -n claude-agi-prod

# 5. Verify
kubectl get pods -n claude-agi-prod
curl https://api.claude-agi.com/health
```

---

## Failover Procedures

### Multi-Region Failover

**Trigger Conditions**:
- Primary region unavailable > 10 minutes
- RTO exceeded in primary region
- Data center outage

**Procedure**:

```bash
# 1. Verify secondary region health
aws --region us-west-2 eks describe-cluster --name claude-agi-dr

# 2. Update DNS to point to DR region
# (Use Route53 health check failover or manual update)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://failover-dns.json

# 3. Monitor DR region
kubectl --context=dr-cluster get pods -n claude-agi-prod -w

# 4. Verify traffic routing
curl https://api.claude-agi.com/health
```

### Database Replication Failover

```bash
# 1. Check replication lag
kubectl exec -n claude-agi-prod postgresql-1 -- \
  psql -U claude_agi -c "SELECT NOW() - pg_last_xact_replay_timestamp() AS lag;"

# 2. If lag < 30s, proceed with failover
kubectl exec -n claude-agi-prod postgresql-1 -- pg_ctl promote

# 3. Update application config
kubectl set env deployment/claude-agi-api \
  POSTGRES_HOST=postgresql-1.postgresql.claude-agi-prod.svc.cluster.local \
  -n claude-agi-prod

# 4. Monitor connections
kubectl logs -f -n claude-agi-prod -l app=claude-agi
```

---

## Post-Incident

### Immediate Actions

1. **Update Status Page**
   - Document incident timeline
   - Notify affected users
   - Provide ETA for full resolution

2. **Preserve Evidence**
   ```bash
   # Collect logs
   kubectl logs -n claude-agi-prod -l app=claude-agi \
     --since=2h > incident-logs.txt

   # Export metrics
   curl "http://prometheus:9090/api/v1/query_range?query=up&start=XXX&end=XXX" \
     > incident-metrics.json

   # Snapshot configuration
   kubectl get all -n claude-agi-prod -o yaml > incident-state.yaml
   ```

3. **Document Actions Taken**
   - Timeline of events
   - Commands executed
   - Configuration changes
   - People involved

### Post-Mortem (Within 48 hours)

**Required Sections**:
1. Incident Summary
2. Timeline
3. Root Cause Analysis
4. Impact Assessment
5. Action Items
   - Immediate fixes
   - Long-term improvements
   - Process changes

**Template**: `docs/templates/post-mortem-template.md`

---

## Testing & Validation

### Disaster Recovery Drills

**Monthly Drills**:
- API pod failure recovery
- Database connection failure
- Redis cluster node failure

**Quarterly Drills**:
- Full database restore
- Multi-region failover
- Complete system recovery

**Annual Drills**:
- Catastrophic failure scenario
- Full DR site activation
- Security incident response

### Validation Checklist

After any recovery:
- [ ] All pods running and healthy
- [ ] Health checks passing
- [ ] API responding within SLA
- [ ] Database replication working
- [ ] Redis cluster healthy
- [ ] Metrics being collected
- [ ] Logs being shipped
- [ ] Authentication working
- [ ] Rate limiting functional
- [ ] No data loss verified
- [ ] Backup job successful
- [ ] Monitoring alerts cleared

---

## Additional Resources

### Documentation
- Architecture Diagram: `docs/architecture/`
- Network Diagram: `docs/network-topology.png`
- Runbook Updates: `docs/runbooks/`

### Tools
- **Monitoring**: https://grafana.claude-agi.com
- **Logs**: https://kibana.claude-agi.com
- **Metrics**: https://prometheus.claude-agi.com
- **Alerts**: https://alertmanager.claude-agi.com

### Training
- DR Drill Recordings: Internal Wiki
- Incident Response Training: Monthly
- On-Call Rotation Schedule: PagerDuty

---

**Remember**:
- Communication is critical during incidents
- Document everything you do
- Don't hesitate to escalate if needed
- Recovery > Root cause analysis (during incident)

**Last Review**: November 2025
**Next Review**: December 2025
