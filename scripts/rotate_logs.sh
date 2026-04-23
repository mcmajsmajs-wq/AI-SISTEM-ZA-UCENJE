#!/bin/bash
# ================================================================================
# LOG ROTATION SCRIPT
# ================================================================================
# Rotira log fajlove
#
# Usage: ./rotate_logs.sh
# ================================================================================

set -euo pipefail

LOG_DIR="${LOG_DIR:-/var/log}"
LOG_FILE="/var/log/ai-learning-rotate.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

main() {
    log "===== Log Rotation Start ====="
    
    # Rotiraj JSON log fajlove
    find "$LOG_DIR" -name "ai-learning*.log" -type f 2>/dev/null | while read -r logfile; do
        if [ -f "$logfile" ] && [ "$(stat -c %s "$logfile" 2>/dev/null || echo 0)" -gt 10485760 ]; then
            log "Rotiram: $logfile"
            mv "$logfile" "${logfile}.old"
            touch "$logfile"
            chmod 644 "$logfile"
        fi
    done
    
    # Obriši stare .log.old fajlove (starije od 7 dana)
    find "$LOG_DIR" -name "*.log.old" -mtime +7 -delete 2>/dev/null || true
    
    log "===== Log Rotation End ====="
}

trap 'log "ERROR" "Log rotation failed with exit code: $?"' ERR
main