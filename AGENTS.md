# AGENTS.md - AI Learning Sistem

## Dostupni Skill-ovi

Koristi `/skill` komandu za učitavanje specifičnih skill-ova:

### AI Learning Skill-ovi

| Skill | Komanda | Opis |
|-------|---------|------|
| ai-learning-dev | `/skill ai-learning-dev` | Opšti razvoj, backend, frontend |
| ai-learning-db | `/skill ai-learning-db` | Database, migracije, backup |
| ai-learning-mcp | `/skill ai-learning-mcp` | MCP Server, tool-ovi |
| ai-learning-docker | `/skill ai-learning-docker` | Docker, container-i, logovi |
| ai-learning-debug | `/skill ai-learning-debug` | Troubleshooting, health check |
| ai-learning-test | `/skill ai-learning-test` | Testiranje - backend, API, E2E |

### Production-Grade Engineering Skill-ovi (addyosmani/agent-skills)

Instalirano 23 engineering skill-a. **Auto-discovery** - agent sam bira skill po potrebi:

| Skill | Trigger | Opis |
|-------|---------|------|
| spec-driven-development | Nov feature/projekat | Piše PRD pre koda |
| planning-and-task-breakdown | Imaš spec | Razbija na male taskove |
| incremental-implementation | Bilo koja promena >1 fajla | Tanki vertikalni slice-ovi |
| test-driven-development | Implementacija, bug fix | Red-Green-Refactor |
| code-review-and-quality | Pre merge-a | 5-osa review |
| debugging-and-error-recovery | Test fail, build break | Reproduce → Localize → Fix |
| security-and-hardening | User input, auth, data | OWASP Top 10 |
| ci-cd-and-automation | Build/deploy pipeline | Shift Left, feature flags |
| git-workflow-and-versioning | Svaka promena | Trunk-based, atomic commits |
| interview-me | Nedovoljno informacija | Izvlači zahteve kroz pitanja |
| idea-refine | Gruba ideja | Divergent/convergent thinking |
| context-engineering | Nov session, switch task | Pravilno hranjenje agenta kontekstom |
| source-driven-development | Framework/library odluka | Ground u official docs |
| doubt-driven-development | High stakes, nepoznat kod | Adversarial review |
| frontend-ui-engineering | UI komponente | Component architecture, a11y |
| api-and-interface-design | API, module boundaries | Contract-first, Hyrum's Law |
| browser-testing-with-devtools | Browser debugging | Chrome DevTools MCP |
| code-simplification | Kod radi ali je komplexan | Chesterton's Fence, Rule of 500 |
| performance-optimization | Performance zahtevi | Core Web Vitals, profiling |
| deprecation-and-migration | Stari sistemi | Code-as-liability mindset |
| documentation-and-adrs | Arhitektonske odluke | ADR, API docs |
| shipping-and-launch | Pre deploy-a | Pre-launch checklist, staged rollout |

**Izvor:** [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (45k ⭐, MIT)  
**Repo lokacija:** `/home/dju/mojAiProjekat/agent-skills`  
**Lokacija skill-ova:** `~/.config/opencode/skills/` (symlinkovani)  
**Srpski priručnik:** `SRPSKI_PRIRUCNIK.md` (u projektu + u repo-u)  
**Ponašanje:** Agent automatski detektuje koji skill treba i učitava ga. Ne moraš ručno da biraš.

### 🔔 Podsetnik za Skill-ove (OBAVEZNO Ponašanje Agenta)

Kad god korisnik započne novi zadatak (feature, bug fix, refactor, deploy, itd.), agent:
1. **Proveri** koji skill-ovi odgovaraju zadatku
2. **Predloži** korisniku koji skill da koristi, npr: "Za ovo bi mogao da koristiš `spec-driven-development` da prvo napišemo spec."
3. **Ne kreni u implementaciju** dok korisnik ne potvrdi ili ne odabere drugi skill

Primeri:
- "Treba mi novi API" → "Predlažem `api-and-interface-design` za contract-first dizajn, pa `incremental-implementation` za implementaciju."
- "Ispravi mi ovaj bug" → "Predlažem `debugging-and-error-recovery` da sistematski nađemo root cause."
- "Hoću da deployujem" → "Predlažem `shipping-and-launch` za pre-deploy checklistu."

Cilj: korisnik **ne mora da pamti** 23 skill-a — agent ga podseća.

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

# PDF quality (kad god se menja pdf_export_service)
git diff --name-only | grep -q "pdf_export_service" && \
  docker exec ai-learning-app python /app/scripts/verify_pdf_quality.py c2750999-61b1-4bf4-a526-4731b8dcd57a

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
| 6 | **L0/L1/L2 tiered loading** — hijerarhijsko grupisanje chunkova + SectionSummary model + tiered RAG | ⏳ NA ČEKANJU | - |
| 7 | **Scrapling integracija** — web scraping za Knowledge base (dodavanje web resursa uz auto anti-bypass) | ⏳ NA ČEKANJU | - |
| 8 | **Refaktor RAG provajdera** — automatski rate limit, +4 provajdera (Cerebras, SambaNova, Cloudflare, GitHub Models), provere kroz sve provajdere | ⏳ NA ČEKANJU | - |
| 9 | **WeLib integracija** — pretraga i download PDF-ova sa welib.st direktno u Knowledge Base | ⏳ NA ČEKANJU | - |

### 📋 Scrapling — Web Scraping za Knowledge Base (2026-05-23)

**Link:** https://github.com/D4Vinci/Scrapling

**Šta je:** Adaptive web scraping framework za Python. Auto-escalation: GET → Fetch → Stealthy fetch (Cloudflare bypass). Ima CLI + Spider framework.

**Svrha u našem sistemu:** Dodavanje web resursa u Knowledge base bez ručnog mučenja sa anti-bot zaštitom.

**Docker:** `pyd4vinci/scrapling` ili `ghcr.io/d4vinci/scrapling:latest`

**Instalacija:** `pip install "scrapling[all]>=0.4.2"` + `scrapling install --force`

**Status:** Čeka na implementaciju

### 📋 AgentScope Framework — Referenca (2026-05-23)

**Link:** https://github.com/agentscope-ai/agentscope

**Šta je:** Agent framework od Alibaba Group (25.5k ⭐, Apache 2.0). Production-ready, built-in ReAct agent, MCP/A2A podrška, memory compression, Agentic RL.

**Zanimljivo za naš sistem:**
- **Memory compression** — referenca za L0/L1 implementaciju
- **Anthropic Agent Skill** — isti pattern kao naši FileSkills
- **MCP integracija** — `HttpStatelessClient` za MCP toolove
- **Long-term memory (ReMe)** — primer organizacije memorije

**Razlika od OpenViking:** AgentScope je agent framework (orchestration, multi-agent), OpenViking je context database (memory, retrieval). Oba su relevantna iz različitih uglova.

### 📋 RAGFlow — RAG Engine (2026-05-23)

**Link:** https://github.com/infiniflow/ragflow (81.1k ⭐, Apache 2.0)

**Šta je:** Open-source RAG engine sa vision-based Deep Document Understanding (DeepDoc). InfiniFlow-ov proizvod. v0.25.5, aktivan (commit pre 2 dana).

**Šta je jedinstveno:**
- **DeepDoc** — vision-based document processing (OCR + layout recognition + table structure). Tretira dokument kao sliku, ne kao tekst. Daleko naprednije od naivnog PyMuPDF/pdfplumber pristupa.
- **Template-based chunking** — layout-aware, korisnik vidi chunkove i može ručno da interveniše
- **Multi-recall + fused reranking** — više strategija pretrage + cross-encoder reranking
- **OpenAI-kompatibilan API** — `/openai/{chat_id}/chat/completions`, drop-in zamena
- **Agentic RAG** — MCP, code executor (gVisor), agent memory
- **Infinity** — njihov custom vector DB (opcija umesto ES)

**Tehnologije:** Python, React/Vite, MySQL + Elasticsearch/Infinity + Redis + MinIO. Docker Compose.

**Šta možemo da uzmemo za naš sistem:**
- DeepDoc pristup za bolje PDF procesiranje (layout-aware chunking)
- OpenAI-kompatibilan API pattern za `/chat` endpoint
- Multi-recall + reranking za poboljšanje RAG query-ja
- Agentic RAG koncept za MCP integraciju

**Zašto ne koristimo direktno:** Težak (4 CPU, 16GB RAM minimum). Naš sistem je lakši i fleksibilniji za custom edukativne feature-e (quiz, translation, itd.).

**Status:** Razmatra se kao referenca za unapređenje RAG sistema

### 📋 WeLib — Besplatni PDF-ovi za Knowledge Base (2026-05-23)

**Link:** https://welib.st/

**Šta je:** Mirror Anna's Archive-a — 43M knjiga, 98M radova, sve besplatno PDF/epub. Server-rendered sajt (nema API), direktni download preko `/auto_download/{md5}/0/0`. 

**Svrha u našem sistemu:** Korisnik pretražuje welib direktno iz app, bira knjigu, klikne "Import" → backend skine PDF → chunk-uje → ubaci u Knowledge Base.

**Plan implementacije:**
1. Dodati "Web Library" tab na stranicu za upload dokumenata
2. Backend endpoint: `POST /api/v1/web-sources/welib/search?q=...` (scrapuje welib, vraća listu)
3. Backend endpoint: `POST /api/v1/web-sources/welib/import/{md5}` (skida PDF, procesira, čuva)
4. Frontend: search field + results grid + "Import" dugme
5. Isti flow kao upload-ovani PDF (MinIO → chunking → baza)

**Tehnički izazovi:**
- Nema API — potreban scraping (BeautifulSoup/Scrapling)
- Rate limiting — welib može da blokira česte zahteve
- Pravni aspekt — piracy site, autorska prava

**Status:** Čeka na implementaciju

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

## 📝 POSLEDNJI UPDATE — 2026-05-26

**PDF bookmark fix + verification:** 2026-05-26

### Problem (3 bugs)
1. **`bm_title[:60]` truncation** — heading tekst skracen na 60 karaktera, sto je seklo reci napola. Skraceni tekst se nalazio u TOC-u (gde je takodje skracen) ali NE u glavnom sadrzaju (gde je pun heading renderovan).
2. **`\n` nije uklonjen** — `text.replace(" ", "").lower()` nije uklanjao `\n` karaktere, pa bookmark sa `\n` nije match-ovao page text gde je `\n` renderovan kao space.
3. **`< 5` filter suvise strog** — kratki heading-i poput "UVOD" (3 karaktera) su preskakani, ostajali na page 1.

### Fix
- `re.sub(r"\s", "", text).lower()` umesto `text.replace(" ", "").lower()` — uklanja SVE whitespace ukljucujuci `\n`
- Uklonjen `[:60]` truncation — koristi se pun bookmark title
- `< 5` → `< 3` — hvata kratke heading-e
- TOC page detection (preskoci stranice sa "SADRŽAJ")

### Verifikovano (60/60 = 100%)
```
Total pages: 138
TOC page bookmarks: 0
Content page bookmarks: 60
CORRECT: 60/60 (100%)
Max bookmark page 137 <= total pages 138
```

### Novi fajlovi
- `scripts/verify_pdf_quality.py` — permanentna skripta za PDF quality check

### Proces improvement
**Kad god se menja `pdf_export_service.py`, obavezno pokrenuti:**
```bash
docker exec ai-learning-app python /app/scripts/verify_pdf_quality.py c2750999-61b1-4bf4-a526-4731b8dcd57a
```
Preporuceno: dodato u KONTROLNA LISTA pre commit-a.

## 📝 POSLEDNJI UPDATE — 2026-05-25

**Translation pipeline fix:** 2026-05-25

### Problem
`auto_pipeline_task` u `quiz.py` import-uje `translate_document_task` ali ga **nikad ne poziva**. Samo setuje status na "translating" i nastavlja dalje. Ceo pipeline (upload dokumenta → auto pipeline) potpuno preskace prevodjenje.

### Root Cause
Linije 225-232 u `quiz.py`:
```python
if not skip_translation:
    logger.info("[PIPELINE] Korak 2: Prevod dokumenta")
    from app.workers.tasks.translation import translate_document_task  # noqa: F401
    # This would run as separate task in production
    # For now, we just set status
    document.status = "translating"
    db.commit()
```

### Fix
1. **`translation.py`** — Extractovana core translation logika u `run_document_translation(db, document_id, provider)` funkciju (bez Celery `@shared_task` dekoratora)
2. **`translate_document_task`** — Refaktorisan u thin wrapper koji poziva `run_document_translation()`
3. **`quiz.py`** — `auto_pipeline_task` sada zove `run_document_translation(db, document.id, provider=translation_provider)` umesto no-op

### Verifikovano
- ✅ `run_document_translation` import radi (`from app.workers.tasks.translation import run_document_translation`)
- ✅ `translate_document_task` registrovan u Celery-ju
- ✅ Translation task radi za dokument `c2750999` (14/207 chunks prevedeno u 64s, progress se upisuje u DB)
- ✅ `translation_progress` sadrzi `translated_chunks`, `total_chunks`, `elapsed_seconds`, `last_activity_at`

### Izmenjeni fajlovi
- `backend/app/workers/tasks/translation.py` — Dodata `run_document_translation()`, refaktorisan `translate_document_task`
- `backend/app/workers/tasks/quiz.py` — `auto_pipeline_task` sada poziva prevod

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

## 🔧 FAZA 13 - File Skills System (2026-04-19) - Anthropic Pattern

### Cilj
Omogućiti korisnicima da koriste lepo formatirane izlaze za prevod i export fajlova po Anthropic skill pattern-u.

### Reference
- [Anthropic Skills](https://github.com/anthropics/skills)
- Skills = folderi sa SKILL.md fajlovima koji sadrže instrukcije za AI

### Implementacija

**Database - FileSkill model** (`app/services/skills/models.py`):
- Novi model za file skill-ove (translate, pdf, docx, xlsx)
- `prompt_template` - skill instrukcije za AI

**Migracija** (`alembic/versions/009_file_skills.py`):
- Kreira tabelu `file_skills`
- Seed-uje 3 skills: translate, pdf, docx

**Skill prompts:**

| Skill | Opis | Prompt |
|-------|------|--------|
| translate | Lep prevod sa poglavljima | "Translate with chapters, headings, markdown..." |
| pdf | Lep PDF sa header/footer | "Add header, page numbers, proper margins..." |
| docx | Lep Word sa stilovima i TOC | "Use heading styles, add TOC, page numbers..." |

**Servis** (`app/services/skills/file_skills.py`):
- `FileSkillService.get_skill_prompt(category)` - dohvata prompt
- `FileSkillService.get_translate_prompt()` - translate prompt
- `FileSkillService.get_pdf_prompt()` - PDF prompt
- `FileSkillService.get_docx_prompt()` - DOCX prompt

### Kako radi

1. Korisnik klikne "Prevedi" → koristi se translate skill prompt
2. Korisnik klikne "Export u PDF" → koristi se pdf skill prompt + svi prevedeni chunks
3. Korisnik klikne "Export u Word" → koristi se docx skill prompt + svi prevedeni chunks

### Korišćenje

```python
from app.services.skills.file_skills import get_file_skill

# Get translate skill prompt
translate_prompt = get_file_skill().get_translate_prompt()

# Get PDF export skill prompt
pdf_prompt = get_file_skill().get_pdf_prompt()

# Get DOCX export skill prompt
docx_prompt = get_file_skill().get_docx_prompt()
```

### Napomene

- Svi korisnici automatski imaju pristup svim file skills
- Nema potrebe za enabled_skills - to je bilo pogrešno shvatanje
- Skills se koriste kao dodatni prompt context pri prevodu/exportu
- Podaci ostaju u chunks-ovima (translated_content polje)

---

## ✅ FAZA A - Layout-Aware PDF Pipeline - KOMPLETNO (2026-05-26)

### Sta je uradjeno

Dodata `layout_data` JSON kolona na `Chunk` model, popunjena prilikom PDF importa sa font/paragraph/page info, i koristi se u PDF exportu.

### Izmenjeni fajlovi

| Fajl | Promena |
|------|---------|
| `backend/app/db/models/document.py` | `layout_data = Column(JSON, nullable=True)` na Chunk |
| `backend/app/services/pdf.py` | `ChunkData.layout_data` field; `smart_chunk_with_fonts()` cuva font info; `smart_chunk()` cuva basic |
| `backend/app/workers/tasks/pdf_processing.py` | Prosledjuje `layout_data` u DB |
| `backend/app/workers/tasks/pdf_export.py` | chunk_dicts sadrze `page_number` + `layout_data` |
| `backend/app/services/pdf_export_service.py` | Nova `_extract_heading_pages()` — koristi chunk `page_number`/`layout_data` za TOC; **eliminisan two-pass** |
| `scripts/backfill_layout_data.py` | **NOVI** — backfill script za 52,896 postojecih chunks |
| `scripts/verify_pdf_quality.py` | Dodati `page_number` i `layout_data` u chunk dicts |

### DB promena

```sql
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS layout_data JSONB;
```

### Backfill rezultat

- **52,896 chunks** popunjeno (10 dokumenata)
- **100%** chunks sa `layout_data` (53,103/53,103 — samo oni sa `page_number`)
- Test dokument: 207 chunks obradjeno za ~1.5s
- Veliki dokumenti (44k chunks): backfill radi batch UPDATE-om

### Verifikacija

```
PDF kvalitet (The Art of War, 138 pages):
✅ Valid PDF (391KB)
✅ 60/60 bookmarks on content pages (100%)
✅ Bookmarks na 55/138 strana (92%)
✅ Max bookmark page 137 <= total 138
✅ Testovi: 424 passed, 5 skipped
```

### Discovery

- `page_number` je postojao na svakom chunk-u ali se **ignorisao** u exportu
- Font info se ekstrahovao ali **discard-ovao** posle chunkovanja
- Two-pass PDF generacija je bila **nepotrebna** — sad single-pass
- **Performance: ~50% brzi export** za velike dokumente

---

## ✅ FAZA B - Layout-Aware Rendering - KOMPLETNO (2026-05-27)

### Sta je uradjeno

Implementirano per-paragraph font/size/bold renderovanje iz `layout_data.paragraphs` u PDF exportu.

### Bug fix

**Uklonjeno dupliciranje heading teksta** u glavnom sadrzaju. Stari kod je renderovao `layout_paras[1:]` (extra paragrafe za heading chunk) koristeci heading tekst kao body tekst, sto je dupliciralo sadrzaj.

### Izmenjen fajl

`backend/app/services/pdf_export_service.py`:

| Promena | Sta |
|---------|-----|
| Uklonjeno renderovanje `layout_paras[1:]` za heading chunkove | heading tekst se vise ne duplicira kao body |
| Uklonjen `Dict`, `Tuple` iz typing importa | F401 fix |
| Uklonjen `fitz` import u `_add_bookmarks_with_pymupdf` | F401 fix |
| Uklonjen `current_h2` dead code | F841 fix |
| Uklonjen `skill_prompt = ""` unused variable | F841 fix |
| E203 whitespace fix | linter cleanup |

### Helper funkcije na modul nivou

| Funkcija | Opis |
|----------|------|
| `_split_paragraphs(text, expected_count)` | Razbija tekst na pasuse sa opcionim split count |
| `_split_evenly(text, n)` | Gruba podela teksta na n delova |
| `_map_font(is_bold)` | Mapira bold/regular na DejaVuSans |
| `_get_layout_paragraphs(chunk)` | Izvlaci paragraphs iz layout_data |
| `_scale_size(orig_size, ref_body)` | Skalira font velicinu sa clamp [7, 20] |

### Metode klase

| Metoda | Opis |
|--------|------|
| `_build_layout_style(para_info, base_style, ref_body)` | Kreira ParagraphStyle iz layout_data |
| `_detect_ref_body_size(chunks_list)` | Detektuje ref body velicinu iz chunkova |
| `emit_body()` | Layout-aware body renderovanje (per-paragraph font) |
| Heading rendering | Per-heading font styling za h1/h2/h3 |

### Dodati testovi (14 novih)

`backend/app/tests/unit/test_pdf_export_service.py`:

| Test | Sta testira |
|------|-------------|
| `test_get_layout_paragraphs_returns_list` | _get_layout_paragraphs vraca listu |
| `test_get_layout_paragraphs_no_layout_data` | Fallback kad nema layout_data |
| `test_get_layout_paragraphs_empty_paragraphs` | Fallback kad su paragraphs prazni |
| `test_map_font_bold` | Mapa za bold font |
| `test_map_font_regular` | Mapa za regular font |
| `test_scale_size_default_ref` | Skaliranje sa default ref |
| `test_scale_size_larger` | Skaliranje veceg fonta (clamp) |
| `test_scale_size_clamped_min` | Clamp na minimum |
| `test_split_paragraphs_empty` | Split praznog teksta |
| `test_generate_with_layout_data_body_chunk` | Body chunk sa layout_data |
| `test_generate_without_layout_data` | Fallback na default body style |
| `test_generate_heading_with_layout_data_no_duplication` | Heading ne duplicira tekst |
| `test_generate_heading_h2_with_layout_data` | H2 sa layout_data |
| `test_generate_heading_h3_with_layout_data` | H3 sa layout_data |

### Verifikacija

- ✅ **20/20 testova** (100%)
- ✅ **Flake8** clean (0 issues)
- ✅ **PDF kvalitet** (The Art of War c2750999): 60/60 bookmarks, 87 pages

### Sledece faze

| Faza | Sta | Status |
|------|-----|--------|
| C | Template abstraction | ✅ ZAVRSENO |

---

## ✅ FAZA D - Roundtrip Export Testovi - KOMPLETNO (2026-05-28)

### Sta je uradjeno

Kreiran **`test_roundtrip_export.py`** sa 18 testova koji verifikuju da export-ovani fajlovi sadrze >= 95% teksta iz originalnih chunkova.

### Roundtrip koncept

```
Chunks (sinteticki) → ExportService.generate() → Export fajl (PDF/DOCX/PPTX/XLSX)
                                                       ↓
                                               Ekstrakcija teksta
                                                       ↓
                                               Word-level match >= 95%
```

### Testovi po formatu

| Format | Testovi | Sta verifikuju |
|--------|---------|----------------|
| **PDF** | 7 | Full content (100%), short content, include_original, empty, special chars, headings preserved, dedup |
| **DOCX** | 4 | Full content (100%), include_original, empty, special chars |
| **PPTX** | 3 | Full content (100%), slide limit (100), empty |
| **XLSX** | 4 | Full content (100%), include_original, many rows (50), empty |

### Helper funkcije

| Funkcija | Opis |
|----------|------|
| `_input_words(chunks)` | Skup svih reci iz chunkova (heading + body) |
| `_compute_match_percentage(chunks, text)` | % reci koje postoje i u inputu i u outputu |
| `_extract_pdf_text(bytes)` | Ekstrakcija teksta iz PDF preko PyMuPDF |
| `_extract_docx_text(bytes)` | Ekstrakcija teksta iz DOCX preko python-docx |
| `_extract_pptx_text(bytes)` | Ekstrakcija teksta iz PPTX preko python-pptx |
| `_extract_xlsx_text(bytes)` | Ekstrakcija teksta iz XLSX preko openpyxl |

### Kljucni detalji

- **Word-level matching** — gleda da li se svaka rec iz input chunkova pojavljuje u export-ovanom fajlu. Ovo je tolerantnije od character-level matching-a, sto je ispravno jer PDF dodatno sadrzi cover, TOC, header, footer tekst.
- **Dedup handling** — export servisi deduplikuju chunkove po sadrzaju; test potvrdjuje da duplikati ne smanjuju match score.
- **Special chars** — testira Unicode (Č Ć Š Đ Ž) i XML specijalne karaktere (<, &).
- **importorskip** — svi testovi koriste `pytest.importorskip` za biblioteke koje postoje samo u Docker-u (fitz, docx, pptx, openpyxl). Na host Python-u se graceful skip-uju.

### Izmenjeni fajlovi

| Fajl | Promena |
|------|---------|
| `backend/app/tests/unit/test_roundtrip_export.py` | **NOVI** — 18 roundtrip testova |

### Verifikacija

- ✅ **18/18 roundtrip testova** (100%)
- ✅ **Flake8** clean (0 issues)
- ✅ **Svi export testovi** 59/59 (41 starih + 18 novih)
- ✅ **Full suite** 540 pass, 16 pre-existing failures (backup scripts, translation API key, auth)
- ✅ **PDF kvalitet** (The Art of War): 60/60 bookmarks, 87 pages

---

## ✅ PDF/DOCX Export - KOMPLETNO TESTIRANO (2026-05-10)

### Problem
PDF/DOCX export jeo je require-ovao translated content (`translated_content IS NOT NULL`), što je uzrokovalo greške za dokumente bez prevoda.

### Rešenje
1. **pdf_export.py** - Uklonjen `translated_content.isnot(None)` filter, koristi se `c.content` kao fallback
2. **docx_export.py** - Isti fix primenjen

### Kompletni Test Rezultati

| Test | Status | Detalji |
|------|--------|---------|
| PDF Export Task | ✅ SUCCESS | `bb4534d7-9308-43fc-a5c3-83d906351e50` |
| PDF Download | ✅ WORKING | 10.6 MB fajl generisan |
| DOCX Export Task | ✅ SUCCESS | `5d2152ee-3b1b-450a-8ca8-09421bfefa44` |
| DOCX Download | ✅ WORKING | 2.9 MB fajl generisan |

### Re-processed Dokument
- **VMware vSphere 8.0** (`8be6216f-d68e-45a9-ab5f-96a511d731db`)
- **44,202 chunks** sa ispravnim heading nivoima:
  - H1: 3,466
  - H2: 4,401
  - H3: 32,544
  - Body: 3,791

### Font-based Heading Detection
- `_detect_font_heading()` metoda u `pdf.py`
- Detektuje heading-e na osnovu font imena i veličine
- Koristi `NHaasGroteskDSPro-75Bd` (Bold) za H1, `NHaasGroteskDSPro-65Md` (Medium) za H2/H3

### Rebuilt Containers
- `docker-worker` - Rebuild sa ispravkama
- `docker-app` - Restartovan posle promena

---

## Dokumentacija

Sva dokumentacija projekta organizovana je u `docs/`:

| Putanja | Sadržaj |
|---------|---------|
| `docs/user/` | UPUTSTVO_ZA_UPOTREBU.md |
| `docs/developer/` | DEVELOPER_GUIDE.md, PRILOG_PROMPT_TEMPLATES.md |
| `docs/operations/` | CI_CD_STRATEGIJA.md, INSTALLATION_GUIDE.md |
| `docs/security/` | SECURITY.md |
| `docs/plans/` | Planovi i analize (MCP, optimizacije, implementacija) |
| `docs/reference/` | CHANGELOG.md, SRPSKI_PRIRUCNIK.md, DEPENDENCIES_STATUS.md |
| `docs/archive/` | Istorijske analize i stara dokumentacija |

Za više informacija o OpenCode skill-ovima: https://opencode.ai/docs/skills/
