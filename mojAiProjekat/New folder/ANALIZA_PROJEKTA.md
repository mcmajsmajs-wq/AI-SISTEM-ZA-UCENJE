# DETALJNA ANALIZA PROJEKTA: AI LEARNING SYSTEM
================================================================================
Datum analize: 2026-02-20
Verzija projekta: 1.0.0
Ukupan progres: ~65%
================================================================================

---

## 1. PREGLED PROJEKTA

**AI Learning System** je full-stack web aplikacija za personalizovano učenje koja:
- Prima PDF dokumente (upload)
- Parsira i chunk-uje tekst iz PDF-a
- Prevodi sadržaj na srpski (Ollama/DeepL/OpenAI/Google/Claude)
- Omogućava pregled i ručno ispravljanje prevoda
- Generiše kvizove (planirano, još nije implementovano)
- Prati napredak učenja (planirano)

---

## 2. ARHITEKTURA

### Stack

| Sloj | Tehnologija |
|---|---|
| Backend API | FastAPI (Python 3.11+) |
| Baza podataka | PostgreSQL + SQLAlchemy + Alembic |
| Keš / Message broker | Redis |
| Storage | MinIO (S3-compatible) |
| Background tasks | Celery + Celery Beat |
| AI / Prevod | Ollama (lokalno) + DeepL/OpenAI/Google/Claude (online) |
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| State management | Zustand (persist u localStorage) |
| HTTP client | Axios sa interceptorima |
| Reverse proxy | Nginx |
| Monitoring | Prometheus + Grafana |
| MCP Server | Python MCP server (za monitoring iz AI alata) |

### Struktura direktorijuma

```
ai-learning-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/       # auth, users, files, documents, health
│   │   │   └── v1/router.py     # centralni router (/api/v1)
│   │   ├── core/
│   │   │   ├── config.py        # pydantic-settings konfiguracija
│   │   │   └── logging_config.py
│   │   ├── db/
│   │   │   ├── base.py          # SQLAlchemy Base
│   │   │   ├── session.py       # engine + get_db()
│   │   │   └── models/          # User, UserSession, File, Document, Chunk
│   │   ├── schemas/             # Pydantic sheme (request/response)
│   │   ├── services/
│   │   │   ├── auth.py          # JWT, bcrypt, get_current_user dependency
│   │   │   ├── pdf.py           # PyMuPDF + OCR + chunking
│   │   │   ├── storage.py       # MinIO (boto3 S3)
│   │   │   └── translation.py   # Multi-provider prevod
│   │   ├── utils/helpers.py     # SHA256, UUID, format_file_size...
│   │   ├── workers/
│   │   │   ├── celery_app.py    # Celery instanca + Beat schedule
│   │   │   └── tasks.py         # process_pdf_task, translate_document_task, ...
│   │   ├── tests/
│   │   │   ├── conftest.py      # fixtures (user, file, document, chunks, mocks)
│   │   │   ├── unit/            # test_auth, test_pdf, test_storage, test_translation
│   │   │   └── integration/     # test_api.py (svi endpointi)
│   │   └── main.py              # FastAPI app + middleware + lifespan
│   ├── alembic/                 # migracije
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.tsx              # routing
│       ├── components/          # Layout, ProtectedRoute
│       ├── pages/               # Login, Register, Dashboard, Documents, DocumentDetail, Review, Settings
│       ├── services/api.ts      # axios instanca + interceptori + svi API pozivi
│       ├── stores/authStore.ts  # Zustand store (persisted token)
│       └── types/index.ts       # TypeScript interfejsi
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── .env.example
└── mcp-server/                  # MCP server za monitoring projekta
```

### Tok podataka - Upload i obrada PDF-a

```
Frontend
  │── POST /api/v1/files/upload (multipart)
Backend - files.py endpoint
  │── Validacija (samo PDF, max 50MB)
  │── Upload u MinIO (storage_service)
  │── Zapis u tabelu `files` (status: uploaded)
  │── Vraća file_id

Frontend
  │── POST /api/v1/documents (file_id, title, source_language, target_language)
Backend - documents.py endpoint
  │── Kreiranje zapisa u `documents` tabeli (status: pending)
  │── Pokretanje Celery taska: process_pdf_task(document_id, file_id)

Celery Worker
  │── Download iz MinIO
  │── PDFService.process_pdf()
  │── ExtractMetadata → ExtractText po stranici → OCR (ako je skenirano)
  │── DenoiseText → SmartChunk (chunking po paragrafima + heading detekcija)
  │── Zapis Chunk redova u bazu
  │── Document status → "completed"

  │── (opciono) translate_document_task(document_id, provider)
  │── TranslationService.translate() po chunk-u (Ollama → DeepL → OpenAI → Google → Claude)
  │── Zapis translated_content u Chunk
```

---

## 3. KLJUČNE KONVENCIJE

### 3.1 Jezički stil komentara
- **Svi docstringovi i komentari su na srpskom jeziku** (srpski sa latiničnim pismom)
- Nazivi promenljivih, klasa i funkcija su **na engleskom**
- Svaki Python fajl počinje `# -*- coding: utf-8 -*-` i ima header blok:
  ```python
  """
  ================================================================================
  NAZIV MODULA
  ================================================================================
  Opis modula.
  Verzija: 1.0.0
  ================================================================================
  """
  ```

### 3.2 Autentikacija i zaštita endpoint-a
- Koristi se **OAuth2 + JWT** sa access tokenom (15 min) i refresh tokenom (7 dana)
- `get_current_user` dependency automatski dekodira token i vraća `User` objekat
- Postoje tri nivoa: `get_current_user`, `get_current_active_user`, `get_current_verified_user`
- Login podržava **dva formata**: OAuth2 form (`/auth/login`) i JSON (`/auth/login/json`)
- Logout je **stateless** – token nije blacklistovan u Redisu (TODO označeno)

### 3.3 Database modeli
- Svi modeli koriste **UUID primarni ključ** (`UUID(as_uuid=True)`)
- **Soft delete** implementiran kroz `deleted_at` timestamp (files tabela)
- `is_translated` i `is_reviewed` u `Chunk` modelu su `Integer` (0/1) **umesto Boolean** – neobično!
- Embedding polje u `Chunk` modelu je zakomentarisano dok se ne doda pgvector

### 3.4 Storage (MinIO)
- Path format za fajlove: `{user_id}/{uuid4}_{sanitized_filename}`
- Checksum se računa kao **SHA256** pre uploada
- Presigned URL-ovi za direktan download (bez prolaska kroz API)

### 3.5 PDF Processing (PDFService)
- `DEFAULT_CHUNK_SIZE = 500` tokena, `DEFAULT_CHUNK_OVERLAP = 100`
- Token brojanje: tiktoken (`cl100k_base`) ako je dostupan, inače broj reči
- OCR podrška: Tesseract (`eng+srp` default), aktivira se automatski za skenirane PDF-e
- Heading detekcija: regex pattern matching (Markdown #, ALL CAPS, numerisane sekcije, rimski brojevi)
- Denoise: uklanjanje brojeva stranica, footer-a, copyright teksta

### 3.6 Translation Service
- **Fallback lanac**: `ollama → deepl → openai → google → claude`
- Konfigurabilno kroz `TRANSLATION_PREFER_LOCAL` i `TRANSLATION_FALLBACK_ORDER`
- Svaki provider se koristi samo ako je konfigurisan (API ključ ili lokalni servis)

### 3.7 Celery Tasks
- `process_pdf_task`: max 3 pokušaja, retry nakon 60s
- `translate_document_task`: max 3 pokušaja, retry nakon 300s
- Beat schedule: cleanup starih fajlova jednom dnevno, study reminders svaki sat
- Celery session management: svaki task kreira sopstvenu DB sesiju (ne deli sa FastAPI)

### 3.8 Frontend arhitektura
- **Zustand** store persista samo `token` i `refreshToken` u localStorage
- Axios interceptor automatski:
  - Dodaje `Authorization: Bearer {token}` na svaki request
  - Pokušava refresh ako dobije 401 (`_retry` flag sprečava loop)
  - Prikazuje `toast.error()` za sve greške osim 401
- **React Query nije korišćen** za data fetching – direktni Axios pozivi u komponentama
- `ProtectedRoute` wrapper proverava `isAuthenticated` iz store-a

---

## 4. NEDOSTAJUĆI KOMENTARI

### 4.1 Frontend - Kritično (nema nijednog komentara)

#### `src/services/api.ts`
```typescript
// NEDOSTAJE: komentar šta radi request interceptor
api.interceptors.request.use(...)

// NEDOSTAJE: komentar o _retry flag mehanizmu i zašto se sprečava beskonačna petlja
if (error.response?.status === 401 && !originalRequest._retry) {

// NEDOSTAJE: komentar zašto postoje dva login metoda (form vs JSON)
loginJson: (email: string, password: string) =>
```

#### `src/stores/authStore.ts`
```typescript
// NEDOSTAJE: komentar zašto se persista samo token a ne ceo user objekat
partialize: (state) => ({ token: state.token, refreshToken: state.refreshToken })

// NEDOSTAJE: komentar o isLoading flow-u (zašto se setLoading(false) poziva u catch)
```

#### `src/types/index.ts`
- Nema nijedan komentar ni na jednom interfejsu
- Posebno važno dokumentovati `DocumentStatus` i `ChunkStatus` tipove i koji su validni prelazi

#### `src/App.tsx`
```typescript
// NEDOSTAJE: komentar šta radi useEffect pri inicijalizaciji (token check)
useEffect(() => {
  if (token && !isAuthenticated) {
    fetchUser()
  } else {
    useAuthStore.getState().setLoading(false)
  }
}, [token, isAuthenticated, fetchUser])
```

#### `src/components/Layout.tsx`
- Nema komentare o navigacionoj strukturi
- Nema objašnjenje za responsive sidebar logiku (zašto je `lg:translate-x-0`)

### 4.2 Backend - Manje kritično (ima dobre komentare, ali postoje praznine)

#### `app/workers/tasks.py`
```python
# NEDOSTAJE: komentar zašto se generate_quiz_task ne retry-uje sa pravom logikom
# (ceo task body je pass sa TODO - treba dokumentovati šta tačno treba implementirati)
@shared_task(bind=True, max_retries=2)
def generate_quiz_task(self, document_id: str, num_questions: int = 5):
    # TODO: Implementirati quiz generation  ← previše uopšteno, treba korake
```

#### `app/db/models/document.py`
```python
# NEDOSTAJE: objašnjenje zašto je Integer umesto Boolean
is_translated = Column(Integer, default=0)  # 0=False, 1=True  ← komentar postoji ali u liniji
is_reviewed = Column(Integer, default=0)    # zašto ne Boolean?
```

#### `app/api/endpoints/users.py`
```python
# TODO komentar postoji ali nedostaje: šta konkretno treba da vrati statistika
# (tabele za statistiku nisu ni kreirane u modelu)
return UserStats(
    total_documents=0,  # placeholder
    ...
)
```

#### `app/api/endpoints/auth.py`
```python
# NEDOSTAJE: objašnjenje zašto logout ne invalidira token (svesna odluka?)
# TODO komentar postoji ali bez konteksta
return {"message": "Successfully logged out"}
```

#### `app/core/config.py`
```python
# NEDOSTAJE: komentar šta znači TRANSLATION_FALLBACK_ORDER format i kako se parsira
TRANSLATION_FALLBACK_ORDER: str = "ollama,deepl,openai,google,claude"
```

---

## 5. NESLAGANJA FRONTEND ↔ BACKEND (KRITIČNI BUGOVI)

Ovo je najvažniji deo analize. Postoje značajna neslaganja između TypeScript tipova u frontendovim fajlovima i stvarnih backend API odgovora:

### 5.1 Tip ID-a: `number` vs `string (UUID)`

| Lokacija | Frontend tip | Backend stvarni tip |
|---|---|---|
| `User.id` | `number` | `string` (UUID) |
| `File.id` u API pozivima | `number` | `string` (UUID) |
| `Document.id` | `number` | `string` (UUID) |
| `Chunk.id` | `number` | `string` (UUID) |

**Problem:** `filesApi.get(id: number)` šalje numerički ID, backend očekuje UUID string.

### 5.2 Document status vrednosti

| Frontend (`types/index.ts`) | Backend (SQLAlchemy Enum) |
|---|---|
| `pending` | `pending` ✅ |
| `processing` | `processing` ✅ |
| `processed` ❌ | `completed` |
| `translating` | `translating` ✅ |
| `translated` ❌ | (ne postoji) |
| `error` | `error` ✅ |

**Problem:** Frontend `DocumentStatus` tip ima `processed` i `translated` koje backend nikad ne vraća.

### 5.3 Chunk model polja

| Frontend (`Chunk` interface) | Backend (`Chunk` SQLAlchemy model) |
|---|---|
| `chunk_index` ❌ | `sequence_number` |
| `original_text` ❌ | `content` |
| `translated_text` ❌ | `translated_content` |
| `is_edited` ❌ | (ne postoji) |
| (ne postoji) | `is_translated` |
| (ne postoji) | `is_reviewed` |
| `heading` ❌ | `parent_heading` |

**Problem:** Sva polja za chunk se zovu drugačije.

### 5.4 FileListResponse struktura

| Frontend (`FileListResponse`) | Backend (`FileListResponse` schema) |
|---|---|
| `files: FileUploadResponse[]` | `items: FileResponse[]` |
| `pages: number` | (ne postoji) |
| (ne postoji) | `skip: int` |
| (ne postoji) | `limit: int` |

### 5.5 conftest.py fixtures - neslaganje sa modelom

```python
# U conftest.py - File fixture koristi nepostojeće polje `filename`:
file = File(
    user_id=test_user.id,
    filename=test_file_data["filename"],          # ← GREŠKA: File model nema `filename`!
    original_filename=test_file_data["original_filename"],  # ← OK
    ...
)
# File model ima: original_filename, storage_path - nema samo `filename`
```

---

## 6. NEDOSTAJUĆE IMPLEMENTACIJE (STATUS)

### Kompletno nedostaje (❌)
- **Quiz generisanje** – `generate_quiz_task` je stub, nema modela u bazi, nema endpoint-a
- **Grafana dashboards** – prazan direktorijum
- **Token blacklist** – logout ne invalidira token u Redisu
- **Email verifikacija** – endpoint postoji ali vraća placeholder
- **Study reminders** – `send_study_reminders` task je stub
- **Cleanup job** – `cleanup_old_files` task je stub
- **pgvector embeddings** – zakomentarisano u Chunk modelu
- **Admin interfejs** – nema router-a ni endpoint-a
- **Search** – nema full-text pretrage
- **Analytics** – nema endpoint-a ni modela

### Parcijalno (🔶)
- **User statistike** – `GET /users/me/stats` vraća nule (placeholder)
- **GDPR brisanje** – soft delete postoji, hard delete nedostaje
- **Rate limiting** – konfiguracija postoji, middleware nije dodat na endpoint-e
- **SSL** – Nginx konfiguracija postoji, `ssl/` direktorijum je prazan

---

## 7. POKRETANJE I RAZVOJ

### Backend testovi
```bash
cd backend
pytest                          # svi testovi
pytest -v                       # verbose
pytest --cov=app                # sa coverage
pytest app/tests/unit           # samo unit testovi
pytest app/tests/integration    # samo integration testovi
pytest app/tests/unit/test_auth.py  # jedan test fajl
pytest -k "test_login"          # testovi po imenu
```

### Frontend razvoj
```bash
cd frontend
npm run dev      # development server (Vite)
npm run build    # TypeScript kompajliranje + Vite build
npm run lint     # ESLint
npm run preview  # preview prod build-a
```

### Docker (pun stack)
```bash
cd docker
cp .env.example .env
docker compose up -d
# ili za produkciju:
docker compose -f docker-compose.prod.yml up -d
```

### Backend (standalone razvoj)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Alembic migracije
```bash
cd backend
alembic upgrade head        # primeni sve migracije
alembic revision --autogenerate -m "opis"  # nova migracija
alembic downgrade -1        # rollback jedne migracije
```

---

## 8. ENVIRONMENT VARIJABLE (ključne)

```bash
# Obavezno promeniti u produkciji:
SECRET_KEY=change-this-in-production
JWT_SECRET=change-this-in-production

# AI/Prevod (bar jedno od sledećeg):
OLLAMA_HOST=http://localhost:11434   # Lokalni (besplatan)
DEEPL_API_KEY=...                    # Online (plaćen)
OPENAI_API_KEY=...                   # Online (plaćen)

# Database
POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB

# Storage
MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY
```

---

## 9. CODE QUALITY ALATI

```bash
# Formatiranje:
black app/
isort app/

# Linting:
flake8 app/
mypy app/

# Security:
bandit -r app/
safety check
```

---

## 10. PREPORUKE ZA SLEDEĆE KORAKE

### Hitno (blokira dalji razvoj):
1. **Uskladiti frontend tipove sa backendom** – popraviti sve ID tipove (number → string), Document status, Chunk polja i File response strukture
2. **Popraviti conftest.py fixture** – `filename` polje ne postoji u File modelu
3. **Dokumentovati Document endpoint-e** (documents.py) – nisu uključeni u ovoj analizi ali postoje nedefinisane reference (conftest koristi polja koja ne postoje u modelu)

### Kratkoročno:
4. **Dodati komentare na frontend** – posebno `api.ts`, `authStore.ts`, `types/index.ts`
5. **Implementirati quiz generisanje** – kreirati model, Celery task, endpoint
6. **Token blacklist** – dodati Redis blacklist za logout
7. **Popuniti Grafana dashboards**

### Dugoročno:
8. **pgvector embeddings** – za semantic search po dokumentima
9. **Email verifikacija flow**
10. **Admin interfejs**
11. **Full-text pretraga**


---

## 11. DODATNI NALAZI (DRUGI PROLAZ)

### 11.1 Kritična greška: Nedostajuće schema klase u schemas/document.py

`documents.py` endpoint importuje klase koje **ne postoje** u `schemas/document.py`:

```python
# U documents.py - linije koje se importuju:
from app.schemas.document import (
    DocumentCreate, 
    DocumentResponse, 
    DocumentListResponse,   # ← NE POSTOJI u schemas/document.py!
    ChunkResponse,          # ← NE POSTOJI u schemas/document.py!
    ChunkUpdate
)
```

Fajl `schemas/document.py` sadrži samo: `DocumentBase`, `DocumentCreate`, `DocumentResponse`, `ChunkUpdate`.

**`DocumentListResponse` i `ChunkResponse` nisu definisani nigde** — aplikacija će pasti sa `ImportError` čim se učita `documents.py`. Ovo je blokiing bug koji sprečava pokretanje servera.

### 11.2 Neslaganje response strukture: DashboardPage

`DashboardPage.tsx` pristupa `recentDocs.data.documents`:
```typescript
{recentDocs?.data?.documents?.length ? (
  recentDocs.data.documents.map((doc: any) => ...)
)}
```

Ali backend `GET /api/v1/documents` vraća `DocumentListResponse` (kada se popravi) sa poljem `items`, ne `documents`:
```python
return DocumentListResponse(
    items=[...],   # ← ne "documents"
    total=total,
    skip=skip,
    limit=limit
)
```

### 11.3 DocumentDetailPage koristi parseInt za UUID

```typescript
// DocumentDetailPage.tsx
const { id } = useParams<{ id: string }>()
const docId = parseInt(id || '0')   // ← parseInt od UUID daje NaN!

documentsApi.get(docId),             // šalje NaN
documentsApi.getChunks(docId, 1, 20) // šalje NaN
```

Sve stranice sa `parseInt(id)` imaju isti problem gde backend vraća UUID string.

### 11.4 Chunk UPDATE endpoint prima query params, ne body

```python
# documents.py - update_chunk endpoint
async def update_chunk(
    document_id: str,
    chunk_id: str,
    content: str = None,              # ← query param, ne body!
    translated_content: str = None,    # ← query param, ne body!
    is_reviewed: bool = None,          # ← query param, ne body!
    ...
```

Frontend šalje podatke u body:
```typescript
documentsApi.updateChunk(documentId, chunkId, { translated_text: "..." })
// api.ts: api.put(`/documents/${documentId}/chunks/${chunkId}`, data)
```

Još jedno neslaganje: frontend šalje `translated_text`, backend očekuje `translated_content`.

### 11.5 Celery queue konfiguracija

Worker startuje sa named queue-ovima:
```yaml
command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4 
         -Q pdf_processing,translation,quiz_generation,default
```

Ali taskovi nemaju `queue` atribut — svi idu u `default` queue:
```python
@shared_task(bind=True, max_retries=3)
def process_pdf_task(...)    # nema queue='pdf_processing'
```

Taskovi će raditi jer idu u `default`, ali nema prioritizacije.

### 11.6 Port konflikt: Grafana vs Vite

Grafana je konfigurisana na portu `3000:3000`. Vite development server takođe startuje na `:3000` po defaultu. Ako se pokrenu zajedno lokalno (bez Docker-a), doći će do konflikta.

Vite config (`vite.config.ts`) verovatno ne menja port — treba proveriti.

### 11.7 Frontend React Query se koristi mešovito

`DashboardPage` i `DocumentDetailPage` koriste `useQuery` iz `@tanstack/react-query`, ali `DocumentsPage` i `ReviewPage` koriste direktne Axios pozive sa `useState/useEffect`. Nema doslednog pristupa data fetching-u.

### 11.8 Celery Queues za taskove nisu definisani

Worker sluša 4 queue-a: `pdf_processing`, `translation`, `quiz_generation`, `default`. Svaki task bi trebalo da ima eksplicitno dodeljen queue za prioritizaciju:
```python
# Treba dodati:
@shared_task(bind=True, max_retries=3, queue='pdf_processing')
def process_pdf_task(...)

@shared_task(bind=True, max_retries=3, queue='translation')
def translate_document_task(...)
```

### 11.9 Export dokumenta je stub

```python
# documents.py
return {
    "document_id": document_id,
    "status": "queued",
    "download_url": None,
    "message": "Export feature coming soon"  # ← stub
}
```

### 11.10 "Izbriši nalog" dugme je disabled bez objašnjenja

```tsx
// SettingsPage.tsx
<button disabled className="btn-danger opacity-50 cursor-not-allowed">
  Izbriši nalog
</button>
```

Nema ni tooltip-a ni objašnjenja zašto je onemogućeno.

---

## 12. KOMPLETAN SPISAK BUGOVA (PRIORITIZOVANO)

### 🔴 KRITIČNO (aplikacija pada / ne radi)

| # | Fajl | Problem |
|---|---|---|
| 1 | `schemas/document.py` | `ChunkResponse` i `DocumentListResponse` nisu definisani — ImportError pri startu |
| 2 | `DocumentDetailPage.tsx` | `parseInt(id)` od UUID = `NaN` — svi API pozivi sa NaN |
| 3 | `conftest.py` | Fixture `test_file` koristi `filename` polje koje ne postoji u `File` modelu |

### 🟠 VISOK PRIORITET (pogrešni podaci / ne radi ispravno)

| # | Fajl | Problem |
|---|---|---|
| 4 | `DashboardPage.tsx` | Pristupa `data.documents` — backend vraća `data.items` |
| 5 | `types/index.ts` | `User.id`, `File.id`, `Document.id` su `number` — backend vraća UUID string |
| 6 | `types/index.ts` | `DocumentStatus` ima `processed`/`translated` — backend nema ove vrednosti |
| 7 | `types/index.ts` | Chunk polja: `original_text`/`translated_text`/`chunk_index`/`is_edited` — backend ima drugačija imena |
| 8 | `documents.py` update_chunk | Parametri su query params a frontend šalje body; polje `translated_text` vs `translated_content` |
| 9 | `api.ts` filesApi | `list`, `get`, `download`, `delete` primaju `number` za ID |

### 🟡 SREDNJI PRIORITET (funkcionalna ograničenja)

| # | Fajl | Problem |
|---|---|---|
| 10 | `auth.py` | Logout ne invalidira token (TODO) |
| 11 | `tasks.py` | Celery taskovi nemaju named queue atribut |
| 12 | `users.py` | `GET /users/me/stats` vraća nule (placeholder) |
| 13 | `documents.py` | Export vraća "coming soon" |
| 14 | `auth.py` | Email verifikacija je placeholder |
| 15 | `docker-compose.yml` | Port 3000 konflikt između Grafane i Vite |

### 🟢 NIZAK PRIORITET (komentari, stil)

| # | Oblast | Problem |
|---|---|---|
| 16 | Frontend (sve) | Gotovo nema komentara — `api.ts`, `authStore.ts`, `types/index.ts`, sve stranice |
| 17 | `document.py` | `is_translated = Integer` umesto Boolean |
| 18 | `workers/tasks.py` | Stub taskovi bez detalja implementacije |
| 19 | `SettingsPage.tsx` | Disabled dugme bez objašnjenja korisniku |
| 20 | Frontend | Mešovita upotreba React Query i direktnog Axios-a |


---

## 13. DODATNE SUGESTIJE

### 13.1 🔴 MCP Server ima pogrešan path (odmah popraviti)

```python
# mcp-server/src/ai_learning_mcp/__init__.py - linija 20
PROJECT_ROOT = Path("/home/dju/moji projekti/AI SISTEM ZA UCENJE/ai-learning-system")
#                               pogrešno!
# Tačan path je:
PROJECT_ROOT = Path("/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system")
```
MCP server ne može da čita ni jedan fajl ni log jer path ne postoji.

---

### 13.2 🔴 Sigurnost: Default sekreti u config.py

config.py ima hardkodovane fallback vrednosti:
```python
SECRET_KEY: str = "change-this-in-production"
JWT_SECRET: str = "change-this-in-production"
```
Ako neko pokrene aplikaciju bez .env fajla, koristiće ove predvidive tajne. Preporučiti validator koji baci grešku pri startu ako je environment "production" a ključevi nisu promenjeni.

---

### 13.3 🟠 Integracioni testovi: dependency_overrides.clear() nije u finally

Svaki test u test_api.py ima pattern:
```python
app.dependency_overrides[get_db] = lambda: db
assert response.status_code == 200   # Ako ovo padne...
app.dependency_overrides.clear()     # ovo se nikad ne izvrši - overrides cure u sledeći test!
```

Preporuka: Koristiti autouse fixture koji uvek čisti overrides.

---

### 13.4 🟠 TypeScript `any` na kritičnim mestima

Sve stranice koje prikazuju podatke koriste doc: any i chunk: any. TypeScript ne može da uhvati greške:
- DashboardPage.tsx - doc: any
- DocumentsPage.tsx - doc: any + pogrešno polje .documents umesto .items
- DocumentDetailPage.tsx - chunk: any + chunks.data.chunks ne postoji (backend vraća array direktno)

---

### 13.5 🟠 Redis je potpuno neiskorišćen osim za Celery

Redis je pokrenut i koristi resurse, ali jedina upotreba je Celery broker. Nema:
- Keširanja API odgovora
- Token blacklist za logout
- Session storage
- Rate limiting (konfigurisan ali ne primenjen)

Preporuka: Implementirati bar token blacklist za logout koristeci Redis SETEX.

---

### 13.6 🟡 Nema globalnog exception handlera

FastAPI po defaultu vraća generičku 500 grešku. Nema middleware koji hvata neočekivane greške, loguje stack trace i vraća konzistentni error format. Preporuka: dodati @app.exception_handler(Exception) u main.py.

---

### 13.7 🟡 Nema indeksa na chunks.sequence_number

Migracija kreira indeks na chunks.document_id, ali ne i na sequence_number. Svaki ORDER BY sequence_number na velikom dokumentu radi full scan. Preporuka: dodati kompozitni indeks (document_id, sequence_number).

---

### 13.8 🟡 Nema foreign key constraint za user_id u modelima

Document i File imaju user_id kolonu ali bez FK constraint na users.id. Moguće je kreirati dokument sa nepostojećim user_id. Samo Chunk.document_id ima pravi FK.

---

### 13.9 🟡 AuthService kao statična klasa je anti-pattern

Klasa koja ima iskljucivo @staticmethod metode je zapravo modul. Nema prednosti od klase, a otežava testiranje i dependency injection. Preporuka: pretvoriti u module-level funkcije.

---

### 13.10 🟡 Translation task nema batch obradu

translate_document_task prevodi chunk po chunk - za dokument sa 100 chunk-ova to je 100 API poziva sekvencijalno. Preporuka: dodati batch podršku za DeepL i OpenAI, ili paralelni processing unutar Celery taska.

---

### 13.11 🟢 DocumentsPage pretražuje klijentski, ne serverski

Pretraga radi samo na učitanoj stranici (20 dokumenata). Ako korisnik ima 100+ dokumenata - ne može naći ono sa sledeće stranice. Preporuka: dodati ?search= query param na backend endpoint.

---

### 13.12 🟢 document_to_response helper duplicira posao Pydantic schemi

documents.py ima pomocne funkcije document_to_response() i chunk_to_response() koje rade isto što i DocumentResponse.model_validate(doc). Treba ukloniti duplikaciju.

---

### SAŽETAK SUGESTIJA PO PRIORITETU

| Prioritet | Broj | Oblast |
|---|---|---|
| 🔴 Odmah | 2 | MCP path bug, Security validator za produkciju |
| 🟠 Pre prvog deploymenta | 4 | Test cleanup, TypeScript any, Redis blacklist, Global error handler |
| 🟡 Kratkoročno | 4 | DB indeksi, FK constraints, AuthService refactor, Batch translation |
| 🟢 Dugoročno | 2 | Server-side search, Schema refactor |
