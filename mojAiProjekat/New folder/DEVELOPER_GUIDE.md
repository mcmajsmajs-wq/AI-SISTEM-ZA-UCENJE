# DEVELOPER GUIDE — AI SISTEM ZA UČENJE
**Verzija:** 2.0.0  
**Poslednje ažuriranje:** 2026-02-25

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
│  port 5173     │      │  port 8000     │
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
uvicorn app.main:app --reload --port 8000
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
│   │   │   ├── pdf_service.py
│   │   │   ├── quiz.py          # Multi-provider quiz generation
│   │   │   └── translation_service.py
│   │   ├── workers/
│   │   │   └── tasks.py         # Celery tasks
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   └── security.py
│   │   └── main.py
│   └── alembic/
│       └── versions/
│           ├── 001_initial.py
│           ├── 002_quiz_tables.py
│           └── 003_study_plan.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── PipelineModal.tsx
│       │   └── StudyPlanTab.tsx
│       ├── pages/
│       │   ├── QuizzesPage.tsx
│       │   ├── QuizPlayPage.tsx
│       │   ├── QuizResultsPage.tsx
│       │   └── SettingsPage.tsx  # sa Plan učenja tabom
│       ├── services/api.ts       # Axios + sve API metode
│       ├── stores/authStore.ts
│       └── types/index.ts
├── docker-compose.yml
└── .env.example
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

### Enum tipovi (PostgreSQL)

- `quizstatus` — `pending`, `generating`, `ready`, `failed`
- `questiontype` — `multiple_choice`, `checkbox`, `true_false`

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
GET    /                Lista dokumenata
POST   /                Upload dokumenta
GET    /{id}            Detalji dokumenta
DELETE /{id}            Brisanje
POST   /{id}/process    Pokretanje PDF obrade
POST   /{id}/translate  Pokretanje prevoda
POST   /{id}/pipeline   🆕 Pokretanje auto pipeline-a
GET    /pipeline/providers  🆕 Lista dostupnih AI provajdera
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

Svi AI provajderi za kviz nasleđuju `BaseQuizClient` iz `backend/app/services/quiz.py`.

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

U `QuizService.__init__()`:
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

Taskovi se nalaze u `backend/app/workers/tasks.py`.

### Postojeći taskovi

| Task | Opis |
|------|------|
| `process_document_task` | PDF ekstrakcija i chunking |
| `translate_document_task` | Prevod svih chunkova |
| `generate_quiz_task` | Generisanje pitanja za kviz (jedan provajder) |
| `auto_pipeline_task` | 🆕 Kompletni pipeline: PDF→Prevod→Kviz |

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

### Struktura testova

```
backend/tests/
├── conftest.py          # pytest fixtures (db, client, auth)
├── test_auth.py
├── test_documents.py
├── test_quiz.py         # TODO — dodati
├── test_study_plan.py   # TODO — dodati
└── test_pipeline.py     # TODO — dodati
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

