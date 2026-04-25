#!/bin/bash
# MCP Servers Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================="
echo "  MCP Servers Starting..."
echo "=================================="

# ANSI colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to start a server
start_server() {
    local name=$1
    local command=$2
    local dir=$3
    
    log_info "Starting $name..."
    
    if [ -d "$dir" ]; then
        cd "$dir"
        $command > /dev/null 2>&1 &
        local pid=$!
        echo $pid > /tmp/mcp_${name}.pid
        log_success "$name started (PID: $pid)"
        cd - > /dev/null
    else
        log_error "$name directory not found: $dir"
    fi
}

# Parse arguments
ACTION=${1:-start}

case $ACTION in
    start)
        echo ""
        log_info "Starting all MCP servers..."
        echo ""
        
        # Start Ubuntu Server
        start_server "ubuntu-server" "node index.js" "$SCRIPT_DIR/servers/javascript/ubuntu-server"
        
        echo ""
        log_success "All MCP servers started!"
        echo ""
        echo "To view PIDs: ls /tmp/mcp_*.pid"
        ;;
        
    stop)
        echo ""
        log_info "Stopping all MCP servers..."
        echo ""
        
        for pidfile in /tmp/mcp_*.pid; do
            if [ -f "$pidfile" ]; then
                name=$(basename "$pidfile" .pid | sed 's/mcp_//')
                pid=$(cat "$pidfile")
                if kill -0 "$pid" 2>/dev/null; then
                    kill "$pid" 2>/dev/null || true
                    log_success "Stopped $name (PID: $pid)"
                fi
                rm -f "$pidfile"
            fi
        done
        
        echo ""
        log_success "All MCP servers stopped!"
        ;;
        
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
        
    status)
        echo ""
        log_info "MCP Servers Status:"
        echo ""
        
        for pidfile in /tmp/mcp_*.pid; do
            if [ -f "$pidfile" ]; then
                name=$(basename "$pidfile" .pid | sed 's/mcp_//')
                pid=$(cat "$pidfile")
                if kill -0 "$pid" 2>/dev/null; then
                    log_success "$name is running (PID: $pid)"
                else
                    log_error "$name is NOT running (stale PID file)"
                fi
            fi
        done
        
        if [ ! -f /tmp/mcp_*.pid ]; then
            log_info "No MCP servers running"
        fi
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
