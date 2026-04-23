#!/bin/bash
# ================================================================================
# GITHUB STATUS CHECKER - Self-Sustaining Monitor
# ================================================================================
# Automatski proverava GitHub CI/CD status, issues, i PR-ove
# Koristi GITHUB_TOKEN iz GitHub Actions secrets (kriptovano)
#
# Usage: ./github_status.sh [options]
# 
# Opcije:
#   --check-runs   Proverava CI/CD workflow runs
#   --check-issues  Proverava otvorene issues
#   --check-prs     Proverava pull request-ove
#   --all          Sve provere (default)
# ================================================================================

set -euo pipefail

# GitHub konfiguracija
REPO="${REPO:-BrankoRF/AI-SISTEM-ZA-UCENJE}"
GITHUB_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"

# Boje
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Provera da li imamo token
check_token() {
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}ERROR: GITHUB_TOKEN nije postavljen!${NC}"
        echo "Postavi ga kao:"
        echo "  export GITHUB_TOKEN=ghp_xxx"
        echo "Ili u GitHub Actions secrets"
        return 1
    fi
    return 0
}

# GitHub API poziv
github_api() {
    local endpoint="$1"
    local method="${2:-GET}"
    
    curl -s -X "$method" \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/$endpoint"
}

# Provera CI/CD workflow runs
check_runs() {
    echo -e "${BLUE}═══ Checking CI/CD Runs ═══${NC}"
    
    local runs
    runs=$(github_api "repos/$REPO/actions/runs?per_page=5")
    
    local total_runs
    total_runs=$(echo "$runs" | jq -r '.workflow_runs | length' 2>/dev/null || echo "0")
    
    if [ "$total_runs" = "0" ] || [ "$total_runs" = "null" ]; then
        echo -e "${YELLOW}⚠ Nema recent workflow runs${NC}"
        return
    fi
    
    echo "$runs" | jq -r '.workflow_runs[] | 
        "\(.status) - \(.conclusion // "running") | \(.name) | \(.created_at[0:10])"' | \
        while read -r status conclusion name date; do
            case "$conclusion" in
                "success")
                    echo -e "  ✅ $name ($date): SUCCESS"
                    ;;
                "failure")
                    echo -e "  ❌ $name ($date): FAILED"
                    echo -e "     URL: $(echo "$runs" | jq -r '.workflow_runs[] | select(.name=="'"$name"'") | .html_url')"
                    ;;
                "in_progress"|"queued")
                    echo -e "  🔄 $name ($date): RUNNING"
                    ;;
                *)
                    echo -e "  ⚪ $name ($date): $conclusion"
                    ;;
            esac
        done
    
    # Najnoviji run
    local latest_status
    latest_status=$(echo "$runs" | jq -r '.workflow_runs[0].conclusion')
    local latest_name
    latest_name=$(echo "$runs" | jq -r '.workflow_runs[0].name')
    
    echo ""
    echo -e "Latest: $latest_name -> $latest_status"
}

# Provera otvorenih issues
check_issues() {
    echo -e "${BLUE}═══ Checking Issues ═══${NC}"
    
    local issues
    issues=$(github_api "repos/$REPO/issues?state=open")
    
    local total
    total=$(echo "$issues" | jq 'length')
    
    if [ "$total" = "0" ]; then
        echo -e "${GREEN}✅ Nema otvorenih issues!${NC}"
        return
    fi
    
    echo -e "${YELLOW}⚠️ $total otvorenih issues:${NC}"
    
    echo "$issues" | jq -r '.[] | 
        "  #\(.number): \(.title)
       User: \(.user.login)
       Labels: \(.labels | map(.name) | join(", "))
       URL: \(.html_url)"' | head -40
}

# Provera PR-ova
check_prs() {
    echo -e "${BLUE}═══ Checking Pull Requests ═══${NC}"
    
    local prs
    prs=$(github_api "repos/$REPO/pulls?state=open")
    
    local total
    total=$(echo "$prs" | jq 'length')
    
    if [ "$total" = "0" ]; then
        echo -e "${GREEN}✅ Nema otvorenih PR-ova!${NC}"
        return
    fi
    
    echo -e "${YELLOW}⚠️ $total otvorenih PR-ova:${NC}"
    
    echo "$prs" | jq -r '.[] | 
        "  #\(.number): \(.title)
       User: \(.user.login)
       Status: \(.mergeable_state)
       URL: \(.html_url)"' | head -30
}

# Provera workflow jobs
check_jobs() {
    echo -e "${BLUE}═══ Checking Latest Workflow Jobs ═══${NC}"
    
    local run_id
    run_id=$(github_api "repos/$REPO/actions/runs?per_page=1" | jq -r '.workflow_runs[0].id')
    
    if [ "$run_id" = "null" ] || [ -z "$run_id" ]; then
        echo -e "${YELLOW}⚠ Nema workflow runs${NC}"
        return
    fi
    
    echo "Run ID: $run_id"
    
    local jobs
    jobs=$(github_api "repos/$REPO/actions/runs/$run_id/jobs")
    
    echo "$jobs" | jq -r '.jobs[] | 
        "  \(.name): \(.status) - \(.conclusion // "pending")"' 
}

# Glavna funkcija
main() {
    local mode="${1:-all}"
    
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}  GitHub Status Checker${NC}"
    echo -e "${BLUE}  Repo: $REPO${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    check_token || exit 1
    
    case "$mode" in
        --check-runs)
            check_runs
            ;;
        --check-issues)
            check_issues
            ;;
        --check-prs)
            check_prs
            ;;
        --check-jobs)
            check_jobs
            ;;
        --all)
            check_runs
            echo ""
            check_issues
            echo ""
            check_prs
            ;;
        *)
            echo "Usage: $0 [--check-runs|--check-issues|--check-prs|--check-jobs|--all]"
            exit 1
            ;;
    esac
}

main "$@"
