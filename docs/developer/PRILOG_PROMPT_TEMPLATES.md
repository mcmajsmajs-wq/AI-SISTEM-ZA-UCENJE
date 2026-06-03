# Prompt Templates — AI Learning System

Verzija: 1.0.0
Datum: 2026-06-03

## Pregled

Prompt template je **reusable, pre-structured format** sa placeholder-ima koji se popunjavaju konkretnim vrednostima. To je blueprint za kreiranje AI prompt-ova.

### Zašto koristiti

| Razlog | Objašnjenje |
|--------|-------------|
| **Konzistentnost** | Svi AI output-i koriste istu strukturu i format |
| **Efikasnost** | Ne pišeš prompt od nula — samo popuniš placeholders |
| **Skalabilnost** | Dodaješ nove provajdere bez prepisivanja prompt logike |
| **Optimizacija** | Jedan template poboljšavaš za sve provajdere odjednom |

### Struktura dobrog template-a

```
1. PERSONA           — "You are an expert educator..."
2. IZVORI            — "Based on the following text..."
3. ZADATAK           — Popunjava se: {num_questions}, {text}, {subject}
4. FORMAT IZLAZA     — "Return ONLY valid JSON array..."
5. STRUKTURA         — JSON šema + primer
```

---

## 1. QUIZ_PROMPT — Generisanje pitanja

**Fajl:** `backend/app/services/quiz/prompts/quiz_prompt.py`

Ovo je glavni template za generisanje kviz pitanja. Koristi ga svih 6 AI provajdera (Ollama, Groq, DeepSeek, Claude, OpenAI, OpenAI Compatible).

### Placeholder-i

| Placeholder | Tip | Opis | Primer |
|-------------|-----|------|--------|
| `{num_questions}` | int | Broj pitanja koje AI treba da generiše | `10` |
| `{text}` | string | Tekst dokumenta (context za pitanja) | do 12000 karaktera |

### Struktura prompt-a

```
SEKCIJA                   OPIS
─────────────────────────────────────────────────────────
PERSONA                   "You are an expert educator and assessment designer"
FILTERING (14 pravila)    Šta ignorišemo (blank pages, copyright, TOC, itd.)
FOKUS                     Od čega pravimo pitanja (facts, concepts, procedures)
TIPOVI PITANJA (6 vrsta)  Distribucija: MC 30%, checkbox 15%, TF 10%, seq 15%, match 15%, cat 15%
SPECIALNE INSTRUKCIJE     Detaljno za svaki tip (sequencing, matching, categorization, text_input)
KVALITET                 "NOT: simple recall — YES: analytical, thought-provoking"
OBJAŠNJENJA              Obavezna 3-7 rečenica sa formulom/logikom
JEZIK                    SRPSKI LATINICA (ne ćirilica)
FORMAT IZLAZA            Valid JSON array sa tačnom šemom
```

### Detaljna pravila po tipu pitanja

| Tip pitanja | Zastupljenost | Opis |
|-------------|---------------|------|
| `multiple_choice` | 30% | 1 tačan, 4 opcije |
| `checkbox` | 15% | 2-4 tačna, 4 opcije (select all) |
| `true_false` | 10% | Balans TRUE/FALSE |
| `sequencing` | 15% | 3-5 elemenata u ispravnom redosledu |
| `matching` | 15% | Spajanje parova (levo-desno) |
| `categorization` | 15% | Razvrstavanje u 2-3 kategorije |

### Struktura izlaznog JSON-a

```json
{
  "question_text": "...",
  "question_type": "multiple_choice",
  "options": ["Opcija A", "Opcija B", "Opcija C", "Opcija D"],
  "correct_answer": "Opcija A",
  "explanation": "Objasnjenje od 3-7 recenica...",
  "points": 1
}
```

### Primer korišćenja

```python
from app.services.quiz.prompts import QUIZ_PROMPT

prompt = QUIZ_PROMPT.format(
    num_questions=10,
    text="Sadržaj dokumenta..."
)
# prompt je sada gotov string koji šaljemo AI provajderu
```

---

## 2. SUBJECT_INSTRUCTIONS — Specijalizacija po oblastima

**Fajl:** `backend/app/services/quiz/prompts/subjects.py`

Dodatne instrukcije koje se append-uju na QUIZ_PROMPT za specifične oblasti.

### Podržane oblasti

| Oblast | Ključ | Fokus |
|--------|-------|-------|
| Matematika | `matematika` | Formule, korak-po-korak, geometrija, algebra |
| Fizika | `fizika` | Fizički zakoni, SI sistem, računski zadaci |
| Hemija | `hemija` | Hemijske reakcije, formule, nomenklatura |
| Biologija | `biologija` | Biološki procesi, organele, latinski nazivi |
| Istorija | `istorija` | Događaji, datumi, hronologija, uzroci/posledice |
| Geografija | `geografija` | Geografske karakteristike, klima, statistički podaci |
| Jezici | `jezici` | Gramatika, sintaksa, semantika, književnost |
| Pravo | `pravo` | Pravni pojmovi, članovi zakona, postupci |
| Ekonomija | `ekonomija` | Ekonomski koncepti, formule, tržišni mehanizmi |
| Informatika | `informatika` | Algoritmi, logika, programski koncepti, kompleksnost |
| Ostalo (default) | `ostalo` | Generički — pokriva sve aspekte teksta |

### Kako radi

```python
from app.services.quiz.prompts import get_specialized_prompt

prompt = get_specialized_prompt(
    subject_area="matematika",
    num_questions=10,
    text="Sadržaj..."
)
# Rezultat: QUIZ_PROMPT + MATEMATIKA SPECIFICNO instrukcije
# Text se automatski truncate na 12000 karaktera
```

### Tok izvršavanja

```
get_specialized_prompt(subject, num, text)
  │
  ├── text = text[:12000]        # Truncate
  ├── base = QUIZ_PROMPT.format(num, text)
  ├── instructions = SUBJECT_INSTRUCTIONS.get(subject, "ostalo")
  └── return base + instructions  # Konkatenacija
```

---

## 3. File Skills — Prompt sabloni za export

**Fajl:** `backend/app/services/skills/file_skills.py`
**DB model:** `file_skills` tabela (FileSkill)

Prompt-ovi za formatiranje output-a pri prevodu i exportu fajlova.

### Dostupni skill-ovi

| Skill | Kategorija | Prompt opis |
|-------|-----------|-------------|
| **translate** | `TRANSLATE` | Prevod sa poglavljima, heading-ovima, markdown formatiranjem |
| **pdf** | `PDF` | PDF sa header-om, footer-om, page numbers, marginama |
| **docx** | `DOCX` | Word sa heading stilovima, TOC, page numbers |
| **xlsx** | `XLSX` | Excel sa kolonama, zaglavljima, formatiranjem |

### Korišćenje

```python
from app.services.skills.file_skills import get_file_skill

# Translate prompt
translate_prompt = get_file_skill().get_translate_prompt()

# PDF export prompt
pdf_prompt = get_file_skill().get_pdf_prompt()

# DOCX export prompt
docx_prompt = get_file_skill().get_docx_prompt()
```

### Arhitektura

```
Korisnik klikne "Prevedi"
  → FileSkillService.get_translate_prompt()
  → Dohvata prompt_template iz file_skills tabele
  → Prompt se koristi kao dodatni context za AI pri prevodu

Korisnik klikne "Export u PDF"
  → FileSkillService.get_pdf_prompt()
  → Prompt se koristi za formatiranje PDF izlaza
  → Primenjuje se na sve prevedene chunk-ove
```

---

## 4. Pregled svih template-ova u sistemu

| Template | Lokacija | Namena | Placeholder-i |
|----------|----------|--------|---------------|
| `QUIZ_PROMPT` | `.../prompts/quiz_prompt.py` | Generisanje kviz pitanja | `{num_questions}`, `{text}` |
| `SUBJECT_INSTRUCTIONS` | `.../prompts/subjects.py` | Specijalizacija po oblasti | `{subject_area}` |
| `get_specialized_prompt()` | `.../prompts/subjects.py` | Kombinuje QUIZ_PROMPT + subject | `{subject_area}`, `{num_questions}`, `{text}` |
| `translate` skill prompt | DB `file_skills` | Prevod dokumenta | (u prompt template koloni) |
| `pdf` skill prompt | DB `file_skills` | PDF export | (u prompt template koloni) |
| `docx` skill prompt | DB `file_skills` | Word export | (u prompt template koloni) |
| `xlsx` skill prompt | DB `file_skills` | Excel export | (u prompt template koloni) |

---

## 5. Kako dodati novi prompt template

### Korak 1 — Definiši template

```python
# backend/app/services/quiz/prompts/moji_prompti.py

MOJ_PROMPT = """
You are a {persona}.
Create {count} items about {topic}.
Return valid JSON array.
"""
```

### Korak 2 — Dodaj u `__init__.py`

```python
from app.services.quiz.prompts.moji_prompti import MOJ_PROMPT

__all__ = [
    "QUIZ_PROMPT",
    "MOJ_PROMPT",  # Novo
    ...
]
```

### Korak 3 — Koristi

```python
from app.services.quiz.prompts import MOJ_PROMPT

prompt = MOJ_PROMPT.format(persona="expert", count=5, topic="AI")
```

### Best practices

1. **Escapeuj vitičaste zagrade** — Python `str.format()` koristi `{` i `{}`, zato u prompt template-u koristi `{{{{` za literalne `{` u JSON primerima (vidi `quiz_prompt.py` linija 60-68)
2. **Stavi placeholdere na kraj** — lakše je debug-ovati kad je templatizovani deo na dnu
3. **Ne mešaj jezike** — template na engleskom, instrukcije na srpskom → konfuzija
4. **Testiraj sa svim provajderima** — Ollama, Groq, Claude, OpenAI različito reaguju na iste instrukcije
5. **Loguj finalni prompt** — `logger.debug(prompt)` pre slanja AI-ju, za debugging

---

## 6. Poznati problemi i rešenja

### Problem: AI ignoriše distribuciju tipova pitanja
**Rešenje:** Postavi eksplicitne procente (30%, 15%, itd.) i ponovi u "CRITICAL" sekciji.

### Problem: JSON parsing fail
**Rešenje:** U promptu navedi tačnu JSON šemu koju očekuješ. Kod `quiz_prompt.py`: `"Return ONLY valid JSON array. Each object must have: question_text, question_type, options, correct_answer, explanation, points"`

### Problem: Ćirilica umesto latinice
**Rešenje:** Dodat `cyrillic_to_latin()` post-processing u `service.py` nakon što AI vrati odgovor. Prompt sam nije dovoljan.

### Problem: Vitičaste zagrade u JSON primerima
**Rešenje:** Koristi `{{{{` umesto `{` u Python stringu. `quiz_prompt.py` linija 60: `'{{{{"A": "Value1", "B": "Value2"}}}}'` — ovo se evaluira u `{"A": "Value1", "B": "Value2"}`.

---

## 7. Integracija sa AI provajderima

Template-ovi su nezavisni od provajdera. Svaki provajder prima isti prompt string:

```
QUIZ_PROMPT.format(num_questions=5, text=...) 
  → "You are an expert educator... [fill-in instrukcije] ... Text: ..."
  
  → Ollama (lokalni, besplatan)
  → Groq (besplatan, 30 RPM)
  → DeepSeek ($0.14/M)
  → Claude ($3/M)
  → OpenAI ($2.50/M)
  → OpenAI Compatible (bilo koji OpenAI-kompatibilan API)
```

Provajderi se biraju kroz `QuizService` koji pokušava redom dok ne uspe:

```
Korisnik izabere "auto"
  → Ollama (ako je dostupan)
  → Groq (ako API key postoji)
  → DeepSeek (ako API key postoji)
  → Claude (ako API key postoji)
  → OpenAI (ako API key postoji - fallback)
```

---

*Dokumentacija kreirana: 2026-06-03*
*Verzija: 1.0.0*
