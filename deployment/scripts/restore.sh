#!/bin/bash
#
# Claude-AGI Backup Restore Script
# =================================
#
# Restores Claude-AGI from a backup archive
#
# Usage:
#   ./restore.sh /path/to/backup.tar.gz
#   ./restore.sh --s3 s3://bucket/backup.tar.gz
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEMP_DIR="/tmp/claude-agi-restore-$$"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <backup-file.tar.gz>"
    log_error "       $0 --s3 s3://bucket/backup.tar.gz"
    exit 1
fi

# Parse arguments
if [ "$1" = "--s3" ]; then
    if [ $# -ne 2 ]; then
        log_error "S3 URL required with --s3 flag"
        exit 1
    fi

    S3_URL="$2"
    BACKUP_FILE="${TEMP_DIR}/backup.tar.gz"

    log_info "Downloading from S3: ${S3_URL}"
    mkdir -p "${TEMP_DIR}"
    aws s3 cp "${S3_URL}" "${BACKUP_FILE}"
else
    BACKUP_FILE="$1"
fi

# Verify backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

log_info "Starting restore from: ${BACKUP_FILE}"

# Create temporary directory
mkdir -p "${TEMP_DIR}"
cd "${TEMP_DIR}"

# Extract backup
log_info "Extracting backup archive..."
tar -xzf "${BACKUP_FILE}"

# Find backup directory
BACKUP_DIR=$(find . -maxdepth 1 -type d -name "claude-agi-backup-*" | head -1)
if [ -z "${BACKUP_DIR}" ]; then
    log_error "Invalid backup archive - no backup directory found"
    rm -rf "${TEMP_DIR}"
    exit 1
fi

cd "${BACKUP_DIR}"

# Verify checksums
log_info "Verifying backup integrity..."
if [ -f "SHA256SUMS" ]; then
    sha256sum -c SHA256SUMS || {
        log_error "Checksum verification failed!"
        exit 1
    }
    log_info "✓ Checksums verified"
else
    log_warn "No checksums found - skipping verification"
fi

# Display backup metadata
if [ -f "backup-metadata.json" ]; then
    log_info "Backup metadata:"
    cat backup-metadata.json | jq .
fi

# Confirm restore
echo ""
read -p "Continue with restore? This will overwrite current data! (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Restore cancelled"
    rm -rf "${TEMP_DIR}"
    exit 0
fi

# 1. Restore PostgreSQL
if [ -f "postgres-dump.sql.gz" ]; then
    log_info "Restoring PostgreSQL database..."

    if command -v docker-compose &> /dev/null; then
        # Docker environment
        gunzip < postgres-dump.sql.gz | docker-compose exec -T postgres psql -U "${POSTGRES_USER:-claude}" "${POSTGRES_DB:-claude_agi}"
    else
        # Local environment
        gunzip < postgres-dump.sql.gz | psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-claude}" "${POSTGRES_DB:-claude_agi}"
    fi

    log_info "✓ PostgreSQL restored"
else
    log_warn "No PostgreSQL dump found - skipping"
fi

# 2. Restore Redis
if [ -f "redis-dump.rdb.gz" ]; then
    log_info "Restoring Redis data..."

    if command -v docker-compose &> /dev/null; then
        # Stop Redis, restore dump, restart
        docker-compose stop redis
        gunzip < redis-dump.rdb.gz > /tmp/dump.rdb
        docker cp /tmp/dump.rdb $(docker-compose ps -q redis):/data/dump.rdb
        docker-compose start redis
        rm /tmp/dump.rdb
    else
        log_warn "Manual Redis restore required for local installation"
    fi

    log_info "✓ Redis restored"
else
    log_warn "No Redis dump found - skipping"
fi

# 3. Restore Configuration
if [ -f "config-backup.tar.gz" ]; then
    log_info "Restoring configuration files..."

    # Backup current config
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        cp "${PROJECT_ROOT}/.env" "${PROJECT_ROOT}/.env.backup-$(date +%Y%m%d_%H%M%S)"
    fi

    # Extract config
    tar -xzf config-backup.tar.gz -C "${PROJECT_ROOT}"

    log_info "✓ Configuration restored"
else
    log_warn "No configuration backup found - skipping"
fi

# 4. Restore Data Directory
if [ -f "data-backup.tar.gz" ]; then
    log_info "Restoring data directory..."
    tar -xzf data-backup.tar.gz -C "${PROJECT_ROOT}"
    log_info "✓ Data directory restored"
else
    log_warn "No data backup found - skipping"
fi

# 5. Restore Logs (optional)
if [ -f "logs-backup.tar.gz" ]; then
    read -p "Restore logs? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Restoring logs..."
        tar -xzf logs-backup.tar.gz -C "${PROJECT_ROOT}"
        log_info "✓ Logs restored"
    fi
fi

# Cleanup
log_info "Cleaning up temporary files..."
cd /
rm -rf "${TEMP_DIR}"

log_info "✓ Restore completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Verify configuration in .env"
echo "  2. Restart services: docker-compose restart"
echo "  3. Check system status: curl http://localhost:8000/health"
echo ""
