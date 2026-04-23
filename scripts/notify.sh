#!/bin/bash
# ================================================================================
# ALERT NOTIFICATION SCRIPT
# ================================================================================
# Šalje notifikacije kada se desi alert
# Podržava: Email, Discord, Slack, Webhook
#
# Usage: ./notify.sh --type email --message "Alert message"
# ================================================================================

set -euo pipefail

# Konfiguracija
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL:-}"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_FROM="${EMAIL_FROM:-alerts@ai-learning.local}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
TG_BOT_TOKEN="${TG_BOT_TOKEN:-}"
TG_CHAT_ID="${TG_CHAT_ID:-}"

# Boje za terminal
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Šalji Discord notifikaciju
notify_discord() {
    local message="$1"
    local color="${2:-16711680}"  # Default red
    
    if [ -z "$DISCORD_WEBHOOK" ]; then
        log "WARN" "Discord webhook nije konfigurisan"
        return 1
    fi
    
    local payload
    payload=$(cat <<EOF
{
  "embeds": [{
    "title": "AI Learning Alert",
    "description": "$message",
    "color": $color,
    "timestamp": "$(date -Iseconds)",
    "footer": {"text": "AI Learning System"}
  }]
}
EOF
)
    
    curl -s -X POST "$DISCORD_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1
    
    log "INFO" "Poslata Discord notifikacija"
}

# Šalji Slack notifikaciju
notify_slack() {
    local message="$1"
    
    if [ -z "$SLACK_WEBHOOK" ]; then
        log "WARN" "Slack webhook nije konfigurisan"
        return 1
    fi
    
    local payload
    payload=$(cat <<EOF
{
  "text": "AI Learning Alert",
  "attachments": [{
    "color": "danger",
    "title": "Alert",
    "text": "$message",
    "footer": "AI Learning System"
  }]
}
EOF
)
    
    curl -s -X POST "$SLACK_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1
    
    log "INFO" "Poslata Slack notifikacija"
}

# Šalji email
notify_email() {
    local message="$1"
    local subject="${2:-AI Learning Alert}"
    
    if [ -z "$EMAIL_TO" ]; then
        log "WARN" "Email nije konfigurisan"
        return 1
    fi
    
    echo -e "$message" | mail -s "$subject" -r "$EMAIL_FROM" "$EMAIL_TO" 2>/dev/null || true
    
    log "INFO" "Poslat email"
}

# Šalji generic webhook
notify_webhook() {
    local message="$1"
    
    if [ -z "$WEBHOOK_URL" ]; then
        log "WARN" "Webhook URL nije konfigurisan"
        return 1
    fi
    
    curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"timestamp\": \"$(date -Iseconds)\"}" >/dev/null 2>&1
    
    log "INFO" "Poslat webhook"
}

# Telegram notifikacija
notify_telegram() {
    local message="$1"
    
    if [ -z "$TG_BOT_TOKEN" ] || [ -z "$TG_CHAT_ID" ]; then
        log "WARN" "Telegram nije konfigurisan"
        return 1
    fi
    
    local url="https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage"
    local payload
    payload=$(cat <<EOF
{
  "chat_id": "$TG_CHAT_ID",
  "text": "AI Learning Alert: $message"
}
EOF
)
    
    curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1
    
    log "INFO" "Poslata Telegram notifikacija"
}

# Glavna funkcija
main() {
    local type="${1:-discord}"
    local message="${2:-Alert from AI Learning System}"
    local title="${3:-}"
    
    log "INFO" "Slanje notifikacije tip: $type, poruka: $message"
    
    case "$type" in
        discord)
            notify_discord "$message" 16711680
            ;;
        slack)
            notify_slack "$message"
            ;;
        email|mail)
            notify_email "$message" "$title"
            ;;
        webhook)
            notify_webhook "$message"
            ;;
        telegram|tg)
            notify_telegram "$message"
            ;;
        all)
            notify_discord "$message" 16711680
            notify_slack "$message"
            notify_telegram "$message"
            ;;
        *)
            log "ERROR" "Nepoznat tip: $type"
            return 1
            ;;
    esac
}

# Help
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [type] [message] [title]"
    echo ""
    echo "Types: discord, slack, email, webhook, telegram, all"
    echo ""
    echo "Environment variables:"
    echo "  DISCORD_WEBHOOK_URL  - Discord webhook URL"
    echo "  SLACK_WEBHOOK_URL - Slack webhook URL"
    echo "  EMAIL_TO            - Email recipient"
    echo "  WEBHOOK_URL       - Generic webhook URL"
    echo "  TG_BOT_TOKEN      - Telegram bot token"
    echo "  TG_CHAT_ID        - Telegram chat ID"
    exit 0
fi

main "$@"