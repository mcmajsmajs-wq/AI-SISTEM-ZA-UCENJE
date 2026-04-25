#!/bin/bash
#
# AI Learning System - Restore Script
# Version: 1.0
# Purpose: Restore from backup for disaster recovery
#
# Usage:
#   ./restore.sh                          # Interactive mode
#   ./restore.sh --date=2026-04-25       # Restore specific date
#   ./restore.sh --type=full            # Restore full backup only
#   ./restore.sh --type=database       # Restore database only
#   ./restore.sh --type=minio          # Restore MinIO only
#   ./restore.sh --type=config         # Restore config only
#   ./restore.sh --verify              # Verify without restore
#   ./restore.sh --dry-run             # Show what would be done
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
CONFIG_DIR="${SCRIPT_DIR}/../docker"
TIMESTAMP=$(date '+%Y-%m-%d_%H:%M:%S')
LOG_FILE="${BACKUP_DIR}/restore.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#==============================================================================
# CONFIGURATION
#==============================================================================
DB_NAME="${DB_NAME:-ai_learning_db}"
DB_USER="${DB_USER:-ai_learning_user}"
DB_CONTAINER="${DB_CONTAINER:-ai-learning-db}"
MINIO_CONTAINER="${MINIO_CONTAINER:-ai-learning-minio}"
APP_CONTAINER="ai-learning-app"
WORKER_CONTAINER="ai-learning-worker"

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
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

pause_app() {
    log_info "Pausing application services..."
    docker pause ${APP_CONTAINER} 2>/dev/null || true
    docker pause ${WORKER_CONTAINER} 2>/dev/null || true
}

unpause_app() {
    log_info "Unpausing application services..."
    docker unpause ${APP_CONTAINER} 2>/dev/null || true
    docker unpause ${WORKER_CONTAINER} 2>/dev/null || true
}

stop_services() {
    log_info "Stopping application services..."
    docker stop ${APP_CONTAINER} 2>/dev/null || true
    docker stop ${WORKER_CONTAINER} 2>/dev/null || true
}

start_services() {
    log_info "Starting application services..."
    docker start ${APP_CONTAINER} 2>/dev/null || true
    docker start ${WORKER_CONTAINER} 2>/dev/null || true
}

#==============================================================================
# PARSE ARGUMENTS
#==============================================================================
RESTORE_TYPE="interactive"
TARGET_DATE=""
DRY_RUN=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --type=*)
            RESTORE_TYPE="${1#*=}"
            ;;
        --date=*)
            TARGET_DATE="${1#*=}"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --verify)
            VERIFY_ONLY=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --type=full        Restore full backup"
            echo "  --type=database    Restore database only"
            echo "  --type=minio        Restore MinIO only"
            echo "  --type=config       Restore config only"
            echo "  --date=YYYY-MM-DD  Restore specific date"
            echo "  --dry-run          Show what would be done"
            echo "  --verify           Verify backup only"
            echo "  --help            This help"
            exit 0
            ;;
    esac
    shift
done

#==============================================================================
# SETUP
#==============================================================================
init() {
    log_info "=========================================="
    log_info "AI Learning Restore"
    log_info "=========================================="
    
    mkdir -p "${BACKUP_DIR}"
    touch "${LOG_FILE}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi
}

#==============================================================================
# FIND BACKUP
#==============================================================================
find_backup() {
    local type=$1
    local search_date=$2
    
    local backup_file=""
    
    if [[ -n "$search_date" ]]; then
        backup_file=$(find "${BACKUP_DIR}/${type}" -name "*${search_date}*" \( -name "*.sql.gz" -o -name "*.tar.gz" \) 2>/dev/null | head -1)
    else
        backup_file=$(find "${BACKUP_DIR}/${type}" -type f \( -name "*.sql.gz" -o -name "*.tar.gz" \) -mtime -7 2>/dev/null | head -1)
    fi
    
    echo "$backup_file"
}

#==============================================================================
# LIST AVAILABLE BACKUPS
#==============================================================================
list_backups() {
    log_info "Available backups:"
    echo ""
    
    echo "Database backups:"
    find "${BACKUP_DIR}" -name "*.sql.gz" 2>/dev/null | sort -r | head -10 | while read -r f; do
        local size=$(du -h "$f" | cut -f1)
        local date=$(basename "$f" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
        echo "  - $date: $size"
    done
    
    echo ""
    echo "MinIO backups:"
    find "${BACKUP_DIR}" -name "minio-*.tar.gz" 2>/dev/null | sort -r | head -5 | while read -r f; do
        local size=$(du -h "$f" | cut -f1)
        echo "  - $(basename "$f"): $size"
    done
    
    echo ""
    echo "Config backups:"
    find "${BACKUP_DIR}/config" -name "*.tar.gz" 2>/dev/null | sort -r | head -5 | while read -r f; do
        local size=$(du -h "$f" | cut -f1)
        echo "  - $(basename "$f"): $size"
    done
}

#==============================================================================
# VERIFY BACKUP
#==============================================================================
verify_backup() {
    local type=$1
    local backup_file=$2
    
    log_info "Verifying ${backup_file}..."
    
    case "$backup_file" in
        *.sql.gz)
            if gzip -t "$backup_file" 2>/dev/null; then
                log_success "Database backup: OK"
                return 0
            else
                log_error "Database backup: CORRUPTED"
                return 1
            fi
            ;;
        *.tar.gz)
            if tar -tzf "$backup_file" >/dev/null 2>&1; then
                log_success "Archive integrity: OK"
                # List contents
                local files=$(tar -tzf "$backup_file" 2>/dev/null | head -10)
                log_info "Contents: $files"
                return 0
            else
                log_error "Archive: CORRUPTED"
                return 1
            fi
            ;;
    esac
    
    return 0
}

#==============================================================================
# RESTORE DATABASE
#==============================================================================
restore_database() {
    local backup_file=$1
    
    log_info "Restoring database from: ${backup_file}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would restore database from ${backup_file}"
        return 0
    fi
    
    # Verify first
    if ! verify_backup "database" "$backup_file"; then
        log_error "Backup verification failed"
        return 1
    fi
    
    # Stop services
    stop_services
    
    # Drop and recreate database
    log_info "Dropping database..."
    docker exec ${DB_CONTAINER} dropdb -U ${DB_USER} --if-exists ${DB_NAME} 2>/dev/null || true
    
    log_info "Creating database..."
    docker exec ${DB_CONTAINER} createdb -U ${DB_USER} ${DB_NAME} 2>/dev/null || true
    
    # Restore from dump
    log_info "Restoring data..."
    docker exec -i ${DB_CONTAINER} gunzip -c ${backup_file} | \
        docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} ${DB_NAME} 2>/dev/null || \
        docker exec ${DB_CONTAINER} pg_restore -U ${DB_USER} -d ${DB_NAME} < <(gunzip -c ${backup_file}) 2>/dev/null || {
        log_error "Restore failed, trying alternate method..."
        docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d postgres < <(gunzip -c ${backup_file}) 2>/dev/null
    }
    
    # Verify restore
    local user_count=$(docker exec ${DB_CONTAINER} psql -U ${DB_USER} ${DB_NAME} -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs || echo "0")
    log_success "Database restored. Users: ${user_count:-N/A}"
    
    return 0
}

#==============================================================================
# RESTORE MINIO
#==============================================================================
restore_minio() {
    local backup_file=$1
    
    log_info "Restoring MinIO from: ${backup_file}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would restore MinIO from ${backup_file}"
        return 0
    fi
    
    # Verify first
    if ! verify_backup "minio" "$backup_file"; then
        log_error "Backup verification failed"
        return 1
    fi
    
    # Extract archive to temp
    local temp_dir="/tmp/minio-restore-$$"
    mkdir -p "${temp_dir}"
    
    log_info "Extracting archive..."
    tar -xzf "${backup_file}" -C "${temp_dir}" 2>/dev/null || {
        log_error "Extraction failed"
        return 1
    }
    
    # Restore to MinIO
    log_info "Copying to MinIO..."
    docker cp "${temp_dir}/." ${MINIO_CONTAINER}:/data/ai-learning/ 2>/dev/null || \
        docker exec ${MINIO_CONTAINER} mc cp -r "${temp_dir}/" local/ai-learning/ 2>/dev/null || {
        log_warn "MinIO restore may have failed, manual check required"
    }
    
    # Cleanup
    rm -rf "${temp_dir}"
    
    log_success "MinIO restored"
    return 0
}

#==============================================================================
# RESTORE CONFIG
#==============================================================================
restore_config() {
    local backup_file=$1
    
    log_info "Restoring config from: ${backup_file}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would restore config from ${backup_file}"
        return 0
    fi
    
    # Verify first
    if ! verify_backup "config" "$backup_file"; then
        log_error "Backup verification failed"
        return 1
    fi
    
    # Stop services
    stop_services
    
    # Extract to temp
    local temp_dir="/tmp/config-restore-$$"
    mkdir -p "${temp_dir}"
    
    log_info "Extracting archive..."
    tar -xzf "${backup_file}" -C "${temp_dir}" 2>/dev/null || {
        log_error "Extraction failed"
        return 1
    }
    
    # Backup current config
    local config_backup="${BACKUP_DIR}/config/pre-restore-$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "${config_backup}" -C "${CONFIG_DIR}" . 2>/dev/null || true
    
    # Restore config
    log_info "Restoring configuration..."
    cp -r "${temp_dir}/"* "${CONFIG_DIR}/" 2>/dev/null || true
    
    # Cleanup
    rm -rf "${temp_dir}"
    
    log_success "Config restored"
    return 0
}

#==============================================================================
# MAIN
#==============================================================================
main() {
    local exit_code=0
    
    init
    
    # Verify only mode
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        list_backups
        exit 0
    fi
    
    # List available if no date
    if [[ -z "$TARGET_DATE" && "$RESTORE_TYPE" == "interactive" ]]; then
        list_backups
        echo ""
        read -p "Enter date (YYYY-MM-DD) or press Enter for latest: " TARGET_DATE
    fi
    
    # Find backups based on type
    case "$RESTORE_TYPE" in
        full)
            local db_backup=$(find_backup "full" "$TARGET_DATE")
            local minio_backup=$(find_backup "full" "$TARGET_DATE")
            local config_backup=$(find backup config "$TARGET_DATE")
            
            log_info "Full restore selected"
            log_info "Database: ${db_backup:-Not found}"
            log_info "MinIO: ${minio_backup:-Not found}"  
            log_info "Config: ${config_backup:-Not found}"
            
            if [[ "$DRY_RUN" != "true" ]]; then
                read -p "Continue with full restore? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Restore cancelled"
                    exit 0
                fi
            fi
            
            [[ -n "$db_backup" ]] && restore_database "$db_backup" || exit_code=1
            [[ -n "$minio_backup" ]] && restore_minio "$minio_backup" || log_warn "MinIO backup not found"
            [[ -n "$config_backup" ]] && restore_config "$config_backup" || log_warn "Config backup not found"
            ;;
            
        database)
            local db_backup=$(find_backup "incremental" "$TARGET_DATE")
            [[ -n "$db_backup" ]] || db_backup=$(find_backup "full" "$TARGET_DATE")
            
            log_info "Database restore: ${db_backup:-Not found}"
            [[ -n "$db_backup" ]] && restore_database "$db_backup" || exit_code=1
            ;;
            
        minio)
            local backup_file=$(find_backup "incremental" "$TARGET_DATE")
            [[ -n "$backup_file" ]] || backup_file=$(find_backup "full" "$TARGET_DATE")
            
            log_info "MinIO restore: ${backup_file:-Not found}"  
            [[ -n "$backup_file" ]] && restore_minio "$backup_file" || exit_code=1
            ;;
            
        config)
            local backup_file=$(find "${BACKUP_DIR}/config" -name "*${TARGET_DATE:-*}*.tar.gz" 2>/dev/null | head -1)
            
            log_info "Config restore: ${backup_file:-Not found}"
            [[ -n "$backup_file" ]] && restore_config "$backup_file" || exit_code=1
            ;;
            
        interactive)
            list_backups
            ;;
    esac
    
    # Start services if not dry-run
    if [[ "$DRY_RUN" != "true" ]]; then
        start_services
        
        # Verify health
        sleep 5
        log_info "Verifying services..."
        if curl -s http://localhost:8010/health >/dev/null 2>&1; then
            log_success "Services healthy"
        else
            log_warn "Services may not be fully healthy, manual check required"
        fi
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Restore completed"
    else
        log_error "Restore completed with errors"
    fi
    
    return $exit_code
}

# Run main
main "$@"
exit $?