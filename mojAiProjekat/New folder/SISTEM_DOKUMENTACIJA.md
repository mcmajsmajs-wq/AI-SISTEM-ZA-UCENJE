# AI Learning System — Kompletna Sistemska Dokumentacija

> **Verzija**: 1.0.0 | **Ažurirano**: 2025  
> Ovaj dokument je centralni referentni vodič za sve aspekte sistema.

---

## 1. Pregled sistema

### Opis aplikacije

AI Learning System je web platforma za učenje bazirana na veštačkoj inteligenciji. Korisnici otpremaju PDF dokumente, sistem ih automatski procesira (ekstrakcija teksta, segmentacija na odeljke, opcioni prevod), a zatim AI generiše kvizove i pitanja za provjeru znanja. Platforma prati napredak korisnika, nudi personalizovane planove učenja i detaljan analitički pregled aktivnosti.

### Ključne funkcionalnosti

- 📄 Upload i procesiranje PDF dokumenata
- 🤖 AI generisanje kvizova (OpenAI / Claude / Ollama / dummy fallback)
- 🌐 Prevod dokumenata (DeepL, Google Translate, LibreTranslate, AI prevod)
- 📊 Analitika i praćenje napretka
- 🗓️ Personalizovani planovi učenja
- 🔐 JWT autentikacija sa blacklist mehanizmom

### Arhitektura

Sistem koristi **microservices** arhitekturu orchestriranu kroz Docker Compose:

```
[Browser] → [Nginx :80] → [FastAPI :8000] → [PostgreSQL :5432]
                                           → [Redis :6379]
                                           → [MinIO :9000]
                                           → [Ollama :11434]
                          [Celery Worker]  ← [Redis (broker)]
                          [Celery Beat]    ← [Redis (broker)]
[Grafana :3000] ← [Prometheus :9090] ← [FastAPI /metrics]
```

### Tehnološki stack

| Sloj | Tehnologija |
|------|-------------|
| Frontend | Vanilla JS / HTML / CSS (serviran kroz Nginx) |
| Backend API | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| Background zadaci | Celery + Redis broker |
| Baza podataka | PostgreSQL 15 |
| Keš / Broker | Redis 7 |
| Object storage | MinIO (S3 compatible) |
| AI (lokalni) | Ollama (llama3.1) |
| AI (cloud) | OpenAI (gpt-4o-mini), Anthropic Claude |
| Monitoring | Prometheus + Grafana |
| Reverse proxy | Nginx |
| Kontejnerizacija | Docker Compose |

---

## 2. Servisi i portovi

| Servis | Kontejner | Port | URL | Opis |
|--------|-----------|------|-----|------|
| Frontend (Nginx) | ai-learning-nginx | 80, 443 | http://localhost | Reverse proxy + staticke fajlove |
| Backend API (FastAPI) | ai-learning-app | 8000 | http://localhost:8000 | REST API |
| Swagger UI | — | — | http://localhost:8000/docs | Interaktivna API dokumentacija |
| ReDoc | — | — | http://localhost:8000/redoc | Alternativna API dokumentacija |
| PostgreSQL | ai-learning-db | 5432 | localhost:5432 | Relaciona baza podataka |
| Redis | ai-learning-redis | 6379 | localhost:6379 | Keš i Celery broker |
| MinIO API | ai-learning-minio | 9000 | http://localhost:9000 | S3 object storage API |
| MinIO Console | ai-learning-minio | 9001 | http://localhost:9001 | MinIO web upravljačka konzola |
| Grafana | ai-learning-grafana | 3000 | http://localhost:3000 | Monitoring dashboards |
| Prometheus | ai-learning-prometheus | 9090 | http://localhost:9090 | Metrics scraping |
| Ollama | ai-learning-ollama | 11434 | http://localhost:11434 | Lokalni LLM inference |
| Celery Worker | ai-learning-worker | — | — | Asinhroni background taskovi |
| Celery Beat | ai-learning-beat | — | — | Scheduled (cron) taskovi |

> **Napomena**: Ollama servis se pokreće samo uz `--profile ollama` flag.

---

## 3. Lozinke i pristupni podaci

Sve vrednosti se podešavaju u fajlu `docker/.env` (kopiran iz `docker/.env.example`).

| Servis | URL | Korisničko ime | Lozinka | .env varijabla |
|--------|-----|----------------|---------|----------------|
| **Grafana** | http://localhost:3000 | admin | admin | `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` |
| **MinIO Console** | http://localhost:9001 | minioadmin | minioadmin | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| **PostgreSQL** | localhost:5432 | ai_learning_user | OlPJqv9Ho4Ls1cFSKKulUiZBDtY | `POSTGRES_USER` / `POSTGRES_PASSWORD` |
| **Redis** | localhost:6379 | — | *(bez lozinke)* | — |
| **API korisnici** | http://localhost/register | *registracija* | *korisnik bira* | — |

> ⚠️ **Promjena lozinki**: Izmijeniti odgovarajuće vrednosti u `docker/.env` i restartovati servise.  
> ⚠️ **Nikad ne commitovati `.env` u git** — fajl je u `.gitignore`.

---

## 4. API Endpointi (kompletna lista)

Baza URL-a: `http://localhost:8000` (direktno) ili `http://localhost/api` (kroz Nginx)

### Autentikacija (`/api/auth`)

| Metod | Putanja | Opis |
|-------|---------|------|
| POST | `/api/auth/register` | Registracija novog korisnika |
| POST | `/api/auth/login` | Prijava (form data) — vraća JWT token |
| POST | `/api/auth/login/json` | Prijava (JSON body) |
| POST | `/api/auth/logout` | Odjava (invalidira token u Redis blacklisti) |
| POST | `/api/auth/refresh` | Osvežavanje access tokena |
| GET | `/api/auth/me` | Informacije o trenutnom korisniku |
| POST | `/api/auth/verify-email` | Verifikacija email adrese |
| POST | `/api/auth/forgot-password` | Zahtev za resetovanje lozinke |
| POST | `/api/auth/reset-password` | Resetovanje lozinke tokenom |

### Korisnici (`/api/users`)

| Metod | Putanja | Opis |
|-------|---------|------|
| GET | `/api/users/me` | Profil trenutnog korisnika |
| PUT | `/api/users/me` | Ažuriranje profila |
| PUT | `/api/users/me/password` | Promjena lozinke |
| GET | `/api/users/me/stats` | Statistike korisnika |
| DELETE | `/api/users/me` | Brisanje naloga |
| GET | `/api/users/me/ai-settings` | AI podešavanja korisnika |
| PUT | `/api/users/me/ai-settings` | Ažuriranje AI podešavanja |

### Dokumenti (`/api/documents`)

| Metod | Putanja | Opis |
|-------|---------|------|
| GET | `/api/documents/` | Lista dokumenata korisnika |
| POST | `/api/documents/` | Kreiranje unosa dokumenta |
| GET | `/api/documents/{document_id}` | Detalji dokumenta |
| DELETE | `/api/documents/{document_id}` | Brisanje dokumenta |
| POST | `/api/documents/{document_id}/process` | Pokretanje AI procesiranja |
| POST | `/api/documents/{document_id}/translate` | Prevođenje dokumenta |
| GET | `/api/documents/translation/providers` | Lista dostupnih prevodnih provajdera |
| POST | `/api/documents/{document_id}/estimate-translation` | Procjena troška prevoda |
| GET | `/api/documents/{document_id}/progress` | Status procesiranja |
| GET | `/api/documents/{document_id}/chunks` | Segmenti (odeljci) dokumenta |
| PUT | `/api/documents/{document_id}/chunks/{chunk_id}` | Ažuriranje segmenta |
| POST | `/api/documents/{document_id}/export` | Eksport dokumenta |
| POST | `/api/documents/{document_id}/pipeline` | Pokretanje kompletnog pipelinea |
| GET | `/api/documents/pipeline/providers` | Dostupni pipeline provajderi |
| GET | `/api/documents/{document_id}/export/pdf` | Eksport u PDF |

### Fajlovi (`/api/files`)

| Metod | Putanja | Opis |
|-------|---------|------|
| POST | `/api/files/upload` | Upload fajla u MinIO |
| GET | `/api/files/` | Lista fajlova korisnika |
| GET | `/api/files/{file_id}` | Detalji fajla |
| GET | `/api/files/{file_id}/download` | Preuzimanje fajla |
| DELETE | `/api/files/{file_id}` | Brisanje fajla |
| GET | `/api/files/{file_id}/status` | Status fajla |
| GET | `/api/files/{file_id}/presigned-url` | Privremeni URL za direktan pristup |

### Kvizovi (`/api/quizzes`)

| Metod | Putanja | Opis |
|-------|---------|------|
| POST | `/api/quizzes` | Kreiranje kviza (AI generisanje pitanja) |
| GET | `/api/quizzes` | Lista kvizova korisnika |
| GET | `/api/quizzes/{quiz_id}` | Detalji kviza sa pitanjima |
| DELETE | `/api/quizzes/{quiz_id}` | Brisanje kviza |
| GET | `/api/quizzes/{quiz_id}/status` | Status generisanja kviza |
| POST | `/api/quizzes/{quiz_id}/attempts` | Pokretanje novog pokušaja |
| POST | `/api/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Predaja odgovora |
| GET | `/api/quizzes/{quiz_id}/attempts` | Lista pokušaja |
| GET | `/api/quizzes/{quiz_id}/attempts/{attempt_id}/result` | Rezultati pokušaja |
| GET | `/api/quizzes/providers/list` | Dostupni AI provajderi za kvizove |
| POST | `/api/quizzes/{id}/chat` | ✅ | AI tutor chat posle potvrde odgovora |

### Analitika (`/api/analytics`)

| Metod | Putanja | Opis |
|-------|---------|------|
| GET | `/api/analytics/me/overview` | Pregled aktivnosti korisnika |
| GET | `/api/analytics/me/activity` | Dnevna/sedmična aktivnost |
| GET | `/api/analytics/me/quizzes` | Analitika kvizova |
| GET | `/api/analytics/me/documents` | Analitika dokumenata |
| GET | `/api/analytics/me/streak-history` | Istorija streak-ova |

### Plan učenja (`/api/study-plan`)

| Metod | Putanja | Opis |
|-------|---------|------|
| GET | `/api/study-plan/me` | Trenutni plan učenja |
| POST | `/api/study-plan/me` | Kreiranje plana |
| PUT | `/api/study-plan/me` | Ažuriranje plana |
| GET | `/api/study-plan/me/items` | Stavke plana |
| POST | `/api/study-plan/me/items` | Dodavanje stavke |
| PUT | `/api/study-plan/me/items/{item_id}` | Ažuriranje stavke |
| POST | `/api/study-plan/me/items/{item_id}/complete` | Označavanje stavke kao završene |
| DELETE | `/api/study-plan/me/items/{item_id}` | Brisanje stavke |
| GET | `/api/study-plan/me/progress` | Napredak u planu |

### Health / Monitoring

| Metod | Putanja | Opis |
|-------|---------|------|
| GET | `/health` | Osnovna provjera živosti |
| GET | `/ready` | Provjera da li su sve zavisnosti dostupne |
| GET | `/live` | Liveness probe (za Kubernetes/Docker) |
| GET | `/metrics` | Prometheus metrics |

### Knowledge Base (`/api/knowledge`)

| Metoda | Putanja | Autentikacija | Opis |
|--------|---------|---------------|------|
| POST | `/api/knowledge/query` | ✅ | RAG upit — AI odgovor sa citatima |
| GET | `/api/knowledge/sources` | ✅ | Lista indeksiranih izvora |
| GET | `/api/knowledge/stats` | ✅ | Statistike baze znanja |
| POST | `/api/knowledge/ingest/url` | ✅ | Indeksiraj URL (opciono rekurzivno) |
| POST | `/api/knowledge/ingest/text` | ✅ | Direktno indeksiranje teksta |
| DELETE | `/api/knowledge/sources/{id}` | ✅ | Ukloni izvor |
| POST | `/api/knowledge/reindex` | ✅ | Pokreni re-indeksiranje MD fajlova |

---

## 5. Docker Compose struktura

Compose fajl: `docker/docker-compose.yml`

### Servisi

| Servis | Image | Opis |
|--------|-------|------|
| `app` | Build iz `backend/Dockerfile` | FastAPI aplikacija |
| `db` | `postgres:15-alpine` | PostgreSQL baza podataka |
| `redis` | `redis:7-alpine` | Redis keš i message broker |
| `worker` | Build iz `backend/Dockerfile` | Celery worker (4 procesa) — queues: `pdf_processing`, `translation`, `quiz_generation`, `default` |
| `beat` | Build iz `backend/Dockerfile` | Celery Beat scheduler (cron zadaci) |
| `minio` | `minio/minio:latest` | Object storage |
| `ollama` | `ollama/ollama:latest` | Lokalni LLM (profile: ollama) |
| `nginx` | `nginx:alpine` | Reverse proxy |
| `prometheus` | `prom/prometheus:latest` | Prikupljanje metrika |
| `grafana` | `grafana/grafana:latest` | Vizualizacija metrika |

### Volumes (trajno čuvanje podataka)

| Volume | Opis |
|--------|------|
| `postgres-data` | PostgreSQL podaci |
| `redis-data` | Redis AOF persistencija |
| `minio-data` | MinIO bucket podaci |
| `ollama-data` | Preuzeti Ollama modeli |
| `app-uploads` | Upload fajlovi aplikacije |
| `prometheus-data` | Prometheus TSDB |
| `grafana-data` | Grafana dashboards i podaci |

### Volume mapeiranje (host ↔ kontejner)

| Host putanja | Kontejner putanja | Servis |
|---|---|---|
| `../logs` | `/app/logs` | app, worker, beat |
| `../backend/app` | `/app/app` | app, worker, beat (hot-reload) |
| `./nginx/nginx.conf` | `/etc/nginx/nginx.conf` | nginx |
| `../frontend/dist` | `/usr/share/nginx/html` | nginx |
| `./prometheus/prometheus.yml` | `/etc/prometheus/prometheus.yml` | prometheus |
| `./grafana/dashboards` | `/etc/grafana/provisioning/dashboards` | grafana |
| `../backups` | `/backups` | db |

### Network

Svi servisi su na mreži `ai-learning-network` (bridge, subnet `172.20.0.0/16`).

---

## 6. AI Provajderi konfiguracija

### Auto (preporučeni mod)

Sistem automatski koristi **fallback lanac**:
```
OpenAI (gpt-4o-mini) → Anthropic Claude → Ollama (llama3.1) → Dummy (testni)
```
Ako prvi provajder nije dostupan (nema API ključa, quota exceeded), prelazi na sljedeći.

### Konfiguracija po provajderu

| Provajder | .env varijabla | Model | Napomene |
|-----------|---------------|-------|----------|
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` | Cloud, plaća se po tokenima |
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude Haiku/Sonnet | Cloud, plaća se po tokenima |
| **Ollama** | `OLLAMA_HOST=http://ollama:11434` | `llama3.1` | Lokalni, besplatan, sporiji |
| **Dummy** | — | — | Samo za testiranje, vraća fiksne odgovore |

### Per-korisnik override

Svaki korisnik može izabrati preferovani AI provajder kroz:
- API: `PUT /api/users/me/ai-settings`
- (Frontend) Settings → AI Provajder tab

---

## 7. CI/CD Pipeline

> Detaljni opis u `CI_CD_STRATEGIJA.md`.

### GitHub Actions workflows

| Workflow | Fajl | Okidač | Opis |
|----------|------|--------|------|
| **CI** | `.github/workflows/ci.yml` | Push na bilo koju granu, PR | Testovi (pytest), lint (flake8), build Docker image |
| **CD** | `.github/workflows/cd.yml` | Push na `main`, tagovi `v*` | Deploy na produkciju / staging |

### Make komande

```bash
make up          # docker compose up -d (sve servise)
make down        # docker compose down
make restart     # down + up
make build       # rebuild Docker image za app servis
make logs        # praćenje logova svih servisa
make test        # pokretanje testova unutar app kontejnera
make lint        # flake8 linter
make migrate     # alembic upgrade head
make shell       # bash unutar app kontejnera
make psql        # psql unutar db kontejnera
```

---

## 8. MCP Server (GitHub Copilot integracija)

### Šta je MCP server

**MCP (Model Context Protocol)** server omogućava GitHub Copilot (i drugim AI asistentima koji podržavaju MCP) da direktno upravljaju i nadgledaju AI Learning System kroz prirodni jezik. Umjesto ručnog pokretanja docker komandi, dovoljno je reći Copilotu npr. "provjeri logove app servisa" ili "pokreni testove".

### Pokretanje MCP servera

```bash
cd mcp-server
pip install -e .
python -m ai_learning_mcp
```

Ili direktno kao stdio server (za integraciju sa Copilot CLI):
```bash
python -c "from ai_learning_mcp import main; import asyncio; asyncio.run(main())"
```

### Konfiguracija

Fajl: `mcp-server/mcp_config.json`

```json
{
  "mcpServers": {
    "ai-learning": {
      "command": "python",
      "args": ["-m", "ai_learning_mcp"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Kompletan spisak MCP Tools

#### Originalni tools (10)

| Tool | Opis |
|------|------|
| `docker_status` | Status svih Docker kontejnera |
| `docker_logs` | Logovi određenog servisa (parametri: `service`, `lines`) |
| `docker_restart` | Restart servisa (parametar: `service`) |
| `health_check` | Health check svih servisa (API, DB, Redis, MinIO, Ollama) |
| `api_docs` | OpenAPI dokumentacija — lista svih endpoinata |
| `read_config` | Čita `.env` konfiguraciju (lozinke su maskovane) |
| `project_status` | Opšti status projekta i faze implementacije |
| `dependencies_check` | Status Python zavisnosti |
| `ollama_status` | Status Ollama servisa i dostupni modeli |
| `pull_ollama_model` | Instrukcije za preuzimanje Ollama modela |

#### Novi tools (10)

| Tool | Opis | Parametri |
|------|------|-----------|
| `run_tests` | Pokretanje pytest testova unutar `ai-learning-app` | `scope` (unit/integration/all), `verbose` |
| `run_lint` | Flake8 linter na backend kodu | — |
| `api_test` | Testiranje API endpointa | `method`, `path`, `body` (opt.), `token` (opt.) |
| `celery_inspect` | Status Celery workera — aktivni taskovi, rezervisani, statistike | — |
| `error_search` | Pretraživanje grešaka u logovima svih kontejnera | `keyword` (def. "ERROR"), `lines` (def. 100) |
| `db_query` | Izvršavanje read-only SQL upita na PostgreSQL | `query` (samo SELECT/SHOW/EXPLAIN) |
| `redis_inspect` | Pregled Redis stanja — memorija, queue duljine, broj ključeva | — |
| `performance_check` | CPU/memorija po kontejneru (`docker stats`) | — |
| `minio_inspect` | Health MinIO + sadržaj bucket-a | — |
| `service_diagnosis` | Kompletna dijagnoza servisa (health + logovi + restart count) | `service` |

---

## 9. Monitoring

### Grafana

- **URL**: http://localhost:3000
- **Podaci za prijavu**: admin / admin (mijenjati u `docker/.env`)
- **Dashboards**: automatski provisioned iz `docker/grafana/dashboards/`
- **Datasource**: Prometheus (automatski konfigurisan)

### Prometheus

- **URL**: http://localhost:9090
- **Konfiguracija**: `docker/prometheus/prometheus.yml`
- **Metrike**: dostupne na `http://localhost:8000/metrics`
- **Retention**: 200 sati

### Logovi aplikacije

- Lokacija na hostu: `logs/` direktorijum (u korenu projekta)
- Logovi po servisu: `logs/app.log`, `logs/worker.log`, `logs/nginx/`
- Docker logovi: `docker compose logs -f [servis]`
- Format: JSON (strukturirani logovi)
- Rotacija: max 100MB po fajlu, max 5 fajlova

---

## 10. Razvoj i deployment

### Lokalni razvoj

```bash
# Kopirati .env
cp docker/.env.example docker/.env
# Editovati docker/.env (lozinke, API ključevi)

# Pokrenuti sve servise
cd docker
docker compose up -d

# Pratiti logove
docker compose logs -f app

# Pristup API-ju
http://localhost:8000/docs
```

### Build frontend-a

Frontend se gradi kroz Docker (Node.js nije potreban lokalno):

```bash
docker run --rm -v "$(pwd)/frontend:/app" node:20-alpine \
  sh -c "cd /app && npm ci && npm run build"
```

Rezultat se nalazi u `frontend/dist/` i automatski servira kroz Nginx.

### Rebuild backend-a

```bash
cd docker
docker compose up -d --build app
# Ili rebuild worker-a:
docker compose up -d --build worker
```

### Database migracije

```bash
# Unutar kontejnera
docker exec -it ai-learning-app alembic upgrade head

# Kreiranje nove migracije
docker exec -it ai-learning-app alembic revision --autogenerate -m "opis_promene"
```

### Korisne docker compose komande

```bash
docker compose ps                     # status svih servisa
docker compose logs -f --tail=50 app  # live logovi app servisa
docker compose exec app bash          # shell unutar app kontejnera
docker compose exec db psql -U ai_learning_user -d ai_learning_db  # psql
docker compose restart app            # restart app servisa
docker compose down -v                # brisanje svih volume-a (OPREZ!)
```

---

## 11. Troubleshooting

### WSL2 Docker networking (iptables greška)

**Simptom**: Docker kontejneri ne mogu komunicirati ili se ne mogu pokrenuti na WSL2.  
**Rješenje**:
```bash
sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
sudo service docker restart
```

### ALLOWED_EXTENSIONS parse error

**Simptom**: App se ne pokreće, greška oko parsiranja `ALLOWED_EXTENSIONS`.  
**Uzrok**: Vrijednost u `.env` nije validni JSON niz.  
**Rješenje**: Provjeriti `docker/.env`:
```env
ALLOWED_EXTENSIONS=["pdf","doc","docx","txt"]
```

### bcrypt / passlib version mismatch

**Simptom**: `AttributeError` ili `ValueError` pri hashiranju lozinki.  
**Rješenje**: Provjeriti `backend/requirements.txt` — koristiti kompatibilne verzije:
```
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
```

### Celery queue name greška

**Simptom**: Taskovi se guraju u redu ali nikad ne izvršavaju.  
**Uzrok**: Worker sluša na pogrešnom redu.  
**Rješenje**: U `docker-compose.yml` worker komanda mora uključivati `-Q default` (ili odgovarajući queue):
```
celery -A app.workers.celery_app worker -Q pdf_processing,translation,quiz_generation,default
```

### JWT Token blacklist (Redis nedostupan)

**Simptom**: Logout ne funkcioniše ili `500` greška pri odjavljivanju.  
**Uzrok**: Redis nije dostupan, blacklist ne može biti ažuriran.  
**Rješenje**: Pokrenuti Redis: `docker compose up -d redis`, provjeriti `docker compose ps redis`.

### OpenAI quota exceeded

**Simptom**: Generisanje kvizova/prevod ne radi, greška `429 Too Many Requests`.  
**Rješenje**: Sistem automatski prelazi na Ollama fallback ako je konfigurisan. Provjeriti `OLLAMA_HOST` u `.env` i da li je Ollama servis pokrenut sa modelom:
```bash
docker compose --profile ollama up -d ollama
docker exec ai-learning-ollama ollama pull llama3.1
```

### Frontend build (Node.js nije lokalno instaliran)

**Simptom**: `npm: command not found`.  
**Rješenje**: Koristiti Node.js u Dockeru:
```bash
docker run --rm -v "$(pwd)/frontend:/app" node:20-alpine sh -c "cd /app && npm ci && npm run build"
```

### Kontejner se kontinualno restartuje

**Dijagnoza**:
```bash
docker compose ps                          # provjeri status
docker compose logs --tail=50 [servis]     # provjeri greške
docker inspect ai-learning-[servis] --format "{{.RestartCount}}"
```

---

## 12. Backup i restore

### PostgreSQL backup

```bash
# Kreiranje backup-a
docker exec ai-learning-db pg_dump \
  -U ai_learning_user \
  -d ai_learning_db \
  --no-password \
  -F c \
  -f /backups/backup_$(date +%Y%m%d_%H%M%S).dump

# Restore backup-a
docker exec -i ai-learning-db pg_restore \
  -U ai_learning_user \
  -d ai_learning_db \
  --no-password \
  /backups/backup_YYYYMMDD_HHMMSS.dump
```

### MinIO backup

MinIO podaci su u Docker volume `minio-data`. Direktni backup volume-a:
```bash
docker run --rm \
  -v ai-learning-system_minio-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

### .env backup

```bash
cp docker/.env backups/.env.backup_$(date +%Y%m%d)
```

> ⚠️ Backup fajlove **nikad ne commitovati** u git repozitorijum!

---

## 13. Bezbjednost

### Tajni podaci

- ✅ `.env` fajl je u `.gitignore` — **nikad ne ide u git**
- ✅ API ključevi (OpenAI, Anthropic) su u `.env`
- ⚠️ Korisničke AI ključeve (per-user settings) sistem trenutno čuva u bazi kao **plain text** — planirati enkripciju u budućoj verziji

### Autentikacija

- JWT tokeni sa kratkim isticanjem (konfigurisati `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Blacklist invalidiranih tokena čuva se u Redis-u (`blacklist:*` ključevi)
- bcrypt hashing za lozinke

### Rate limiting

- 100 zahtjeva / 60 sekundi po IP (konfigurisano u FastAPI middleware)

### CORS

- Dozvoljeni origini konfigurisani u `docker/.env` (`ALLOWED_ORIGINS`)
- U development modu: `http://localhost`, `http://localhost:3000`, `http://localhost:8000`

### Network isolation

- Svi servisi su na internoj Docker mreži (`ai-learning-network`)
- Spolja su dostupni samo eksplicitno eksponovani portovi

### MinIO

- Bucket `ai-learning-uploads` dostupan samo kroz aplikaciju (presigned URL-ovi)
- Root kredencijali samo za administratorsku konzolu

---

## 14. Changelog

Detaljne promjene po verzijama dostupne su u:

📄 [`CHANGELOG.md`](./CHANGELOG.md)

Kratki pregled ključnih faza:
- **v0.1** — Inicijalna arhitektura, Docker Compose setup, baza podataka
- **v0.2** — FastAPI backend, autentikacija, upload fajlova
- **v0.3** — Celery taskovi, PDF procesiranje, AI integracija
- **v0.4** — Kvizovi, analitika, plan učenja
- **v0.5** — Monitoring (Prometheus + Grafana), CI/CD pipeline
- **v0.6** — MCP server integracija (20 tools), ova dokumentacija
- **v0.7** — Rekurzivni URL crawler (crawl_site_task), RAG proširenje

---

*Dokument generisan i održavan kao dio AI Learning System projekta.*  
*Za pitanja ili ispravke — ažurirati direktno ovaj fajl.*

---

## 15. Indeksiranje online dokumentacije (Rekurzivni Crawler)

### Kako indeksirati online dokumentaciju

#### Jednokratna stranica
Baza Znanja → Dodaj URL → unesi URL → klikni Dodaj

#### Cela dokumentacija (rekurzivno)
Baza Znanja → Dodaj URL → uključi "Rekurzivni crawler" → podesi dubinu i max stranica

Preporučene postavke po tipu:
| Dokumentacija | Dubina | Max stranica |
|---|---|---|
| Jedna referentna stranica | 1 | 10 |
| Tutorijal sa više poglavlja | 2 | 30 |
| Kompletan docs sajt | 2-3 | 50-100 |

#### Primeri korisnih URL-ova za indeksiranje:
- FastAPI docs: `https://fastapi.tiangolo.com/`
- Docker docs: `https://docs.docker.com/`
- React docs: `https://react.dev/learn`
- Python docs: `https://docs.python.org/3/tutorial/`

### API parametri (`POST /api/knowledge/ingest/url`)

| Parametar | Tip | Default | Opis |
|---|---|---|---|
| `url` | string | — | URL za indeksiranje |
| `name` | string | null | Naziv izvora |
| `recursive` | bool | false | Rekurzivno pratiti linkove |
| `max_depth` | int | 2 | Maksimalna dubina (1-3) |
| `max_pages` | int | 30 | Maksimalan broj stranica (1-100) |

---

## 16. RAG Knowledge Base sistem

### Arhitektura

```
Izvor podataka → Ingestion Pipeline → Embedding → pgvector baza
                                                        ↓
Korisnik pita → Embedding upita → Similarity search → Top-5 chunks → LLM → Odgovor
```

### Embedding model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`  
- **Dimenzije**: 384  
- **Rad**: potpuno offline (ne zahteva internet niti API ključ)  
- **Preuzimanje**: automatski pri prvom pozivu (~90MB)

### DB tabele

| Tabela | Opis |
|--------|------|
| `knowledge_sources` | Meta-podaci o izvoru (tip, naziv, URL, status, broj chunk-ova) |
| `knowledge_chunks` | Tekst chunk-ovi sa `vector(384)` kolonom |

### Podržani tipovi izvora

| Tip | Kako se dodaje | Automatski |
|-----|----------------|------------|
| `pdf` | PDF upload → automatski indeksiran | ✅ |
| `url` | Baza Znanja → Dodaj URL | ❌ |
| `markdown` | Celery Beat svakih 24h | ✅ |
| `log` | Planirano (index_logs_task) | ✅ |
| `manual` | API: POST /knowledge/ingest/text | ❌ |

### Celery tasks

| Task | Trigger | Učestalost |
|------|---------|------------|
| `index_document_task` | Posle PDF obrade | Automatski |
| `crawl_project_docs_task` | Beat schedule | Svakih 24h u 02:00 |
| `crawl_url_task` | API zahtev | Na zahtev |
| `crawl_site_task` | API zahtev (recursive=true) | Na zahtev |

### Chunking parametri
- Veličina chunk-a: **500 reči**
- Overlap: **50 reči**
- Top-K za pretragu: **5 chunk-ova**

### Rekurzivni crawler parametri

| Parametar | Opis | Default | Opseg |
|-----------|------|---------|-------|
| `recursive` | Pratiti linkove unutar domena | false | true/false |
| `max_depth` | Dubina praćenja linkova | 2 | 1-3 |
| `max_pages` | Maksimalan broj stranica | 30 | 1-100 |

---

## 17. Quiz Post-Answer AI Chat

Posle potvrde odgovora na kviz pitanje, korisnik može pitati AI tutora za dodatna objašnjenja.

### Flow
1. Korisnik bira odgovor → klik "Potvrdi odgovor"
2. Prikazuje se feedback panel (✅/❌ + objašnjenje)
3. **Chat sekcija se otključava** ispod feedback panela
4. Korisnik može postavljati pitanja AI-u
5. AI ima kontekst: pitanje, opcije, tačan odgovor, korisnikov odgovor, objašnjenje

### API Endpoint
`POST /api/quizzes/{quiz_id}/chat`

```json
{
  "message": "Zašto je opcija C pogrešna?",
  "question_id": "uuid",
  "user_answer": "B",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
```

### Karakteristike
- Chat je **zaključan** dok odgovor nije potvrđen
- Svako pitanje ima sopstvenu historiju razgovora
- Historija se čuva lokalno tokom trajanja kviza
- Koristi isti AI provajder kao korisnikova podešavanja
- Maksimalno 8 poruka u kontekstu (sliding window)
