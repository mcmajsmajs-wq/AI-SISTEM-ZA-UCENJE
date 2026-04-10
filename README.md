# ================================================================================
# AI LEARNING SYSTEM
# ================================================================================

Personalizovana aplikacija za učenje koja automatizuje proces konverzije stranih stručnih PDF materijala na srpski jezik, generiše fizičke i digitalne materijale za proveru znanja, i inteligentno upravlja tempom učenja kroz kalendar i analitiku.

## Funkcionalnosti

- **PDF Upload & Processing**: Upload i obrada PDF fajlova sa OCR podrškom
- **AI Translation**: Automatski prevod na srpski jezik koristeći Ollama/OpenAI
- **Human-in-the-Loop Review**: Interfejs za pregled i korekciju prevoda
- **Quiz Generation**: AI generisanje kvizova sa višestrukim odgovorima
- **Spaced Repetition**: Pametno planiranje učenja kroz kalendar
- **Analytics Dashboard**: Praćenje napretka i identifikacija slabih tačaka
- **Semantic Search**: Pretraga kroz dokumente po značenju

## Arhitektura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   FastAPI    │────▶│  PostgreSQL  │
│  (React/Vue) │◀────│   Backend    │◀────│   Database   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│    Redis     │   │    Ollama    │   │   MinIO/S3   │
│   (Queue)    │   │    (AI LLM)  │   │(File Storage)│
└──────────────┘   └──────────────┘   └──────────────┘
```

## Tehnologije

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Celery
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: PostgreSQL 15, Redis 7
- **AI**: Ollama (Llama 3.1), OpenAI API, DeepL, Google Translate, Claude
- **Storage**: MinIO (S3 compatible)
- **Monitoring**: Prometheus, Grafana
- **PDF**: PyMuPDF, ReportLab, Tesseract OCR
- **Testing**: pytest, pytest-asyncio, pytest-cov

## Instalacija

### Preduslovi

- Docker i Docker Compose
- Git

### Koraci

1. **Kloniranje repozitorijuma**
```bash
git clone <repository-url>
cd ai-learning-system
```

2. **Konfiguracija environment variables**
```bash
cd docker
cp .env.example .env
# Izmeni .env fajl sa tvojim vrednostima
```

3. **Pokretanje servisa**
```bash
docker-compose up -d
```

4. **Verifikacija**
```bash
# Proveri status servisa
docker-compose ps

# Health check
curl http://localhost:8000/health
```

## Servisi

Nakon pokretanja, sledeći servisi su dostupni:

| Servis | URL | Opis |
|--------|-----|------|
| FastAPI App | http://localhost:8000 | Glavna API aplikacija (direct) |
| Nginx/Frontend | http://localhost:8083 | Frontend preko NGINX |
| API Docs | http://localhost:8000/docs | Swagger UI dokumentacija |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache & Queue |
| MinIO | http://localhost:9001 | File Storage Console |
| Grafana | http://localhost:3000 | Monitoring Dashboards |
| Prometheus | http://localhost:9090 | Metrics |
| Ollama | http://localhost:11434 | Local AI LLM |

## API Endpoint-i

### Autentikacija
- `POST /api/v1/auth/register` - Registracija
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout

### Fajlovi
- `POST /api/v1/files/upload` - Upload PDF fajla
- `GET /api/v1/files` - Lista fajlova
- `GET /api/v1/files/{id}` - Detalji fajla
- `DELETE /api/v1/files/{id}` - Brisanje fajla

### Dokumenti
- `GET /api/v1/documents` - Lista dokumenata
- `POST /api/v1/documents` - Kreiranje dokumenta
- `GET /api/v1/documents/{id}` - Detalji dokumenta
- `POST /api/v1/documents/{id}/process` - Pokreni obradu
- `POST /api/v1/documents/{id}/translate` - Pokreni prevod

## Razvoj

### Lokalan razvoj (bez Docker-a)

1. **Kreiranje virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ili
venv\Scripts\activate  # Windows
```

2. **Instalacija dependenci**
```bash
pip install -r requirements.txt
```

3. **Pokretanje PostgreSQL i Redis**
```bash
# Koristi Docker samo za servise
docker-compose up -d db redis minio
```

4. **Konfiguracija .env**
```bash
cp docker/.env.example backend/.env
# Izmeni vrednosti za lokalni razvoj
```

5. **Pokretanje aplikacije**
```bash
cd backend
uvicorn app.main:app --reload
```

### Alembic Migrations

```bash
# Kreiranje nove migracije
cd backend
alembic revision --autogenerate -m "opis promene"

# Apliciranje migracija
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testiranje

```bash
# Pokretanje testova
cd backend
pytest

# Sa coverage-om
pytest --cov=app --cov-report=html

# Specifičan test
pytest app/tests/unit/test_auth.py -v

# Integration testovi
pytest app/tests/integration/ -v

# Test coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Verifikacija sistema (FAZA 10-11)

```bash
# Verifikacija FAZA 10 - Testovi i integracija
make verify-faza10
# Ili: docker compose exec app python backend/scripts/verify_faza10.py

# Verifikacija FAZA 11 - Optimizacije i CI/CD
make verify-faza11
# Ili: docker compose exec app python backend/scripts/verify_faza11.py

# Sve verifikacije
make verify
```

### FAZA 10-11 Komanda

```bash
# Provera optimizacija (cache, rate limit, DB pool)
make optimize-stats
```

## Test Coverage (~386 testova)

| Komponenta | Testovi |
|------------|---------|
| Auth Service | ~30 |
| Storage Service | ~20 |
| PDF Service | ~50 |
| Translation Service | ~60 |
| API Integration | ~25 |
```

### Frontend Razvoj

1. **Instalacija**
```bash
cd frontend
npm install
```

2. **Development server**
```bash
npm run dev
# Frontend: http://localhost:3000
# API proxy: http://localhost:8000
```

3. **Build za produkciju**
```bash
npm run build
npm run preview
```

4. **Environment konfiguracija**
```bash
cp .env.example .env
# Podesi VITE_API_URL po potrebi
```

## Frontend Stranice

| Stranica | URL | Opis |
|----------|-----|------|
| Login | /login | Prijava korisnika |
| Register | /register | Registracija novog korisnika |
| Dashboard | / | Početna sa statistikama |
| Documents | /documents | Lista dokumenata + upload |
| Document Detail | /documents/:id | Detalji dokumenta |
| Review | /review/:id | Human-in-loop pregled prevoda |
| Settings | /settings | Korisnička podešavanja |

## Logovi

Logovi se nalaze u:
- **Docker**: `docker-compose logs -f app`
- **Lokalno**: `backend/logs/`
- **Struktura**: JSON format za produkciju, colored text za development

## Troubleshooting

### Problem: Servisi se ne pokreću
```bash
# Proveri logove
docker-compose logs

# Restart servisa
docker-compose restart

# Kompletan rebuild
docker-compose down -v
docker-compose up --build
```

### Problem: Database connection error
```bash
# Proveri da li je PostgreSQL pokrenut
docker-compose ps db

# Reset baze (PAZI: briše sve podatke!)
docker-compose down -v
```

### Problem: AI servis ne radi
```bash
# Proveri Ollama
curl http://localhost:11434/api/tags

# Pull modela ako nedostaje
docker-compose exec ollama ollama pull llama3.1
```

## Licenca

MIT License - vidi LICENSE fajl za detalje.

## Kontakt

Za pitanja i predloge, kontaktirajte nas na: support@ai-learning.com
