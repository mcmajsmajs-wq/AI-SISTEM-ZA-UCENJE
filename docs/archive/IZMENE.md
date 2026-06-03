# IZMENE — AI Learning System
================================================================================
Datum izmena: 2026-02-20
Na osnovu: ANALIZA_PROJEKTA.md
================================================================================

## PREGLED IZMENA

Ukupno izmenjenih fajlova: **9**
Kritičnih bugova popravljeno: **5**
Frontend/Backend neusklađenosti popravljeno: **12**

---

## 1. BACKEND

### 1.1 `backend/app/schemas/document.py` 🔴 KRITIČNO
**Problem:** `ChunkResponse` i `DocumentListResponse` su se importovale u `documents.py`
ali nisu bile definisane — server nije mogao da startuje (`ImportError`).

**Izmena:** Dodate dve nove klase:

```python
class ChunkResponse(BaseModel):
    id: str
    document_id: str
    sequence_number: int
    content: str
    translated_content: Optional[str] = None
    token_count: Optional[int] = None
    heading_level: int = 0
    parent_heading: Optional[str] = None
    is_translated: bool = False
    is_reviewed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int
```

---

### 1.2 `backend/app/tests/conftest.py` 🔴 KRITIČNO
**Problem:** Tri fixture-a koristili su polja koja ne postoje na modelima — svi testovi su padali.

#### `test_file_data` / `test_file`
- Uklonjeno polje `filename` (ne postoji na `File` modelu)
- Dodata `storage_path` (obavezno polje na modelu)
- Ispravljen status vrednost u test podacima

#### `test_document_data` / `test_document`
- Uklonjeno polje `author` (ne postoji na `Document` modelu)
- Uklonjeno polje `processing_progress` (ne postoji na `Document` modelu)
- Ispravljen status: `"processed"` → `"completed"` (jedini ispravni statusi su pending/processing/translating/completed/error)

#### `test_chunks`
- `chunk_index` → `sequence_number`
- `original_text` → `content`
- `translated_text` → `translated_content`
- Uklonjeno `status` polje (ne postoji na Chunk modelu)
- Uklonjeno `page_number` (ne postoji na Chunk modelu)
- `heading` → `parent_heading`
- Uklonjeno `is_edited` (ne postoji na Chunk modelu)
- Ispravno: `is_translated = 1` umesto `status = "translated"`

---

## 2. MCP SERVER

### 2.1 `mcp-server/src/ai_learning_mcp/__init__.py` 🔴 KRITIČNO
**Problem:** Hardkodovani path je bio pogrešan — MCP server nije mogao da čita ni jedan fajl.

```python
# BILO:
PROJECT_ROOT = Path("/home/dju/moji projekti/AI SISTEM ZA UCENJE/ai-learning-system")

# SADA:
PROJECT_ROOT = Path("/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system")
```

---

## 3. FRONTEND

### 3.1 `frontend/src/types/index.ts` 🔴 KRITIČNO
Sve TypeScript interfejs definicije su bile neusklađene sa backendom.

#### ID tipovi
Svi `id: number` → `id: string` (backend koristi UUID stringove)
Pogođeni interfejsi: `User`, `FileUploadResponse`, `Document`, `Chunk`, `Quiz`, `Question`, `QuizAttempt`

#### `FileUploadResponse`
- Uklonjeno polje `filename` (ne postoji na backend modelu)

#### `FileListResponse`
- `files: FileUploadResponse[]` → `items: FileUploadResponse[]`
- `page: number` → `skip: number`
- `size: number` → `limit: number`
- Uklonjeno `pages: number`

#### `Document` interfejs
- Dodata polja: `user_id`, `description`, `metadata`
- Uklonjeno polje `author` (ne postoji na modelu)
- Uklonjeno polje `processing_progress` (ne postoji na modelu)

#### `DocumentStatus` tip
- Uklonjeni: `'processed'`, `'translated'`
- Dodat: `'completed'`
- Backend Enum vrednosti: pending/processing/translating/completed/error

#### `Chunk` interfejs — kompletno prepisan
```typescript
// BILO (pogrešno):
chunk_index: number       → sequence_number: number
original_text: string     → content: string
translated_text: string   → translated_content: string | null
status: ChunkStatus       → is_translated: boolean + is_reviewed: boolean
page_number: number       → (uklonjeno, ne postoji na modelu)
heading: string           → parent_heading: string | null
is_edited: boolean        → (uklonjeno, ne postoji na modelu)
```

#### `ChunkStatus` tip
- Kompletno uklonjen (zamenjen sa `is_translated`/`is_reviewed` boolean vrednostima)

#### `ChunkUpdate` interfejs
- `translated_text: string` → `translated_content?: string`
- `status?: ChunkStatus` → `is_reviewed?: boolean`

---

### 3.2 `frontend/src/services/api.ts` 🔴 KRITIČNO
Svi API pozivi koristili su pogrešne tipove i parametre.

#### `filesApi`
- `list(page, size)` → `list(skip, limit)` — ispravni query parametri
- Svi ID parametri: `number` → `string`

#### `documentsApi`
- `list(page, size, status)` → `list(skip, limit, status)` — query params: `page/size` → `skip/limit`; filter param: `status` → `status_filter` (tačan naziv backend query parametra)
- Svi ID parametri: `number` → `string`
- `getChunks(id, page, size)` → `getChunks(id, skip, limit)` — ispravni query parametri
- `updateChunk()` — kompletno prepisano:
  - BILO: šalje JSON body sa `{ translated_text, status }` 
  - SADA: šalje query params sa `translated_content` i `is_reviewed` (backend čeka query params)
  - Ispravljena polja: `translated_text` → `translated_content`
- `estimateCost()`: endpoint `/estimate-cost` → `/estimate-translation` (tačan backend endpoint)

---

### 3.3 `frontend/src/pages/DashboardPage.tsx` 🟠 VISOK PRIORITET
- `documentsApi.list(1, 5)` → `documentsApi.list(0, 5)` (skip=0 ne page=1)
- `recentDocs?.data?.documents` → `recentDocs?.data?.items`
- Status vrednosti u badge mapama: `processed`/`translated` → `completed`

---

### 3.4 `frontend/src/pages/DocumentsPage.tsx` 🟠 VISOK PRIORITET
- `showTranslateModal: number | null` → `string | null`
- Mutacija tipovi: `(id: number)` → `(id: string)`
- `documentsApi.list(page, 10)` → `documentsApi.list((page-1)*10, 10)` (ispravna paginacija)
- `documents?.data?.documents` → `documents?.data?.items`
- Status vrednosti u badge mapama: `processed`/`translated` → `completed`
- Filter `<option>`: uklonjen `processed`/`translated`, dodat `completed`
- Uslov za prikaz Prevedi/Pregledaj: `doc.status === 'processed' || doc.status === 'translated'` → `doc.status === 'completed'`

---

### 3.5 `frontend/src/pages/DocumentDetailPage.tsx` 🔴 KRITIČNO
- `parseInt(id || '0')` → direktna upotreba `id` stringa (parseInt na UUID daje NaN)
- `getChunks(docId, 1, 20)` → `getChunks(docId, 0, 20)` (skip=0)
- Status vrednosti: `processed`/`translated` → `completed`
- `doc.author` → `doc.description`
- `doc.processing_progress` → `doc.status`
- `chunks?.data?.chunks?.length` → `Array.isArray(chunks?.data) && chunks.data.length > 0`
- `chunk.chunk_index` → `chunk.sequence_number`
- `chunk.original_text` → `chunk.content`
- `chunk.translated_text` → `chunk.translated_content`
- `chunk.heading` → `chunk.parent_heading`
- Uklonjeno: `chunk.page_number` (ne postoji na modelu)
- Uslov za Review link: `doc.status === 'translated'` → `doc.status === 'completed'`

---

### 3.6 `frontend/src/pages/ReviewPage.tsx` �� KRITIČNO
- `parseInt(id || '0')` → direktna upotreba `id` stringa
- `getChunks(docId, 1, 100)` → `getChunks(docId, 0, 100)` (skip=0)
- `chunks?.data?.chunks || []` → `Array.isArray(chunks?.data) ? chunks.data : []`
- `currentChunk?.translated_text` → `currentChunk?.translated_content`
- `currentChunk?.original_text` → `currentChunk?.content`
- `currentChunk?.heading` → `currentChunk?.parent_heading`
- Uklonjeno: `currentChunk?.page_number`
- Chunk status badge: `chunk.status === 'approved'/'edited'/'translated'` → `chunk.is_reviewed`/`chunk.is_translated` boolean
- `updateMutation` parametri: `{ translated_text, status }` → `{ translated_content?, is_reviewed? }`
- `handleApprove()`: šalje `{ is_reviewed: true }` umesto `{ translated_text, status: 'approved' }`
- `handleSave()`: šalje `{ translated_content, is_reviewed: true }` umesto `{ translated_text, status: 'edited' }`
- Navigacioni breadcrumb dugmad: `chunk.status === 'approved' || 'edited'` → `chunk.is_reviewed`

---

## 4. SAŽETAK IZMENA PO KATEGORIJI

| Kategorija | Fajlova | Bugova/Izmena |
|---|---|---|
| Backend schemas | 1 | 2 nove klase |
| Backend testovi | 1 | 3 fixture-a ispravljena |
| MCP Server | 1 | 1 path bug |
| Frontend tipovi | 1 | ~15 ispravki |
| Frontend API | 1 | ~8 ispravki |
| Frontend stranice | 4 | ~20 ispravki |
| **Ukupno** | **9** | **~49** |

---

## 5. PREOSTALE NAPOMENE

### Šta JE ispravno i radi:
- Svi backend API endpoint-i i njihovi URL-ovi
- Autentifikacija (JWT, refresh token, interceptori)
- Upload logika
- Celery task pokretanje
- Health endpoint-i

### Šta JOŠ NIJE implementovano (van scope-a ovih izmena):
- Kvizovi (endpoints ne postoje)
- Export PDF funkcionalnost (vraća "coming soon")
- Batch translation u Celery taskovima
- Redis token blacklist za logout
- Server-side search za dokumente
