# AI Learning System - Dokumentacija Funkcionalnosti

**Verzija dokumenta:** 1.0.0  
**Datum kreiranja:** 08.03.2026  
**Autor:** AI Assistant

---

## Sadržaj

1. [Pregled sistema](#pregled-sistema)
2. [Autentifikacija i autorizacija](#autentifikacija-i-autorizacija)
3. [Upload fajlova](#upload-fajlova)
4. [Obrada dokumenata](#obrada-dokumenata)
5. [AI Provajderi](#ai-provajderi)
6. [OCR Implementacija](#ocr-implementacija)
7. [Quiz generacija](#quiz-generacija)
8. [Storage rešenje](#storage-rešenje)
9. [MinIO integracija](#minio-integracija)
10. [Nedavne ispravke](#nedavne-ispravke)

---

## 1. Pregled sistema

AI Learning System je web aplikacija za učenje uz pomoć veštačke inteligencije. Sistem omogućava:

- Upload PDF, TXT, DOCX i sličnih fajlova
- OCR procesuiranje skeniranih dokumenata
- Ekstrakciju teksta iz dokumenata
- Prevođenje sadržaja na različite jezike
- Generaciju kvizova na osnovu dokumenta
- Praćenje napredovanja u učenju

**Tehnologije:**
- Backend: FastAPI (Python 3.11+)
- Frontend: React + TypeScript + Vite
- Baza: PostgreSQL
- Cache/Queue: Redis + Celery
- Storage: MinIO (S3-compatible)
- OCR: Tesseract

---

## 2. Autentifikacija i autorizacija

**Datum implementacije:** Mart 2026

### Login Endpoint
- **PUTANJA:** `POST /api/v1/auth/login`
- **Tip sadržaja:** `application/x-www-form-urlencoded`
- **Parametri:**
  - `username` - Email korisnika
  - `password` - Lozinka

### Refresh Token
- **PUTANJA:** `POST /api/v1/auth/refresh`
- **Tip sadržaja:** `application/json`
- **Parametri:**
  - `refresh_token` - Refresh token

### JWT Tokeni
- Access token: 15 minuta
- Refresh token: 7 dana

---

## 3. Upload fajlova

**Datum implementacije:** Mart 2026  
**Poslednja izmena:** 08.03.2026

### Podržani formati
- PDF (`.pdf`)
- TXT (`.txt`)
- DOCX (`.docx`)
- Slike: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP

### Maksimalna veličina
- 50MB po fajlu

### Endpoint
- **PUTANJA:** `POST /api/v1/files/upload`
- **Autentifikacija:** Bearer token

### Kod izmene (files.py:33)
```python
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
```

---

## 4. Obrada dokumenata

**Datum implementacije:** Mart 2026  
**Poslednja izmena:** 08.03.2026

### PDF Processing
- Ekstrakcija teksta pomoću PyMuPDF
- Automatsko čišćenje teksta (header-i, footer-i, brojevi stranica)
- Smart chunking sa overlap-om
- Preskakanje praznih stranica
- Preskakanje TOC (Sadržaj) stranica

### Empty Page Detection
**Datum izmene:** 08.03.2026

Dodata nova metoda `is_empty_page()` koja detektuje stranice sa < 50 karaktera.

```python
def is_empty_page(self, page: fitz.Page, text: str = None) -> bool:
    """Proverava da li je stranica prazna ili skoro prazna."""
    if text is not None:
        char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        if char_count < 50:
            return True
        return False
    text = self.extract_text_from_page(page)
    return self.is_empty_page(page, text)
```

### Metadata
```python
@dataclass
class PDFMetadata:
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    total_pages: int = 0
    total_chars: int = 0
    has_images: bool = False
    is_scanned: bool = False
    skipped_pages: int = 0  # Broj preskočenih praznih/TOC stranica
```

---

## 5. AI Provajderi

**Datum implementacije:** Mart 2026

### Podržani provajderi
1. **Ollama** - Lokalni AI (podrazumevano)
2. **OpenAI** - GPT-4, GPT-4o-mini
3. **Claude** - Anthropic Claude 3
4. **Google** - Gemini
5. **Groq** - Fast inference
6. **Mistral** - Mistral AI
7. **DeepL** - Prevod

### Konfiguracija (.env)
```
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.1

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

ANTHROPIC_API_KEY=your-anthropic-key
CLAUDE_MODEL=claude-3-sonnet-20240229

GROQ_API_KEY=your-groq-key
MISTRAL_API_KEY=your-mistral-key
DEEPL_API_KEY=your-deepl-key
```

### Fallback redosled
```python
TRANSLATION_PREFER_LOCAL: bool = True
TRANSLATION_FALLBACK_ORDER: str = "ollama,deepl,openai,google,claude"
```

---

## 6. OCR Implementacija

**Datum implementacije:** Mart 2026

### Tesseract OCR
- Koristi `pytesseract` za OCR
- Podržava više jezika: engleski i srpski (`eng+srp`)
- Automatski se aktivira za skenirane PDF-ove

### Implementacija (pdf.py:225)
```python
def perform_ocr(self, pdf_bytes: bytes, page_numbers: List[int] = None) -> Dict[int, str]:
    """Izvršava OCR na PDF stranicama."""
    if not self.use_ocr:
        logger.warning("OCR not available or disabled")
        return {}
    
    images = convert_from_bytes(pdf_bytes, dpi=200, ...)
    
    for idx, image in enumerate(images):
        text = pytesseract.image_to_string(image, lang=self.ocr_language)
        ocr_results[page_num] = text.strip()
    
    return ocr_results
```

### Detekcija skeniranih dokumenata
```python
is_scanned = total_chars < 100 and has_images
```

---

## 7. Quiz generacija

**Datum implementacije:** Mart 2026

### Proces
1. Ekstrakcija svih chunk-ova iz dokumenta
2. Ravnomerna distribucija uzoraka kroz dokument
3. Kombinovanje teksta (do 10,000 karaktera)
4. Slanje AI provajderu sa prompt-om
5. Parsiranje odgovora u JSON format
6. Kreiranje pitanja u bazi

### Endpoint
- **Kreiranje:** `POST /api/v1/quizzes`
- **Parametri:**
  - `document_id` - ID dokumenta
  - `num_questions` - Broj pitanja (podrazumevano 5)
  - `time_limit` - Vreme za kviz (opciono)
  - `passing_score` - Prolazni skor (podrazumevano 60%)

### AI Prompt
```python
QUIZ_PROMPT = """You are an expert educator. Based on the following text, 
generate exactly {num_questions} quiz questions."""
```

---

## 8. Storage rešenje

**Datum implementacije:** Mart 2026  
**Poslednja izmena:** 08.03.2026

### Podržani backend-i
1. **Lokalni fajl sistem** (podrazumevano)
2. **MinIO/S3** (cloud storage)

### Konfiguracija
```python
# .env
STORAGE_BACKEND=s3  # ili "local"
CLOUD_STORAGE_ENDPOINT=http://minio:9000
CLOUD_STORAGE_ACCESS_KEY=minioadmin
CLOUD_STORAGE_SECRET_KEY=minioadmin123
CLOUD_STORAGE_BUCKET_NAME=ai-learning-uploads
```

### Factory pattern (storage.py)
```python
def get_storage_service():
    backend = getattr(settings, 'STORAGE_BACKEND', 'local') or 'local'
    if backend == 's3':
        return CloudStorageService(...)
    else:
        return LocalStorageService(...)
```

---

## 9. MinIO integracija

**Datum implementacije:** Mart 2026  
**Poslednja izmena:** 08.03.2026

### MinIO Container
- Endpoint: `http://localhost:9000`
- Console: `http://localhost:9001`
- Credentials: `minioadmin` / `minioadmin123`

### Bucket
- Ime: `ai-learning-uploads`

### Testiranje konekcije
```bash
docker exec ai-learning-minio mc ls local/ai-learning-uploads/
```

---

## 10. Nedavne ispravke

### 08.03.2026 - Ispravka Login-a
**Problem:** Login nije radio  
**Uzrok:** Frontend je slao JSON ali je backend očekivao form-data  
**Rešenje:** Endpoint sada prihvata oba formata

### 08.03.2026 - Refresh Token
**Problem:** Refresh token je zahtevao query parametar  
**Uzrok:** Backend je očekivao `?refresh_token=` umesto JSON body  
**Rešenje:** Dodata podrška za JSON body

### 08.03.2026 - Nginx Redirect
**Problem:** 307 redirect na pogrešan port  
**Uzrok:** Nginx konfiguracija  
**Rešenje:** Ispravljen redirect u nginx.conf

### 08.03.2026 - MinIO
**Problem:** File upload nije radio sa MinIO  
**Uzrok:** Pogrešna lozinka  
**Rešenje:** Promenjena lozinka u `minioadmin123`

### 08.03.2026 - Novi tipovi fajlova
**Problem:** Nije bilo moguće upload-ovati slike, txt, docx  
**Rešenje:** Dodato u ALLOWED_EXTENSIONS

### 08.03.2026 - Empty page filtering
**Problem:** Prazne stranice su uključene u processing  
**Rešenje:** Dodato preskakanje praznih stranica

---

## Testiranje

### Login test
```bash
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@test.com&password=Test1234!"
```

### File upload test
```bash
TOKEN=$(curl -s -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@test.com&password=Test1234!" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8081/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"
```

### Documents API test
```bash
curl "http://localhost:8081/api/v1/documents?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Često postavljana pitanja

### Kako dodati novi AI provajder?
1. Dodaj konfiguraciju u `config.py`
2. Kreiraj klijenta u odgovarajućem service fajlu
3. Dodaj u fallback order

### Kako testirati OCR?
1. Upload-uj skenirani PDF
2. Pokreni processing
3. Proveri logove za OCR aktivnost

### Kako podesiti MinIO?
1. MinIO je već podešen u Docker compose
2. Pristupi console na http://localhost:9001
3. Koristi credentials: minioadmin / minioadmin123

---

## Reference

- [FastAPI](https://fastapi.tiangolo.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [MinIO](https://min.io/)
- [Ollama](https://ollama.ai/)
- [LangChain](https://python.langchain.com/)

---

*Document generated on 08.03.2026*
*Last updated: 08.03.2026*
