#!/bin/bash
# ================================================================================
# AI LEARNING SYSTEM - COMPLETE SETUP
# ================================================================================
# Ova skripta instalira sve potrebno i pokreće projekat lokalno
# ================================================================================

set -e

echo "=========================================="
echo "AI LEARNING SYSTEM - COMPLETE SETUP"
echo "=========================================="

# ================================================================================
# 1. INSTALACIJA DOCKERA
# ================================================================================
echo ""
echo "🐳 [1/6] Instalacija Docker-a..."

if command -v docker &> /dev/null; then
    echo "✅ Docker je već instaliran: $(docker --version)"
else
    echo "📥 Instaliram Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✅ Docker instaliran!"
    echo "⚠️  Morate se logout/login ili pokrenuti: newgrp docker"
fi

# ================================================================================
# 2. INSTALACIJA DOCKER COMPOSE
# ================================================================================
echo ""
echo "📦 [2/6] Provera Docker Compose..."

if docker compose version &> /dev/null; then
    echo "✅ Docker Compose je instaliran: $(docker compose version)"
else
    echo "📥 Instaliram Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose instaliran!"
fi

# ================================================================================
# 3. INSTALACIJA PYTHON 3.11
# ================================================================================
echo ""
echo "🐍 [3/6] Provera Python 3.11..."

if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 je instaliran: $(python3.11 --version)"
elif command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 je instaliran: $(python3.12 --version)"
    ln -sf /usr/bin/python3.12 /usr/bin/python3.11 2>/dev/null || true
else
    echo "📥 Instaliram Python 3.11..."
    sudo apt-get update
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
    echo "✅ Python 3.11 instaliran!"
fi

# ================================================================================
# 4. KONFIGURACIJA PROJEKTA
# ================================================================================
echo ""
echo "⚙️ [4/6] Konfiguracija projekta..."

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Kreiraj .env ako ne postoji
if [ ! -f "docker/.env" ]; then
    echo "📝 Kreiram .env fajl..."
    cp docker/.env.example docker/.env 2>/dev/null || true
fi

# Kreiraj direktorijume
mkdir -p logs backups storage/uploads

echo "✅ Konfiguracija završena!"

# ================================================================================
# 5. PYTHON VENV
# ================================================================================
echo ""
echo "🐍 [5/6] Postavljanje Python okruženja..."

cd "$PROJECT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "📥 Kreiram virtualno okruženje sa Python 3.11..."
    python3.11 -m venv .venv
    echo "✅ Virtualno okruženje kreirano!"
else
    echo "✅ Virtualno okruženje već postoji"
fi

source .venv/bin/activate

echo "📥 Instaliram Python pakete..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python paketi instalirani!"

# ================================================================================
# 6. FRONTEND
# ================================================================================
echo ""
echo "⚛️ [6/6] Postavljanje Frontend-a..."

cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "📥 Instaliram npm pakete..."
    npm install
    echo "✅ npm paketi instalirani!"
else
    echo "✅ node_modules već postoji"
fi

# ================================================================================
# ZAVRŠETAK
# ================================================================================
echo ""
echo "=========================================="
echo "✅ SVE JE SPREMNO!"
echo "=========================================="
echo ""
echo "📋 SLEDEĆI KORACI:"
echo ""
echo "1. AKO STE PRVI PUT INSTALIRALI DOCKER:"
echo "   - Logout i login"
echo "   - Ili pokrenite: newgrp docker"
echo ""
echo "2. POKRENITE APLIKACIJU:"
echo "   cd $PROJECT_DIR"
echo "   docker compose -f docker/docker-compose.yml up -d"
echo ""
echo "3. ILI POKRENITE BEZ DOCKERA (samo backend):"
echo "   cd $PROJECT_DIR/backend"
echo "   source .venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🌐 DOSTUPNI SERVISI (sa Docker-om):"
echo "   - Backend:      http://localhost:8000"
echo "   - API Docs:    http://localhost:8000/docs"
echo "   - Frontend:    http://localhost:5173"
echo "   - MinIO:       http://localhost:9001"
echo "   - Prometheus:  http://localhost:9090"
echo "   - Grafana:     http://localhost:3000"
echo ""
echo "=========================================="
