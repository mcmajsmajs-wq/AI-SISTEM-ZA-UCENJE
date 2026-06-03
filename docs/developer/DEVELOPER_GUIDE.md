# DEVELOPER GUIDE — AI SISTEM ZA UČENJE
**Verzija:** 2.2.0  
**Poslednje ažuriranje:** 2026-06-03

---

## Sadržaj

1. [Arhitektura sistema](#1-arhitektura-sistema)
2. [Tech Stack](#2-tech-stack)
3. [Lokalno pokretanje](#3-lokalno-pokretanje)
4. [Struktura projekta](#4-struktura-projekta)
5. [Baza podataka](#5-baza-podataka)
6. [API referenca](#6-api-referenca)
7. [Dodavanje novog AI provajdera](#7-dodavanje-novog-ai-provajdera)
8. [Celery taskovi](#8-celery-taskovi)
9. [Frontend arhitektura](#9-frontend-arhitektura)
10. [Alembic migracije](#10-alembic-migracije)
11. [Testiranje](#11-testiranje)

---

## 1. Arhitektura sistema

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (port 80)                       │
│         reverse proxy → frontend + backend              │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌────────────────┐      ┌────────────────┐
│  React Frontend│      │ FastAPI Backend │
│  Vite + TS     │      │  Python 3.11   │
│  port 5173     │      │  port 8010     │
└────────────────┘      └───────┬────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                   ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │  PostgreSQL  │  │    Redis     │  │    MinIO     │
     │  (SQLAlchemy)│  │ (Celery + Q) │  │ (File Store) │
     └──────────────┘  └──────┬───────┘  └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
           ┌─────────────┐    ┌──────────────────┐
           │Celery Worker│    │  AI Providers:   │
           │  (bg tasks) │    │  Ollama (local)  │
           └─────────────┘    │  OpenAI (API)    │
                              │  Claude (API)    │
                              └──────────────────┘
```

---

## 2. Tech Stack

### Backend
- **FastAPI** — REST API framework
- **SQLAlchemy 2.0** — ORM (async engine)
- **Alembic** — database migrations
- **Celery + Redis** — async task queue
- **Pydantic v2** — data validation
- **python-jose** — JWT auth
- **boto3** — MinIO/S3 storage

### Frontend
- **React 18** + **TypeScript**
- **Vite** — build tool
- **React Query (TanStack)** — server state
- **Zustand** — client state (auth)
- **React Router v6** — routing
- **Tailwind CSS** — styling
- **Lucide React** — icons

### Infrastructure
- **Docker Compose** — orchestration
- **Nginx** — reverse proxy
- **Prometheus + Grafana** — monitoring
- **ReportLab** — PDF export
- **python-docx** — DOCX export
- **python-pptx** — PPTX export
- **openpyxl** — XLSX export
- **Tesseract OCR** — OCR processing
- **pytest + pytest-cov** — testiranje

---

## 3. Lokalno pokretanje

### Zahtevi

- Docker Desktop 4.x+
- Node.js 18+ (samo za frontend dev)
- Python 3.11+ (samo za backend dev bez Dockera)

### Docker (preporučeno)

```bash
cp .env.example .env
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### Backend bez Dockera

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8010
```

### Frontend bez Dockera

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 4. Struktura projekta

```
ai-learning-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/       # Route handlers
│   │   │   │   ├── auth.py
│   │   │   │   ├── documents.py # + pipeline endpointi
│   │   │   │   ├── quizzes.py
│   │   │   │   ├── study_plan.py
│   │   │   │   └── users.py
│   │   │   └── v1/router.py     # Router registry
│   │   ├── db/
│   │   │   ├── models/          # SQLAlchemy modeli
│   │   │   │   ├── document.py
│   │   │   │   ├── quiz.py      # Quiz, Question, Attempt, Answer
│   │   │   │   ├── study_plan.py
│   │   │   │   └── user.py
│   │   │   └── session.py       # DB engine + session
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── quiz/            # FAZA 1-3: Modular quiz service
│   │   │   │   ├── __init__.py  # Exports
│   │   │   │   ├── service.py   # QuizService
│   │   │   │   ├── prompts/     # Quiz prompts
│   │   │   │   ├── helpers/     # Parsing, validation
│   │   │   │   └── clients/    # AI providers (7 providers)
│   │   │   ├── translation/     # FAZA 5: Modular translation
│   │   │   │   ├── service.py   # TranslationService
│   │   │   │   ├── clients/    # Translation clients
│   │   │   │   └── providers.py
│   │   │   ├── skills/          # FAZA 6: Skill detection
│   │   │   │   ├── detector.py # SkillDetector
│   │   │   │   ├── templates/  # Skill templates
│   │   │   │   ├── keywords/   # Subject keywords
│   │   │   │   ├── models.py   # Skill models
│   │   │   │   └── pdf_detector.py
│   │   │   ├── security/       # FAZA 8: API key security
│   │   │   │   ├── encryption.py
│   │   │   │   ├── key_manager.py
│   │   │   │   └── validators.py
│   │   │   ├── optimization/   # FAZA 11: Performance
│   │   │   │   ├── rate_limiter.py  # Rate limiting
│   │   │   │   ├── caching.py       # Cache with TTL
│   │   │   │   └── connection_pool.py # HTTP pooling
│   │   │   ├── pdf_service.py
│   │   │   ├── rag.py
│   │   │   ├── storage.py
│   │   │   └── ai_chat.py
│   │   ├── workers/
│   │   │   └── tasks/          # FAZA 4: Modular tasks
│   │   │       ├── __init__.py
│   │   │       ├── pdf_processing.py
│   │   │       ├── translation.py
│   │   │       ├── quiz.py
│   │   │       ├── maintenance.py
│   │   │       └── knowledge.py
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   └── security.py
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_initial.py
│   │       ├── 002_quiz_tables.py
│   │       └── 003_study_plan.py
│   ├── tests/                  # FAZA 10: Test suite
│   │   └── unit/
│   ├── scripts/
│   │   ├── verify_faza10.py    # FAZA 10 verification
│   │   └── verify_faza11.py    # FAZA 11 verification
│   └── requirements.txt
├── mcp-server/                 # FAZA 7: MCP Server
│   ├── src/
│   │   └── ai_learning_mcp/
│   │       ├── __init__.py     # MCP tools (17)
│   │       └── tools/
│   └── tests/
├── frontend/
│   └── src/
├── docker/                     # Docker + Nginx config
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
└── Makefile
```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/           # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── analytics.py     # Analytics dashboard
│   │   │   ├── documents.py     # + pipeline endpointi
│   │   │   ├── quizzes.py
│   │   │   ├── study_plan.py
│   │   │   └── users.py
│   │   └── v1/router.py         # Router registry
│   ├── db/
│   │   ├── models/              # SQLAlchemy modeli
│   │   │   ├── document.py      # Document, Chunk (+ layout_data)
│   │   │   ├── quiz.py          # Quiz, Question, Attempt, Answer
│   │   │   ├── study_plan.py
│   │   │   ├── user.py
│   │   │   └── skills.py        # FileSkill model (FAZA 13)
│   │   └── session.py           # DB engine + session
│   ├── schemas/                 # Pydantic schemas
│   ├── services/
│   │   ├── pdf_service.py       # PDF processing + font detection
│   │   ├── pdf_export_service.py# PDF/DOCX/PPTX/XLSX export
│   │   ├── translation/         # FAZA 5: Modular translation
│   │   │   ├── service.py
│   │   │   ├── clients/         # Translation clients
│   │   │   └── providers.py
│   │   ├── quiz/                # Quiz generation system
│   │   │   ├── service.py       # QuizService orchestrator
│   │   │   ├── helpers/         # _parse_questions, _validate_questions
│   │   │   ├── prompts/         # QUIZ_PROMPT, subject prompts
│   │   │   │   ├── quiz_prompt.py
│   │   │   │   └── subjects.py
│   │   │   ├── clients/         # AI provider clients (6)
│   │   │   │   ├── ollama.py
│   │   │   │   ├── groq.py
│   │   │   │   ├── deepseek.py
│   │   │   │   ├── claude.py
│   │   │   │   ├── openai.py
│   │   │   │   └── openai_compat.py
│   │   │   └── evaluation.py    # evaluate_answer()
│   │   ├── skills/              # FAZA 6 + 13: File Skills
│   │   │   ├── detector.py
│   │   │   ├── file_skills.py   # FileSkillService
│   │   │   └── models.py
│   │   ├── rag.py
│   │   ├── storage.py
│   │   └── optimization/        # FAZA 11: Performance
│   │       ├── rate_limiter.py
│   │       ├── caching.py
│   │       └── connection_pool.py
│   ├── workers/
│   │   └── tasks/               # FAZA 4: Modular Celery tasks
│   │       ├── pdf_processing.py
│   │       ├── translation.py   # + run_document_translation()
│   │       ├── quiz.py          # + auto_pipeline_task
│   │       ├── pdf_export.py
│   │       ├── maintenance.py
│   │       └── knowledge.py
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── security.py
│   └── main.py
├── alembic/
│   └── versions/                # 013 migrations total
│       ├── 001_initial.py
│       ├── 002_quiz_tables.py
│       ├── 003_study_plan.py
│       ├── ...
│       └── 013_add_text_input_type.py
├── tests/
│   └── unit/                    # 587+ testova
│       ├── test_auth.py
│       ├── test_quiz_service.py
│       ├── test_pdf_service.py
│       ├── test_pdf_export_service.py
│       ├── test_roundtrip_export.py  # FAZA D (18 testova)
│       └── ...
└── scripts/
    ├── verify_faza10.py
    ├── verify_faza11.py
    ├── backfill_layout_data.py  # FAZA A
    └── verify_pdf_quality.py    # PDF bookmark verification
```

---

## 5. Baza podataka

### Modeli

| Model | Tabela | Opis |
|-------|--------|------|
| `User` | `users` | Korisnički nalog |
| `UserSession` | `user_sessions` | JWT sesije |
| `File` | `files` | Uploadovani fajlovi (MinIO ref) |
| `Document` | `documents` | Obradjen PDF |
| `Chunk` | `chunks` | Segmenti teksta sa prevodom |
| `Quiz` | `quizzes` | Kviz metapodaci |
| `Question` | `questions` | Pitanja kviza |
| `QuizAttempt` | `quiz_attempts` | Pokušaj rešavanja |
| `QuizAnswer` | `quiz_answers` | Odgovori po pitanju |
| `StudyPlan` | `study_plans` | Lični plan korisnika (1:1 sa User) |
| `StudyPlanItem` | `study_plan_items` | Zakazani kviz u planu |
| `FileSkill` | `file_skills` | FAZA 13: File skill prompt sabloni |

### Chunk model — dodatna polja

| Polje | Tip | Opis | FAZA |
|-------|-----|------|------|
| `layout_data` | `JSON` | Font/paragraph/page info | A |
| `page_number` | `Integer` | Stranica u PDF-u | (starije) |
| `token_count` | `Integer` | Broj tokena | (starije) |

### Enum tipovi (PostgreSQL)

- `quizstatus` — `pending`, `generating`, `ready`, `failed`
- `questiontype` — `multiple_choice`, `checkbox`, `true_false`, `fill_blank`, `sequencing`, `matching`, `categorization`

---

## 6. API referenca

### Auth (`/api/v1/auth`)
```
POST /register          Registracija
POST /login             Prijava (JWT token)
POST /logout            Odjava
GET  /me                Trenutni korisnik
```

### Documents (`/api/v1/documents`)
```
GET    /                  Lista dokumenata
POST   /                  Upload dokumenta
GET    /{id}              Detalji dokumenta
DELETE /{id}              Brisanje
POST   /{id}/process      Pokretanje PDF obrade
POST   /{id}/translate    Pokretanje prevoda
POST   /{id}/pipeline     Auto pipeline (PDF→prevod→kviz)
GET    /pipeline/providers Lista dostupnih AI provajdera
GET    /{id}/export/pdf   Preuzmi PDF export
GET    /{id}/export/docx  Preuzmi DOCX export
GET    /{id}/export/pptx  Preuzmi PPTX export
GET    /{id}/export/xlsx  Preuzmi XLSX export
```

### Quizzes (`/api/v1/quizzes`)
```
GET    /                Lista kvizova
POST   /                Kreiranje kviza (pokreće Celery task)
GET    /{id}            Kviz sa pitanjima
DELETE /{id}            Brisanje
POST   /{id}/start      Pokretanje novog pokušaja
POST   /{id}/submit     Predaja odgovora → rezultat
GET    /{id}/attempts   Lista pokušaja korisnika
GET    /providers/list  🆕 Lista dostupnih AI provajdera
```

### Analytics (`/api/v1/analytics`)
```
GET  /me/overview       Streak, avg score, prolaznost
GET  /me/quizzes        Performanse po kvizovima
GET  /me/documents      Aktivnost po dokumentima
GET  /me/daily          Dnevna aktivnost (7/14/30/60 dana)
GET  /me/heatmap        GitHub-style aktivnost (8 nedelja)
```

### Study Plan (`/api/v1/study-plan`)
```
GET  /me                Moj plan (auto-kreira ako ne postoji)
PUT  /me                Ažuriranje ciljeva plana
GET  /me/progress       Streak, nedeljni/dnevni napredak, predstojeći
GET  /me/items          Lista stavki (filtriranje po datumu)
POST /me/items          Dodavanje kviza u plan
PUT  /me/items/{id}     Ažuriranje stavke
POST /me/items/{id}/complete  Označavanje kao završeno
DELETE /me/items/{id}   Brisanje stavke
```

---

## 7. Dodavanje novog AI provajdera

Svi AI provajderi za kviz nasleđuju `BaseQuizClient` iz `backend/app/services/quiz/clients/`.

Postojeći provajderi:

| Provajder | Klasa | Fajl | Cena |
|-----------|-------|------|------|
| Ollama | `OllamaQuizClient` | `clients/ollama.py` | Besplatno (lokalno) |
| Groq | `GroqQuizClient` | `clients/groq.py` | Besplatno (30 RPM) |
| DeepSeek | `DeepSeekQuizClient` | `clients/deepseek.py` | $0.14/M |
| Claude | `ClaudeQuizClient` | `clients/claude.py` | $3/M |
| OpenAI | `OpenAIQuizClient` | `clients/openai.py` | $2.50/M |
| OpenAI Compatible | `OpenAICompatibleClient` | `clients/openai_compat.py` | Zavisi od API-ja |

### Korak 1 — Implementiraj klijenta

```python
class MojProvajderClient(BaseQuizClient):
    def __init__(self):
        self.api_key = settings.MOJ_PROVAJDER_API_KEY
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self, text: str, num_questions: int
    ) -> tuple[bool, str, str]:
        # Vrati: (uspeh: bool, json_string: str, greška: str)
        try:
            # ... poziv API-ja ...
            return True, json_result, ""
        except Exception as e:
            return False, "", str(e)
```

### Korak 2 — Registruj provajdera

U `backend/app/services/quiz/service.py` → `QuizService.__init__()`:
```python
self._clients["mojprovajder"] = MojProvajderClient()
```

### Korak 3 — Dodaj .env varijablu

```bash
# .env.example
MOJ_PROVAJDER_API_KEY=
```

### Korak 4 — Isti princip važi za Translation

Pogledaj `backend/app/services/translation_service.py` → `BaseTranslationClient`.

---

## 8. Celery taskovi

Taskovi se nalaze u `backend/app/workers/tasks/` (modularna struktura od FAZA 4).

### Postojeći taskovi

| Task | Fajl | Opis |
|------|------|------|
| `process_document_task` | `pdf_processing.py` | PDF ekstrakcija i chunking (+ layout_data) |
| `translate_document_task` | `translation.py` | Prevod svih chunkova |
| `run_document_translation` | `translation.py` | Core translation logika (koristi je i pipeline) |
| `generate_quiz_task` | `quiz.py` | Generisanje pitanja za kviz (jedan provajder) |
| `auto_pipeline_task` | `quiz.py` | Kompletni pipeline: PDF→Prevod→Kviz |
| `export_pdf_task` | `pdf_export.py` | PDF export dokumenta |
| `export_docx_task` | `pdf_export.py` | DOCX export dokumenta |
| `export_pptx_task` | `pdf_export.py` | PPTX export dokumenta |
| `export_xlsx_task` | `pdf_export.py` | XLSX export dokumenta |

### Dodavanje novog taska

```python
@celery_app.task(bind=True, max_retries=3)
def moj_task(self, document_id: str) -> dict:
    db = SessionLocal()
    try:
        # ... logika ...
        return {"status": "success"}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
    finally:
        db.close()
```

### Pokretanje iz API-ja

```python
task = moj_task.delay(document_id)
return {"task_id": task.id}
```

---

## 9. Frontend arhitektura

### State management

- **Zustand** (`authStore`) — auth token, korisnik
- **React Query** — server state (caching, invalidation)
- Lokalni `useState` — UI state (modal otvoreno, forma)

### Dodavanje nove stranice

1. Kreiraj `frontend/src/pages/MojaStrana.tsx`
2. Dodaj u `frontend/src/App.tsx`:
   ```tsx
   <Route path="/moja-strana" element={<MojaStrana />} />
   ```
3. Opciono dodaj u `Layout.tsx` navigaciju

### API pozivi

Sve API metode su u `frontend/src/services/api.ts`.

```typescript
export const mojaApi = {
  getList: () => api.get('/moj-endpoint'),
  create: (data: MojType) => api.post('/moj-endpoint', data),
}
```

### Tipovi

Dodavaj u `frontend/src/types/index.ts`.

---

## 10. Alembic migracije

### Kreiranje nove migracije

```bash
# Auto-detect iz modela (pokrenuti unutar Docker kontejnera)
docker-compose exec app alembic revision --autogenerate -m "opis_migracije"

# Ručna migracija
docker-compose exec app alembic revision -m "opis_migracije"
```

### Primena migracija

```bash
docker-compose exec app alembic upgrade head
```

### Rollback

```bash
docker-compose exec app alembic downgrade -1
```

### Konvencija imenovanja fajlova

```
versions/
  001_initial.py
  002_quiz_tables.py
  003_study_plan.py
  004_sledeca_migracija.py
```

---

## 11. Testiranje

### Pokretanje testova

```bash
cd backend
pytest tests/ -v
```

### Trenutni status testova

- **~605 testova** ukupno (587 pass, 18 skip)
- **Coverage: ~63%** (backend)
- **Roundtrip testovi** — FAZA D: 18 testova za PDF/DOCX/PPTX/XLSX export (word-level matching >= 95%)

### Struktura testova

```
backend/tests/
├── conftest.py              # pytest fixtures (db, client, auth)
├── unit/
│   ├── test_auth.py
│   ├── test_documents.py
│   ├── test_quiz_service.py # 50+ testova za quiz helpers, parse, validate
│   ├── test_pdf_service.py
│   ├── test_pdf_export_service.py  # 50+ testova za PDF export + layout
│   ├── test_roundtrip_export.py    # FAZA D: 18 testova
│   ├── test_translation.py
│   ├── test_storage_service.py
│   ├── test_helpers.py
│   ├── test_monitoring_utils.py
│   └── ...
└── integration/
    └── ...
```

### Pisanje novog testa

```python
def test_create_quiz(client, auth_headers, test_document):
    response = client.post(
        "/api/v1/quizzes/",
        json={"document_id": test_document.id, "num_questions": 5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
```

---

## 12. Poznate napomene

### Celery Beat raspored

Beat raspored je definisan **isključivo** u `backend/app/workers/celery_app.py`.
Ne dodavati `beat_schedule` u `config.py` — `celery_app.conf.beat_schedule = {...}` uvek preuzima.

```bash
# Pokretanje Celery Beat workera
docker-compose exec worker celery -A app.workers.celery_app beat --loglevel=info
```

### Email notifikacije

SMTP konfiguracija se vrši u `docker/.env`:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=vas-email@gmail.com
SMTP_PASSWORD=vas-app-password
```

Ako SMTP nije konfigurisan, email_service.is_configured() vraća False i email se tiho preskače.  
Welcome email se šalje automatski pri registraciji (BackgroundTask — ne blokira response).

### PDF Export polja

Chunk model koristi:
- `content` — originalni tekst  
- `translated_content` — prevedeni tekst  
- `sequence_number` — redosled  

**Ne koristiti** `original_text`, `translated_text`, `chunk_index` — ne postoje u modelu.

### Quiz status vrednosti

| Status | Opis |
|--------|------|
| `generating` | Celery task aktivan |
| `ready` | Spreman za igranje |
| `error` | Generisanje neuspelo |

Nema `failed` ili `pending` statusa za kvizove.


---

## 13. Password Reset Flow

Token se čuva **in-memory** u `_reset_tokens` dict u `auth.py`.

> ⚠️ **Produkcija**: Migrirati na Redis (`redis.setex(token_hash, 3600, user_id)`).

```
POST /auth/forgot-password   { "email": "user@example.com" }
→ Generiše raw_token (32B URL-safe)
→ Čuva SHA-256 hash → {user_id, expires_at: now+1h}
→ Šalje email sa: FRONTEND_URL/reset-password?token=<raw>

POST /auth/reset-password    { "token": "...", "new_password": "..." }
→ SHA-256(token) → lookup
→ Proverava expires_at
→ bcrypt hashing + save + DELETE token (single-use)
```

`FRONTEND_URL` se konfiguriše u `docker/.env`:
```
FRONTEND_URL=https://vas-domen.com
```

---

## 14. Rate Limiting

Implementirano sa `slowapi` (wrapper oko `limits`).

```python
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# auth.py
@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, ...):
```

Limiti:
| Endpoint | Limit |
|----------|-------|
| `POST /auth/register` | 5/minuta |
| `POST /auth/login` | 10/minuta |
| `POST /auth/forgot-password` | 3/minuta |

---

## 15. Quiz Shuffle

Ako `quiz.shuffle_questions = True`, `GET /quizzes/{id}` vraća pitanja u **nasumičnom redosledu** (Python `random.shuffle`).

```python
# Kreiranje kviza sa shuffle
POST /quizzes
{ "document_id": "...", "num_questions": 10, "shuffle_questions": true }
```

---

## 16. CI/CD (GitHub Actions)

Fajl: `.github/workflows/ci.yml`

| Job | Aktivator | Šta radi |
|-----|-----------|----------|
| `backend` | push/PR na main/develop | flake8 lint → pytest unit → pytest integration → coverage ≥60% |
| `frontend` | push/PR na main/develop | tsc --noEmit → npm run build |
| `docker-build` | push na main | docker build backend + frontend |

Services koji se startuju za backend testove: PostgreSQL 15, Redis 7.

---

## 17. Grafana Monitoring

Provisioning fajlovi:
- `docker/grafana/datasources/prometheus.yml` — Prometheus datasource
- `docker/grafana/dashboards/dashboards.yml` — provider konfiguracija
- `docker/grafana/dashboards/ai_learning.json` — dashboard sa 10 panela

Dashboard URL: http://localhost:3000 (admin/admin po defaultu)

Paneli:
- HTTP Request Rate, Error Rate, P95 Latency
- Celery Active Tasks, Queue Size
- DB Connection Pool
- Quiz Generation Duration (p50/p95)
- Business metrics: Users, Quizzes, Documents

---

## 18. FAZA 13 — File Skills System (Anthropic Pattern)

**Datum:** 2026-04-19

Omogućava lepo formatirane izlaze za prevod i export fajlova koristeći Anthropic-style skill pattern.

### Model

| Polje | Tip | Opis |
|-------|-----|------|
| `id` | UUID | Primary key |
| `category` | Enum | TRANSLATE, PDF, DOCX, XLSX |
| `prompt_template` | Text | Skill instrukcije za AI |
| `is_active` | Boolean | Da li je skill aktivan |

### Servis

`FileSkillService` u `backend/app/services/skills/file_skills.py`:
- `get_skill_prompt(category)` — dohvata prompt za kategoriju
- `get_translate_prompt()` — translate skill
- `get_pdf_prompt()` — PDF export skill
- `get_docx_prompt()` — DOCX export skill

### Tok

```
Korisnik klikne "Prevedi"
  → FileSkillService.get_translate_prompt()
  → Prompt se koristi kao dodatni context za AI

Korisnik klikne "Export u PDF/DOCX"
  → FileSkillService.get_pdf_prompt() / get_docx_prompt()
  → Prompt se koristi za formatiranje izlaza
```

---

## 19. FAZA A — Layout-Aware PDF Pipeline

**Datum:** 2026-05-26

Dodata `layout_data` JSON kolona na `Chunk` model sa font/paragraph/page informacijama.

### Promene

| Fajl | Promena |
|------|---------|
| `db/models/document.py` | `layout_data = Column(JSON, nullable=True)` na Chunk |
| `services/pdf.py` | `smart_chunk_with_fonts()` čuva font info |
| `workers/tasks/pdf_processing.py` | Prosleđuje `layout_data` u DB |
| `workers/tasks/pdf_export.py` | chunk_dicts sadrže `page_number` + `layout_data` |
| `services/pdf_export_service.py` | `_extract_heading_pages()` koristi chunk page_number + layout_data |
| `scripts/backfill_layout_data.py` | Backfill za 52,896 postojećih chunkova |

### Backfill

```sql
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS layout_data JSONB;
```

- **52,896 chunks** popunjeno (10 dokumenata)
- **100%** chunks sa `layout_data` od onih sa `page_number`

---

## 20. FAZA B — Layout-Aware Rendering

**Datum:** 2026-05-27

Per-paragraph font/size/bold renderovanje u PDF exportu.

### Helper funkcije (modul nivo)

| Funkcija | Opis |
|----------|------|
| `_split_paragraphs(text, expected_count)` | Razbija tekst na pasuse |
| `_split_evenly(text, n)` | Gruba podela teksta na n delova |
| `_map_font(is_bold)` | Mapira bold/regular na DejaVuSans |
| `_get_layout_paragraphs(chunk)` | Izvlači paragraphs iz layout_data |
| `_scale_size(orig_size, ref_body)` | Skalira font sa clamp [7, 20] |

### Metode klase

| Metoda | Opis |
|--------|------|
| `_build_layout_style(para_info, base_style, ref_body)` | Kreira ParagraphStyle iz layout_data |
| `_detect_ref_body_size(chunks_list)` | Detektuje ref body veličinu |
| `emit_body()` | Layout-aware body renderovanje |

### Verifikacija

- ✅ **20/20 layout testova** (100%)
- ✅ **Flake8 clean** (0 issues)
- ✅ **PDF kvalitet**: 60/60 bookmarks, 87 pages

---

## 21. FAZA D — Roundtrip Export Testovi

**Datum:** 2026-05-28

18 testova koji verifikuju da export-ovani fajlovi sadrže >= 95% teksta iz originalnih chunkova.

### Koncept

```
Chunks (sintetički) → ExportService.generate() → PDF/DOCX/PPTX/XLSX
                                                       ↓
                                               Ekstrakcija teksta
                                                       ↓
                                               Word-level match >= 95%
```

### Testovi po formatu

| Format | Testova | Šta verifikuju |
|--------|---------|----------------|
| PDF | 7 | Full content, short content, include_original, empty, special chars, headings, dedup |
| DOCX | 4 | Full content, include_original, empty, special chars |
| PPTX | 3 | Full content, slide limit, empty |
| XLSX | 4 | Full content, include_original, many rows, empty |

Helper funkcije: `_extract_pdf_text()`, `_extract_docx_text()`, `_extract_pptx_text()`, `_extract_xlsx_text()`

