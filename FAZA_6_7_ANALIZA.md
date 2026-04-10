# FAZA 7 + FAZA 6 (Skill System) - Kompletna Analiza

**Datum:** 2026-04-09  
**Analizu uradio:** Claude Code

---

## 1. FAZA 7: KVIZ SISTEM - Šta Je Implementirano

### 1.1 Komponente (iz NEDOSTAJUCE_STVARI.md)

| Komponenta | Status | Napomena |
|----------|--------|---------|
| Quiz modeli (Quiz, Question, QuizAttempt) | ✅ | SQLAlchemy |
| Quiz schemas | ✅ | Pydantic |
| AI generisanje pitanja | ✅ | Multi-provider |
| Multiple choice | ✅ | |
| Checkbox pitanja | ✅ | Više tačnih |
| True/False pitanja | ✅ | |
| REST API (10 endpoints) | ✅ | CRUD + play |
| Frontend (play, results) | ✅ | |
| Real-time scoring | ✅ | |
| Explanation za pitanja | ✅ | |
| Alembic migracije | ✅ | |
| Celery task | ✅ | generate_quiz_task |
| Auto Pipeline | ✅ | PDF→Translate→Quiz |
| StudyPlan (7b) | ✅ | Plan učenja |

### 1.2 Nedostaju (iz NEDOSTAJUCE_STVARI.md)

- Time limit po pitanju
- Shuffle questions opcija
- Progress save (duži kvizovi)
- Leaderboard (opciono)
- Email notifikacije

---

## 2. FAZA 6: SKILL SISTEM - Nova Implementacija

### 2.1 Šta je Kreirano

| Fajl | Linije | Opis |
|------|--------|------|
| `app/services/skills/pdf_detector.py` | 3219 | PDF Subject Detection |
| `tests/test_pdf_skill_detector.py` | 448 | Testovi (59) |
| `app/services/skills/__init__.py` | Updated | Novi exports |

### 2.2 PDF Detector Mogućnosti

- **68 subject areas** (vs 11 u starom sistemu)
- **English + Serbian** keywords
- **68+ quiz rules** za generisanje pitanja

### 2.3 Funkcije

```python
detect_subject_from_text(text) → oblast
detect_subject_from_chunks(chunks) → oblast
get_prompt_for_subject(oblast) → prompt
get_rules_for_subject(oblast) → rules
detect_and_prepare_quiz(text/chunks) → {subject_area, prompt, rules, confidence}
```

---

## 3. INTEGRACIONI PROBLEMI - KRITIČNO!

### 3.1 Identifikovani Problem

PostoJE DVA odvojena sistema za detekciju oblasti:

| Sistem | Lokacija | Broj oblasti | Jezik |
|--------|----------|---------------|------|
| **Stari** | `quiz/helpers/subject_detection.py` | 11 | Samo SR |
| **Novi** | `skills/pdf_detector.py` | 68 | SR + EN |

### 3.2 Test rezultati

```
Test: "The mitochondria is the powerhouse..."
  Stari detector → "ostalo" (NE RADI!)
  Novi detector  → "biologija" (RADI!)

Test: "Newton formulated the laws..."
  Stari detector → "matematika" (POGREŠAN)
  Novi detector  → "fizika" (RADI!)
```

### 3.3 Šta Quiz Koristi

```python
# app/services/quiz/service.py:316
from app.services.quiz.helpers.subject_detection import detect_subject_area

# Znači:
# - English PDF dokumenti → "ostalo" 
# - Pogrešni prompts
# - Loši quiz rezultati
```

### 3.4 pdf_detector NIJE integrisan

- ✗ `quiz/service.py` - ne koristi pdf_detector
- ✗ `quiz/helpers/subject_detection.py` - nije ažuriran
- ✗ `api/endpoints/quizzes.py` - nema konekcije
- ✗ `auto_pipeline_task` - koristi stari sistem

---

## 4. MISSING / NEDOSTACI

### 4.1 [KRITIČNO] Integracija

| # | Problem | Lokacija | Prioritet |
|---|--------|---------|-----------|
| 1 | Quiz koristi stari detector | `quiz/service.py:316` | HIGH |
| 2 | English PDF → "ostalo" | Subject detection | HIGH |
| 3 | pdf_detector nepovezan | Sve quiz fajlove | HIGH |
| 4 | Nema integration test | `tests/` | MEDIUM |

### 4.2 [SREDNJI] Funkcionalnost

| # | Problem | Lokacija |
|---|---------|---------|
| 5 | Nema auto-detect u pipeline | `workers/tasks/quiz.py` |
| 6 | Quiz rules ne koriste novi detector | `quiz/prompts/` |
| 7 | MCP server ne koristi pdf_detector | `mcp-server/` |

### 4.3 [LOW] Dokumentacija

| # |Problem | Lokacija |
|---|--------|---------|
| 8 | pdf_detector nije dokumentovan | README |
| 9 | Integracija nije objašnjena | NEDOSTAJUCE_STVARI |

---

## 5. ZAVISNOST SA OSTALIM FAZAMA

### 5.1 Trenutna Arhitektura

```
PDF Upload
    ↓
PDF Service (app/services/pdf.py)
    ↓
[FAZA 7] Quiz Generation
    ↓ detect_subject_area() ← STARI (SR only)
    ↓ get_specialized_prompt()
    ↓ AI generate (Ollama/OpenAI/Claude)
    ↓
Quiz Results
```

### 5.2 Potencijalna Arhitektura

```
PDF Upload
    ↓
PDF Service
    ↓
[FAZA 6] PDF Skill Detector ← NOVI (SR+EN, 68 oblasti)
    ↓ detect_subject_from_text()
    ↓ get_prompt_for_subject()
    ↓ get_rules_for_subject()
    ↓
[FAZA 7] Quiz Generation
    ↓ AI generate
    ↓
Quiz Results
```

### 5.3 Šta Moramo Promeniti

1. **Quiz service import:**
   ```python
   # Trenutno:
   from app.services.quiz.helpers.subject_detection import detect_subject_area
   
   # Treba:
   from app.services.skills.pdf_detector import detect_subject_from_text as detect_subject_area
   ```

2. **Pipeline integracija:**
   - Koristiti `detect_and_prepare_quiz()` umesto odvojenih koraka

3. **MCP server:**
   - Dodati tool za `pdf_detector`

---

## 6. TEST REZULTATI

### 6.1 Test Pokrivenost

| Test Suite | Broj testova | Status |
|------------|-------------|--------|
| `test_quiz_modules.py` | 24 | ✅ Pass |
| `test_quiz_clients.py` | 74 | ✅ Pass |
| `test_pdf_skill_detector.py` | 59 | ✅ Pass |
| **UKUPNO** | **207** | ✅ **100%** |

### 6.2 Nedostaju Testovi

- ✗ Integration test: PDF upload → detect → quiz
- ✗ English PDF → subject detection
- ✗ Pipeline end-to-end
- ✗ MCP tools za pdf_detector

---

## 7. PREPORUKE ZA FUTURE RAD

### 7.1 Visok Prioritet (Uradi Odmah)

1. **Integrisati pdf_detector u Quiz:**
   ```python
   # U quiz/service.py:316
   from app.services.skills.pdf_detector import detect_subject_from_text
   # ILI
   from app.services.skills import detect_subject_from_text as detect_subject_area
   ```

2. **Dodati integration test:**
   ```python
   def test_pdf_to_quiz_integration():
       # Upload English PDF
       # Generate quiz
       # Verify subject != "ostalo"
       # Verify questions match subject
   ```

### 7.2 Srednji Prioritet

3. **Ažurirati auto_pipeline:**
   - Koristiti `detect_and_prepare_quiz()`

4. **MCP server integration:**
   - Dodati skill detection tool

### 7.3 Nizak Prioritet

5. **Dokumentacija**
6. **Leaderboard**
7. **Time limits**

---

## 8. ZAKLJUČAK

### Šta Je Uradjeno (FAZA 6)

- ✅ Kreiran pdf_detector.py (3219 linija)
- ✅ 68 subject areas (SR+EN)
- ✅ 59 testova (100% passing)
- ✅ Eksporti u skills/__init__.py
- ✅ Quiz rules za sve oblasti

### Šta Nedostaje (FAZA 6+7 Integracija)

- 🚫 **pdf_detector NOT connected to Quiz** (CRITICAL)
- 🚫 English PDF → "ostalo" subject (BUG)
- 🚫 Auto pipeline koristi stari sistem
- 🚫 MCP tools ne koriste pdf_detector

### Šta Je Potrebno Uraditi

1. **Update quiz/service.py** - zameniti import
2. **Add integration test** - PDF → Quiz workflow
3. **Update pipeline** - koristiti nove funkcije
4. **Dokumentovati** - šta je novo

---

## 9. ACTION ITEMS

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Integrisati pdf_detector u Quiz service | Claude | PENDING |
| 2 | Dodati integration test | Claude | PENDING |
| 3 | Ažurirati auto_pipeline | Claude | PENDING |
| 4 | Testirati sa English PDF | User | PENDING |

---

*Ova analiza će se koristiti za dalji razvoj i dokumentaciju.*