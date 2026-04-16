#!/bin/bash

set -e

echo "=== Auto-fix ports for AI Learning System ==="

# Auto-detect project root (where docker-compose.yml is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -z "$PROJECT_ROOT" ] || [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "Error: Cannot find project root (docker-compose.yml not found)"
    exit 1
fi

echo "Project root: $PROJECT_ROOT"

NGINX_PORT=$(docker port ai-learning-nginx 2>/dev/null | head -1 | cut -d':' -f2)
APP_PORT=$(docker port ai-learning-app 2>/dev/null | head -1 | cut -d':' -f2)

if [ -z "$NGINX_PORT" ]; then
    NGINX_PORT=8888
fi

if [ -z "$APP_PORT" ]; then
    APP_PORT=8010
fi

echo "Detected ports:"
echo "  - Nginx (Frontend): $NGINX_PORT"
echo "  - App (API): $APP_PORT"

FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ -f "$FRONTEND_DIR/.env" ]; then
    sed -i "s|http://localhost:[0-9]*/api/v1|http://localhost:$NGINX_PORT/api/v1|g" "$FRONTEND_DIR/.env"
    sed -i "s|http://localhost:[0-9]*/ws|http://localhost:$NGINX_PORT/ws|g" "$FRONTEND_DIR/.env"
    echo "Updated $FRONTEND_DIR/.env"
fi

echo ""
echo "Rebuilding frontend..."
cd "$FRONTEND_DIR"
npm run build > /dev/null 2>&1

echo "Restarting nginx..."
docker restart ai-learning-nginx > /dev/null 2>&1

echo ""
echo "Done! Frontend is now configured for port $NGINX_PORT"
echo "Access the app at: http://localhost:$NGINX_PORT"
