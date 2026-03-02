#!/bin/bash
# ================================================================================
# LOCAL DEV SETUP — AI Learning System
# ================================================================================
# Postavlja lokalno razvojno okruženje za pokretanje testova BEZ Dockera.
# Za pokretanje kompletne aplikacije koristi Docker (docker-compose).
#
# Upotreba:
#   chmod +x setup_local_dev.sh
#   ./setup_local_dev.sh
# ================================================================================

set -e
YELLOW='\033[1;33m'; GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} AI Learning System — Local Dev Setup  ${NC}"
echo -e "${BLUE}========================================${NC}"

# ── 1. Python venv ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/5] Kreiranje Python virtualnog okruženja...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✅ venv kreiran: backend/.venv${NC}"
else
    echo -e "${GREEN}✅ venv već postoji${NC}"
fi

source .venv/bin/activate

# ── 2. Install dev dependencies ────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/5] Instalacija Python dev paketa...${NC}"
pip install --upgrade pip -q
pip install -r requirements-dev.txt -q
echo -e "${GREEN}✅ Python paketi instalirani${NC}"

# ── 3. Env file ────────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/5] Provera .env fajla...${NC}"
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  .env kreiran iz .env.example — popuni API ključeve!${NC}"
elif [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env postoji${NC}"
else
    cat > .env << 'ENVEOF'
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=dev-secret-key-change-in-production
UPLOAD_FOLDER=/tmp/ai-learning-uploads
REDIS_URL=redis://localhost:6379/0
ENVEOF
    echo -e "${GREEN}✅ Minimalan .env kreiran (SQLite + /tmp za testove)${NC}"
fi

# ── 4. Run unit tests ──────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[4/5] Pokretanje unit testova...${NC}"
SQLALCHEMY_DATABASE_URI="sqlite:///./test_local.db" PYTHONPATH=. .venv/bin/pytest app/tests/unit/ \
    -v --timeout=30 -q 2>&1 | tail -20
rm -f test_local.db
echo ""

# ── 5. Frontend ────────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[5/5] Provera Frontend paketa...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Instalacija npm paketa...${NC}"
    npm install --legacy-peer-deps -q
    echo -e "${GREEN}✅ npm paketi instalirani${NC}"
else
    echo -e "${GREEN}✅ node_modules postoji${NC}"
fi

# TypeScript provjera
echo -e "${YELLOW}TypeScript provjera tipova...${NC}"
npx tsc --noEmit 2>&1 | head -20 && echo -e "${GREEN}✅ TypeScript OK${NC}" || echo -e "${YELLOW}⚠️  TypeScript upozorenja (ne blokiraju build)${NC}"

# ── Sažetak ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Setup završen!${NC}"
echo ""
echo -e "${YELLOW}📋 Lokalne komande:${NC}"
echo -e "  ${BLUE}Unit testovi:${NC}     cd backend && source .venv/bin/activate && pytest app/tests/unit/ -v"
echo -e "  ${BLUE}Sve komande:${NC}      cd backend && source .venv/bin/activate && pytest app/tests/ -v"
echo -e "  ${BLUE}Frontend dev:${NC}     cd frontend && npm run dev"
echo ""
echo -e "${YELLOW}🐳 Docker komande (puna aplikacija):${NC}"
echo -e "  ${BLUE}Pokretanje:${NC}       cd docker && docker compose up -d"
echo -e "  ${BLUE}Rebuild:${NC}          cd docker && docker compose up --build -d"
echo -e "  ${BLUE}Worker logovi:${NC}    cd docker && docker compose logs worker -f"
echo -e "  ${BLUE}App logovi:${NC}       cd docker && docker compose logs app -f"
echo -e "${BLUE}========================================${NC}"
