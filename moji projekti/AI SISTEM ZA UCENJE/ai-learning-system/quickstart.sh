#!/bin/bash
# ================================================================================
# AI LEARNING SYSTEM - QUICK START
# ================================================================================
# Pokreni: bash quickstart.sh
# ================================================================================

PROJECT_DIR="$HOME/ai-learning-system"

echo "=========================================="
echo "AI Learning System - Quick Start"
echo "=========================================="

# Proveri da li direktorijum postoji
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Projekat nije pronađen. Pokreni prvo install.sh"
    exit 1
fi

# ================================================================================
# POKRENI BACKEND
# ================================================================================
echo ""
echo "🐍 Pokrećem backend..."

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "❌ Virtualno okruženje ne postoji. Pokreni install.sh"
    exit 1
fi

source venv/bin/activate

# Pokreni u pozadini
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "✅ Backend pokrenut (PID: $BACKEND_PID)"

# ================================================================================
# POKRENI FRONTEND
# ================================================================================
echo ""
echo "⚛️ Pokrećem frontend..."

cd "$PROJECT_DIR/frontend"

# Proveri da li node_modules postoji
if [ ! -d "node_modules" ]; then
    echo "❌ npm paketi nisu instalirani. Pokreni install.sh"
    exit 1
fi

# Pokreni u pozadini
npm run dev &
FRONTEND_PID=$!

echo "✅ Frontend pokrenut (PID: $FRONTEND_PID)"

# ================================================================================
# INFORMACIJE
# ================================================================================
echo ""
echo "=========================================="
echo "🎉 SISTEM JE POKRENUT!"
echo "=========================================="
echo ""
echo "🌐 Pristupi aplikaciji:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Da zaustaviš sistem, pokreni:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=========================================="

# Čekaj da korisnik pritisne Ctrl+C
trap "echo ''; echo '🛑 Zaustavljam...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
