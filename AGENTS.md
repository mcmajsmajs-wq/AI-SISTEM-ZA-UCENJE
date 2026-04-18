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
| Frontend | 8090 | Nginx (Web aplikacija) |
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

### 📝 Learning from mistakes

**2026-04-18: Frontend TypeScript error u CI-u**
- Problem: Push-ovao kod sa TS greškama u test fajlovima (unused imports, property type error)
- Uzrok: Nisam pokrenuo `tsc --noEmit` pre commit-a
- Rešenje: Popravljeno u commit cea3858

**KONTROLNA LISTA pre svakog commit-a:**
```bash
# Backend
flake8 app/ --max-line-length=120                    # Linting
pytest app/tests/ -v --tb=short --cov-fail-under=60   # Testovi + coverage

# Frontend
npx tsc --noEmit                                      # TypeScript
npm run build                                         # Build

# Safety
git diff --cached --name-only | grep -E "\.env|secrets"  # Provera da nije .env

# Bonus
git diff --name-only | xargs grep -l "TODO\|FIXME" 2>/dev/null || echo "Nema"
```

---

### 📝 POSLEDNJI UPDATE — 2026-04-18

**CI/CD procedura zavrsena:** 2026-04-18

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

### ⚠️ SQLAlchemy Model Pravila

**VRATNO ZAPAMTI - ČESTE GREŠKE:**

| Greška | Uzrok | Rešenje |
|--------|-------|---------|
| `'Chunk' object has no attribute 'get'` | Tretiranje SQLAlchemy objekata kao dict | Koristi `chunk.content` umesto `chunk.get("text")` |
| `used_for_quiz = True` | Integer kolona umesto Boolean | Koristi `used_for_quiz = 1` |
| `char_count` invalid argument | Chunk nema taj atribut | Koristi `token_count` |
| `populate_quiz_questions` not found | Pogrešno ime metode | Koristi `generate_quiz_questions` |
| `total_questions` = 0 | Polje nije ažurirano | Ažuriraj `quiz.total_questions = len(questions)` |
| User.skills relationship error | Skill model nije uvezen | Dodaj import u `models/__init__.py` |

**Chunk Model Atributi:**
- `content` (ne `text`)
- `used_for_quiz` = Integer (0/1, ne True/False)
- `is_translated` = Integer (0/1)
- `is_reviewed` = Integer (0/1)

**Vidi:** `FAZA12_BUGFIXES.md` za detaljnu dokumentaciju svih ispravki.

### 🔧 FAZA 12 - Ispravljeni Bug-ovi (2026-04-12) - VERZIJA 2.0

| # | Bug | Status |
|---|-----|--------|
| 1 | OCR Dependencies | ✅ |
| 2 | `char_count` argument | ✅ |
| 3 | `populate_quiz_questions` | ✅ |
| 4 | `Chunk.get()` error | ✅ |
| 5 | User.skills relationship | ✅ |
| 6 | `total_questions` not updated | ✅ |
| 7 | `process_pdf()` signature (5 args vs 2-4) | ✅ |
| 8 | Chunks never saved to database! | ✅ |
| 9 | Quiz progress bar updates | ✅ |

**Test Quiz ID:** `71391f02-d00d-4102-a6e0-087e138713d7`

**Verifikovani Dokumenti:**
- `e0ba8f2d-0bd6-4208-a3b0-3f5000eda2a3` - vmware-vsphere-8-0 (3807 chunks) ✅
- `520838d0-a82c-45d4-bf0b-4f2fe5ff6b87` - Hemija Test Dokument 4 ✅

**CRITICAL FIX:** Chunks su se ČITALI iz PDF-a ali NIKAD čuvali u bazi! Sad rade.

### 🔧 FAZA 12.1 - Dodatni Fix-ovi (2026-04-13)

**Ispravljeni problemi:**

| # | Problem | Uzrok | Rešenje | Status |
|---|---------|-------|---------|--------|
| 1 | Backend ne startuje | `posthog` modul nije instaliran | Fix `posthog.py` sa try/except importom | ✅ |
| 2 | Login endpoint 500 error | `OAuth2PasswordRequestForm` nije kompatibilan sa Pydantic 2 | Zamenjen sa `Form()` parameter-ima | ✅ |
| 3 | Rate limiter konflikat | `slowapi` i `Request` parametri | Privremeno uklonjen rate limiter sa login endpointa | ✅ |
| 4 | Quiz pitanja na ćirilici | AI generiše ćirilicu umesto latinice | Ažuriran prompt + post-processing konverzija | ✅ |
| 5 | Analytics stranica radi | Ranije vraćala 500 | Sada radi ispravno | ✅ |
| 6 | Quiz submit radi | Ranije vraćao 500 | Sada ispravno evaluira odgovore | ✅ |

**Izmenjeni fajlovi:**
- `backend/app/core/posthog.py` - Dodat try/except za import
- `backend/app/api/endpoints/auth.py` - OAuth2PasswordRequestForm → Form() parametri, uklonjen rate limiter
- `backend/app/services/quiz/prompts/quiz_prompt.py` - Promenjen jezik na srpsku latinicnu
- `backend/app/services/quiz/service.py` - Dodat `cyrillic_to_latin()` post-processing

**Test koraci:**
```bash
# Login
curl -X POST 'http://localhost:8010/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=test@example.com&password=TestPass123!'

# Analytics
curl 'http://localhost:8010/api/v1/analytics/me/overview' \
  -H "Authorization: Bearer $TOKEN"

# Quiz submit
curl -X POST "http://localhost:8010/api/v1/quizzes/$QUIZ_ID/attempts/$ATTEMPT_ID/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"answers": [{"question_id": "...", "user_answer": "..."}]}'
```

### 🔧 FAZA 12.2 - Syntax Error & Latin Script E2E Test (2026-04-13)

**Ispravljeni problemi:**

| # | Problem | Uzrok | Rešenje | Status |
|---|---------|-------|---------|--------|
| 1 | Quiz generacija vraća 500 | Em dash (—) u quiz_prompt.py kao SyntaxError | Zamenjen sa regularnim hyphen-om (-) | ✅ |
| 2 | Quiz pitanja i dalje na ćirilici | AI model ne poštuje prompt instrukcije | Dodat post-processing: `cyrillic_to_latin()` funkcija | ✅ |
| 3 | Dokument ima error status | `process_pdf()` signature mismatch | Dokument koristi prethodno obrađene chunks | ✅ |
| 4 | Analytics `/me/quizzes` vraća 500 | `max()` sa None percentage/datetime | Dodat filter za None vrednosti i `datetime.min` | ✅ |

**E2E Test Rezultat (2026-04-13):**
- ✅ Quiz kreiran: `940c13df-05ce-421b-a212-445ee9fc9c2e`
- ✅ Quiz playing: Started attempt `ff154d10-1531-4856-8a2f-c302869e91e2`
- ✅ Quiz submit: 100% score (2/2 tačnih odgovora)
- ✅ Latin script: Sva pitanja na srpskoj latinicnoj

**Primer generisanog pitanja:**
```json
{
  "question_text": "Sta su atomi u hemiji?",
  "question_type": "multiple_choice",
  "options": [
    "Skupovi atoma povezanih hemijskim vezama",
    "Osnovne cestice koje ne mogu biti dalje podeljene",
    "Hemijska jedinjenja sa molekulskom masom",
    "Vrsta hemijske veze"
  ],
  "correct_answer": "Osnovne cestice koje ne mogu biti dalje podeljene"
}
```

**Rebuild komande nakon izmena:**
```bash
cd /home/dju/mojAiProjekat/New\ folder/docker
docker-compose build app worker
docker-compose up -d app worker
```


## Plan: Novi Translation Provideri (2026-04-17)

### Cilj
Zameniti postojeće skupe translation provajdere (OpenAI, Claude, Gemini) sa besplatnim alternativama.

### Besplatni Provideri za Prevod

| Provider | Besplatno | Link | Status |
|----------|-----------|------|--------|
| Microsoft Translator | 2M karaktera/mesečno | https://portal.azure.com/ | ⏳ Na čekanju |
| DeepL Free | 500K karaktera/mesečno | https://www.deepl.com/pro-api | ⏳ Na čekanju |
| SimplyTranslate | 100 req/day | https://simplytranslate.ai/ | ⏳ Na čekanju |

### Provideri za Quiz (ostaju)

| Provider | Cena | Status |
|----------|------|--------|
| Ollama | Besplatno (lokalno) | ✅ Radi |
| Groq | Besplatno (30 RPM) | ✅ Radi |
| DeepSeek | $0.14/M | ✅ Radi |
| Claude | $3/M | ✅ Radi |
| OpenAI | $2.50/M | ✅ Radi |

### Separacija Servisa

```
TRANSLATION SERVICE (novi)      →     QUIZ SERVICE (stari)
├── Microsoft Translator              ├── generate_quiz()
├── DeepL API                         ├── generate_questions()
├── SimplyTranslate (fallback)         ├── evaluate_answer()
└── LLM fallback (Ollama/Groq)        └── (isti provajderi)
```

### sledeći koraci
1. ⏳ Korisnik pravi Azure nalog → Translator resource → F0 tier
2. 🔄 Refaktorisati translation service
3. 🔄 Dodati nove provajdere
4. 🔄 Testirati

---

---

## Prompt Templates (2026-04-18)

### Concept
Prompt template je reusable, pre-structured format sa placeholder-ima koji se popunjavaju sa konkretnim vrednostima. To je blueprint za kreiranje AI prompt-ova.

### Zašto koristiti:
- **Konzistentnost** - svi output-i izgledaju isto
- **Efikasnost** - ne pišeš prompt od nule
- **Skalabilnost** - lako kreiraš više prompt-ova
- **Optimizacija** - improve-aš template over time

### Struktura Prompt Template-a

```
1. PERSONA
   "You are an expert technical writer..."

2. IZVORI INFORMACIJA  
   "Use these sources as truth..."

3. ZADATAK
   *Topic:* <popuni>
   *Product:* <popuni>
   *Audience:* <popuni>

4. IZLAZNI FORMAT
   "Generate content with..."

5. STRUKTURA
   [template sa section-ima]
```

### Primer: Quiz Prompt Template

```python
QUIZ_PROMPT = """
You are an expert teacher for {subject}.
Create {num_questions} quiz questions about: {topic}

Requirements:
- Clear and specific
- 4 options (1 correct)
- Difficulty: {difficulty}

Context:
{context}
"""
# Popuniš: {subject}, {topic}, {num_questions}, {difficulty}, {context}
# Dobiješ: gotov prompt za quiz
```

### Kada koristiti:
Kad trebaš da kreiraš više sličnih content-a (dokumentacija, quiz pitanja, email-ovi, itd) - definišeš template JEDNOM, pa samo menjaš promenljive.

---

## 📝 POSLEDNJI UPDATE — 2026-04-18

**CI/CD procedura zavrsena:** 2026-04-18

| Rezultat | Vrednost |
|----------|----------|
| Testovi | 443 passed, 3 skipped |
| Coverage | 63.22% (iznad 60% threshold) |
| Commit | 461a269 |
| GitHub push | ✅ Uspesno |

**Sta je urađeno:**
1. Analiziran MCP server vs MCP dokumentacija (modelcontextprotocol.io)
2. FastMCP vs low-level Server - razlike dokumentovane
3. Popravljen CI coverage threshold (50% → 60%) u ci.yml
4. Verifikovani svi testovi prolaze lokalno
5. Commit + push po CI_CD_STRATEGIJA.md proceduri

**MCP Server Status:**
- Ima 30+ tool-ova (docker, health, quiz, translate, document, skills)
- Koristi low-level Server klasu (ne FastMCP - radi ali nije optimalno)
- Svi tool-ovi imaju ispravne inputSchema i descriptions
- Response format koristi TextContent - ispravno

**Nije urađeno (nije kritično):**
- Refaktor na FastMCP - trenutni kod radi ispravno

---

## Dokumentacija

Detaljno uputstvo: [OPENCODE_SKILLS_GUIDE.md](./OPENCODE_SKILLS_GUIDE.md)

---

Za više informacija o OpenCode skill-ovima: https://opencode.ai/docs/skills/
