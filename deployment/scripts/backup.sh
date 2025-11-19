#!/bin/bash
#
# Claude-AGI Automated Backup Script
# ===================================
#
# Performs automated backups of:
# - PostgreSQL database
# - Redis data
# - Configuration files
# - Logs
#
# Usage:
#   ./backup.sh                    # Local backup
#   ./backup.sh --s3               # Backup to S3
#   ./backup.sh --retention 7      # Keep 7 days
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_ROOT}/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="claude-agi-backup-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
S3_BACKUP=false
RETENTION_DAYS=30

while [[ $# -gt 0 ]]; do
    case $1 in
        --s3)
            S3_BACKUP=true
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
cd "${BACKUP_DIR}/${BACKUP_NAME}"

log_info "Starting backup: ${BACKUP_NAME}"

# 1. Backup PostgreSQL Database
log_info "Backing up PostgreSQL database..."
if command -v docker-compose &> /dev/null; then
    # Docker Compose environment
    docker-compose exec -T postgres pg_dump -U "${POSTGRES_USER:-claude}" "${POSTGRES_DB:-claude_agi}" | gzip > postgres-dump.sql.gz
elif command -v pg_dump &> /dev/null; then
    # Local PostgreSQL
    pg_dump -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-claude}" "${POSTGRES_DB:-claude_agi}" | gzip > postgres-dump.sql.gz
else
    log_warn "PostgreSQL backup skipped - no pg_dump available"
fi

# 2. Backup Redis Data
log_info "Backing up Redis data..."
if command -v docker-compose &> /dev/null; then
    # Docker Compose environment
    docker-compose exec -T redis redis-cli --rdb - | gzip > redis-dump.rdb.gz
elif command -v redis-cli &> /dev/null; then
    # Local Redis
    redis-cli --rdb - | gzip > redis-dump.rdb.gz
else
    log_warn "Redis backup skipped - no redis-cli available"
fi

# 3. Backup Configuration Files
log_info "Backing up configuration files..."
tar -czf config-backup.tar.gz \
    -C "${PROJECT_ROOT}" \
    .env \
    config/ \
    deployment/kubernetes/ \
    docker-compose.yml \
    2>/dev/null || log_warn "Some config files may be missing"

# 4. Backup Logs (last 7 days)
log_info "Backing up recent logs..."
if [ -d "${PROJECT_ROOT}/logs" ]; then
    find "${PROJECT_ROOT}/logs" -type f -mtime -7 -print0 | \
        tar -czf logs-backup.tar.gz --null -T - 2>/dev/null || \
        log_warn "No recent logs found"
fi

# 5. Backup Data Directory
log_info "Backing up data directory..."
if [ -d "${PROJECT_ROOT}/data" ]; then
    tar -czf data-backup.tar.gz -C "${PROJECT_ROOT}" data/ 2>/dev/null || \
        log_warn "Data directory backup incomplete"
fi

# 6. Create metadata file
log_info "Creating backup metadata..."
cat > backup-metadata.json <<EOF
{
  "backup_name": "${BACKUP_NAME}",
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "version": "$(cd ${PROJECT_ROOT} && git describe --tags --always 2>/dev/null || echo 'unknown')",
  "commit": "$(cd ${PROJECT_ROOT} && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "files": [
    $(ls -1 | jq -R -s -c 'split("\n")[:-1]')
  ]
}
EOF

# 7. Calculate checksums
log_info "Calculating checksums..."
sha256sum * > SHA256SUMS

# 8. Create compressed archive
log_info "Creating final archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)

log_info "Backup created: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"

# 9. Upload to S3 if requested
if [ "$S3_BACKUP" = true ]; then
    if command -v aws &> /dev/null; then
        S3_BUCKET="${S3_BACKUP_BUCKET:-claude-agi-backups}"
        log_info "Uploading to S3: s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz"

        aws s3 cp "${BACKUP_NAME}.tar.gz" "s3://${S3_BUCKET}/${BACKUP_NAME}.tar.gz" \
            --storage-class STANDARD_IA

        log_info "S3 upload complete"
    else
        log_error "AWS CLI not found - S3 backup skipped"
    fi
fi

# 10. Cleanup old backups
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "claude-agi-backup-*.tar.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -type d -name "claude-agi-backup-*" -mtime +${RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null || true

# Remove temporary directory
rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"

log_info "✓ Backup completed successfully!"
log_info "Backup location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Output backup info
echo ""
echo "Backup Summary:"
echo "  Name: ${BACKUP_NAME}"
echo "  Size: ${BACKUP_SIZE}"
echo "  Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
if [ "$S3_BACKUP" = true ]; then
    echo "  S3: s3://${S3_BUCKET:-claude-agi-backups}/${BACKUP_NAME}.tar.gz"
fi
echo ""
