# IMPLEMENTACIJA I TESTIRANJE — AI SISTEM ZA UČENJE
### Korak-po-korak vodič: od nule do pokretanja u produkciji

**Verzija:** 1.1.0-rc2 | **Ažurirano:** 2026-03-01  
**Projekat:** `/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system`

---

## Sadržaj

1. [Preduslovi](#1-preduslovi)
2. [Kloniranje i struktura projekta](#2-kloniranje-i-struktura-projekta)
3. [Konfiguracija okruženja (.env)](#3-konfiguracija-okruženja-env)
4. [Pokretanje sistema (Docker)](#4-pokretanje-sistema-docker)
5. [Inicijalizacija baze podataka](#5-inicijalizacija-baze-podataka)
6. [AI model — Ollama setup](#6-ai-model--ollama-setup)
7. [Pokretanje bez Dockera (development)](#7-pokretanje-bez-dockera-development)
8. [Testiranje backend sistema](#8-testiranje-backend-sistema)
9. [Testiranje frontend sistema](#9-testiranje-frontend-sistema)
10. [End-to-End testiranje aplikacije](#10-end-to-end-testiranje-aplikacije)
11. [Monitoring i logovi](#11-monitoring-i-logovi)
12. [Produkcijsko deployment](#12-produkcijsko-deployment)
13. [Česti problemi i rešenja](#13-česti-problemi-i-rešenja)

---

## 1. Preduslovi

### Obavezno

| Alat | Minimalna verzija | Provera |
|------|------------------|---------|
| Docker | 24.x | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.x | `git --version` |

### Opciono (za development bez Dockera)

| Alat | Verzija | Svrha |
|------|---------|-------|
| Python | 3.11 | Backend |
| Node.js | 20 LTS | Frontend |
| PostgreSQL | 15 | Baza |
| Redis | 7 | Cache/Queue |

### Hardver (preporučeno)

| Komponenta | Minimum | Preporučeno |
|-----------|---------|------------|
| RAM | 4 GB | 8 GB (za Ollama LLM) |
| Disk | 10 GB | 20 GB |
| CPU | 2 jezgra | 4+ jezgara |
| GPU (opciono) | — | NVIDIA za brži LLM |

---

## 2. Kloniranje i struktura projekta

```bash
# Projekat je već na disku:
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system"

# Ili klonirati iz repozitorijuma:
git clone <REPO_URL> ai-learning-system
cd ai-learning-system
```

### Struktura direktorijuma

```
ai-learning-system/
├── backend/                    # FastAPI Python aplikacija
│   ├── app/
│   │   ├── api/               # HTTP endpointi
│   │   │   └── endpoints/     # auth, documents, quizzes, analytics...
│   │   ├── core/              # config.py, logging
│   │   ├── db/
│   │   │   ├── models/        # SQLAlchemy modeli
│   │   │   └── migrations/    # Alembic
│   │   ├── services/          # Biznis logika
│   │   ├── workers/           # Celery taskovi
│   │   └── tests/
│   │       ├── unit/          # test_auth, test_pdf, test_storage...
│   │       └── integration/   # test_api, test_quiz, test_study_plan...
│   ├── alembic/               # Migracije
│   │   └── versions/          # 001_initial, 002_quiz, 003_study_plan
│   └── requirements.txt
│
├── frontend/                   # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── pages/             # LoginPage, DashboardPage, QuizzesPage...
│   │   ├── components/        # Layout, PipelineModal, StudyPlanTab...
│   │   ├── services/          # api.ts (axios client)
│   │   ├── stores/            # authStore (Zustand)
│   │   └── types/             # TypeScript interfejsi
│   └── package.json
│
├── docker/                     # Docker konfiguracija
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── nginx/                 # Reverse proxy config
│   ├── grafana/
│   │   ├── datasources/       # prometheus.yml
│   │   └── dashboards/        # ai_learning.json
│   └── prometheus/
│
└── .github/
    └── workflows/
        └── ci.yml             # GitHub Actions CI/CD
```

---

## 3. Konfiguracija okruženja (.env)

### Korak 1 — Kreiraj .env fajl

```bash
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system/docker"
cp .env.example .env
```

### Korak 2 — Uredi .env

Otvorite `docker/.env` u editoru i podesite sledeće:

#### 🔑 Obavezno promeniti (bezbednost)

```env
# Generisati jakim ključevima (64 hex karaktera)
SECRET_KEY=<generisati: openssl rand -hex 32>
JWT_SECRET=<generisati: openssl rand -hex 32>

# Promeniti sa default vrednosti
POSTGRES_PASSWORD=<vaša-lozinka>
MINIO_ROOT_PASSWORD=<vaša-lozinka>
```

```bash
# Brz način generisanja ključeva:
openssl rand -hex 32   # SECRET_KEY
openssl rand -hex 32   # JWT_SECRET
```

#### 🤖 AI Provajderi (opciono)

```env
# Ollama (ugrađen — ne treba ključ)
OLLAMA_HOST=http://ollama:11434

# OpenAI (opciono)
OPENAI_API_KEY=sk-...

# Anthropic Claude (opciono)
ANTHROPIC_API_KEY=sk-ant-...
```

#### 📧 Email notifikacije (opciono)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=vas-email@gmail.com
SMTP_PASSWORD=vas-app-password    # Google App Password, ne main lozinka
SMTP_TLS=true
FRONTEND_URL=http://localhost:5173
```

> **Gmail App Password:** Google Account → Security → 2FA → App Passwords → Generate

#### 🌐 Frontend URL (za password reset emailove)

```env
FRONTEND_URL=http://localhost:5173   # development
# FRONTEND_URL=https://vasdomen.com # produkcija
```

---

## 4. Pokretanje sistema (Docker)

### Brzi start (preporučeno)

```bash
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system"
bash quick-start.sh
```

### Manuelno pokretanje

```bash
cd docker/

# Pokrenuti sve servise u pozadini
docker compose up -d --build

# Pratiti logove tokom starta
docker compose logs -f
```

### Servisi koji se pokreću

| Servis | Port | Opis |
|--------|------|------|
| `app` (FastAPI) | 8000 | Backend API |
| `frontend` (Nginx) | 80 | React aplikacija |
| `db` (PostgreSQL 15) | 5432 | Baza podataka |
| `redis` (Redis 7) | 6379 | Cache + Celery broker |
| `minio` | 9000/9001 | Fajl storage |
| `worker` (Celery) | — | Async taskovi |
| `beat` (Celery Beat) | — | Periodični taskovi |
| `ollama` | 11434 | LLM inference |
| `prometheus` | 9090 | Metrics scraping |
| `grafana` | 3000 | Dashboards |

### Provera statusa servisa

```bash
# Pregled svih servisa
docker compose ps

# Health check aplikacije
curl http://localhost:8000/health

# Očekivan odgovor:
# { "status": "healthy", "environment": "development", ... }
```

### Zaustavljanje

```bash
docker compose down           # zaustavi, sačuvaj podatke
docker compose down -v        # zaustavi i obriši podatke (OPASNO!)
```

---

## 5. Inicijalizacija baze podataka

### Automatski (pri prvom pokretanju)

Aplikacija automatski kreira tabele pri startu. Provjeri:

```bash
# Pregled migracija u bazi
docker compose exec app alembic history

# Trebalo bi videti:
# 003_study_plan -> head
# 002_quiz_tables -> 003_study_plan
# 001_initial -> 002_quiz_tables
```

### Manuelno pokretanje migracija

```bash
# Pokrenuti sve migracije (ako nisu automatski)
docker compose exec app alembic upgrade head

# Provera trenutne verzije
docker compose exec app alembic current
```

### Kreiranje test korisnika (opciono)

```bash
docker compose exec app python3 -c "
from app.db.session import SessionLocal
from app.db.models.user import User
from app.services.auth import AuthService
db = SessionLocal()
u = User(email='admin@test.com', hashed_password=AuthService.get_password_hash('Admin123!'), full_name='Admin', is_active=True, is_verified=True)
db.add(u)
db.commit()
print('Kreiran: admin@test.com / Admin123!')
"
```

---

## 6. AI model — Ollama setup

Ollama je lokalni LLM inference server. Preuzimanje modela je obavezno pre korišćenja kviz generatora.

### Preuzimanje modela

```bash
# Preporučen model (4.7GB, dobar balans brzine i kvaliteta)
docker compose exec ollama ollama pull llama3.1

# Alternativno — brži ali lošiji kvalitet (2.3GB):
docker compose exec ollama ollama pull mistral

# Lakši model za sisteme sa manje RAM-a (1.6GB):
docker compose exec ollama ollama pull phi3:mini
```

### Provera dostupnih modela

```bash
docker compose exec ollama ollama list
# NAME          ID            SIZE    MODIFIED
# llama3.1:8b   ...           4.7 GB  ...
```

### Test generisanja

```bash
docker compose exec ollama ollama run llama3.1 "Napiši 3 pitanja iz istorije Srbije"
```

> ⏱️ **Vreme preuzimanja:** llama3.1 ~15-30 min (zavisi od interneta). Preuzimanje se radi jednom.

---

## 7. Pokretanje bez Dockera (development)

Za brži development loop bez rebuilda Docker image-a.

### Backend setup

```bash
cd backend/

# Kreirati virtuelno okruženje
python3.11 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Instalirati zavisnosti
pip install -r requirements.txt

# Kopirati environment varijable
cp ../docker/.env.example .env
# Urediti .env — promeniti DB/Redis hostove sa 'db' na 'localhost'
```

```env
# .env za local development (bez Docker-a)
DATABASE_URL=postgresql://ai_learning_user:lozinka@localhost:5432/ai_learning_db
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
OLLAMA_HOST=http://localhost:11434
```

```bash
# Pokrenuti aplikaciju
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Pokrenuti Celery worker (u drugom terminalu)
celery -A app.workers.celery_app worker --loglevel=info

# Pokrenuti Celery Beat (u trećem terminalu)
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend setup

```bash
cd frontend/

# Instalirati zavisnosti
npm install

# Pokrenuti development server
npm run dev
# → http://localhost:5173

# Build za produkciju
npm run build

# Preview build-a
npm run preview
```

### Vite proxy konfiguracija

`vite.config.ts` automatski proksira API pozive:
- `http://localhost:5173/api/*` → `http://localhost:8000/api/*`

Ovo znači da frontend šalje zahteve ka portu 5173, ali se preusmere na 8000.

---

## 8. Testiranje backend sistema

### Setup testnog okruženja

```bash
cd backend/

# Aktivirati venv (ako nije aktivan)
source venv/bin/activate

# Instalirati test zavisnosti (već u requirements.txt)
pip install pytest pytest-cov pytest-mock httpx
```

### Pokretanje testova

```bash
# Svi testovi
pytest app/tests/ -v

# Samo unit testovi (brži, bez DB)
pytest app/tests/unit/ -v

# Samo integration testovi
pytest app/tests/integration/ -v

# Specifičan fajl
pytest app/tests/integration/test_quiz.py -v

# Specifična klasa ili metoda
pytest app/tests/integration/test_quiz.py::TestQuizModel -v
pytest app/tests/integration/test_quiz.py::TestAnswerChecking::test_checkbox_correct_different_order -v
```

### Pokretanje sa coverage izveštajem

```bash
pytest app/tests/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  -v

# HTML izveštaj
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html   # Linux
```

### Pokretanje u Docker-u

```bash
# Testovi direktno u kontejneru
docker compose exec app pytest app/tests/ -v --tb=short

# Sa coverage
docker compose exec app pytest app/tests/ --cov=app --cov-report=term-missing -q
```

### Šta svaki test fajl testira

#### `tests/unit/test_auth.py`
```
✔ Kreiranje korisnika, hashing lozinke
✔ JWT token generisanje i verifikacija
✔ Login flow (ispravna/neispravna lozinka)
```

#### `tests/unit/test_pdf.py`
```
✔ PDF ekstrakcija teksta
✔ Chunking algoritam (podela na odlomke)
✔ Prepoznavanje naslova poglavlja
```

#### `tests/unit/test_storage.py`
```
✔ MinIO upload/download
✔ Presigned URL generisanje
✔ Brisanje fajlova
```

#### `tests/unit/test_translation.py`
```
✔ Ollama translation service
✔ Fallback na OpenAI/Claude
✔ Error handling
```

#### `tests/integration/test_api.py`
```
✔ Health check endpoint
✔ API verzija i status
```

#### `tests/integration/test_quiz.py`
```
✔ Kreiranje Quiz zapisa u bazi
✔ Status tranzicije: generating → ready → error
✔ Tipovi pitanja: multiple_choice, true_false, checkbox
✔ QuizAttempt scoring (% i prolaz/pad)
✔ Answer checking (case-insensitive, checkbox set)
✔ Dostupni AI provajderi
```

#### `tests/integration/test_study_plan.py`
```
✔ Kreiranje plana učenja
✔ Default vrednosti
✔ Study days kao lista
✔ Unique constraint (jedan plan po korisniku)
✔ StudyPlanItem: kreiranje, prioriteti, brisanje
✔ Označavanje stavke kao završene
✔ Praćenje napretka
```

#### `tests/integration/test_analytics.py`
```
✔ Streak algoritam (konsekutivni dani)
✔ Streak koji se prekida praznim danom
✔ Agregacije pokušaja (count, avg score, pass rate)
✔ Activity window filtriranje (30 dana)
✔ Grupiranje po danima
✔ Ukupan broj dokumenata
```

### Primer ispisa uspešnih testova

```
========================== test session starts ==========================
platform linux -- Python 3.11.x, pytest-7.4.3
collected 67 items

app/tests/unit/test_auth.py::TestUserCreation::test_create_user PASSED
app/tests/unit/test_auth.py::TestTokens::test_access_token PASSED
...
app/tests/integration/test_quiz.py::TestQuizModel::test_create_quiz PASSED
app/tests/integration/test_quiz.py::TestAnswerChecking::test_checkbox_correct_different_order PASSED
...
app/tests/integration/test_analytics.py::TestStreakCalculation::test_consecutive_days_streak PASSED

========================== 67 passed in 4.23s ==========================
```

---

## 9. Testiranje frontend sistema

### TypeScript typecheck

```bash
cd frontend/

# Provjera tipova bez builda
npx tsc --noEmit

# Trebalo bi biti bez grešaka
```

### Build provjera

```bash
npm run build
# Trebalo bi završiti sa: "✓ built in X.Xs"
```

### Development provjera

```bash
npm run dev
# → http://localhost:5173
```

Otvorite browser i proverite:
- [ ] Prikazuje se login stranica
- [ ] Linkovi na navigaciji rade
- [ ] Nema konzolnih grešaka (`F12 → Console`)

---

## 10. End-to-End testiranje aplikacije

Ovo je **ručni test workflow** koji pokriva sve ključne funkcije.

### Scenario A: Registracija i osnovno korišćenje

```
1. Otvori http://localhost:5173
2. Klikni "Registruj se"
3. Unesi: email, lozinka (min 8 kar), ime
4. → Treba da te prebaci na Dashboard
5. Provjeri da su vidljive stat kartice (dokumenti, kvizovi)
```

### Scenario B: Upload i obrada PDF-a

```
1. Dokumenti → "Upload dokumenta"
2. Prevuci PDF fajl (ili klikni za odabir)
3. Sačekaj status "uploaded" → "completed"
4. Otvori dokument → provjeri da su vidljivi chunks teksta
5. Klikni "Preuzmi PDF" → treba se downloadati PDF
```

### Scenario C: AI Pipeline (automatski)

```
1. Na stranici dokumenta klikni "Auto Pipeline" (ljubičasto dugme)
2. Odaberi provajdera (preporučeno: Ollama)
3. Klikni "Pokreni"
4. Prati progress bar:
   → "Obrada PDF-a..."
   → "Prevođenje..."
   → "Generisanje kviza..."
5. Po završetku: dokument predan + kviz kreiran
```

> ⏱️ Trajanje: 2-10 minuta zavisno od veličine PDF-a i brzine Ollama

### Scenario D: Ručno kreiranje kviza

```
1. Kvizovi → "+ Novi kviz"
2. Odaberi dokument koji je "completed"
3. Postavi broj pitanja: 5
4. Opciono: označi "Mešati redosled pitanja"
5. Klikni "Generiši"
6. Sačekaj status "ready" (30-60 sek)
```

### Scenario E: Igranje kviza

```
1. Kvizovi → klikni na naziv kviza sa statusom "ready"
2. Klikni "Igraj kviz"
3. Odgovori na sva pitanja
4. Klikni "Završi kviz"
5. Provjeri:
   → Prikazuje se % tačnih odgovora
   → Prikazuju se tačni odgovori sa objašnjenjima
   → Dugme "Pokušaj ponovo" radi
```

### Scenario F: Plan učenja

```
1. Podešavanja → tab "Plan učenja"
2. Postavi dnevni cilj: 2 kviza/dan
3. Odaberi dane učenja: ponedeljak-petak
4. Opciono: uključi podsetnik, postavi vreme (08:00)
5. Zakaži kviz: klikni "+ Zakaži kviz", odaberi kviz i datum
6. Provjeri da se pojavi u listi
```

### Scenario G: Analitika

```
1. Navigacija → "Analitika"
2. Provjeri:
   → Stat kartice (dokumenti, kvizovi, streak, avg score)
   → Bar chart aktivnosti za 7/14/30/60 dana
   → GitHub heatmap (zelene ćelije na dane kada si radio)
   → Tabela performansi kvizova
```

### Scenario H: Password Reset (zahteva SMTP)

```
1. Odjavi se (logout)
2. Na login stranici: "Zaboravili ste lozinku?"
3. Unesi email adresu
4. Provjeri email (i Spam)
5. Klikni link u emailu
6. Unesi novu lozinku (min 8 kar)
7. Prijavi se sa novom lozinkom
```

> ⚠️ Zahteva podešen SMTP u docker/.env

### Scenario I: API direktno testiranje (Swagger UI)

```
1. http://localhost:8000/docs
2. Klikni "Authorize" → unesi JWT token (dobijen loginom)
3. Testiraj endpointe:
   GET /api/v1/documents/           → lista dokumenata
   GET /api/v1/analytics/me/overview → analytics stats
   GET /api/v1/study-plan/me         → plan učenja
```

---

## 11. Regresioni test slučajevi (bugovi iz produkcije)

Ovi test slučajevi su uvedeni na osnovu stvarnih bugova pronađenih tokom testiranja.
Treba ih proći svaki put kada se radi deployment ili veća promena.

> **Kako pokrenuti:** Manuelno prateći korake + provera u Docker logovima  
> `docker logs ai-learning-app --tail=50 2>&1 | grep -v sqlalchemy`

---

### TC-01: Dashboard — prikaz statistika

**Bug:** Dashboard pokazuje 0 dokumenata, 0 kvizova, 0% napretka, 0 dana streak.  
**Provjera:**
```
1. Prijavi se korisnik koji ima uploadovane dokumente i odgovorene kvizove
2. Otvori Dashboard (http://localhost/)
3. ✅ Stat kartice prikazuju realne vrednosti (ne 0)
4. ✅ Prikazuje se broj dokumenata, procenat prevoda, dani niz učenje
5. ✅ Grafici aktivnosti nisu prazni
```

---

### TC-02: Upload dokumenta — dvokoračni tok

**Bug:** Nakon uploada stranica `/documents` bila prazna; naziv dokumenta nije bio vidljiv.  
**Provjera:**
```
1. Dokumenti → prevuci ili klikni za odabir PDF fajla
2. ✅ Pojavljuje se zelena zona sa imenom fajla i poljem za naslov (pre-popunjen)
3. Ispravi naslov ako treba → klikni "Dodaj dokument"
4. ✅ Prebacuje na stranicu dokumenta (ne ostaje na /documents prazno)
5. ✅ Naslov dokumenta je vidljiv na kartici i u detalju
```

---

### TC-03: Napredak obrade PDF-a — progress bar

**Bug:** Tokom obrade velikih PDF fajlova nije bilo nikakve povratne informacije o napretku.  
**Provjera:**
```
1. Upload PDF fajla (barem 5+ strana)
2. Otvori stranicu dokumenta
3. ✅ Prikazuje se progress card sa:
   - Procentom napretka (npr. "47%")
   - Animiranim progress bar-om
   - Brojem obrađenih strana (npr. "Strana 45 / 100")
   - Brojem kreiranih odlomaka
   - Proteklim vremenom (npr. "1m 23s")
4. ✅ Progress se ažurira svakih ~2s automatski
5. ✅ Kad obrada završi, progress card nestaje i vide se odlomci
```

---

### TC-04: Dokument zaglavljen u prevodu

**Bug:** Dokumenti su ostajali u statusu "translating" zauvek.  
**Provjera:**
```
1. Na listi dokumenata pronađi dokument u statusu "Prevodi se"
2. Ako prevod traje >10 minuta bez napretka:
   ✅ Treba se pojaviti dugme za ponovni pokušaj (refresh ikona)
3. U logovima: docker logs ai-learning-worker --tail=20
   ✅ Nema zapisa "translating" bez completion-a
4. DB provjera — dokument ne sme biti zaglavljen:
   docker exec ai-learning-db psql -U ai_learning_user -d ai_learning_db \
     -c "SELECT id, title, status FROM documents WHERE status='translating';"
   ✅ Lista treba biti prazna ili sa recentno pokrenutim prevodima
```

---

### TC-05: Prevod — svi AI provajderi vidljivi u modalnom

**Bug:** U modalnom za prevod nisu bili vidljivi Gemini, Groq i Mistral.  
**Provjera:**
```
1. Dokumenti → klikni dugme "Prevedi" na nekom dokumentu
2. ✅ U listi provajdera vidljivi SVI:
   - Ollama (lokalni)
   - DeepL
   - OpenAI
   - Google Translate
   - Claude
   - Gemini (free)
   - Groq (free)
   - Mistral
3. ✅ Dugme "Prevedi" aktivira se tek kad je provajder odabran
```

---

### TC-06: Pregled prevoda — sidebar i navigacija

**Bug:** Stranica pregleda prevoda prikazivala 404; sidebar nije bio vidljiv.  
**Provjera:**
```
1. Dokumenti → otvori dokument sa statusom "completed"
2. Klikni "Pregledaj prevode"
3. ✅ URL je /review/{documentId} — ne 404
4. ✅ Sidebar (navigacija) je vidljiv sa levog strane
5. ✅ Prikazuju se odlomci sa originalnim i prevedenim tekstom
6. ✅ Postoji dugme "Nazad" za povratak na listu dokumenata
```

---

### TC-07: Lista dokumenata — status prevoda vidljiv

**Bug:** Na kartici dokumenta na listi nije bilo vidljivo je li dokument preveden.  
**Provjera:**
```
1. Dokumenti → lista dokumenata
2. ✅ Kartica prevedenog dokumenta prikazuje oznaku/ikonu da je preveden
3. ✅ Odlomci koji su prevedeni prikazuju se sa prevedenim sadržajem
   u DetailPage (ne samo originalni tekst)
```

---

### TC-08: Kviz — tačan odgovor sa objašnjenjem

**Bug:** Nakon odgovaranja na pitanje prikazivalo se "undefined" umesto tačnog odgovora.  
**Provjera:**
```
1. Kvizovi → odaberi kviz sa statusom "ready" → "Igraj kviz"
2. Odgovori na pitanje i potvrdi
3. ✅ Prikazuje se ✓ Tačno ili ✗ Netačno (ne "undefined")
4. ✅ Za netačan odgovor: "Tačan odgovor: [konkretno slovo/tekst]"
5. ✅ Prikazuje se polje "Objašnjenje" sa edukativnim tekstom
   (NIJE "Ova tvrdnja je direktno navedena u tekstu.")
6. ✅ Pitanja su pretežno višestruki izbor (multiple_choice), ne samo true/false
```

---

### TC-09: Kviz — AI chat pojašnjenje

**Bug:** Chat za pojašnjenje u kvizu vraćao "Izvini, trenutno ne mogu da odgovorim."  
**Provjera:**
```
1. U toku igranja kviza, potvrdi odgovor
2. U sekciji "Pitaj AI za pojašnjenje" unesi pitanje (npr. "Zašto je ovo tačno?")
3. ✅ AI odgovara konkretnim odgovorom (ne fallback porukom)
4. ✅ Postoji selektor provajdera (Gemini / Groq / Mistral / OpenAI / Claude / Ollama)
5. ✅ Odabir provajdera menja koji AI odgovara
6. Provjeri loglove:
   docker logs ai-learning-app --tail=20 2>&1 | grep -i "chat\|gemini\|groq\|200"
   ✅ Treba da se vidi "HTTP/1.1 200 OK" za odabranog provajdera
```

---

### TC-10: Kviz rezultati — prikaz posle igranja

**Bug:** Stranica kviz rezultata nije prikazivala ništa.  
**Provjera:**
```
1. Završi kviz (odgovori na sva pitanja → "Završi kviz")
2. ✅ Prebacuje na stranicu rezultata
3. ✅ Prikazuje se % tačnih odgovora
4. ✅ Prikazuje se lista pitanja sa tačnim/netačnim odgovorima i objašnjenjima
5. ✅ Dugme "Pokušaj ponovo" radi
6. Alternativno: idi na listu kvizova → klikni "Rezultati" na kvizu
   ✅ Prikazuje se poslednji pokušaj (ne prazna stranica)
```

---

### TC-11: Baza znanja — AI selektor i odgovori

**Bug:** U bazi znanja nije bilo mogućnosti izbora AI provajdera; odgovori nisu radili.  
**Provjera:**
```
1. Navigacija → "Baza Znanja"
2. ✅ Iznad polja za pitanje vidljivi su provajder čipovi (Auto/Ollama/Gemini/Groq/…)
3. Postavi pitanje (npr. "Šta je machine learning?")
4. ✅ AI daje odgovor baziran na indeksiranim dokumentima
5. ✅ Pored odgovora prikazuje se naziv provajdera koji je odgovorio
```

---

### TC-12: URL ingest u bazi znanja

**Bug:** Ubacivanje URL-a u bazu znanja nije radilo (URL se nije razrešavao).  
**Provjera:**
```
1. Baza Znanja → tab "Dodaj izvor" → "Web URL"
2. Unesi validan URL (npr. https://en.wikipedia.org/wiki/Machine_learning)
3. Klikni "Indeksiraj"
4. ✅ Status se menja u "indexing" a zatim "indexed"
5. ✅ Postavi pitanje vezano za sadržaj URL-a → AI daje odgovor
```

---

### TC-13: AI provajder podešavanja — custom ključevi

**Bug:** Nije bila opcija za dodavanje sopstvenih API ključeva za sve provajdere.  
**Provjera:**
```
1. Podešavanja → tab "AI Provajder"
2. ✅ Vidljiva polja za API ključeve:
   - OpenAI API Key
   - Claude (Anthropic) API Key
   - Google Gemini API Key
   - Groq API Key
   - Mistral API Key
   - Custom Base URL + Custom API Key
3. Unesi Gemini API ključ → klikni "Sačuvaj"
4. Idi na kviz → pokreni AI chat
5. ✅ Chat radi sa Gemini provajderom
```

---

### TC-14: AI modeli — validacija aktuelnih verzija

**Bug:** Modeli `gemini-1.5-flash` (404) i `llama3-8b-8192` (400) bili su deprecated.  
**Provjera:**
```
1. Proveri aktuelne modele u kodu:
   grep -r "gemini\|llama\|mistral-small" backend/app/services/ backend/app/api/
   
   ✅ Gemini: "gemini-2.0-flash" (ili "gemini-1.5-flash-latest")
   ✅ Groq: "llama-3.1-8b-instant" (ili "llama3-8b-8192" kao fallback)
   ✅ Mistral: "mistral-small-latest"

2. Pokreni quiz chat sa Gemini API ključem → provjeri logove:
   docker logs ai-learning-app --tail=10 | grep -i "gemini\|200\|404"
   ✅ Treba da se vidi "200 OK" — ne 404 ili 400

3. Ako se pojavi nova greška modela (4xx), ažuriraj u:
   - backend/app/api/endpoints/quizzes.py  (linije ~610-625)
   - backend/app/services/rag.py            (linije ~278-292)
   - backend/app/services/translation.py   (make_gemini_client, make_groq_client)
   - backend/app/services/quiz.py           (_build_clients funkcija)

4. Referentni modeli (validni na 2026-03-01):
   | Provajder | Model            | Endpoint                                           |
   |-----------|------------------|----------------------------------------------------|
   | Gemini    | gemini-2.0-flash | generativelanguage.googleapis.com/v1beta/openai    |
   | Groq      | llama-3.1-8b-instant | api.groq.com/openai/v1                         |
   | Mistral   | mistral-small-latest | api.mistral.ai/v1                              |
   | OpenAI    | gpt-4o-mini      | api.openai.com/v1                                  |
   | Claude    | claude-3-haiku-20240307 | api.anthropic.com/v1/messages               |
```

---

### TC-15: PDF parser — ignorisanje sadržaja (TOC)

**Bug:** PDF parser je parsirao sadržaj (Table of Contents) umesto da ga preskače.  
**Provjera:**
```
1. Upload PDF-a koji ima stranicu sadržaja (TOC)
2. Nakon obrade, otvori dokument → pregled odlomaka
3. ✅ Odlomci NE sadrže linije oblika "Uvod ............. 5"
4. ✅ Odlomci NE sadrže linije oblika "Poglavlje 1    12"
5. ✅ Sadržaj odlomaka su pravi tekstualni pasusi, ne TOC unosi
```

---

### TC-16: Kviz generacija — raznovrsna pitanja sa objašnjenjima

**Bug:** Kada AI nije radio, kviz je generisao samo true/false pitanja bez pravih objašnjenja.  
**Provjera:**
```
1. Kreiraj kviz za dokument koji ima smisleni tekstualni sadržaj
2. Sačekaj da status postane "ready"
3. Otvori kviz
4. ✅ Pitanja su pretežno multiple_choice (ne samo true/false)
5. ✅ Svako pitanje ima konkretno objašnjenje (ne "Ova tvrdnja je direktno navedena")
6. ✅ Tačni odgovori su logični i vezani za sadržaj dokumenta
7. Provjeri koji provajder je koristio:
   docker logs ai-learning-worker --tail=20 | grep "Generisano.*pitanja"
   ✅ Treba da kaže "[gemini]" ili "[groq]" ili "[mistral]" — NE "[fallback]"
```

---

### Brza checklist za svaki deploy

```
□ TC-01  Dashboard prikazuje realne statistike
□ TC-02  Upload dokumenta — dvokoračni tok sa naslovom
□ TC-03  Progress bar tokom obrade PDF-a
□ TC-04  Nema dokumenata zaglavljenih u "translating"
□ TC-05  Svi provajderi vidljivi u modalnom za prevod
□ TC-06  Pregled prevoda — sidebar + navigacija rade
□ TC-07  Status prevoda vidljiv na listi dokumenata
□ TC-08  Kviz — tačan odgovor i objašnjenje (ne "undefined")
□ TC-09  Kviz AI chat — provajderi rade, nema fallback poruke
□ TC-10  Kviz rezultati prikazuju se posle igranja
□ TC-11  Baza znanja — AI selektor i odgovori rade
□ TC-12  URL ingest u bazi znanja radi
□ TC-13  Podešavanja — custom API ključevi se čuvaju
□ TC-14  AI modeli — aktuelne verzije (gemini-2.0-flash, llama-3.1-8b-instant)
□ TC-15  PDF TOC stranice se preskakuju tokom parsiranja
□ TC-16  Kviz generacija — raznovrsna pitanja sa stvarnim objašnjenjima
```

---



### Logovi aplikacije

```bash
# Live logovi FastAPI aplikacije
docker compose logs -f app

# Logovi Celery workera
docker compose logs -f worker

# Logovi specifičnog servisa
docker compose logs --tail=100 app

# Sve greške
docker compose logs app | grep ERROR
```

### Grafana Dashboard

1. Otvori **http://localhost:3000**
2. Login: `admin` / `admin` (promeniti pri prvom loginu!)
3. Dashboards → Browse → "AI Sistem za učenje — Overview"

**Dostupni paneli:**
- HTTP Request Rate i Error Rate
- API Latency P95
- Celery Queue Size i Active Tasks
- DB Connection Pool
- Quiz Generation Duration (p50/p95)
- Business KPIs: korisnici, kvizovi, dokumenti

### Prometheus Metrics

```bash
# Raw metrics
http://localhost:9090

# Primer upita:
# rate(http_requests_total[5m])          → zahtevi po sekundi
# celery_workers_active                  → aktivni Celery taskovi
# sqlalchemy_pool_checkedout             → DB konekcije
```

### Celery monitoring

```bash
# Aktivni taskovi
docker compose exec worker celery -A app.workers.celery_app inspect active

# Zakazani (Beat) taskovi
docker compose exec worker celery -A app.workers.celery_app inspect scheduled

# Queue statistike
docker compose exec worker celery -A app.workers.celery_app inspect stats
```

---

## 12. Produkcijsko deployment

### Izmene za produkciju

#### 1. Bezbednost

```env
# docker/.env — produkcija
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<64-char-random>
JWT_SECRET=<64-char-random>
POSTGRES_PASSWORD=<jako-duga-lozinka>
MINIO_ROOT_PASSWORD=<jako-duga-lozinka>
FRONTEND_URL=https://vasdomen.com
```

#### 2. SSL/HTTPS

```bash
# Kopirati SSL sertifikate
cp /path/to/cert.pem docker/nginx/ssl/cert.pem
cp /path/to/key.pem docker/nginx/ssl/key.pem

# Nginx config → uncomment HTTPS blok u docker/nginx/nginx.conf
```

#### 3. Docker Compose override

```bash
# Koristiti produkcijski compose file (bez exposed portova)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 4. Generisanje ključeva

```bash
# Jednom za produkciju
python3 -c "import secrets; print(secrets.token_hex(32))"
# → kopirati u SECRET_KEY i JWT_SECRET
```

### Deployment checklist

```
[ ] SECRET_KEY i JWT_SECRET promenjeni (ne default vrednosti!)
[ ] DEBUG=false
[ ] POSTGRES_PASSWORD promenjen
[ ] MINIO_ROOT_PASSWORD promenjen
[ ] FRONTEND_URL podešen na pravi domen
[ ] SSL sertifikati postavljeni
[ ] SMTP konfigurisan (ili emailovi će biti preskočeni)
[ ] Ollama model preuzet (ollama pull llama3.1)
[ ] Grafana lozinka promenjena (admin/admin → sigurna lozinka)
[ ] docker compose up -d --build
[ ] Health check: curl https://vasdomen.com/health
[ ] Testirati registraciju korisnika
```

---

## 13. Česti problemi i rešenja

### ❌ "Connection refused" na localhost:8000

```bash
# Provjeri da li su kontejneri pokrenuti
docker compose ps

# Provjeri logove za greške
docker compose logs app | tail -50

# Restart ako je potrebno
docker compose restart app
```

### ❌ Kviz ostaje na "generating" zauvek

```bash
# Provjeri da li Worker radi
docker compose ps worker
# Status treba biti: Up

# Provjeri logove workera
docker compose logs worker | grep ERROR

# Restart workera
docker compose restart worker
```

Uzrok: najčešće Ollama nije odgovorio (model nije preuzet).

```bash
# Provjeri dostupne modele
docker compose exec ollama ollama list

# Ako je lista prazna — preuzeti model
docker compose exec ollama ollama pull llama3.1
```

### ❌ Greška pri upload PDF-a

```bash
# Provjeri MinIO status
docker compose ps minio

# Provjeri storage logs
docker compose logs app | grep "minio\|storage"

# Ručno kreirati bucket ako ne postoji
docker compose exec minio mc mb /data/ai-learning-uploads
```

### ❌ pytest greška: "No module named 'app'"

```bash
# Pokrenuti iz backend/ direktorijuma
cd backend/
pytest app/tests/ -v

# Ili sa PYTHONPATH
PYTHONPATH=. pytest app/tests/ -v
```

### ❌ Alembic greška pri migraciji

```bash
# Provjeri trenutni status
docker compose exec app alembic current

# Ako su tabele stare ali migracije nisu pokrenute
docker compose exec app alembic stamp head

# Pokrenuti migracije
docker compose exec app alembic upgrade head
```

### ❌ "Rate limit exceeded" pri testiranju

API ima limite: 5/min (register), 10/min (login), 3/min (forgot-password).

Za testiranje resetovati limitere:
```bash
# Restart backend servisa (briše in-memory limitere)
docker compose restart app
```

### ❌ Email se ne šalje

```bash
# Provjeri SMTP konfiguraciju
grep SMTP docker/.env

# Provjeri da su svi parametri postavljeni:
# SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

# Test slanje
docker compose exec app python3 -c "
from app.services.email_service import email_service
print('SMTP konfigurisan:', email_service.is_configured())
result = email_service.send_welcome('test@example.com', 'Test User')
print('Email poslat:', result)
"
```

### ❌ Frontend pokazuje praznu stranicu ili 404

```bash
# Provjeri da li Nginx radi
docker compose ps frontend

# Provjeri konzolu browsera (F12)
# Čest uzrok: API URL mismatch

# Provjeri vite.config.ts proxy setup
grep -A5 "proxy" frontend/vite.config.ts
```

---

## Dodatak A: Korisne komande

```bash
# ── Docker ──────────────────────────────────────────────────────────
docker compose ps                          # status svih servisa
docker compose logs -f app worker          # live logovi
docker compose restart worker              # restart Celery
docker compose exec app bash               # shell u kontejneru

# ── Baza podataka ───────────────────────────────────────────────────
docker compose exec db psql -U ai_learning_user -d ai_learning_db
\dt                                        # lista tabela
SELECT count(*) FROM users;               # broj korisnika
SELECT id, title, status FROM quizzes;    # kvizovi

# ── Alembic ─────────────────────────────────────────────────────────
docker compose exec app alembic history    # sve migracije
docker compose exec app alembic current    # aktivna verzija
docker compose exec app alembic upgrade head  # pokreni sve

# ── Celery ──────────────────────────────────────────────────────────
docker compose exec worker celery inspect active
docker compose exec worker celery inspect scheduled
docker compose exec worker celery purge   # obriši sve taskove (pažnja!)

# ── Testovi ─────────────────────────────────────────────────────────
cd backend && pytest app/tests/ -v --tb=short
pytest app/tests/integration/test_quiz.py -v -k "test_create"
pytest app/tests/ --cov=app --cov-report=term-missing -q

# ── Ollama ──────────────────────────────────────────────────────────
docker compose exec ollama ollama list     # modeli
docker compose exec ollama ollama pull llama3.1  # preuzeti
docker compose exec ollama ollama run llama3.1"hello"  # test
```

---

## Dodatak B: URL mapa

| URL | Opis |
|-----|------|
| `http://localhost:5173` | React aplikacija (dev) |
| `http://localhost:80` | React aplikacija (Docker/Nginx) |
| `http://localhost:8000/docs` | Swagger UI — API dokumentacija |
| `http://localhost:8000/redoc` | ReDoc — API dokumentacija |
| `http://localhost:8000/health` | Health check |
| `http://localhost:9001` | MinIO Console (admin UI) |
| `http://localhost:3000` | Grafana (admin/admin) |
| `http://localhost:9090` | Prometheus |
| `http://localhost:11434` | Ollama API |

---

## Dodatak C: Puna lista API endpointa

### Auth
```
POST /api/v1/auth/register           Registracija
POST /api/v1/auth/login              Prijava (form)
POST /api/v1/auth/login-json         Prijava (JSON)
POST /api/v1/auth/refresh            Refresh tokena
GET  /api/v1/auth/me                 Moji podaci
POST /api/v1/auth/forgot-password    Zahtev za reset
POST /api/v1/auth/reset-password     Reset lozinke
```

### Dokumenti
```
GET  /api/v1/documents/              Lista dokumenata
POST /api/v1/documents/upload        Upload PDF
GET  /api/v1/documents/{id}          Detalji dokumenta
GET  /api/v1/documents/{id}/chunks   Chunks teksta
POST /api/v1/documents/{id}/process  Pokrenuti obradu
POST /api/v1/documents/{id}/translate  Pokrenuti prevod
GET  /api/v1/documents/{id}/export/pdf  Preuzeti PDF
POST /api/v1/documents/{id}/pipeline   Auto pipeline
DELETE /api/v1/documents/{id}        Brisanje
```

### Kvizovi
```
POST /api/v1/quizzes/                Kreirati kviz
GET  /api/v1/quizzes/                Lista kvizova
GET  /api/v1/quizzes/{id}            Kviz sa pitanjima
DELETE /api/v1/quizzes/{id}          Brisanje kviza
GET  /api/v1/quizzes/providers       AI provajderi
POST /api/v1/quizzes/{id}/attempts   Pokrenuti pokušaj
POST /api/v1/quizzes/{id}/attempts/{aid}/submit  Submitovati
GET  /api/v1/quizzes/{id}/results    Rezultati
```

### Plan učenja
```
GET  /api/v1/study-plan/me           Moj plan
PUT  /api/v1/study-plan/me           Ažurirati plan
POST /api/v1/study-plan/me/items     Dodati kviz
POST /api/v1/study-plan/items/{id}/complete  Označiti završenim
DELETE /api/v1/study-plan/items/{id}  Obrisati stavku
GET  /api/v1/study-plan/me/progress  Napredak danas
```

### Analitika
```
GET  /api/v1/analytics/me/overview      Ukupni stats
GET  /api/v1/analytics/me/activity      Dnevna aktivnost
GET  /api/v1/analytics/me/quizzes       Performanse kvizova
GET  /api/v1/analytics/me/documents     Stats dokumenata
GET  /api/v1/analytics/me/streak-history  Heatmap podaci
```

---

*Dokument kreiran: 2026-02-28 | Ažuriran: 2026-03-01 | AI Sistem za učenje v1.1.0-rc2*
