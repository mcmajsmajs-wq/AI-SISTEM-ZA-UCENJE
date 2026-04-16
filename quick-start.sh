#!/bin/bash
# ================================================================================
# QUICK START SCRIPT - AI LEARNING SYSTEM
# ================================================================================
# Pokrenite ovaj skript za brzo pokretanje projekta
# ================================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$PROJECT_DIR/docker"

echo "=================================================="
echo "AI LEARNING SYSTEM - QUICK START"
echo "=================================================="

# Provera Docker-a
echo ""
echo "[1/5] Provera Docker instalacije..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nije instaliran!"
    echo ""
    echo "Pokrenite sledeće komande za instalaciju:"
    echo "  curl -fsSL https://get.docker.com | sh"
    echo "  sudo usermod -aG docker \$USER"
    echo "  newgrp docker"
    exit 1
fi
echo "✅ Docker je instaliran: $(docker --version)"

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose nije instaliran!"
    exit 1
fi
echo "✅ Docker Compose je instaliran: $(docker compose version)"

# Provera .env fajla
echo ""
echo "[2/5] Provera konfiguracije..."
if [ ! -f "$DOCKER_DIR/.env" ]; then
    echo "Kreiram .env fajl..."
    cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
    echo "✅ .env fajl kreiran"
else
    echo "✅ .env fajl postoji"
fi

# Kreiranje __init__.py fajlova
echo ""
echo "[3/5] Kreiranje Python modula..."
cd "$PROJECT_DIR/backend/app"
find . -type d -exec touch {}/__init__.py \; 2>/dev/null || true
echo "✅ Python moduli kreirani"

# Kreiranje direktorijuma
echo ""
echo "[4/5] Kreiranje direktorijuma..."
cd "$PROJECT_DIR"
mkdir -p logs backups docker/nginx/ssl docker/grafana/dashboards docker/grafana/datasources
echo "✅ Direktorijumi kreirani"

# Pokretanje Docker-a
echo ""
echo "[5/5] Pokretanje Docker kontejnera..."
cd "$DOCKER_DIR"
echo "Ovo može potrajati nekoliko minuta..."
docker compose up -d --build

echo ""
echo "=================================================="
echo "Čekam da se servisi podignu..."
echo "=================================================="
sleep 10

# Provera statusa
echo ""
echo "Status servisa:"
docker compose ps

echo ""
echo "=================================================="
echo "VERIFIKACIJA"
echo "=================================================="

# Health check - proverava oba porta
echo ""
echo "Health check (backend):"
curl -s http://localhost:8010/health 2>/dev/null | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8010/health

echo ""
echo "Health check (nginx):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/ || echo "Nginx nije dostupan"

echo ""
echo ""
echo "=================================================="
echo "DOSTUPNI SERVISI"
echo "=================================================="
echo "Frontend (NGINX): http://localhost:8090"
echo "Backend API:      http://localhost:8010"
echo "API Docs:         http://localhost:8010/docs"
echo "MinIO API:        http://localhost:9002"
echo "MinIO Console:    http://localhost:9003"
echo "Grafana:          http://localhost:3000"
echo "Prometheus:       http://localhost:9090"
echo "Ollama API:       http://localhost:11434"
echo ""
echo "=================================================="
echo "VERIFIKACIJA (FAZA 10-11)"
echo "=================================================="
echo ""
echo "Pokrenite verifikaciju:"
echo "  make verify-faza10  # Testovi i integracija"
echo "  make verify-faza11  # Optimizacije"
echo ""
echo "Ili ručno:"
echo "  docker compose exec app python backend/scripts/verify_faza10.py"
echo "  docker compose exec app python backend/scripts/verify_faza11.py"
echo ""
echo "=================================================="
echo "SLEDEĆI KORACI"
echo "=================================================="
echo "1. Preuzmite AI model:"
echo "   docker compose exec ollama ollama pull llama3.1"
echo ""
echo "2. Pratite logove:"
echo "   docker compose logs -f app"
echo ""
echo "3. Proverite status optimizacija:"
echo "   make optimize-stats"
echo ""
echo "4. Zaustavite servis:"
echo "   docker compose down"
echo ""
echo "=================================================="
