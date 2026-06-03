# CHANGELOG

Sve značajne izmene u projektu su dokumentovane ovde.
Format: [Verzija] — Datum
Kategorije: ✅ Dodato | 🔧 Izmenjeno | 🐛 Ispravka | 🗑️ Uklonjeno

---

## [2.0.1] — 2026-03-14

### 🐛 Ispravke

#### PDF Processing za skenirane dokumente
- **Problem:** Skenirani PDF-ovi (skenovi knjiga) nisu se obrađivali - 0 chunks
- **Uzrok:** Worker kontejner nije imao instaliran Poppler
- **Rešenje:** Dodati `poppler-utils` u Dockerfile

#### Storage konfiguracija za Worker
- **Problem:** Worker nije mogao da pronađe fajlove u MinIO storage-u
- **Uzrok:** Worker nije imao S3/MinIO konfiguraciju u environment
- **Rešenje:** Dodati STORAGE_BACKEND i CLOUD_STORAGE promenjive u docker-compose.yml

#### Translation API ključevi
- **Problem:** Prevod je koristio placeholder API ključeve umesto korisničkih
- **Uzrok:** translate_document_task koristi sistemske ključeve umesto korisničkih
- **Rešenje:** Izmenjena logika da prvo koristi korisničke API ključeve (Groq, Mistral, Gemini)

#### Povećan limit za upload fajlova
- **Problem:** Maksimalna veličina fajla bila je 50MB
- **Rešenje:** Povećano na 100MB u backend, frontend i nginx konfiguraciji

### ✅ Dodato

#### OCR podrška za srpski jezik
- Dodat `tesseract-ocr-srp` paket za prepoznavanje srpskog teksta

#### Dokumentacija zavisnosti
- Ažuriran IMPLEMENTATION_LOG.md sa detaljnim opisom problema i rešenja
- Dodat poglavlje "OBAVEZNE ZAVISNOSTI za rad aplikacije"

---

## [2.0.0] — 2026-03-01

### ✅ Dodato

#### RAG Knowledge Base sistem (pgvector + Ollama)
- `docker/docker-compose.yml`: PostgreSQL image promenjen na `pgvector/pgvector:pg15`
- Nove DB tabele: `knowledge_sources`, `knowledge_chunks` (sa `vector(384)` kolonom i IVFFlat indeksom)
- `backend/app/services/rag.py`: embed_text, embed_texts, chunk_text, save_chunks_to_db, similarity_search, rag_query
- `backend/app/services/knowledge_ingestion.py`: ingestion za PDF, Markdown, web URL, logove
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384 dim, potpuno offline)
- Kviz generator obogaćen RAG kontekstom iz baze znanja
- Novi Knowledge API endpoints:
  - `POST /knowledge/query` — RAG upit sa AI sintezom
  - `GET /knowledge/sources` — lista indeksiranih izvora
  - `GET /knowledge/stats` — statistike (chunks, sources, po tipu)
  - `POST /knowledge/ingest/url` — async indeksiranje URL-a (jednokratno ili rekurzivno)
  - `POST /knowledge/ingest/text` — direktno indeksiranje teksta
  - `DELETE /knowledge/sources/{id}` — uklanjanje izvora
  - `POST /knowledge/reindex` — ponovni index markdown fajlova
- `frontend/src/pages/KnowledgeBasePage.tsx`: Chat tab (RAG chat sa AI) + Sources tab (upravljanje izvorima)
- "Baza Znanja" navigacijska stavka u Layout-u

#### Rekurzivni URL Crawler
- Novi Celery task `crawl_site_task`: BFS crawler, isti domen, dubina 1-3, max 1-100 stranica
- `POST /knowledge/ingest/url` proširen sa `recursive`, `max_depth`, `max_pages` parametrima
- Frontend forma sa checkbox za rekurzivni mod, dropdown za dubinu i max stranice

#### Quiz Post-Answer AI Chat
- `POST /quizzes/{quiz_id}/chat` — AI tutor chat sa kontekstom pitanja
- Sistem prompt: pitanje + opcije + tačan odgovor + korisnikov odgovor + objašnjenje
- Chat je zaključan dok korisnik ne potvrdi odgovor (`confirmed` state)
- Per-pitanje historija razgovora (čuva se tokom trajanja kviza)
- Poštuje `user.ai_provider` podešavanja (auto/ollama/openai/claude)

#### AI Provajder po korisniku
- 3 nova polja u `users` tabeli: `ai_provider VARCHAR(50)`, `ai_api_key_openai TEXT`, `ai_api_key_claude TEXT`
- `GET /users/me/ai-settings` i `PUT /users/me/ai-settings` endpoints
- API ključevi se prikazuju samo kao `...last4chars` (sigurnost)
- `frontend/src/pages/SettingsPage.tsx`: novi "AI Provajder" tab sa 4 kartice (Auto/Ollama/OpenAI/Claude)
- `frontend/src/pages/DashboardPage.tsx`: AI Provider status kartica u sidebaru

#### CI/CD Pipeline
- `.github/workflows/cd.yml`: CD workflow za staging (push na main) i production (v* tag)
- Podržava: Docker Hub push, SSH deploy, Slack notifikacije (sve opciono)
- `Makefile`: 35+ targeta (`make build`, `make test`, `make deploy-local`, `make deploy-prod TAG=v1.2.3`...)
- `scripts/deploy.sh`: shell skript za ručni deploy sa zdravstenom proverom i rollback-om
- `CI_CD_STRATEGIJA.md`: kompletna dokumentacija CI/CD strategije na srpskom

#### MCP Server — novi tools (20 ukupno)
- `run_tests` — pytest u Docker containeru
- `run_lint` — flake8 na backend kodu
- `api_test` — test bilo kojeg API endpointa sa opcionalnom autentikacijom
- `celery_inspect` — stanje Celery workera i aktivnih taskova
- `error_search` — pretraga logova svih servisa po ključnoj reči
- `db_query` — read-only SQL upiti (samo SELECT/SHOW/EXPLAIN)
- `redis_inspect` — Redis ključevi, queue dužine, memorija
- `performance_check` — CPU/RAM po containeru u realnom vremenu
- `minio_inspect` — status MinIO bucketa i fajlova
- `service_diagnosis` — kompletna dijagnoza jednog servisa

#### Dokumentacija
- `SISTEM_DOKUMENTACIJA.md` — master dokument sistema (636+ linija)
- `CI_CD_STRATEGIJA.md` — kompletna CI/CD strategija
- `IMPLEMENTATION_LOG.md` — RAG-1 do RAG-7 sa arhitekturnim dijagramima

### 🔧 Izmenjeno

#### Kviz sistem
- `backend/app/schemas/quiz.py`: `num_questions` limit povećan `le=30` → `le=50`
- `frontend/src/components/PipelineModal.tsx`: slider `max={20}` → `max={50}`
- `frontend/src/pages/QuizzesPage.tsx`: slider `max={20}` → `max={50}`
- `backend/app/services/quiz.py`: QUIZ_PROMPT prepisan — generiše detaljna objašnjenja (zašto tačan + zašto netačni)
- `backend/app/services/quiz.py`: text limit 6000→12000 chars, chunk limit 10→20
- `frontend/src/pages/QuizPlayPage.tsx`: "Potvrdi odgovor" flow — feedback panel sa per-opcija bojom i objašnjenjem

#### JWT Autentikacija — Token Blacklist
- `backend/app/services/auth.py`: `blacklist_token()`, `is_token_blacklisted()` putem Redis
- `backend/app/api/endpoints/auth.py`: logout čita Bearer token i dodaje ga u Redis blacklist
- Ključ: `blacklist:{token}`, TTL = preostalo vreme do isteka tokena
- Graceful degradacija: ako Redis nije dostupan, blacklist se preskače

#### Requirements
- `langchain==0.0.340` → `langchain>=0.2.16`
- Dodato: `langchain-community>=0.2.16`, `langchain-ollama>=0.1.3`, `pgvector>=0.3.0`
- Dodato: `beautifulsoup4>=4.12.0`, `lxml>=4.9.0`

#### Docker Compose
- `postgres:15-alpine` → `pgvector/pgvector:pg15`
- Nginx volume mount za frontend dist: `../frontend/dist:/usr/share/nginx/html:ro`

---

## [1.0.0] — 2026-03-01

### ✅ Dodato

#### Frontend Build & Deploy
- React/Vite frontend buildan i pokrenut kroz Nginx
- `frontend/dist/` se servira na `http://localhost` (port 80)
- Volume mount dodat u `docker-compose.yml`: `../frontend/dist:/usr/share/nginx/html:ro`

### 🐛 Ispravka

#### Frontend CSS Build Greške
- `src/index.css`: `@apply border-border` → `@apply border-gray-200` (klasa `border-border` ne postoji u Tailwind konfigu)
- `src/index.css`: `@apply card overflow-hidden group` → `@apply card overflow-hidden` (`group` ne može u `@apply`)

#### Docker / Celery / Worker
- `docker-compose.yml`: Dodate Celery-specifične healthcheck komande za `worker` i `beat` servise (prethodni Dockerfile HEALTHCHECK je koristio `curl http://localhost:8000/health` što nije radilo za worker/beat koji ne pokreću HTTP server)
- `backend/app/workers/celery_app.py`: importovan u `main.py` da bi `@shared_task` radilo ispravno iz API procesa
- `backend/app/core/config.py`: dodat `task_default_queue: "default"` u `CELERY_CONFIG` (mismatch između podrazumevane Celery `celery` queue i worker queue-a `default`)

#### bcrypt / passlib Kompatibilnost
- `requirements.txt`: pinkovan `bcrypt==3.2.2` — `bcrypt>=4.0` nije kompatibilan sa `passlib==1.7.4`

#### PDF Processing / tiktoken
- `backend/app/services/pdf.py`: `tiktoken.get_encoding()` wrapovan u `ThreadPoolExecutor` sa `timeout=5s` i `shutdown(wait=False)` — sprečava beskonačno čekanje bez internet konekcije

#### OpenAI Model
- `docker/.env`: `OPENAI_MODEL=gpt-4` → `OPENAI_MODEL=gpt-4o-mini` (gpt-4 nije dostupan na ovom planu)

#### Debug Print Statements
- Uklonjeni svi `print()` debug iskazi iz `storage.py`, `router.py`, `files.py`

#### WSL2 Docker Networking
- Dodat persistence script `/etc/network/if-up.d/docker-iptables` za iptables pravila
- Rešen problem praznog `DOCKER-INTERNAL` lanca nakon restart Docker daemon-a
- Dodata MASQUERADE pravila za internet pristup iz kontejnera

---
## [1.0.0-rc1] — 2026-02-25

### ✅ Dodato

#### Password Reset Flow
- `POST /auth/forgot-password` — generiše token (1h), šalje email sa linkom
- `POST /auth/reset-password` — verifikuje token, menja lozinku (single-use)
- `ForgotPasswordPage.tsx` — forma za unos emaila, success state
- `ResetPasswordPage.tsx` — forma za novu lozinku sa potvrdom
- "Zaboravili ste lozinku?" link u `LoginPage.tsx`
- `email_service.send_password_reset()` — HTML email template

#### Security / Rate Limiting
- `slowapi` dodat u `requirements.txt`
- `Limiter(key_func=get_remote_address)` inicijalizovan u `main.py`
- `RateLimitExceeded` exception handler dodat
- Rate limits na auth endpointima:
  - `POST /auth/register` — 5 req/min
  - `POST /auth/login` — 10 req/min
  - `POST /auth/forgot-password` — 3 req/min

#### Quiz Poboljšanja
- `shuffle_questions: Boolean` kolona dodata u `Quiz` model
- `QuizCreate.shuffle_questions: bool = False` u Pydantic schema
- `QuizResponse.shuffle_questions` u response schema
- `GET /quizzes/{id}` — vraća pitanja u nasumičnom redosledu ako `shuffle_questions=True`
- `QuizService._check_answer_static()` — statička metoda za testiranje

#### Testovi
- `tests/integration/test_quiz.py` — testovi za Quiz, Question, QuizAttempt, answer checking, provajderi
- `tests/integration/test_study_plan.py` — testovi za StudyPlan, StudyPlanItem, napredak
- `tests/integration/test_analytics.py` — testovi za streak, agregacije, aktivnost, overview

#### CI/CD
- `.github/workflows/ci.yml` — GitHub Actions:
  - Backend: flake8 lint + unit testovi + integration testovi + coverage (>60%)
  - Frontend: TypeScript typecheck + `npm run build`
  - Docker build check (samo na main)
  - Services: PostgreSQL 15 + Redis 7

#### Monitoring / Grafana
- `docker/grafana/datasources/prometheus.yml` — Prometheus datasource provisioning
- `docker/grafana/dashboards/dashboards.yml` — Dashboard provider provisioning
- `docker/grafana/dashboards/ai_learning.json` — Grafana dashboard sa panelima:
  - HTTP Request Rate (req/s)
  - HTTP Error Rate (%)
  - API Latency P95 (ms)
  - Celery Active Tasks & Queue Size
  - DB Connection Pool
  - Quiz Generation Duration (p50/p95)
  - Total Users / Quizzes / Documents (stat panels)

#### Konfiguracija
- `settings.FRONTEND_URL: str = "http://localhost:5173"` — dodat u `config.py`
- `docker/.env.example` — ažurirano sa `FRONTEND_URL`

---

## [0.9.0] — 2026-02-19

### ✅ Dodato

#### Analytics (Faza 9)
- `backend/app/api/endpoints/analytics.py`:
  - `GET /analytics/me/overview` — ukupni stats (kvizovi, dokumenti, streak, avg score)
  - `GET /analytics/me/activity` — dnevna aktivnost (7/14/30/60d)
  - `GET /analytics/me/quizzes` — performanse po kvizovima
  - `GET /analytics/me/documents` — statistike dokumenata
  - `GET /analytics/me/streak-history` — GitHub heatmap podaci
- `frontend/src/pages/AnalyticsPage.tsx` — SVG bar chart, heatmap, tabele

#### Email Notifikacije
- `backend/app/services/email_service.py`:
  - `send_welcome()` — email pri registraciji
  - `send_daily_reminder()` — podsetnik za kvizove
  - `send_weekly_summary()` — nedeljni izveštaj sa statsom
- Celery task `send_study_reminders` (svaki sat)
- Celery task `send_weekly_summaries` (nedeljom u 10:00)

#### PDF Export (Faza 6)
- `backend/app/services/pdf_export_service.py` — ReportLab PDF generacija
- `GET /documents/{id}/export/pdf?include_original=false`
- "Preuzmi PDF" dugme u `DocumentDetailPage.tsx`

#### Plan Učenja (Faza 7b)
- `frontend/src/components/StudyPlanTab.tsx` — slider za ciljeve, dani, zakazivanje kvizova
- 4. tab u SettingsPage

### 🔧 Izmenjeno
- `DashboardPage.tsx` — live stats iz analytics API, funkcionalni linkovi ka Kvizovi/Analitika

### 🐛 Ispravke
- `documents.py` PDF export: ispravni nazivi Chunk kolona (`content`, `translated_content`, `sequence_number`)
- `celery_app.py` — pravilno `crontab` iz `celery.schedules`, uklonjeno iz `config.py`
- `tasks.py` — uklonjen duplikat importa, unused `json`
- `auth.py` — welcome email via `BackgroundTasks`

---

## [0.8.0] — 2026-02-10

### ✅ Dodato
- Kviz sistem (Faza 7): generisanje AI kvizova, igranje, rezultati, istorija pokušaja
- Auto Pipeline (Faza 7a): PDF → prevod → kviz u jednom klipu
- 3 AI provajdera za kvizove: Ollama (local), OpenAI, Claude sa fallback lancem
- Alembic migracija 003: study_plan tabele

---

## [0.7.0] — 2026-02-01

### ✅ Dodato
- Human-in-Loop review (Faza 5): ReviewPage sa diff pregledom
- AI Translation (Faza 4): Ollama/OpenAI/Claude prevod sa Celery
- File management (Faza 2): MinIO storage, upload, download, presigned URLs
- PDF Processing (Faza 3): pdfminer.six ekstrakcija, chunking po poglavljima

---

## [0.5.0] — 2026-01-20

### ✅ Dodato
- Autentikacija (Faza 1): JWT access+refresh token, Zustand store
- Osnovna infrastruktura (Faza 0): FastAPI + PostgreSQL + Redis + MinIO + Celery + Nginx
- Alembic migracija 001 (initial) + 002 (quiz tables)
- Docker Compose sa svim servisima
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS
