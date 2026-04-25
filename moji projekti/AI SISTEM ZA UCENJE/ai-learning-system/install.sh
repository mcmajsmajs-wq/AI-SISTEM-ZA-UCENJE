#!/bin/bash
# ================================================================================
# AI LEARNING SYSTEM - AUTOMATIC INSTALLER
# ================================================================================
# Pokreni ovu skriptu na Ubuntu: bash install.sh
# ================================================================================

set -e

echo "=========================================="
echo "AI Learning System - Installer"
echo "=========================================="

# ================================================================================
# 1. PREUVETI
# ================================================================================
echo ""
echo "📦 Provera sistema..."

# Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nije instaliran. Instaliram..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip
fi

# Node.js 18+
if ! command -v node &> /dev/null; then
    echo "❌ Node.js nije instaliran. Instaliram..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

# Git
if ! command -v git &> /dev/null; then
    echo "❌ Git nije instaliran. Instaliram..."
    apt-get install -y git
fi

echo "✅ Sistem spreman!"

# ================================================================================
# 2. KREIRANJE DIREKTORIJUMA
# ================================================================================
echo ""
echo "📁 Kreiram direktorijume..."

PROJECT_DIR="$HOME/ai-learning-system"
mkdir -p "$PROJECT_DIR/backend"
mkdir -p "$PROJECT_DIR/frontend"
mkdir -p "$PROJECT_DIR/docker"
mkdir -p "$PROJECT_DIR/backups"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/storage/uploads"

cd "$PROJECT_DIR"

echo "✅ Direktorijumi kreirani u: $PROJECT_DIR"

# ================================================================================
# 3. BACKEND SETUP
# ================================================================================
echo ""
echo "🐍 Postavljam Python backend..."

cd "$PROJECT_DIR/backend"

# Kreiraj virtualno okruženje
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Kreiraj requirements.txt ako ne postoji
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Config
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Storage
boto3==1.34.14
botocore==1.34.14

# PDF Processing
pymupdf==1.23.8
Pillow==10.2.0

# AI/LLM
langchain==0.1.4
langchain-community==0.0.16
openai==1.10.0
tiktoken==0.5.2

# Utilities
python-dateutil==2.8.2
pytz==2024.1
aiofiles==23.2.1
python-magic==0.4.27

# Monitoring
prometheus-client==0.19.0
structlog==24.1.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.4
pytest-cov==4.1.0
black==24.1.1
flake8==7.0.0
mypy==1.8.0
EOF
fi

# Instaliraj dependencies
pip install -r requirements.txt

echo "✅ Python backend spreman!"

# ================================================================================
# 4. FRONTEND SETUP
# ================================================================================
echo ""
echo "⚛️ Postavljam React frontend..."

cd "$PROJECT_DIR/frontend"

# Kreiraj package.json
if [ ! -f "package.json" ]; then
    cat > package.json << 'EOF'
{
  "name": "ai-learning-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.17.19",
    "axios": "^1.6.7",
    "zustand": "^4.5.0",
    "lucide-react": "^0.323.0",
    "clsx": "^2.1.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.0"
  }
}
EOF
fi

# Instaliraj
npm install

echo "✅ Frontend spreman!"

# ================================================================================
# 5. KONFIGURACIJA
# ================================================================================
echo ""
echo "⚙️ Kreiram konfiguraciju..."

cd "$PROJECT_DIR/backend"

# .env fajl
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# ========================
# APLIKACIJA
# ========================
PROJECT_NAME="AI Learning System"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production

# ========================
# DATABASE
# ========================
DATABASE_URL=sqlite:///./ai_learning.db

# ========================
# REDIS
# ========================
REDIS_HOST=localhost
REDIS_PORT=6379

# ========================
# STORAGE (LOKALNI)
# ========================
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=../storage/uploads

# ========================
# AI / LLM
# ========================
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ========================
# CORS
# ========================
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# ========================
# RATE LIMITING
# ========================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
EOF
fi

cd "$PROJECT_DIR/frontend"

# .env fajl
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000/api/v1
EOF
fi

echo "✅ Konfiguracija kreirana!"

# ================================================================================
# 6. DOCKER (OPCIIONO)
# ================================================================================
echo ""
echo "🐳 Da li želite da instalirate Docker? (y/n)"
read -r response

if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    echo "Instaliram Docker..."
    
    # Docker
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $USER
    
    # Docker Compose
    apt-get install -y docker-compose
    
    echo "✅ Docker instaliran!"
    echo "⚠️  Morate se logout/login ili pokrenuti: newgrp docker"
fi

# ================================================================================
# 7. ZAVRŠETAK
# ================================================================================
echo ""
echo "=========================================="
echo "✅ INSTALACIJA ZAVRŠENA!"
echo "=========================================="
echo ""
echo "📋 SLEDEĆI KORACI:"
echo ""
echo "1. Aktiviraj Python virtualno okruženje:"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo ""
echo "2. Pokreni backend:"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. U novom terminalu, pokreni frontend:"
echo "   cd $PROJECT_DIR/frontend"
echo "   npm run dev"
echo ""
echo "🌐 Aplikacija će biti dostupna na:"
echo "   - Backend: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Frontend: http://localhost:5173"
echo ""
echo "=========================================="
