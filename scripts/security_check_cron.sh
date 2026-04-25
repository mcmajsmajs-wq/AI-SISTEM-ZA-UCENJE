#!/bin/bash
# Lightweight Security Monitor - Cron version
# Run this every 5 minutes from crontab

LOG_FILE="/var/log/ai-security-monitor.log"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_failed_auth() {
    failed=$(grep -c "Failed password\|authentication failure" /var/log/auth.log 2>/dev/null | tail -1 || echo 0)
    if [ "$failed" -gt 5 ]; then
        log "⚠️ High failed auth: $failed"
        [ -n "$ALERT_WEBHOOK" ] && curl -s -X POST "$ALERT_WEBHOOK" -d "{\"text\":\"⚠️ High failed auth: $failed\"}" || true
    fi
}

check_suspicious_processes() {
    sus=$(ps aux 2>/dev/null | grep -E "nc -l|bash -i.*&|wget.*\|.*bash" | grep -v grep || true)
    if [ -n "$sus" ]; then
        log "🚨 SUSPICIOUS PROCESS: $sus"
        [ -n "$ALERT_WEBHOOK" ] && curl -s -X POST "$ALERT_WEBHOOK" -d "{\"text\":\"🚨 Suspicious process: $sus\"}" || true
    fi
}

check_ports() {
    ports=$(ss -tulpn 2>/dev/null | grep LISTEN || true)
    # Alert if unusual ports (beyond common ones)
    unusual=$(echo "$ports" | grep -vE ":80|:443|:22|:5432|:6379|:3000|:8000|:9000|:9200" || true)
    if [ -n "$unusual" ]; then
        log "⚠️ Unusual ports: $unusual"
    fi
}

check_containers() {
    bad=$(docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null | grep -E "unhealthy|Exited" || true)
    if [ -n "$bad" ]; then
        log "⚠️ Container issues: $bad"
        [ -n "$ALERT_WEBHOOK" ] && curl -s -X POST "$ALERT_WEBHOOK" -d "{\"text\":\"⚠️ Container down: $bad\"}" || true
    fi
}

disk_check() {
    usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        log "🚨 Disk at ${usage}%"
    fi
}

# Run all checks
check_failed_auth
check_suspicious_processes
check_ports
check_containers
disk_check

log "✓ Security check complete"