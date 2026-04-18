# FAZA 12 - Ispravke BUG-ova i Dokumentacija

**Datum:** 2026-04-12
**Verzija:** 2.0.0

---

## 1. Ispravljeni Bug-ovi (Ažurirano: 2026-04-12)

### 1.1 `process_pdf()` Signature Error
**Problem:** `"PDFService.process_pdf() takes from 2 to 4 positional arguments but 5 were given"`

**Lokacija:** `/backend/app/workers/tasks/pdf_processing.py:84-89`

**Stari kod (❌):**
```python
result = pdf_service.process_pdf(
    file_bytes,
    file.original_filename or "document.pdf",  # positional, ali je title
    document_id,      # EXTRA argument - ne postoji
    db,               # EXTRA argument - ne postoji
)
```

**Novi kod (✅):**
```python
result = pdf_service.process_pdf(
    file_bytes,
    title=file.original_filename or "document.pdf",  # keyword argument
)
```

**Ispravke na 3 mesta:**
1. `pdf_processing.py:84-89` - PDF processing task
2. `quiz.py:208-213` - Quiz pipeline task
3. `pdf_detector.py:44` - PDF skill detector (dodato `open()` za čitanje fajla)

**Napomena:** `process_pdf()` vraća `ProcessingResult` dataclass, ne dict. Pristup podacima:
```python
result.success      # bool
result.chunks       # List[ChunkData]
result.metadata     # PDFMetadata
result.error         # Optional[str]
```

---

### 1.2 Chunks NIKAD Čuvani u Bazi!
**Problem:** Dokument pokazuje `total_chunks=3807` ali u bazi nema chunks!

**Lokacija:** `/backend/app/workers/tasks/pdf_processing.py`

**Stari kod (❌):**
```python
result = pdf_service.process_pdf(file_bytes, title=...)
document.total_chunks = len(result.chunks)  # Samo count, NE čuva chunks!
# NEDOSTAJE: db.add(chunk) za svaki chunk!
```

**Novi kod (✅):**
```python
result = pdf_service.process_pdf(file_bytes, title=...)

for chunk_data in result.chunks:
    chunk = Chunk(
        id=uuid.uuid4(),
        document_id=document.id,
        content=chunk_data.content,
        sequence_number=chunk_data.sequence_number,
        token_count=chunk_data.token_count,
        page_number=chunk_data.page_number,
    )
    db.add(chunk)

document.total_pages = result.metadata.total_pages
document.status = "completed"
document.total_chunks = len(result.chunks)
```

**Verifikacija:**
```sql
SELECT id, title, status, total_chunks, total_pages 
FROM documents 
WHERE id = 'e0ba8f2d-0bd6-4208-a3b0-3f5000eda2a3';
-- Result: completed, 3807 chunks, 3792 pages ✅
```

---

### 1.3 Quiz Progress Bars - Nisu se Ažurirali
**Problem:** Funkcija `update_quiz_progress()` postoji ali se nikad ne poziva tokom generacije.

**Lokacija:** `/backend/app/services/quiz/service.py:447-472`

**Dodato (✅):**
```python
num_to_generate = _auto_num_questions(len(selected_chunks), num_questions)

from app.services.quiz import update_quiz_progress
update_quiz_progress(quiz_id, 0, num_to_generate)  # Početak

ok, questions, provider = self.generate_questions_with_ai(...)

if not ok or not questions:
    quiz.status = "failed"
    db.commit()
    update_quiz_progress(quiz_id, -1, num_to_generate)  # Greška
    return False, f"Greška pri generisanju: {provider}"

update_quiz_progress(quiz_id, len(questions), num_to_generate)  # Uspelo
```

---

### 1.4 OCR Dependencies
**Problem:** Nedostajali su `poppler-utils` i `tesseract-ocr-srp` u Docker container-u.

**Lokacija:** Docker container (runtime)
**Datum:** 2026-04-12

**Rešenje:**
```bash
# Instalacija u running container
apt-get update && apt-get install -y poppler-utils tesseract-ocr-srp
```

**Verifikacija:** OCR pipeline radi - `pdf2image` → `pytesseract` → text extraction

---

### 1.2 `char_count` argument u Chunk modelu
**Problem:** `"'char_count' is an invalid keyword argument for Chunk"`

**Lokacija:** `/backend/app/workers/tasks/pdf_processing.py:113`

**Stari kod:**
```python
chunk = Chunk(
    id=uuid.uuid4(),
    document_id=document.id,
    content=text_content,
    sequence_number=1,
    char_count=len(text_content),  # ❌ NE POSTOJI
)
```

**Novi kod:**
```python
chunk = Chunk(
    id=uuid.uuid4(),
    document_id=document.id,
    content=text_content,
    sequence_number=1,
    token_count=len(text_content) // 4,  # ✅ Ispravno
)
```

**Rešenje:** Uklonjen `char_count` argument. Chunk model nema taj atribut.

---

### 1.3 Pogrešno ime metode `populate_quiz_questions`
**Problem:** `"'QuizService' object has no attribute 'populate_quiz_questions'"`

**Lokacija:** `/backend/app/workers/tasks/quiz.py:76`

**Stari kod:**
```python
success, used_provider = quiz_service.populate_quiz_questions(  # ❌
    db=db,
    quiz_id=quiz_id,
    ...
)
```

**Novi kod:**
```python
success, used_provider = quiz_service.generate_quiz_questions(  # ✅
    db=db,
    quiz_id=quiz_id,
    ...
)
```

**Rešenje:** Metoda preimenovana u `generate_quiz_questions`.

---

### 1.4 `Chunk.get()` - SQLAlchemy vs Dictionary
**Problem:** `"'Chunk' object has no attribute 'get'"`

**Lokacija:** `/backend/app/services/quiz/helpers/__init__.py`

**Uzrok:** Helper funkcije su tretirale SQLAlchemy objekte kao dictionary-e.

**Ispravke:**

#### Funkcija: `select_chunks_for_quiz()`
```python
# STARI KOD (❌):
quality_chunks = [c for c in chunks if is_chunk_quality(c.get("text", ""))]
text = chunk.get("text", "")
result.append({**chunk, "text": text[:remaining]})

# NOVI KOD (✅):
quality_chunks = [c for c in chunks if is_chunk_quality(c.content)]
text = chunk.content or ""
chunk.content = text[:remaining]  # Direktno modifikujemo atribut
```

#### Funkcija: `get_images_for_chunks()`
```python
# STARI KOD (❌):
chunk_id = chunk.get("id")

# NOVI KOD (✅):
chunk_id = chunk.id
```

#### Funkcija: `get_quiz_usage_stats()`
```python
# STARI KOD (❌):
used = sum(1 for c in chunks if c.get("used_in_quiz", False))

# NOVI KOD (✅):
used = sum(1 for c in chunks if c.used_for_quiz)
```

#### Funkcija: `mark_chunks_as_used()`
```python
# STARI KOD (❌):
{"used_in_quiz": True}

# NOVI KOD (✅):
{"used_for_quiz": 1}  # Integer, ne Boolean
```

---

### 1.5 User.skills Relationship
**Problem:** SQLAlchemy mapper error - User model nema `skills` relationship.

**Lokacija:** `/backend/app/db/models/user.py` i `/backend/app/db/models/__init__.py`

**Rešenje:**

1. Dodat `skills` relationship u User model:
```python
# user.py
skills = relationship(
    "Skill", back_populates="user", cascade="all, delete-orphan"
)
```

2. Dodat import Skill modela u models/__init__.py:
```python
# Import Skill model to ensure it's registered before User relationship is established
try:
    from app.services.skills.models import Skill, SkillTemplate, DocumentType
except ImportError:
    pass
```

---

## 2. Chunk Model Atributi

Za buduće reference - Chunk SQLAlchemy model ima sledeće atribute:

```python
class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Sadržaj
    sequence_number = Column(Integer)
    content = Column(Text)           # ✅ "text" u helpersima = "content"
    translated_content = Column(Text)
    token_count = Column(Integer)
    
    # Struktura
    heading_level = Column(Integer)
    parent_heading = Column(String)
    
    # Status (Integer, ne Boolean!)
    is_translated = Column(Integer)      # 0=False, 1=True
    is_reviewed = Column(Integer)        # 0=False, 1=True
    used_for_quiz = Column(Integer)      # 0=False, 1=True  ✅ "used_for_quiz" NE "used_in_quiz"
    
    page_number = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

---

### 1.6 `total_questions` nije ažuriran nakon generacije
**Problem:** Quiz pokazuje "0 pitanja" iako su pitanja uspešno generisana.

**Lokacija:** `/backend/app/services/quiz/service.py:483-484`

**Stari kod:**
```python
quiz.status = "ready"
db.commit()
```

**Novi kod:**
```python
quiz.status = "ready"
quiz.total_questions = len(questions)
if quiz.target_questions == 0:
    quiz.target_questions = num_questions
db.commit()
```

**Uzrok:** `total_questions` polje se nikada nije ažuriralo nakon uspešne generacije pitanja.

**Verifikacija:**
```sql
SELECT q.id, q.total_questions, q.target_questions,
       (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) as actual_questions
FROM quizzes q;
```

---

## 3. Testiranje

### 3.1 Quiz Generation Test
```python
from app.workers.tasks import get_db_session
from app.services.quiz import quiz_service

db = get_db_session()
quiz_id = 'your-quiz-id'

success, used_provider = quiz_service.generate_quiz_questions(
    db=db,
    quiz_id=quiz_id,
    num_questions=3,
)

print(f'Success: {success}')
print(f'Provider: {used_provider}')
```

### 3.2 Verifikacija Chunk Helper-a
```python
from app.services.quiz.helpers import select_chunks_for_quiz, get_quiz_usage_stats

chunks = db.query(Chunk).filter(...).all()
selected = select_chunks_for_quiz(chunks)
stats = get_quiz_usage_stats(chunks)

print(f'Odabrano: {len(selected)}')
print(f'Stats: {stats}')
```

---

## 7. Izmenjeni Fajlovi (Kompletna Lista)

| Fajl | Izmena | Status |
|------|--------|--------|
| `backend/app/workers/tasks/pdf_processing.py` | Ispravljen `process_pdf()` poziv + dodato čuvanje chunks | ✅ |
| `backend/app/workers/tasks/quiz.py` | Ispravljen `process_pdf()` poziv | ✅ |
| `backend/app/services/skills/pdf_detector.py` | Dodato `open()` za čitanje PDF fajla | ✅ |
| `backend/app/services/quiz/service.py` | Dodato `update_quiz_progress()` pozive | ✅ |
| `backend/app/workers/tasks/pdf_processing.py` | Uklonjen `char_count` argument | ✅ |
| `backend/app/workers/tasks/quiz.py` | `populate_quiz_questions` → `generate_quiz_questions` | ✅ |
| `backend/app/services/quiz/helpers/__init__.py` | Ispravljeni `.get()` pozivi na Chunk objektima | ✅ |
| `backend/app/db/models/user.py` | Dodat `skills` relationship | ✅ |
| `backend/app/db/models/__init__.py` | Dodat import Skill modela | ✅ |

---

## 8. Verifikacija (2026-04-12)

### Test Rezultati:
```
438 passed, 1 failed, 2 skipped
```

### Dokument Processing Test:
```sql
-- Pre
SELECT total_chunks FROM documents WHERE id = '...';  -- 3807 (ali nema chunks!)

-- Posle
SELECT COUNT(*) FROM chunks WHERE document_id = '...';  -- 3807 ✅
```

### Test Quiz ID: `71391f02-d00d-4102-a6e0-087e138713d7`
- Status: ready
- Questions: 3
- Total chunks: 3

---

## 9. Best Practices

### 5.1 SQLAlchemy vs Dictionary
**Uvek** pristupajte atributima SQLAlchemy objekata direktno:
```python
# ❌ NE KORISTI:
chunk.get("content", "")
chunk.get("used_for_quiz", False)

# ✅ KORISTI:
chunk.content
chunk.used_for_quiz
```

### 5.2 Integer vs Boolean za status
Chunk model koristi Integer (0/1) umesto Boolean:
```python
# ❌ NE KORISTI:
chunk.used_for_quiz = True
db.query(Chunk).update({"used_for_quiz": True})

# ✅ KORISTI:
chunk.used_for_quiz = 1
db.query(Chunk).update({"used_for_quiz": 1})
```

### 5.3 Import redosled
Kada dodajete nove modele sa relationship-ima:
1. Uverite se da su svi povezani modeli uvezeni u `models/__init__.py`
2. Relationship-i moraju biti definisani nakon oba modela
3. Koristite `try/except` za opcione module

---

## 6. Napomene

- OCR zavisi od `poppler-utils` i `tesseract-ocr-srp` - moraju biti instalirani u Docker image
- Worker container mora biti restarovan nakon promena modela
- Quiz `total_questions` polje se ne ažurira automatski - to je zaseban bug za ispraviti
