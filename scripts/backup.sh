#!/bin/bash
#
# AI Learning System - Backup Script
# Version: 1.0
# Purpose: Automated backup system for self-sustaining AI Learning
#
# Usage:
#   ./backup.sh                    # Auto-detect type based on day
#   ./backup.sh --type=full        # Force full backup
#   ./backup.sh --type=incremental  # Force incremental backup
#   ./backup.sh --verify          # Verify last backup only
#
# Cron:
#   0 2 * * 0 root /home/dju/projects/ai-learning/scripts/backup.sh --type=full      # Nedjelja
#   0 2 * * 1-6 root /home/dju/projects/ai-learning/scripts/backup.sh        # Pon-Sub
#   0 3 1 * * root /home/dju/projects/ai-learning/scripts/backup.sh --type=archive  # Monthly
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
CONFIG_DIR="${SCRIPT_DIR}/../docker"
TIMESTAMP=$(date '+%Y-%m-%d_%H:%M:%S')
DATE=$(date '+%Y-%m-%d')
LOG_FILE="${BACKUP_DIR}/backup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

#==============================================================================
# CONFIGURATION
#==============================================================================
DB_NAME="${DB_NAME:-ai_learning_db}"
DB_USER="${DB_USER:-ai_learning_user}"
DB_CONTAINER="${DB_CONTAINER:-ai-learning-db}"
MINIO_CONTAINER="${MINIO_CONTAINER:-ai-learning-minio}"

# Retention
RETENTION_DAILY=7
RETENTION_WEEKLY=4
RETENTION_MONTHLY=12

#==============================================================================
# FUNCTIONS
#==============================================================================
log() {
    local msg="[${TIMESTAMP}] $1"
    echo -e "$msg"
    echo "$msg" >> "${LOG_FILE}"
}

log_success() {
    log "${GREEN}✓ SUCCESS:${NC} $1"
}

log_error() {
    log "${RED}✗ ERROR:${NC} $1"
}

log_warn() {
    log "${YELLOW}⚠ WARNING:${NC} $1"
}

log_info() {
    echo "[${TIMESTAMP}] ℹ INFO: $1"
}

#==============================================================================
# PARSE ARGUMENTS
#==============================================================================
BACKUP_TYPE="auto"

while [[ $# -gt 0 ]]; do
    case $1 in
        --type=*)
            BACKUP_TYPE="${1#*=}"
            ;;
        --verify)
            verify_backup
            exit $?
            ;;
        --test)
            TEST_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --type=full        Force full backup"
            echo "  --type=incremental Force incremental backup"
            echo "  --type=archive    Monthly archive"
            echo "  --verify          Verify last backup only"
            echo "  --test           Test mode (no actual backup)"
            echo "  --help           This help"
            exit 0
            ;;
    esac
    shift
done

# Auto-detect backup type
if [[ "$BACKUP_TYPE" == "auto" ]]; then
    DAY_OF_WEEK=$(date '+%u')
    if [[ "$DAY_OF_WEEK" == "7" ]]; then
        BACKUP_TYPE="full"
    else
        BACKUP_TYPE="incremental"
    fi
fi

#==============================================================================
# SETUP
#==============================================================================
init() {
    log_info "=========================================="
    log_info "AI Learning Backup - ${BACKUP_TYPE}"
    log_info "=========================================="
    
    # Create directories
    mkdir -p "${BACKUP_DIR}"/{full,incremental,config,logs}
    
    # Touch log file
    touch "${LOG_FILE}"
    
    # Test mode
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        log_warn "TEST MODE - No actual backup will be created"
    fi
}

#==============================================================================
# DATABASE BACKUP
#==============================================================================
backup_database() {
    local type=$1
    local output_file="${BACKUP_DIR}/${type}/db-${DATE}.sql.gz"
    
    log_info "Backing up database: ${DB_NAME}"
    
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        log_info "TEST: Would run: docker exec ${DB_CONTAINER} pg_dump -Fc ${DB_NAME}"
        return 0
    fi
    
    # Check if database is accessible
    if ! docker exec "${DB_CONTAINER}" pg_isready -U "${DB_USER}" >/dev/null 2>&1; then
        log_error "Database not accessible"
        return 1
    fi
    
    # pg_dump with compression
    docker exec "${DB_CONTAINER}" pg_dump -Fc -U "${DB_USER}" "${DB_NAME}" 2>/dev/null | \
        gzip > "${output_file}"
    
    if [[ -f "$output_file" ]]; then
        local size=$(du -h "$output_file" | cut -f1)
        log_success "Database backup: ${output_file} (${size})"
        echo "$output_file" > "${BACKUP_DIR}/.last_db_backup"
        return 0
    else
        log_error "Database backup failed"
        return 1
    fi
}

#==============================================================================
# MINIO BACKUP
#==============================================================================
backup_minio() {
    local type=$1
    local output_dir="${BACKUP_DIR}/${type}/minio"
    
    log_info "Backing up MinIO data..."
    
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        log_info "TEST: Would run: mc mirror to ${output_dir}"
        return 0
    fi
    
    # Ensure mc is available
    if ! docker exec "${MINIO_CONTAINER}" mc --version >/dev/null 2>&1; then
        log_warn "MinIO client not available, skipping file backup"
        return 0
    fi
    
    # Create backup directory
    mkdir -p "${output_dir}"
    
    # Mirror MinIO data (local to local backup)
    # Note: This mirrors from MinIO to local backup dir
    docker exec "${MINIO_CONTAINER}" mc cp -r local/ai-learning "${output_dir}/" 2>/dev/null || \
        docker exec "${MINIO_CONTAINER}" mc mirror fetch local/ai-learning "${output_dir}/" 2>/dev/null || \
        true
    
    # Create tar archive
    local archive="${BACKUP_DIR}/${type}/minio-${DATE}.tar.gz"
    if [[ -d "${output_dir}" ]] && [[ "$(ls -A ${output_dir} 2>/dev/null)" ]]; then
        tar -czf "${archive}" -C "${output_dir}" . 2>/dev/null
        local size=$(du -h "${archive}" | cut -f1)
        log_success "MinIO backup: ${archive} (${size})"
        echo "${archive}" > "${BACKUP_DIR}/.last_minio_backup"
        return 0
    else
        log_warn "MinIO backup empty or skipped"
        return 0
    fi
}

#==============================================================================
# CONFIG BACKUP
#==============================================================================
backup_config() {
    local output_file="${BACKUP_DIR}/config/config-${DATE}.tar.gz"
    
    log_info "Backing up configuration..."
    
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        log_info "TEST: Would backup ${CONFIG_DIR}"
        return 0
    fi
    
    # Create config archive (excluding .env for security)
    cd "${CONFIG_DIR}" || CONFIG_DIR="/home/dju/projects/ai-learning/docker"
    
    if [[ -d "${CONFIG_DIR}" ]]; then
        tar -czf "${output_file}" \
            --exclude='.env' \
            --exclude='*.log' \
            --exclude='node_modules' \
            -C "$(dirname "${CONFIG_DIR}")" \
            "$(basename "${CONFIG_DIR}")" 2>/dev/null
        
        local size=$(du -h "${output_file}" | cut -f1)
        log_success "Config backup: ${output_file} (${size})"
        return 0
    else
        log_warn "Config directory not found"
        return 0
    fi
}

#==============================================================================
# METADATA
#==============================================================================
save_metadata() {
    local type=$1
    
    # Save backup metadata
    cat > "${BACKUP_DIR}/${type}/meta-${DATE}.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "date": "${DATE}",
    "type": "${type}",
    "components": {
        "database": $(test -f "${BACKUP_DIR}/${type}/db-${DATE}.sql.gz" && echo "true" || echo "false"),
        "minio": $(test -f "${BACKUP_DIR}/${type}/minio-${DATE}.tar.gz" && echo "true" || echo "false"),
        "config": $(test -f "${BACKUP_DIR}/config/config-${DATE}.tar.gz" && echo "true" || echo "false")
    },
    "docker": {
        "db_version": "$(docker exec ${DB_CONTAINER} psql --version 2>/dev/null | head -1 || echo 'N/A')",
        "containers": "$(docker ps --format '{{.Names}}' | tr '\n' ',')"
    }
}
EOF
    
    log_info "Metadata saved"
}

#==============================================================================
# VERIFICATION
#==============================================================================
verify_backup() {
    log_info "Verifying last backup..."
    
    local last_db=$(cat "${BACKUP_DIR}/.last_db_backup" 2>/dev/null)
    
    if [[ -n "$last_db" && -f "$last_db" ]]; then
        local size=$(du -h "$last_db" | cut -f1)
        log_success "Last DB backup: ${last_db} (${size})"
        
        # Verify gzip
        if gzip -t "$last_db" 2>/dev/null; then
            log_success "DB backup integrity: OK"
        else
            log_error "DB backup corrupted!"
            return 1
        fi
    else
        log_error "No DB backup found"
        return 1
    fi
    
    return 0
}

#==============================================================================
# RETENTION
#==============================================================================
cleanup_old_backups() {
    log_info "Cleaning old backups (retention policy)..."
    
    # Dnevni (7 dana)
    find "${BACKUP_DIR}"/incremental -name "*.sql.gz" -mtime +${RETENTION_DAILY} -delete 2>/dev/null || true
    find "${BACKUP_DIR}"/incremental -name "*.tar.gz" -mtime +${RETENTION_DAILY} -delete 2>/dev/null || true
    
    # Nedjeljni (4 nedjelje) - keep only full
    find "${BACKUP_DIR}"/full -name "*.tar.gz" -mtime +$((RETENTION_WEEKLY * 7)) -delete 2>/dev/null || true
    
    # Mjesečni (12 mjeseci)
    find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +$((RETENTION_MONTHLY * 30)) -delete 2>/dev/null || true
    
    log_info "Retention cleanup complete"
}

#==============================================================================
# ALERT
#==============================================================================
send_alert() {
    local status=$1
    local message=$2
    
    if [[ -n "${WEBHOOK_URL:-}" ]]; then
        curl -s -X POST "${WEBHOOK_URL}" \
            -H "Content-Type: application/json" \
            -d "{
                \"title\": \"${status} Backup\",
                \"description\": \"${message}\",
                \"timestamp\": \"${TIMESTAMP}\",
                \"type\": \"${BACKUP_TYPE}\"
            }" 2>/dev/null || true
    fi
}

#==============================================================================
# MAIN
#==============================================================================
main() {
    local exit_code=0
    
    init
    
    # Run backup based on type
    case "$BACKUP_TYPE" in
        full)
            backup_database "full" || exit_code=1
            backup_minio "full" || exit_code=1
            backup_config || exit_code=1
            ;;
        incremental|daily)
            backup_database "incremental" || exit_code=1
            backup_minio "incremental" || exit_code=1
            ;;
        archive)
            backup_database "full" || exit_code=1
            backup_config || exit_code=1
            ;;
    esac
    
    # Save metadata
    save_metadata "${BACKUP_TYPE}"
    
    # Cleanup old
    cleanup_old_backups
    
    # Verify
    verify_backup || exit_code=1
    
    # Alert
    if [[ $exit_code -eq 0 ]]; then
        log_success "Backup completed successfully"
        send_alert "✅" "Backup ${BACKUP_TYPE} completed"
    else
        log_error "Backup completed with errors"
        send_alert "⚠️" "Backup completed with errors"
    fi
    
    return $exit_code
}

# Run main
main "$@"
exit $?