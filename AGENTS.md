# AGENTS.md - AI Learning Sistem

## Dostupni Skill-ovi

Koristi `/skill` komandu za učitavanje specifičnih skill-ova:

| Skill | Komanda | Opis |
|-------|---------|------|
| ai-learning-dev | `/skill ai-learning-dev` | Opšti razvoj, backend, frontend |
| ai-learning-db | `/skill ai-learning-db` | Database, migracije, backup |
| ai-learning-mcp | `/skill ai-learning-mcp` | MCP Server, tool-ovi |
| ai-learning-docker | `/skill ai-learning-docker` | Docker, container-i, logovi |
| ai-learning-debug | `/skill ai-learning-debug` | Troubleshooting, health check |
| ai-learning-test | `/skill ai-learning-test` | Testiranje - backend, API, E2E |

## Projekat Struktura

```
/home/dju/mojAiProjekat/New folder/
├── backend/          # FastAPI + SQLAlchemy
├── frontend/         # TypeScript + Vite
├── mcp-server/      # MCP Server
├── docker/           # Docker konfiguracija
├── scripts/         # Pomocne skripte
└── .opencode/       # OpenCode konfiguracija
```

## Česte Komande

### Development
```bash
cd /home/dju/mojAiProjekat/New\ folder
make dev          # Start development
make test         # Run tests
```

### Docker
```bash
make up           # Start all services
make down         # Stop all services
make logs         # View logs
```

### Database
```bash
alembic upgrade head           # Migracije
docker exec -it ai-learning-db psql -U ai_learning_user -d ai_learning_db
```

## Servisi

| Servis | Port | Opis |
|--------|------|------|
| Backend API | 8010 | FastAPI |
| Frontend | 8083 | Nginx |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Cache |
| MinIO | 9002 | S3 Storage |

## Kada Koristiti

- **ai-learning-dev**: Razvoj novih feature-a, API endpoint-a, modela
- **ai-learning-db**: Database promene, migracije, provera podataka
- **ai-learning-mcp**: Rad sa MCP serverom
- **ai-learning-docker**: Start/stop servisa, logovi
- **ai-learning-debug**: Nešto ne radi, health check
- **ai-learning-test**: Testiranje svih delova sistema

## Memory - Pamćenje Konteksta

Ovaj projekat koristi perzistentnu memoriju za pamćenje između sesija.

### Šta se pamti:

| Tip | Primer |
|-----|--------|
| **Odluke** | "Koristimo PostgreSQL, ne SQLite" |
| **Preference** | "Volimo crvenu temu, ne plavu" |
| **Problemi** | "MinIO connection timeout rešen sa restart docker-compose" |
| **Zaključci** | "Auth service radi bolje od JWT" |

### Kako koristiti:

```
# Kad nešto naučiš ili odlučiš:
" zapamti da koristimo alembic za migracije"

# Kad trebaš da se podsetiš:
" šta smo odlučili o auth-u prošli put?"
```

### Pamćenje preživljava:

- Nove sesije
- Restart OpenCode-a
- Context loss

### 📝 PRVA ANALIZA — 2026-04-04

**Analiza backend-a urađena:** 2026-04-04

| Rezultat | Vrednost |
|----------|----------|
| Testovi | 271 (269 ✅, 2 ❌) |
| Coverage | 53% |
| Failed testovi | 2 |

**Identifikovani problemi:**
1. ❌ `test_prompt_mentions_full_text_options` - quiz service (POPRAVLJENO)
2. ❌ `test_is_available` - Claude client (POPRAVLJENO)
3. ⚠️ Coverage ispod 60% (CI threshold)
4. ⚠️ quiz.py prevelik (3068 linija)
5. ⚠️ 70% funkcija bez dokumentacije

**Spisak zadataka po prioritetu:**

| # | Zadatak | Status | Datum |
|---|---------|--------|-------|
| 1 | Popraviti 2 failed testa | ✅ ZAVRŠENO | 2026-04-04 |
| 2 | Podići coverage na 60% | ✅ ZAVRŠENO | 2026-04-04 |
| 3 | Podeliti quiz.py na manje fajlove | ⏳ NA ČEKANJU | - |
| 4 | Dodati docstrings za funkcije | ✅ ZAVRŠENO | 2026-04-04 |
| 5 | Očistiti neiskorišćene fajlove | ⏳ NA ČEKANJU | - |

**Novi test fajlovi dodati:**
- `test_storage_service.py` - 27 testova
- `test_pdf_export_service.py` - 7 testova  
- `test_helpers.py` - 25 testova
- `test_monitoring_utils.py` - 10 testova
- `test_monitoring_functions.py` - 10 testova
- `test_monitor_quiz_images.py` - 5 testova
- `test_file_processing.py` - 14 testova

**Docstrings dodati na srpskom jeziku:**
- `rag.py`: get_embedding_model, embed_text, embed_texts, chunk_text, save_chunks_to_db, similarity_search
- `auth.py`: get_redis
- `translation.py`: make_gemini_client, make_groq_client, make_mistral_client
- `workers/tasks.py`: translate_with_fallback, get_db_session

**Finalni rezultati:**
- ✅ 386 testova prolazi (svi)
- ✅ **Coverage: 60%** - CI threshold dostignut!
- ✅ Docstrings dodati na srpskom jeziku

**Fajl sa analizom:** `Analiza_backenda_2026-04-04.md`

### Kako pristupiti zadacima:

Kad počneš novu sesiju, uvek proveri AGENTS.md za trenutni status zadataka!

### Best Practices:

1. **Konkreten** — "Koristimo Redis za cache" (ne "koristimo cache")
2. **Sa razlogom** — "JWT jer je stateless, ne sesije"
3. **Actionable** — "Kreiraj migration sa: alembic revision --autogenerate"

## Dokumentacija

Detaljno uputstvo: [OPENCODE_SKILLS_GUIDE.md](./OPENCODE_SKILLS_GUIDE.md)

---

Za više informacija o OpenCode skill-ovima: https://opencode.ai/docs/skills/
