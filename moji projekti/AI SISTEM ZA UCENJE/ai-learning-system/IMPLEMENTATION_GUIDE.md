# ================================================================================
# AI LEARNING SYSTEM - KOMPLETAN VODIČ ZA IMPLEMENTACIJU
# ================================================================================
# Verzija: 2.0.0
# Datum: 2026-02-28
# Autor: AI Assistant
# ================================================================================

Ovaj dokument sadrži kompletan vodič za implementaciju i konfiguraciju AI Learning System aplikacije.

---

# ================================================================================
# SADRŽAJ
# ================================================================================

1. [Preduvjeti](#1-preduvjeti)
2. [Struktura Projekta](#2-struktura-projekta)
3. [Konfiguracija Okruženja](#3-konfiguracija-okruženja)
4. [Backend Implementacija](#4-backend-implementacija)
5. [Frontend Implementacija](#5-frontend-implementacija)
6. [Servisi i Endpoint-i](#6-servisi-i-endpoint-i)
7. [Docker Implementacija](#7-docker-implementacija)
8. [Pokretanje Aplikacije](#8-pokretanje-aplikacije)
9. [Najčešća Pitanja](#9-najčešća-pitanja)

---

# ================================================================================
# 1. PREDMVETI
# ================================================================================

## 1.1 Hardverski Zahtevi

| Komponenta | Minimalno | Preporučeno |
|------------|-----------|-------------|
| CPU | 2 jezgra | 4+ jezgara |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB |
| GPU | Nije obavezno | NVIDIA sa 4GB VRAM |

## 1.2 Softverski Zahtevi

| Alat | Verzija | Napomena |
|------|---------|----------|
| Python | 3.11+ | Obavezno |
| Node.js | 18+ | Za frontend |
| npm | 9+ | Dolazi sa Node.js |
| PostgreSQL | 15+ | Za produkciju |
| Redis | 7+ | Za cache i queue |
| Docker | 24+ | Za containerization |
| Docker Compose | 2.20+ | Za orchestraciju |

## 1.3 Python Dependencies

```bash
# Osnovne dependencies
pip install fastapi uvicorn[standard] sqlalchemy pydantic-settings
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip install pymupdf aiofiles pytz python-dotenv

# AI/LLM
pip install langchain openai ollama tiktoken

# Storage
pip install boto3 botocore

# PDF
pip install reportlab Pillow pdf2image

# Monitoring
pip install prometheus-client structlog

# Development
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

---

# ================================================================================
# 2. STRUKTURA PROJEKTA
# ================================================================================

```
ai-learning-system/
├── backend/                    # FastAPI aplikacija
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   └── endpoints/    # Router fajlovi
│   │   │       ├── auth.py       # Autentikacija
│   │   │       ├── users.py      # Korisnici
│   │   │       ├── files.py      # Fajlovi
│   │   │       ├── documents.py  # Dokumenti
│   │   │       ├── quiz.py       # Kvizovi
│   │   │       ├── calendar.py   # Kalendar
│   │   │       ├── analytics.py  # Analitika
│   │   │       ├── backup.py     # Backup
│   │   │       └── pdf_generator.py  # PDF export
│   │   ├── core/              # Core konfiguracija
│   │   │   ├── config.py      # Settings
│   │   │   └── logging_config.py
│   │   ├── db/                # Database
│   │   │   ├── models/       # SQLAlchemy modeli
│   │   │   ├── session.py    # DB session
│   │   │   └── base.py      # Base klase
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── auth.py       # JWT autentikacija
│   │   │   ├── storage.py    # Storage (local/minio)
│   │   │   ├── pdf.py        # PDF processing
│   │   │   ├── translation.py # AI prevod
│   │   │   ├── quiz.py       # Kviz sistem
│   │   │   ├── calendar.py   # Kalendar/Spaced repetition
│   │   │   ├── analytics.py  # Analitika
│   │   │   ├── backup.py    # Backup sistem
│   │   │   ├── monitoring.py # Prometheus metrike
│   │   │   ├── security.py   # Rate limiting, etc.
│   │   │   ├── search.py     # Semantic search
│   │   │   └── theme.py      # Dark/Light mode
│   │   ├── workers/          # Celery zadaci
│   │   ├── main.py           # FastAPI app
│   │   └── tests/           # Testovi
│   ├── alembic/             # Migracije
│   ├── requirements.txt     # Python dependencies
│   └── .env.example          # Environment primer
│
├── frontend/                  # React aplikacija
│   ├── src/
│   │   ├── components/       # React komponente
│   │   ├── pages/           # stranice
│   │   ├── services/        # API pozivi
│   │   ├── stores/          # Zustand state
│   │   ├── types/           # TypeScript tipovi
│   │   ├── hooks/           # Custom hooks
│   │   └── utils/          # Util funkcije
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docker/                    # Docker konfiguracija
│   ├── docker-compose.yml
│   ├── prometheus/
│   └── nginx/
│
├── docs/                     # Dokumentacija
├── scripts/                  # Skripte
├── backups/                 # Backup direktorijum
├── logs/                    # Log direktorijum
├── storage/                 # Lokalni fajlovi
│
└── .github/                 # GitHub Actions
    └── workflows/           # CI/CD pipelines
```

---

# ================================================================================
# 3. KONFIGURACIJA OKRUŽENJA
# ================================================================================

## 3.1 Backend .env fajl

Kreiraj `backend/.env`:

```bash
# ========================
# APLIKACIJA
# ========================
PROJECT_NAME="AI Learning System"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-key

# ========================
# DATABASE
# ========================
# Za lokalni razvoj (SQLite)
DATABASE_URL=sqlite:///./ai_learning.db

# Za produkciju (PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_learning_db

# ========================
# REDIS
# ========================
REDIS_HOST=localhost
REDIS_PORT=6379

# ========================
# STORAGE - LOKALNI RAZVOJ
# ========================
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage/uploads

# ========================
# STORAGE - MINIO (ZA PRODUKCIJU)
# ========================
# STORAGE_TYPE=minio
# MINIO_ENDPOINT=minio:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# MINIO_BUCKET_NAME=ai-learning-uploads

# ========================
# AI / LLM
# ========================
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1

# OpenAI (opciono)
# OPENAI_API_KEY=sk-...

# DeepL (opciono)
# DEEPL_API_KEY=...

# ========================
# CORS
# ========================
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# ========================
# RATE LIMITING
# ========================
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## 3.2 Frontend .env fajl

Kreiraj `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

---

# ================================================================================
# 4. BACKEND IMPLEMENTACIJA
# ================================================================================

## 4.1 Glavna Aplikacija (main.py)

```python
# app/main.py - FastAPI app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## 4.2 Konfiguracija (config.py)

```python
# app/core/config.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Learning System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_learning.db"
    
    # Storage
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage/uploads"
    
    # Security
    SECRET_KEY: str = "change-this"
    JWT_SECRET: str = "change-this"
    JWT_ALGORITHM: str = "HS256"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 4.3 Storage Servis (local/minio)

```python
# app/services/storage.py

class LocalStorageService:
    """Lokalni fajl sistem"""
    
    def __init__(self):
        self.base_dir = Path(settings.LOCAL_STORAGE_PATH)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file_content, filename, user_id):
        # Upload logika
        pass
    
    def download_file(self, storage_path):
        # Download logika
        pass


class MinIOStorageService:
    """MinIO/S3 storage"""
    
    def __init__(self):
        self.client = boto3.client('s3', ...)
    
    def upload_file(self, file_content, filename, user_id):
        # Upload logika
        pass


class StorageService:
    """Facade - bira implementaciju"""
    
    def __init__(self):
        if settings.STORAGE_TYPE == "local":
            self._storage = LocalStorageService()
        else:
            self._storage = MinIOStorageService()
    
    def __getattr__(self, name):
        return getattr(self._storage, name)

storage_service = StorageService()
```

---

# ================================================================================
# 5. FRONTEND IMPLEMENTACIJA
# ================================================================================

## 5.1 Vite Konfiguracija

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## 5.2 Tailwind Konfiguracija

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        accent: {
          500: '#8b5cf6',
          600: '#7c3aed',
        },
      },
    },
  },
  plugins: [],
}
```

## 5.3 API Service

```typescript
// src/services/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor za token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  login: (email: string, password: string) => 
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, name: string) =>
    api.post('/auth/register', { email, password, name }),
}

export const documentsApi = {
  list: (page = 1, limit = 20) => 
    api.get(`/documents/?page=${page}&limit=${limit}`),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/files/upload', formData)
  },
}

export const quizApi = {
  list: () => api.get('/quizzes/'),
  get: (id: string) => api.get(`/quizzes/${id}`),
  generate: (data: any) => api.post('/quizzes/generate', data),
}

export default api
```

---

# ================================================================================
# 6. SERVISI I ENDPOINT-I
# ================================================================================

## 6.1 API Endpoints Pregled

| Prefix | Endpoint | Opis |
|--------|----------|------|
| `/auth` | POST /login | Prijava |
| `/auth` | POST /register | Registracija |
| `/auth` | POST /refresh | Refresh token |
| `/users` | GET /me | Trenutni korisnik |
| `/files` | POST /upload | Upload fajla |
| `/files` | GET / | Lista fajlova |
| `/files` | GET /{id}/download | Download |
| `/documents` | GET / | Lista dokumenata |
| `/documents` | POST / | Kreiranje |
| `/documents` | GET /{id} | Detalji |
| `/documents` | POST /{id}/translate | Prevod |
| `/quizzes` | GET / | Lista kvizova |
| `/quizzes` | POST /generate | Generisanje |
| `/quizzes` | GET /{id}/play | Igranje |
| `/export` | GET /documents/{id}/export-pdf | PDF export |
| `/export` | GET /quizzes/{id}/export-pDF | Kviz PDF |
| `/calendar` | GET /weekly | Nedeljni kalendar |
| `/calendar` | GET /due | Za ponavljanje |
| `/backup` | POST /database | Backup baze |
| `/backup` | POST /restore | Restore |
| `/analytics` | GET /overview | Pregled |
| `/metrics` | GET / | Prometheus metrike |

## 6.2 Servisi

| Servis | Fajl | Funkcija |
|--------|------|----------|
| Auth | `services/auth.py` | JWT token, password hashing |
| Storage | `services/storage.py` | Local/MinIO fajl sistem |
| PDF | `services/pdf.py` | Ekstrakcija, chunking |
| Translation | `services/translation.py` | AI prevod (Ollama, DeepL, OpenAI) |
| Quiz | `services/quiz.py` | Generisanje pitanja |
| Calendar | `services/calendar.py` | Spaced repetition |
| Analytics | `services/analytics.py` | Statistike |
| Backup | `services/backup.py` | DB backup/restore |
| Monitoring | `services/monitoring.py` | Prometheus metrike |
| Security | `services/security.py` | Rate limiting, sanitization |
| Search | `services/search.py` | Semantic search (pgvector) |
| Theme | `services/theme.py` | Dark/Light mode |

---

# ================================================================================
# 7. DOCKER IMPLEMENTACIJA
# ================================================================================

## 7.1 docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ai_learning_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ai_learning_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # MinIO
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"

  # Ollama (AI)
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"

  # Backend
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ai_learning_user:password@db:5432/ai_learning_db
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_TYPE=minio
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - db
      - redis
      - minio

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "5173:5173"

  # Prometheus
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  # Grafana
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"

volumes:
  postgres-data:
  minio-data:
```

## 7.2 Pokretanje sa Docker-om

```bash
# Kloniraj projekat
git clone <repo-url>
cd ai-learning-system

# Pokreni sve servise
docker-compose up -d

# Proveri status
docker-compose ps

# Pregled logova
docker-compose logs -f app
```

---

# ================================================================================
# 8. POKRETANJE APLIKACIJE
# ================================================================================

## 8.1 Lokalni Razvoj (Bez Docker-a)

### Backend:

```bash
cd backend

# Kreiraj virtualno okruženje
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ili: venv\Scripts\activate  # Windows

# Instalacija dependencies
pip install -r requirements.txt

# Kreiraj .env fajl
cp .env.example .env
# Edituj .env sa svojim vrednostima

# Pokreni server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Backend je dostupan na: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend:

```bash
cd frontend

# Instalacija
npm install

# Kreiraj .env
cp .env.example .env

# Pokreni dev server
npm run dev

# Frontend je dostupan na: http://localhost:5173
```

## 8.2 Docker Razvoj

```bash
# Potrebni servisi (db, redis, minio, ollama)
cd docker
docker-compose up -d db redis minio ollama

# Backend
cd backend
docker build -t ai-learning-backend .
docker run -p 8000:8000 ai-learning-backend

# Frontend
cd frontend
docker build -t ai-learning-frontend .
docker run -p 5173:5173 ai-learning-frontend
```

---

# ================================================================================
# 9. NAJČEŠĆA PITANJA
# ================================================================================

## Q: Kako da koristim SQLite umesto PostgreSQL za lokalni razvoj?

A: U `backend/.env`:
```bash
DATABASE_URL=sqlite:///./ai_learning.db
STORAGE_TYPE=local
```

## Q: Kako da podesim Ollama za lokalni AI prevod?

A: 
1. Instaliraj Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Pokreni: `ollama serve`
3. Preuzmi model: `ollama pull llama3.1`
4. U .env: `OLLAMA_HOST=http://localhost:11434`

## Q: Kako da omogućim Dark Mode?

A: Koristi `theme_service` iz `services/theme.py`:
```python
from app.services.theme import theme_service

# Get CSS variables
css = theme_service.get_css_variables('dark')

# Toggle
new_theme = theme_service.toggle_theme(current_theme)
```

## Q: Kako da konfigurišem MinIO?

A: U `docker-compose.yml` već je konfigurisan. Za lokalni rad:
```bash
# Pristup MinIO console
http://localhost:9001
# credentials: minioadmin / minioadmin
```

## Q: Kako da pokrenem testove?

```bash
cd backend
pytest --cov=app --cov-report=html
```

## Q: Kako da dodam nove AI provajdere za prevod?

A: Dodaj u `services/translation.py`:
```python
class NewProviderClient:
    def translate(self, text: str, source: str, target: str) -> str:
        # Implementacija
        pass
```

---

# ================================================================================
# KONTAKT I PODRŠKA
# ================================================================================

- Dokumentacija: `/docs`
- API Reference: `/redoc`
- Health Check: `/health`
- Metrics: `/metrics`

---

**Napomena**: Ovaj vodič je namenjen za razvojnu i produkcijsku implementaciju. Za produkciju obavezno promeniti sve `SECRET_KEY`, `JWT_SECRET` i lozinke za bazu.
