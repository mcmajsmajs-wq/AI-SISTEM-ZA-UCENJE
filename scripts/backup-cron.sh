#!/bin/bash
#
# AI Learning System - Cron Setup
# Version: 1.0
# Purpose: Setup automated backup cron jobs
#
# Usage:
#   ./backup-cron.sh           # Setup all cron jobs
#   ./backup-cron.sh --remove  # Remove all cron jobs
#   ./backup-cron.sh --verify # Verify cron is running
#

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
RESTORE_SCRIPT="${SCRIPT_DIR}/restore.sh"

CRON_FILE="/etc/cron.d/ai-learning-backup"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

#==============================================================================
# PARSE ARGUMENTS
#==============================================================================
ACTION="install"

while [[ $# -gt 0 ]]; do
    case $1 in
        --remove|--uninstall)
            ACTION="remove"
            ;;
        --verify|--status)
            ACTION="verify"
            ;;
    esac
    shift
done

#==============================================================================
# INSTALL
#==============================================================================
install_cron() {
    log "Installing backup cron jobs..."
    
    # Make scripts executable
    chmod +x "${BACKUP_SCRIPT}" "${RESTORE_SCRIPT}"
    
    # Create cron file
    cat > "${CRON_FILE}" <<EOF
# AI Learning System - Backup Cron Jobs
# Managed by backup-cron.sh

# Full backup - Nedjelja u 02:00
0 2 * * 0 root ${BACKUP_SCRIPT} --type=full >> ${BACKUP_DIR}/cron.log 2>&1

# Incremental backup - Ponedjeljak do Subota u 02:00
0 2 * * 1-6 root ${BACKUP_SCRIPT} >> ${BACKUP_DIR}/cron.log 2>&1

# Monthly archive - 1. u mjesecu u 03:00
0 3 1 * * root ${BACKUP_SCRIPT} --type=archive >> ${BACKUP_DIR}/cron.log 2>&1

# Security check - svaki sati u 00:00
0 0 * * * root /home/dju/projects/ai-learning/scripts/security_check_cron.sh >> /var/log/ai-security-monitor.log 2>&1

EOF
    
    chmod 644 "${CRON_FILE}"
    
    echo -e "${GREEN}✓ Cron jobs installed${NC}"
    echo ""
    echo "Schedule:"
    echo "  - Full backup: Nedjelja 02:00"
    echo "  - Incremental: Pon-Sub 02:00"
    echo "  - Monthly: 1. u mjesecu 03:00"
    echo "  - Security: svaki sat"
}

#==============================================================================
# REMOVE
#==============================================================================
remove_cron() {
    log "Removing backup cron jobs..."
    
    rm -f "${CRON_FILE}"
    
    echo -e "${GREEN}✓ Cron jobs removed${NC}"
}

#==============================================================================
# VERIFY
#==============================================================================
verify_cron() {
    log "Verifying cron jobs..."
    
    if [[ -f "${CRON_FILE}" ]]; then
        echo -e "${GREEN}✓ Cron file exists${NC}"
        echo ""
        cat "${CRON_FILE}"
    else
        echo -e "${RED}✗ Cron file not found${NC}"
    fi
    
    # Check if cron is running
    if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
        echo -e "${GREEN}✓ Cron service is running${NC}"
    else
        echo -e "${RED}✗ Cron service not running${NC}"
    fi
    
    # Show next runs
    echo ""
    echo "Next scheduled backups:"
    crontab -l 2>/dev/null | grep backup || echo "No backup crontab entries"
}

#==============================================================================
# MAIN
#==============================================================================
case "$ACTION" in
    install)
        install_cron
        verify_cron
        ;;
    remove)
        remove_cron
        ;;
    verify)
        verify_cron
        ;;
esac