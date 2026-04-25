================================================================================
DETALJAN WORKFLOW PLAN - AI SISTEM ZA UČENJE
Implementacioni vodič korak po korak
================================================================================

SADRŽAJ:
1. Arhitektura sistema
2. Kompletan workflow po fazama
3. Checklist za svaku fazu
4. Test scenarios
5. Deployment plan

================================================================================
SEKCIJA 1: ARHITEKTURA SISTEMA
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI LEARNING SYSTEM ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │   Klijent    │────▶│   FastAPI    │────▶│  PostgreSQL  │                │
│   │  (React/Vue) │◀────│   Backend    │◀────│   Database   │                │
│   └──────────────┘     └──────┬───────┘     └──────────────┘                │
│                               │                                              │
│          ┌────────────────────┼────────────────────┐                        │
│          │                    │                    │                        │
│          ▼                    ▼                    ▼                        │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │    Redis     │     │    Ollama    │     │   MinIO/S3   │                │
│   │   (Queue)    │     │    (AI LLM)  │     │(File Storage)│                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│          │                                              │                    │
│          │         ┌──────────────┐                    │                    │
│          └────────▶│   Celery     │────────────────────┘                    │
│                    │   Workers    │                                         │
│                    └──────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
SEKCIJA 2: KOMPLETAN WORKFLOW PO FAZAMA
================================================================================

───────────────────────────────────────────────────────────────────────────────
FAZA 0: INFRASTRUKTURA I SETUP (Foundation)
───────────────────────────────────────────────────────────────────────────────

0.1. KREIRANJE PROJEKTNE STRUKTURE
    └── 📁 ai-learning-system/
        ├── 📁 backend/
        │   ├── 📁 app/
        │   │   ├── 📁 api/              # API endpoint-i
        │   │   ├── 📁 core/             # Core funkcionalnosti
        │   │   ├── 📁 db/               # Database models i migrations
        │   │   ├── 📁 services/         # Business logic
        │   │   ├── 📁 utils/            # Utility funkcije
        │   │   ├── 📁 workers/          # Celery task-ovi
        │   │   ├── 📁 schemas/          # Pydantic models
        │   │   └── 📁 tests/            # Testovi
        │   ├── 📁 alembic/              # Database migrations
        │   ├── 📄 requirements.txt
        │   ├── 📄 Dockerfile
        │   └── 📄 pytest.ini
        ├── 📁 frontend/
        │   ├── 📁 src/
        │   ├── 📁 public/
        │   └── 📄 package.json
        ├── 📁 docker/
        │   ├── 📄 docker-compose.yml
        │   ├── 📄 docker-compose.prod.yml
        │   └── 📄 .env.example
        ├── 📁 docs/
        │   ├── 📄 api-specification.md
        │   └── 📄 deployment-guide.md
        └── 📁 scripts/
            ├── 📄 setup.sh
            └── 📄 deploy.sh

0.2. DOCKER INFRASTRUKTURA
    ☐ Kreirati docker-compose.yml sa servisima:
        - app (FastAPI)
        - db (PostgreSQL 15)
        - redis (Redis 7)
        - worker (Celery)
        - minio (MinIO - S3 compatible)
        - ollama (AI LLM - optional)
        - nginx (Reverse proxy)
        - prometheus (Monitoring)
        - grafana (Dashboards)
    
    ☐ Definisati environment variables (.env.example):
        - Database credentials
        - JWT secret keys
        - API keys (OpenAI, etc.)
        - Storage configuration
        - Email settings

0.3. DATABASE SETUP
    ☐ Instalirati PostgreSQL 15
    ☐ Kreirati database i korisnika
    ☐ Postaviti Alembic za migrations
    ☐ Definisati osnovne tabele (vidi sekciju 3)

0.4. SECURITY SETUP
    ☐ Konfigurisati HTTPS/TLS
    ☐ Postaviti CORS policy
    ☐ Implementirati CSRF protection
    ☐ Rate limiting (100 req/min po IP)
    ☐ Input validation i sanitization
    ☐ Helmet headers

───────────────────────────────────────────────────────────────────────────────
FAZA 1: AUTENTIKACIJA I KORISNIČKI SISTEM
───────────────────────────────────────────────────────────────────────────────

1.1. USER MODEL I DATABASE SCHEMA
    ☐ Tabela: users
        - id (UUID, PK)
        - email (unique, indexed)
        - hashed_password
        - full_name
        - is_active (boolean)
        - is_verified (boolean)
        - role (enum: admin, user)
        - created_at, updated_at
    
    ☐ Tabela: user_sessions
        - id (UUID, PK)
        - user_id (FK)
        - token (JWT)
        - expires_at
        - ip_address
        - user_agent

1.2. AUTHENTIKACIJA IMPLEMENTACIJA
    ☐ JWT token generation (access + refresh tokens)
    ☐ Login endpoint (/api/v1/auth/login)
    ☐ Register endpoint (/api/v1/auth/register)
    ☐ Logout endpoint (/api/v1/auth/logout)
    ☐ Password reset flow
    ☐ Email verification
    ☐ OAuth2 integration (Google, GitHub)

1.3. AUTORIZACIJA
    ☐ Role-based access control (RBAC)
    ☐ JWT middleware za zaštitu endpoint-a
    ☐ Permission decorators
    ☐ API key autentikacija za servise

───────────────────────────────────────────────────────────────────────────────
FAZA 2: FILE MANAGEMENT SISTEM
───────────────────────────────────────────────────────────────────────────────

2.1. FILE STORAGE SETUP (MinIO/S3)
    ☐ Instalirati i konfigurisati MinIO
    ☐ Kreirati buckets:
        - uploads (raw PDFs)
        - processed (processed files)
        - exports (generated PDFs)
        - backups (database backups)
    ☐ Postaviti lifecycle policies (30 dana za uploads)
    ☐ Konfigurisati CORS za bucket-e

2.2. FILE UPLOAD SISTEM
    ☐ Endpoint: POST /api/v1/files/upload
    ☐ Validacija fajla:
        - Ekstenzija: .pdf
        - MIME type: application/pdf
        - Maksimalna veličina: 50MB
        - Malware scan (ClamAV)
    ☐ Chunked upload za velike fajlove
    ☐ Progress tracking (WebSocket/SSE)
    ☐ Virus scanning pre snimanja

2.3. FILE METADATA I UPRAVLJANJE
    ☐ Tabela: files
        - id (UUID, PK)
        - user_id (FK)
        - original_filename
        - storage_path
        - file_size
        - mime_type
        - checksum (SHA256)
        - status (enum: uploaded, processing, completed, error)
        - metadata (JSONB)
        - created_at, updated_at
    
    ☐ Endpoint-i:
        - GET /api/v1/files (list sa pagination)
        - GET /api/v1/files/{id} (details)
        - DELETE /api/v1/files/{id} (soft delete)
        - GET /api/v1/files/{id}/download

───────────────────────────────────────────────────────────────────────────────
FAZA 3: INGEST I SEGMENTACIJA (Core Engine)
───────────────────────────────────────────────────────────────────────────────

3.1. PDF PROCESSING PIPELINE
    ☐ Koristiti PyMuPDF (fitz) za ekstrakciju
    ☐ Proveriti integritet PDF-a
    ☐ Ekstrahovati:
        - Tekst (UTF-8)
        - Slike (opciono)
        - Tabele (opciono)
        - Metadata (author, title, pages)
    ☐ OCR za skenirane PDF-ove (Tesseract)

3.2. DENOISING I ČIŠĆENJE
    ☐ Ukloniti zaglavlja i podnožja
    ☐ Ukloniti brojeve stranica
    ☐ Ukloniti watermark-e
    ☐ Normalizovati whitespace
    ☐ Fix encoding issues
    ☐ Remove special artifacts

3.3. CHUNKING STRATEGIJA
    ☐ Semantički chunking:
        - Po poglavljima/sekcijama
        - Po naslovima (h1, h2, h3)
        - Max 2000 tokena po chunk-u
        - Min 500 tokena (izbegavati previše male)
        - Overlap: 200 tokena između chunk-ova
    
    ☐ Algoritam:
        1. Split by headings
        2. Merge small chunks
        3. Split large chunks
        4. Add context headers
        5. Calculate embeddings (opционо)

3.4. TEKSUALNI MODEL I BAZA
    ☐ Tabela: documents
        - id (UUID, PK)
        - user_id (FK)
        - file_id (FK)
        - title
        - description
        - total_pages
        - total_chunks
        - status
        - metadata (JSONB)
    
    ☐ Tabela: chunks
        - id (UUID, PK)
        - document_id (FK)
        - sequence_number
        - content (TEXT)
        - token_count
        - heading_level
        - parent_heading
        - embedding (vector, optional)

3.5. BACKGROUND PROCESSING
    ☐ Celery task za ingest:
        - async_pdf_processing_task
        - chunking_task
        - quality_check_task
    ☐ Queue prioriteti:
        - high: urgent processing
        - default: normal processing
        - low: batch processing
    ☐ Retry policy:
        - Max retries: 3
        - Backoff: exponential (5min, 15min, 45min)
        - Dead letter queue za failed tasks

3.6. LOGOVANJE I MONITORING
    ☐ JSON log format:
        {
          "timestamp": "2024-01-15T10:30:00Z",
          "level": "INFO",
          "phase": "INGEST",
          "event": "CHUNK_CREATED",
          "document_id": "uuid",
          "user_id": "uuid",
          "chunk_id": "uuid",
          "message": "Chunk created successfully",
          "duration_ms": 150,
          "metadata": {...}
        }
    
    ☐ Metrike:
        - Processing time per document
        - Success/failure rate
        - Queue depth
        - Worker utilization

───────────────────────────────────────────────────────────────────────────────
FAZA 4: AI PREVOD I GENERISANJE PITANJA
───────────────────────────────────────────────────────────────────────────────

4.1. AI PROVIDER SETUP
    ☐ Primary: Ollama (Llama 3.1) - lokalno
    ☐ Fallback: OpenAI API (GPT-4)
    ☐ Rate limiting:
        - Ollama: 10 req/min
        - OpenAI: zavisno od tier-a
    ☐ Caching layer (Redis):
        - TTL: 24h za prevode
        - Key: hash(content + prompt)

4.2. PROMPT ENGINEERING
    ☐ System prompt za prevod:
        ```
        Ti si stručni prevodilac. Prevedi sledeći tekst na srpski jezik.
        Pravila:
        1. Sačuvaj stručnu terminologiju u originalu u zagradama
        2. Koristi padeže ispravno
        3. Zadrži strukturu i formatiranje
        4. Prevedi na srpski (latinica ili ćirilica po izboru)
        5. Sačuvaj kontekst i značenje
        ```
    
    ☐ System prompt za kviz:
        ```
        Na osnovu sledećeg teksta, generiši 3-5 pitanja sa višestrukim odgovorima.
        Format: JSON
        {
          "questions": [
            {
              "question": "tekst pitanja",
              "options": ["odgovor1", "odgovor2", "odgovor3", "odgovor4"],
              "correct_indices": [0, 2],
              "explanation": "objašnjenje",
              "difficulty": "easy|medium|hard"
            }
          ]
        }
        ```

4.3. ASINHRONA OBRADA
    ☐ Celery task: translate_chunks_task
        - Input: list chunk IDs
        - Process: 5 chunk-ova paralelno
        - Output: translated content
    
    ☐ Progress tracking:
        - WebSocket/SSE za real-time update
        - Progress stored in Redis
        - Endpoint: GET /api/v1/tasks/{task_id}/progress

4.4. KVIZ GENERATOR
    ☐ Endpoint: POST /api/v1/documents/{id}/generate-quiz
    ☐ Parametri:
        - num_questions (5-50)
        - difficulty (mixed, easy, medium, hard)
        - question_types (multiple_choice, checkbox, true_false)
    ☐ AI prompt tuning za bolje rezultate
    ☐ Validacija generisanih pitanja

4.5. ERROR HANDLING I RETRY
    ☐ LLM timeout: retry sa exponential backoff
    ☐ Invalid response format: retry sa drugačijim promptom
    ☐ Rate limit exceeded: queue za kasnije
    ☐ Circuit breaker pattern za OpenAI

───────────────────────────────────────────────────────────────────────────────
FAZA 5: HUMAN-IN-THE-LOOP SISTEM
───────────────────────────────────────────────────────────────────────────────

5.1. REVIEW INTERFACE
    ☐ Side-by-side preview:
        - Levo: originalni tekst
        - Desno: prevedeni tekst (editable)
    ☐ Diff highlighting za izmene
    ☐ Inline editing sa auto-save
    ☐ Batch operations (approve all, reject all)
    ☐ Search i filter po sekcijama

5.2. TERMINOLOŠKA VALIDACIJA
    ☐ Markiranje stručnih termina
    ☐ Sugestije iz glossary-a
    ☐ User-defined glossary per document
    ☐ Spell check za srpski jezik

5.3. WORKFLOW MANAGEMENT
    ☐ Statusi:
        - draft (AI generisano)
        - in_review (čeka proveru)
        - approved (odobreno)
        - published (konačno)
    ☐ Versioning: čuvanje svih izmena
    ☐ Comments i annotations
    ☐ Export u različitim formatima

5.4. NOTIFICATIONS
    ☐ Email notifikacije za review tasks
    ☐ In-app notifikacije
    ☐ Due date reminders
    ☐ Team assignment

───────────────────────────────────────────────────────────────────────────────
FAZA 6: PDF GENERATOR
───────────────────────────────────────────────────────────────────────────────

6.1. FONT I ENCODING SETUP
    ☐ Instalirati fontove sa srpskim karakterima:
        - Noto Sans (Latin i Cyrillic)
        - Arial Unicode MS (fallback)
    ☐ UTF-8 encoding za sve tekstove
    ☐ Testiranje specijalnih karaktera (č, ć, ž, š, đ)

6.2. LAYOUT DESIGN
    ☐ Template struktura:
        - Naslovna strana
        - Sadržaj (TOC)
        - Glavni sadržaj (paginated)
        - Kviz sekcija (na kraju)
        - Odgovori i objašnjenja
    
    ☐ Stilovi:
        - Naslovi: 18pt bold
        - Podnaslovi: 14pt bold
        - Tekst: 12pt regular
        - Margine: 2.5cm sve strane
        - Header/footer sa brojem strane

6.3. GENERISANJE PDF-a
    ☐ Biblioteka: ReportLab + Platypus
    ☐ Koraci:
        1. Učitaj template
        2. Renderuj sadržaj
        3. Dodaj kviz
        4. Generiši TOC
        5. Dodaj page numbers
        6. Export PDF
    ☐ Filename format: {title}_SRB_{timestamp}.pdf
    ☐ Metadata embedding (title, author, subject)

6.4. PREVIEW I DOWNLOAD
    ☐ PDF.js za browser preview
    ☐ Download endpoint sa auth check
    ☐ File size optimization (compress images)

───────────────────────────────────────────────────────────────────────────────
FAZA 7: INTERAKTIVNI KVIZ I BAZA PODATAKA
───────────────────────────────────────────────────────────────────────────────

7.1. DATABASE SCHEMA ZA KVIZ
    ☐ Tabela: quizzes
        - id (UUID, PK)
        - document_id (FK)
        - user_id (FK)
        - title
        - description
        - settings (JSONB)
        - is_published
        - created_at
    
    ☐ Tabela: questions
        - id (UUID, PK)
        - quiz_id (FK)
        - question_text
        - question_type (multiple_choice, checkbox, true_false)
        - options (JSONB)
        - correct_answers (JSONB)
        - explanation
        - difficulty
        - points
        - sequence_order
    
    ☐ Tabela: quiz_attempts
        - id (UUID, PK)
        - quiz_id (FK)
        - user_id (FK)
        - started_at
        - completed_at
        - score
        - total_points
        - percentage
        - time_spent_seconds
        - status (in_progress, completed, abandoned)
    
    ☐ Tabela: answers
        - id (UUID, PK)
        - attempt_id (FK)
        - question_id (FK)
        - selected_options (JSONB)
        - is_correct
        - points_earned
        - time_spent_seconds
        - answered_at

7.2. KVIZ INTERFACE
    ☐ React/Vue komponente:
        - QuizCard (prikaz kviza)
        - QuestionRenderer (dinamički po tipu)
        - ProgressBar
        - Timer
        - Navigation (next/prev)
    ☐ Features:
        - Shuffle questions (opciono)
        - Time limit po pitanju
        - Flag for review
        - Save progress (auto-save)
        - Submit confirmation

7.3. VALIDACIJA I FEEDBACK
    ☐ Trenutna validacija:
        - Instant feedback (tačno/nažalost netačno)
        - Prikaz objašnjenja
        - Highlight tačnih odgovora
    ☐ End-of-quiz summary:
        - Total score
        - Breakdown by question
        - Time analysis
        - Suggested review areas

7.4. API ENDPOINT-I
    ☐ GET /api/v1/quizzes (list)
    ☐ GET /api/v1/quizzes/{id} (details)
    ☐ POST /api/v1/quizzes/{id}/attempts (start)
    ☐ POST /api/v1/quizzes/{id}/submit (submit answer)
    ☐ GET /api/v1/quizzes/{id}/results (get results)
    ☐ GET /api/v1/quizzes/{id}/leaderboard (optional)

───────────────────────────────────────────────────────────────────────────────
FAZA 8: KALENDAR I SPACED REPETITION
───────────────────────────────────────────────────────────────────────────────

8.1. SPACED REPETITION ALGORITAM
    ☐ Implementirati SM-2 algoritam (SuperMemo 2)
    ☐ Parametri:
        - ease_factor (default: 2.5)
        - interval (1, 6, 14, 30, 90 dana...)
        - repetition_count
        - quality (0-5 score)
    
    ☐ Formula:
        IF quality >= 3:
            IF repetition_count == 0: interval = 1
            IF repetition_count == 1: interval = 6
            ELSE: interval = interval * ease_factor
        ELSE:
            repetition_count = 0
            interval = 1

8.2. DATABASE SCHEMA
    ☐ Tabela: study_schedules
        - id (UUID, PK)
        - user_id (FK)
        - document_id (FK)
        - quiz_id (FK)
        - next_review_date
        - interval_days
        - ease_factor
        - repetition_count
        - last_quality
        - streak_count
        - is_active
    
    ☐ Tabela: study_sessions
        - id (UUID, PK)
        - schedule_id (FK)
        - scheduled_date
        - completed_date
        - status (scheduled, completed, skipped, overdue)
        - performance_score
        - notes

8.3. KALENDAR INTERFACE
    ☐ FullCalendar.io integracija
    ☐ Views: month, week, day, list
    ☐ Event types:
        - Study session (plavo)
        - Quiz (zeleno)
        - Review (žuto)
        - Overdue (crveno)
    ☐ Features:
        - Drag & drop rescheduling
        - Quick add
        - Recurring events
        - Filters by document/topic

8.4. NOTIFIKACIJE I REMINDERS
    ☐ Email reminders:
        - 24h pre sesije
        - Morning digest (overdue items)
    ☐ In-app notifikacije:
        - Dashboard widgets
        - Browser push notifications
        - Bell icon counter
    ☐ Celery Beat schedule:
        - Daily at 8am: send reminders
        - Hourly: check overdue items

8.5. API ENDPOINT-I
    ☐ GET /api/v1/calendar/events (get events za date range)
    ☐ POST /api/v1/calendar/events (create event)
    ☐ PUT /api/v1/calendar/events/{id} (update)
    ☐ DELETE /api/v1/calendar/events/{id}
    ☐ POST /api/v1/calendar/events/{id}/complete
    ☐ GET /api/v1/study-schedule (get user's schedule)

───────────────────────────────────────────────────────────────────────────────
FAZA 9: ANALITIKA I DASHBOARD
───────────────────────────────────────────────────────────────────────────────

9.1. METRIKE I IZRAČUNAVANJE
    ☐ Individualne metrike:
        - Total documents studied
        - Total quizzes taken
        - Average score
        - Total study time
        - Current streak (days)
        - Longest streak
        - Mastery level per topic
    
    ☐ Time-series metrike:
        - Daily study time
        - Daily quiz scores
        - Topics progress over time
        - Retention rate

9.2. HEATMAP VIZUALIZACIJA
    ☐ Activity heatmap (GitHub-style):
        - Last 365 days
        - Color intensity by activity level
        - Hover: show details
    
    ☐ Knowledge heatmap:
        - Grid: topics x time
        - Colors: red (<50%), yellow (50-80%), green (>80%)
        - Drill-down capability

9.3. MASTERY LEVELS
    ☐ Izračunavanje:
        - Mastery % = (avg_score * 0.6) + (completion_rate * 0.4)
        - Categories: beginner (0-40%), intermediate (40-70%), expert (70-100%)
    
    ☐ Progress tracking:
        - Per document
        - Per topic
        - Overall progress

9.4. CHARTS I GRAFIKONI
    ☐ Chart.js/D3.js implementacija:
        - Line chart: progress over time
        - Bar chart: scores by topic
        - Pie chart: time distribution
        - Radar chart: skill assessment
        - Trend lines i predictions

9.5. API ENDPOINT-I
    ☐ GET /api/v1/analytics/overview (summary stats)
    ☐ GET /api/v1/analytics/activity (activity data za heatmap)
    ☐ GET /api/v1/analytics/progress (progress by document)
    ☐ GET /api/v1/analytics/mastery (mastery levels)
    ☐ GET /api/v1/analytics/export (export data)

───────────────────────────────────────────────────────────────────────────────
FAZA 10: SEMANTIČKA PRETRAGA
───────────────────────────────────────────────────────────────────────────────

10.1. VECTOR DATABASE
    ☐ Opcije:
        - pgvector (PostgreSQL ekstenzija) - PREPORUČENO
        - Pinecone (cloud)
        - Weaviate (self-hosted)
        - Chroma (lokalno)
    
    ☐ Embeddings model:
        - OpenAI: text-embedding-ada-002 ili text-embedding-3-small
        - Lokalno: sentence-transformers (all-MiniLM-L6-v2)

10.2. INDEXING PIPELINE
    ☐ Celery task: index_chunks_task
        - Generate embedding za svaki chunk
        - Store in vector DB
        - Metadata: document_id, chunk_id, user_id
    
    ☐ Batch processing:
        - Process 100 chunks at a time
        - Retry failed embeddings
        - Progress tracking

10.3. SEARCH INTERFACE
    ☐ Endpoint: POST /api/v1/search
    ☐ Query parameters:
        - q (search query)
        - document_id (optional filter)
        - limit (default: 10)
        - threshold (similarity threshold, default: 0.7)
    
    ☐ Response format:
        ```json
        {
          "query": "...",
          "results": [
            {
              "chunk_id": "uuid",
              "document_id": "uuid",
              "content": "...",
              "similarity_score": 0.92,
              "metadata": {...}
            }
          ],
          "total_results": 42
        }
        ```

10.4. ADVANCED SEARCH
    ☐ Hybrid search:
        - Vector similarity (70% weight)
        - Keyword matching (30% weight)
    ☐ Filters:
        - By document
        - By date range
        - By user (admin only)
    ☐ Autocomplete sugestije

───────────────────────────────────────────────────────────────────────────────
FAZA 11: BACKUP I DATA MANAGEMENT
───────────────────────────────────────────────────────────────────────────────

11.1. DATABASE BACKUP
    ☐ Automated daily backups (pg_dump)
    ☐ Retention policy:
        - Daily: 7 days
        - Weekly: 4 weeks
        - Monthly: 12 months
    ☐ Storage: MinIO/S3 bucket
    ☐ Encryption: AES-256

11.2. FILE BACKUP
    ☐ Cross-region replication (ako je cloud)
    ☐ Versioning za buckets
    ☐ Lifecycle: archive old versions

11.3. BACKUP RESTORE
    ☐ Restore procedure dokumentacija
    ☐ Test restore monthly
    ☐ Point-in-time recovery (PITR)

11.4. DATA RETENTION
    ☐ Soft delete (mark as deleted)
    ☐ Hard delete after 30 days
    ☐ GDPR compliance:
        - Right to be forgotten
        - Data export
        - Consent tracking

───────────────────────────────────────────────────────────────────────────────
FAZA 12: MONITORING I LOGGING
───────────────────────────────────────────────────────────────────────────────

12.1. APPLICATION LOGGING
    ☐ Structured JSON logs
    ☐ Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    ☐ Centralized logging (ELK stack ili Grafana Loki)
    ☐ Log rotation (daily, keep 30 days)
    
    ☐ Log categories:
        - application.log (general)
        - error.log (errors only)
        - audit.log (security events)
        - access.log (HTTP requests)

12.2. METRICS COLLECTION
    ☐ Prometheus metrics:
        - Request count/latency
        - Database connection pool
        - Queue depth
        - Error rate
        - AI API usage
    ☐ Custom business metrics:
        - Documents processed
        - Quizzes taken
        - Active users

12.3. ALERTING
    ☐ Alertmanager + Prometheus
    ☐ Alert conditions:
        - Error rate > 5%
        - Response time > 2s
        - Queue depth > 1000
        - Disk usage > 80%
        - AI API failures > 10%
    ☐ Notification channels:
        - Email
        - Slack/Discord
        - PagerDuty (critical)

12.4. HEALTH CHECKS
    ☐ Endpoint: GET /health
        - Database connectivity
        - Redis connectivity
        - AI service status
        - Disk space
    ☐ Readiness probe: /ready
    ☐ Liveness probe: /live

───────────────────────────────────────────────────────────────────────────────
FAZA 13: TESTING STRATEGIJA
───────────────────────────────────────────────────────────────────────────────

13.1. UNIT TESTS
    ☐ Pytest za Python
    ☐ Coverage: minimum 80%
    ☐ Test categories:
        - Models i schemas
        - Utility funkcije
        - Business logic
        - AI prompt engineering

13.2. INTEGRATION TESTS
    ☐ TestContainers za baze
    ☐ API endpoint testovi
    ☐ Celery task testovi
    ☐ File upload/download testovi
    ☐ Authentication flow testovi

13.3. E2E TESTS
    ☐ Playwright ili Cypress
    ☐ Kritični user flow-evi:
        - Upload → Process → Review → Export
        - Quiz taking flow
        - Calendar management
        - Search functionality

13.4. PERFORMANCE TESTS
    ☐ Locust ili k6
    ☐ Scenariji:
        - 100 concurrent users
        - PDF upload 50MB
        - AI translation stress test
    ☐ Benchmarks:
        - API response < 200ms (95th percentile)
        - PDF processing < 2min
        - Page load < 3s

13.5. TEST ENVIRONMENT
    ☐ Separate test database
    ☐ Mock eksternih servisa (AI API)
    ☐ Test fixtures i factories
    ☐ CI integration (automated testing)

───────────────────────────────────────────────────────────────────────────────
FAZA 14: SECURITY IMPLEMENTATION
───────────────────────────────────────────────────────────────────────────────

14.1. AUTHENTIKACIJA I AUTORIZACIJA
    ☐ JWT tokens (HS256 ili RS256)
    ☐ Access token: 15 min
    ☐ Refresh token: 7 dana
    ☐ Password policy:
        - Min 8 karaktera
        - Mixed case
        - Numbers i symbols
        - Not in breach database
    ☐ 2FA (optional, TOTP)

14.2. INPUT VALIDATION
    ☐ Pydantic models za sve input-e
    ☐ SQL injection prevention (SQLAlchemy)
    ☐ XSS prevention (output encoding)
    ☐ File upload validacija
    ☐ Rate limiting

14.3. DATA PROTECTION
    ☐ Encryption at rest (database, files)
    ☐ Encryption in transit (TLS 1.3)
    ☐ Sensitive data masking u logovima
    ☐ API key rotation
    ☐ Secrets management (Vault ili env)

14.4. COMPLIANCE
    ☐ GDPR:
        - Privacy policy
        - Cookie consent
        - Data retention
        - Right to erasure
    ☐ Security headers:
        - HSTS
        - X-Frame-Options
        - CSP
        - X-Content-Type-Options

───────────────────────────────────────────────────────────────────────────────
FAZA 15: CI/CD I DEPLOYMENT
───────────────────────────────────────────────────────────────────────────────

15.1. VERSION CONTROL
    ☐ Git workflow: GitFlow ili GitHub Flow
    ☐ Branch protection:
        - Required PR reviews
        - Status checks (tests)
        - No direct push to main
    ☐ Semantic versioning (semver)
    ☐ Conventional commits

15.2. CI/CD PIPELINE (GitHub Actions)
    ☐ On pull request:
        - Run lint (ruff, black)
        - Run type check (mypy)
        - Run unit tests
        - Run integration tests
        - Security scan (bandit, safety)
    
    ☐ On merge to main:
        - Build Docker images
        - Push to registry
        - Deploy to staging
        - Run smoke tests
        - Deploy to production (manual approval)

15.3. DEPLOYMENT STRATEGY
    ☐ Blue-green deployment
    ☐ Database migrations:
        - Backward compatible
        - Run before app deployment
        - Rollback plan
    ☐ Feature flags za gradual rollout

15.4. ENVIRONMENT MANAGEMENT
    ☐ Environments:
        - Development (local)
        - Staging (cloud)
        - Production (cloud)
    ☐ Environment-specific config
    ☐ Secret management per environment

15.5. INFRASTRUCTURE
    ☐ Cloud provider: AWS, GCP, ili Azure
    ☐ Alternativa: Self-hosted (Hetzner, DigitalOcean)
    ☐ Container orchestration: Docker Swarm ili Kubernetes
    ☐ Load balancer: Nginx ili AWS ALB
    ☐ CDN: CloudFront ili CloudFlare

================================================================================
SEKCIJA 3: DETALJAN DATABASE SCHEMA
================================================================================

```sql
-- ========================================
-- CORE TABLES
-- ========================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    timezone VARCHAR(50) DEFAULT 'Europe/Belgrade',
    language VARCHAR(10) DEFAULT 'sr',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- FILE MANAGEMENT
-- ========================================

CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    status VARCHAR(50) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'error', 'deleted')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- ========================================
-- DOCUMENT PROCESSING
-- ========================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    total_pages INTEGER,
    total_chunks INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'translating', 'completed', 'error')),
    source_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) DEFAULT 'sr',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    translated_content TEXT,
    token_count INTEGER,
    heading_level INTEGER DEFAULT 0,
    parent_heading VARCHAR(500),
    embedding VECTOR(1536), -- Za pgvector
    is_translated BOOLEAN DEFAULT FALSE,
    is_reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, sequence_number)
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);

-- ========================================
-- QUIZ SYSTEM
-- ========================================

CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{
        "shuffle_questions": false,
        "show_correct_immediately": true,
        "time_limit_minutes": null,
        "passing_score": 70
    }',
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice' CHECK (question_type IN ('multiple_choice', 'checkbox', 'true_false')),
    options JSONB NOT NULL,
    correct_answers JSONB NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    points INTEGER DEFAULT 1,
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    score INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    percentage DECIMAL(5,2),
    time_spent_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    selected_options JSONB NOT NULL,
    is_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    time_spent_seconds INTEGER,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- STUDY SCHEDULE & SPACED REPETITION
-- ========================================

CREATE TABLE study_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    quiz_id UUID REFERENCES quizzes(id) ON DELETE SET NULL,
    next_review_date DATE NOT NULL,
    interval_days INTEGER DEFAULT 1,
    ease_factor DECIMAL(3,2) DEFAULT 2.5,
    repetition_count INTEGER DEFAULT 0,
    last_quality INTEGER CHECK (last_quality >= 0 AND last_quality <= 5),
    streak_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES study_schedules(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    completed_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'skipped', 'overdue')),
    performance_score INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- GLOSSARY & TRANSLATION MEMORY
-- ========================================

CREATE TABLE glossaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    source_term VARCHAR(500) NOT NULL,
    target_term VARCHAR(500) NOT NULL,
    context TEXT,
    is_global BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- ACTIVITY LOG & AUDIT
-- ========================================

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_user ON activity_logs(user_id, created_at DESC);
CREATE INDEX idx_activity_logs_action ON activity_logs(action, created_at DESC);

-- ========================================
-- VECTOR SEARCH (pgvector)
-- ========================================

-- Instalirati ekstenziju: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_doc_embeddings ON document_embeddings USING ivfflat (embedding vector_cosine_ops);
```

================================================================================
SEKCIJA 4: API ENDPOINT SPECIFIKACIJA
================================================================================

Format: `METHOD /api/v1/path`

───────────────────────────────────────────────────────────────────────────────
AUTHENTICATION
───────────────────────────────────────────────────────────────────────────────
POST   /auth/register              # Registracija novog korisnika
POST   /auth/login                 # Login, vraca JWT token
POST   /auth/logout                # Logout, invalidira token
POST   /auth/refresh               # Refresh access tokena
POST   /auth/forgot-password       # Zahtev za reset lozinke
POST   /auth/reset-password        # Reset lozinke sa tokenom
POST   /auth/verify-email          # Verifikacija email-a

───────────────────────────────────────────────────────────────────────────────
USERS
───────────────────────────────────────────────────────────────────────────────
GET    /users/me                   # Trenutni korisnik
PUT    /users/me                   # Update profila
PUT    /users/me/password          # Promena lozinke
DELETE /users/me                   # Brisanje naloga
GET    /users/me/stats             # Statistika korisnika

───────────────────────────────────────────────────────────────────────────────
FILES
───────────────────────────────────────────────────────────────────────────────
POST   /files                      # Upload fajla
GET    /files                      # Lista fajlova (paginated)
GET    /files/{id}                 # Detalji fajla
DELETE /files/{id}                 # Brisanje fajla
GET    /files/{id}/download        # Download fajla
GET    /files/{id}/status          # Status procesiranja
POST   /files/{id}/process         # Pokreni obradu

───────────────────────────────────────────────────────────────────────────────
DOCUMENTS
───────────────────────────────────────────────────────────────────────────────
GET    /documents                  # Lista dokumenata
GET    /documents/{id}             # Detalji dokumenta
PUT    /documents/{id}             # Update dokumenta
DELETE /documents/{id}             # Brisanje dokumenta
GET    /documents/{id}/chunks      # Lista chunk-ova
PUT    /documents/{id}/chunks/{cid}# Update chunk-a (prevod)
POST   /documents/{id}/translate   # Pokreni prevod
GET    /documents/{id}/progress    # Progres prevoda
POST   /documents/{id}/export      # Eksportuj PDF

───────────────────────────────────────────────────────────────────────────────
QUIZZES
───────────────────────────────────────────────────────────────────────────────
GET    /quizzes                    # Lista kvizova
POST   /quizzes                    # Kreiraj kviz
GET    /quizzes/{id}               # Detalji kviza
PUT    /quizzes/{id}               # Update kviza
DELETE /quizzes/{id}               # Brisanje kviza
POST   /quizzes/{id}/generate      # AI generisanje pitanja
POST   /quizzes/{id}/attempts      # Počni kviz
GET    /quizzes/{id}/attempts      # Lista pokušaja
POST   /quizzes/{id}/submit        # Predaj odgovore
GET    /quizzes/{id}/results       # Rezultati

───────────────────────────────────────────────────────────────────────────────
STUDY SCHEDULE & CALENDAR
───────────────────────────────────────────────────────────────────────────────
GET    /calendar/events            # Događaji za kalendar
POST   /calendar/events            # Kreiraj događaj
PUT    /calendar/events/{id}       # Update događaja
DELETE /calendar/events/{id}       # Obriši događaj
POST   /calendar/events/{id}/complete # Označi kao završeno
GET    /study-schedule             # Raspored učenja
POST   /study-schedule             # Kreiraj raspored
PUT    /study-schedule/{id}        # Update rasporeda
POST   /study-schedule/{id}/review # Oceni sesiju (SM-2)

───────────────────────────────────────────────────────────────────────────────
ANALYTICS
───────────────────────────────────────────────────────────────────────────────
GET    /analytics/overview         # Pregled statistike
GET    /analytics/activity         # Aktivnost za heatmap
GET    /analytics/progress         # Progres po dokumentima
GET    /analytics/mastery          # Nivoi znanja
GET    /analytics/export           # Eksport podataka

───────────────────────────────────────────────────────────────────────────────
SEARCH
───────────────────────────────────────────────────────────────────────────────
POST   /search                     # Semantička pretraga
GET    /search/suggestions         # Autocomplete
GET    /glossary                   # Rečnik termina
POST   /glossary                   # Dodaj termin

───────────────────────────────────────────────────────────────────────────────
ADMIN (samo za admin role)
───────────────────────────────────────────────────────────────────────────────
GET    /admin/users                # Lista korisnika
GET    /admin/users/{id}           # Detalji korisnika
PUT    /admin/users/{id}           # Update korisnika
DELETE /admin/users/{id}           # Brisanje korisnika
GET    /admin/stats                # Sistemska statistika
GET    /admin/logs                 # Sistemski logovi
POST   /admin/backup               # Pokreni backup

================================================================================
SEKCIJA 5: CHECKLIST ZA IMPLEMENTACIJU
================================================================================

Faza 0: Setup ☐
  ☐ Kreirati projektnu strukturu
  ☐ Postaviti Docker Compose
  ☐ Konfigurisati PostgreSQL
  ☐ Postaviti Redis
  ☐ Konfigurisati MinIO
  ☐ Kreirati .env fajlove

Faza 1: Autentikacija ☐
  ☐ Implementirati User model
  ☐ JWT autentikacija
  ☐ Register/Login endpoint-i
  ☐ Password reset
  ☐ Email verification

Faza 2: File Management ☐
  ☐ File upload endpoint
  ☐ File validation
  ☐ Storage integration
  ☐ Metadata tracking

Faza 3: PDF Processing ☐
  ☐ PyMuPDF integracija
  ☐ OCR support
  ☐ Chunking algoritam
  ☐ Celery tasks
  ☐ Progress tracking

Faza 4: AI Translation ☐
  ☐ Ollama setup
  ☐ OpenAI fallback
  ☐ Prompt engineering
  ☐ Async processing
  ☐ Caching layer

Faza 5: Human Review ☐
  ☐ Review interface
  ☐ Inline editing
  ☐ Versioning
  ☐ Approval workflow

Faza 6: PDF Generator ☐
  ☐ ReportLab setup
  ☐ Serbian fonts
  ☐ Layout templates
  ☐ Export functionality

Faza 7: Quiz System ☐
  ☐ Database schema
  ☐ Quiz interface
  ☐ Question types
  ☐ Scoring system
  ☐ Results tracking

Faza 8: Spaced Repetition ☐
  ☐ SM-2 algoritam
  ☐ Calendar integration
  ☐ Notifications
  ☐ Scheduling logic

Faza 9: Analytics ☐
  ☐ Metrics calculation
  ☐ Heatmap vizualizacija
  ☐ Charts
  ☐ Dashboard

Faza 10: Semantic Search ☐
  ☐ pgvector setup
  ☐ Embeddings generation
  ☐ Search endpoint
  ☐ Hybrid search

Faza 11: Backup ☐
  ☐ Automated backups
  ☐ Retention policy
  ☐ Restore procedure

Faza 12: Monitoring ☐
  ☐ Structured logging
  ☐ Prometheus metrics
  ☐ Grafana dashboards
  ☐ Alerting

Faza 13: Testing ☐
  ☐ Unit tests (80%+ coverage)
  ☐ Integration tests
  ☐ E2E tests
  ☐ Performance tests

Faza 14: Security ☐
  ☐ Input validation
  ☐ Rate limiting
  ☐ Security headers
  ☐ GDPR compliance

Faza 15: CI/CD ☐
  ☐ GitHub Actions
  ☐ Docker builds
  ☐ Automated testing
  ☐ Deployment pipeline

================================================================================
SEKCIJA 6: TEHNOLOGIJE I BIBLIOTEKE
================================================================================

Backend:
  - Python 3.11+
  - FastAPI (web framework)
  - SQLAlchemy (ORM)
  - Alembic (migrations)
  - Pydantic (validation)
  - Celery (task queue)
  - Redis (cache & broker)
  - PostgreSQL 15+ (database)
  - pgvector (vector search)
  - PyMuPDF (PDF processing)
  - ReportLab (PDF generation)
  - Passlib (password hashing)
  - PyJWT (authentication)
  - Python-multipart (file upload)
  - Boto3 (S3/MinIO)
  - Ollama / OpenAI (AI)
  - Pytest (testing)
  - Prometheous Client (metrics)

Frontend:
  - React 18+ / Vue 3
  - TypeScript
  - Tailwind CSS
  - FullCalendar.io
  - Chart.js / D3.js
  - React Query / SWR
  - Axios (HTTP client)
  - PDF.js (PDF preview)
  - React Hook Form

DevOps:
  - Docker & Docker Compose
  - GitHub Actions
  - Nginx (reverse proxy)
  - Prometheus (monitoring)
  - Grafana (visualization)
  - MinIO (object storage)

AI/ML:
  - Ollama (local LLM)
  - LangChain (LLM framework)
  - Sentence-Transformers (embeddings)
  - Tesseract (OCR)

================================================================================
SEKCIJA 7: PROJEKTNI TIMELINE
================================================================================

NEDELJA 1-2: Foundation
  - Faza 0, 1, 2
  - Docker setup
  - Auth system
  - File upload

NEDELJA 3-4: Core Processing
  - Faza 3
  - PDF parsing
  - Chunking
  - Database models

NEDELJA 5-6: AI Integration
  - Faza 4
  - Translation engine
  - Quiz generation

NEDELJA 7-8: User Interface
  - Faza 5, 6, 7
  - Review system
  - PDF export
  - Quiz interface

NEDELJA 9-10: Advanced Features
  - Faza 8, 9, 10
  - Calendar
  - Analytics
  - Search

NEDELJA 11: Quality & Security
  - Faza 11, 12, 13, 14
  - Testing
  - Security audit
  - Documentation

NEDELJA 12: Deployment
  - Faza 15
  - CI/CD
  - Production deployment
  - Monitoring setup

================================================================================
KRAJ DOKUMENTA
================================================================================
