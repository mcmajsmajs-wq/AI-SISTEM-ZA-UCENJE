#!/bin/bash
# ================================================================================
# CLEANUP SCRIPT
# ================================================================================
# Čišćenje stare podatke iz baze
#
# Usage: ./cleanup_db.sh
# ================================================================================

set -euo pipefail

LOG_FILE="/var/log/ai-learning-cleanup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

main() {
    log "===== Database Cleanup Start ====="
    
    local db_container="ai-learning-db"
    local db_name="${POSTGRES_DB:-ai_learning_db}"
    local db_user="${POSTGRES_USER:-ai_learning_user}"
    
    # Proveri da container radi
    if ! docker ps --format '{{.Names}}' | grep -q "^${db_container}$"; then
        log "ERROR" "Container $db_container ne radi!"
        exit 1
    fi
    
    # Obriši stare sesije (starije od 30 dana)
    log "Brišem stare sesije..."
    docker exec "$db_container" psql -U "$db_user" -d "$db_name" -c "
        DELETE FROM user_sessions 
        WHERE created_at < NOW() - INTERVAL '30 days'
    " 2>/dev/null || true
    
    # Obriši stare chat poruke (starije od 90 dana)
    log "Brišem stare chat poruke..."
    docker exec "$db_container" psql -U "$db_user" -d "$db_name" -c "
        DELETE FROM messages 
        WHERE created_at < NOW() - INTERVAL '90 days'
    " 2>/dev/null || true
    
    # Obriši neuspele pokušaje logina (starije od 7 dana)
    log "Brišem neuspele logine..."
    docker exec "$db_container" psql -U "$db_user" -d "$db_name" -c "
        DELETE FROM login_attempts 
        WHERE created_at < NOW() - INTERVAL '7 days'
    " 2>/dev/null || true
    
    # VACUUM - oslobodi prostor
    log "Pokrećem VACUUM..."
    docker exec "$db_container" psql -U "$db_user" -d "$db_name" -c "VACUUM ANALYZE;" 2>/dev/null || true
    
    log "===== Database Cleanup End ====="
}

trap 'log "ERROR" "Cleanup failed with exit code: $?"' ERR
main