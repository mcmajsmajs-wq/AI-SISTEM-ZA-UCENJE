#!/bin/bash
# ================================================================================
# DATABASE BACKUP SCRIPT
# ================================================================================
# Automatski backup PostgreSQL baze
# Čuva zadnjih 7 dnevnih, 4 nedeljna i 6 mesečnih backup-a
#
# Usage: ./backup_db.sh [ --keep-local ]
# ================================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/home/dju/projects/ai-learning/backups}"
LOG_FILE="/var/log/ai-learning-backup.log"

# Dani za čuvanje
DAILY_KEEP=7      # 7 dnevnih
WEEKLY_KEEP=4      # 4 nedeljna
MONTHLY_KEEP=6     # 6 mesečnih

# Format vremena
TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
DATE=$(date '+%Y-%m-%d')
DAY_OF_WEEK=$(date '+%u')
DAY_OF_MONTH=$(date '+%d')

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Kreiraj backup direktorijum
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}

# Glavna funkcija
main() {
    log "===== Database Backup Start ====="
    
    local db_container="ai-learning-db"
    local db_name="${POSTGRES_DB:-ai_learning_db}"
    local db_user="${POSTGRES_USER:-ai_learning_user}"
    local backup_file="$BACKUP_DIR/daily/${db_name}_${TIMESTAMP}.sql.gz"
    
    # Proveri da container radi
    if ! docker ps --format '{{.Names}}' | grep -q "^${db_container}$"; then
        log "ERROR" "Container $db_container ne radi!"
        exit 1
    fi
    
    log "Kreiram backup: $backup_file"
    
    # Kreiraj backup
    docker exec "$db_container" pg_dump -U "$db_user" -d "$db_name" | gzip > "$backup_file"
    
    # Proveri da li je backup uspešan
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        local size
        size=$(du -h "$backup_file" | cut -f1)
        log "Uspešan backup: $backup_file ($size)"
    else
        log "ERROR" "Backup neuspešan ili prazan!"
        exit 1
    fi
    
    # Očisti stare backup-e
    cleanup_old_backups
    
    log "===== Database Backup End ====="
}

# Čišćenje starih backup-a
cleanup_old_backups() {
    log "Čišćenje starih backup-a..."
    
    # Dnevni backup-i (briši starije od $DAILY_KEEP dana)
    find "$BACKUP_DIR/daily" -name "*.sql.gz" -mtime +$DAILY_KEEP -delete 2>/dev/null || true
    
    # Nedeljni backup-i (briši ako ima više od $WEEKLY_KEEP)
    local weekly_count
    weekly_count=$(find "$BACKUP_DIR/weekly" -name "*.sql.gz" 2>/dev/null | wc -l)
    if [ "$weekly_count" -ge "$WEEKLY_KEEP" ]; then
        find "$BACKUP_DIR/weekly" -name "*.sql.gz" -oldest -delete 2>/dev/null || true
    fi
    
    # Mesečni backup-i (briši ako ima više od $MONTHLY_KEEP)
    local monthly_count
    monthly_count=$(find "$BACKUP_DIR/monthly" -name "*.sql.gz" 2>/dev/null | wc -l)
    if [ "$monthly_count" -ge "$MONTHLY_KEEP" ]; then
        find "$BACKUP_DIR/monthly" -name "*.sql.gz" -oldest -delete 2>/dev/null || true
    fi
    
    log "Čišćenje završeno"
}

# Kreiraj nedeljni/mesečni backup kopijom
create_periodic_backup() {
    local latest_daily
    latest_daily=$(ls -t "$BACKUP_DIR/daily"/*.sql.gz 2>/dev/null | head -1)
    
    if [ -z "$latest_daily" ]; then
        log "WARN" "Nema dnevnih backup-a za arhiviranje"
        return
    fi
    
    # Nedeljno (nedelja)
    if [ "$DAY_OF_WEEK" = "7" ]; then
        cp "$latest_daily" "$BACKUP_DIR/weekly/"
        log "Kreiran nedeljni backup"
    fi
    
    # Mesečno (prvi dan meseca)
    if [ "$DAY_OF_MONTH" = "01" ]; then
        cp "$latest_daily" "$BACKUP_DIR/monthly/"
        log "Kreiran mesečni backup"
    fi
}

# Exit code za cron
trap 'log "ERROR" "Backup script failed with exit code: $?"' ERR

main "$@"
create_periodic_backup