# ================================================================================
# LOKALNI RAZVOJ - QUICK START GUIDE
# ================================================================================
# Vodič za pokretanje AI Learning System bez Docker-a
# Verzija: 1.0.0
# Datum: 2026-02-28
# ================================================================================

## Preduvjeti

| Alat | Verzija | Napomena |
|------|---------|----------|
| Python | 3.11+ | Preporučeno 3.11 ili 3.12 |
| Node.js | 18+ | Za frontend |
| npm | 9+ | Dolazi sa Node.js |
| SQLite | - | Ugrađen u Python |

---

## 1. Backend Setup

### 1.1 Kreiranje virtualnog okruženja

```bash
cd ai-learning-system/backend

# Kreiranje virtualnog okruženja
python3 -m venv venv

# Aktivacija (Linux/Mac)
source venv/bin/activate

# Aktivacija (Windows)
venv\Scripts\activate
```

### 1.2 Instalacija dependencies

```bash
# Sa requirements.txt
pip install -r requirements.txt

# Ili minimalna instalacija za lokalni razvoj
pip install fastapi uvicorn[standard] sqlalchemy pydantic-settings \
    python-jose[cryptography] passlib[bcrypt] python-multipart \
    pymupdf aiofiles pytz python-dotenv
```

### 1.3 Konfiguracija (.env)

Kreiraj `backend/.env` fajl:

```bash
# Aplikacija
PROJECT_NAME="AI Learning System"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production

# Storage - LOKALNI RAZVOJ (ovo je default)
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage/uploads

# Baza podataka - SQLite za lokalni razvoj
DATABASE_URL=sqlite:///./ai_learning.db

# Redis (opciono - za produkciju)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 1.4 Kreiranje baze podataka

```bash
cd backend

# Inicijalizacija baze (automatski pri startu u debug modu)
# Ili ručno:
python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
```

### 1.5 Pokretanje backend-a

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Backend će biti dostupan na: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## 2. Frontend Setup

### 2.1 Instalacija

```bash
cd ai-learning-system/frontend
npm install
```

### 2.2 Konfiguracija (.env)

Kreiraj `frontend/.env` fajl:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### 2.3 Pokretanje frontend-a

```bash
npm run dev

# Frontend će biti dostupan na: http://localhost:5173
```

---

## 3. Opcioni servisi

### 3.1 Ollama (za lokalni AI prevod)

```bash
# Instalacija Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pokretanje
ollama serve

# U terminalu, preuzimanje modela:
ollama pull llama3.1
```

### 3.2 PostgreSQL (opciono umesto SQLite)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Kreiranje baze
sudo -u postgres createdb ai_learning_db
sudo -u postgres createuser ai_learning_user

# Šifra za korisnika
sudo -u postgres psql -c "ALTER USER ai_learning_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_learning_db TO ai_learning_user;"
```

Ažuriraj `.env`:

```bash
DATABASE_URL=postgresql://ai_learning_user:your_password@localhost:5432/ai_learning_db
```

---

## 4. Struktura projekta

```
ai-learning-system/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, logging
│   │   ├── db/           # Database models i session
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── workers/      # Celery tasks
│   │   └── main.py       # FastAPI app
│   ├── storage/          # Lokalni fajlovi (auto-kreirano)
│   ├── tests/            # Testovi
│   ├── requirements.txt  # Python dependencies
│   └── .env              # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/   # React komponente
│   │   ├── pages/        # stranice
│   │   ├── services/     # API pozivi
│   │   ├── stores/       # Zustand state
│   │   └── types/        # TypeScript tipovi
│   ├── package.json      # Node dependencies
│   └── .env              # Environment variables
└── docs/                 # Dokumentacija
```

---

## 5. Troubleshooting

### Problem: "Module not found"

```bash
# Reinstalacija svih paketa
pip install -r requirements.txt --force-reinstall
```

### Problem: SQLite permission error

```bash
# Kreiraj storage direktorijum ručno
mkdir -p backend/storage/uploads
chmod 777 backend/storage/uploads
```

### Problem: CORS greške

Proveri `CORS_ORIGINS` u `config.py`:
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",  # React default port
]
```

### Problem: Port već u upotrebi

```bash
# Nađi proces koji koristi port
lsof -i :8000

# Ubij proces
kill -9 <PID>
```

---

## 6. Korisne komande

```bash
# Backend
cd backend
uvicorn app.main:app --reload          # Dev server
pytest                                  # Run tests
pytest --cov=app --cov-report=html     # Sa coverage

# Frontend  
cd frontend
npm run dev                            # Dev server
npm run build                          # Production build
npm run lint                           # Linting
```

---

## 7. Prelazak na MinIO (Produkcija)

Za produkciju, promeni storage tip u `.env`:

```bash
STORAGE_TYPE=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=ai-learning-uploads
```

I pokreni MinIO preko Docker-a:

```bash
cd ai-learning-system/docker
docker-compose up -d minio
```

---

## 8. Dodatni resursi

- **API Dokumentacija**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:5173

---

**Napomena**: Ovaj vodič je namenjen lokalnom razvoju. Za produkciju koristite Docker compose iz `docker/` foldera.
