#!/bin/bash
# ================================================================================
# HEALTH MONITORING SCRIPT
# ================================================================================
# Automatski prati zdravlje Docker container-a i restartuje nezdrave
# Pokreće se kao cron job svakih 5 minuta
# 
# Usage: ./health_monitor.sh [ --dry-run ]
# ================================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_DIR:-/var/log}/ai-learning-health.log"

# Kolori izlaz
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local level="$1"
    shift
    local msg="[$level] $(date '+%Y-%m-%d %H:%M:%S') $*"
    echo -e "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# Container-i za praćenje
CONTAINERS=("ai-learning-app" "ai-learning-worker" "ai-learning-beat" "ai-learning-db" "ai-learning-redis" "ai-learning-nginx" "ai-learning-minio")

# Provera da li je container zdrav
check_container_health() {
    local container="$1"
    
    # Proveri da li container postoji
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "NOT_RUNNING"
        return
    fi
    
    # Dohvati health status
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "NO_HEALTH_CHECK")
    
    # Ako nema health check, proveri da li container radi
    if [ "$health_status" = "NO_HEALTH_CHECK" ]; then
        local container_status
        container_status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        if [ "$container_status" = "running" ]; then
            echo "HEALTHY"
        else
            echo "UNHEALTHY"
        fi
        return
    fi
    
    echo "$health_status"
}

# Restartuj container
restart_container() {
    local container="$1"
    local dry_run="${2:-false}"
    
    log "WARN" "Container $container je nezdrav! Restartuje se..."
    
    if [ "$dry_run" = "true" ]; then
        log "INFO" "[DRY-RUN] Restartovao bi: $container"
        return 0
    fi
    
    docker restart "$container"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "INFO" "Uspešno restartovan: $container"
    else
        log "ERROR" "Neuspešan restart: $container (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Glavna funkcija
main() {
    local dry_run=false
    
    if [[ "${1:-}" == "--dry-run" ]]; then
        dry_run=true
        echo "Pokrećem se u DRY-RUN modu..."
    fi
    
    log "INFO" "===== Health Monitoring Start ====="
    
    local unhealthy_containers=()
    local restarted_count=0
    
    for container in "${CONTAINERS[@]}"; do
        local health
        health=$(check_container_health "$container")
        
        echo -n "Container: $container -> Health: $health "
        
        case "$health" in
            "healthy")
                echo -e "${GREEN}✓${NC}"
                ;;
            "unhealthy|starting")
                echo -e "${RED}✗${NC}"
                unhealthy_containers+=("$container")
                if restart_container "$container" "$dry_run"; then
                    ((restarted_count++))
                fi
                ;;
            "NO_HEALTH_CHECK")
                echo -e "${YELLOW}?${NC} (nema health check)"
                ;;
            "NOT_RUNNING")
                echo -e "${RED}✗${NC} (ne radi)"
                unhealthy_containers+=("$container")
                if [ "$dry_run" = "false" ]; then
                    docker start "$container" 2>/dev/null || true
                fi
                ;;
            *)
                echo -e "${YELLOW}?${NC} (status: $health)"
                ;;
        esac
    done
    
    log "INFO" "===== Health Monitoring End ====="
    log "INFO" "Pronađeno ${#unhealthy_containers[@]} nezdravih container-a, restartovano: $restarted_count"
    
    # Exit code: 0 ako je sve OK, 1 ako ima nezdravih
    if [ ${#unhealthy_containers[@]} -gt 0 ]; then
        return 1
    fi
    return 0
}

# Kreiraj log direktorijum ako ne postoji
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# Pokreni
main "$@"