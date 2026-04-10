---
name: ai-learning-skills
description: |
  AI Learning Skills - Automatska detekcija tipa dokumenta, generisanje prompt šablona i integracija sa quiz sistemom.
  Koristi ovaj skill kada korisnik želi da: 
  - Detektuje tip dokumenta (legal, medical, technical, academic, textbook, general) iz teksta ili PDF chunk-ova
  - Generiše specijalizovani prompt šablon za quiz generisanje na osnovu tipa dokumenta
  - Koristi skill_detect_and_get_template() za integraciju sa quiz sistemom
  - Na osnovu chunk-ova generiše pitanja za quiz
  - Detektuje kategoriju dokumenta i prima odgovarajući prompt template za generisanje pitanja
 Make sure to use this skill whenever the user asks about skills, document type detection, quiz templates, quiz generation from documents, or integrating skills with the quiz system.
---

# AI Learning Skills

Skill sistem za automatsku detekciju tipa dokumenta, generisanje prompt šablona i integraciju sa quiz sistemom.

## Šta skill radi

Ovaj skill omogućava:
1. **Automatsku detekciju tipa dokumenta** - Na osnovu sadržaja (tekst, chunks) ili naslova
2. **Generisanje prompt šablona** - Za različite tipove dokumenata (legal, medical, technical, academic, textbook, general)
3. **Integraciju sa Quiz sistemom** - Detektovan tip dokumenta se koristi za generisanje pitanja

## Korišćenje

### Osnovni import

```python
from app.services.skills import SkillService, SkillDetector

# Kreiraj instancu
skill_service = SkillService()
```

### Detekcija tipa dokumenta

```python
# Detekcija iz teksta
detector = SkillDetector()
result = detector.analyze_text("Contractor agreement between parties...")
# Returns: {"category": "legal", "confidence": 85.0, "scores": {...}}

# Detekcija iz chunks-a
result = detector.detect_from_chunks(chunks)
# chunks je lista stringova iz PDF-a
```

### Get template za Quiz

```python
# Detekcija + vraćanje template-a
result = skill_service.detect_and_get_template(text, title, chunks)
# Returns: {"template": {...}, "category": "legal", "confidence": 85.0}

# Template sadrži:
# - prompt_template: str (glavni prompt za AI)
# - rules: dict (pravila za generisanje pitanja)
# - category: str
```

### Integracija sa QuizService

```python
# Detektovana kategorija -> Quiz prompt
service = SkillService()
result = service.detect_and_get_template(document_text)

category = result["category"]
template = result["template"]

# Koristi template za quiz generisanje
quiz_prompt = template["prompt_template"]
quiz_rules = template.get("rules", {})

#Quiz rules sadrži:
# - difficulty: "easy", "medium", "hard"
# - question_types: ["multiple_choice", "true_false", "fill_blank"]
# - num_questions: int
# - focus_areas: list
```

## Dostupne kategorije

| Kategorija | Opis |
|------------|------|
| legal | Pravni dokumenti, ugovori, zakoni |
| medical | Medicinska dokumentacija |
| technical | Tehnički priručnici, API dokumentacija |
| academic | Akademski radovi, istraživanja |
| textbook | Udžbenici, nastavni materijali |
| general | Opšti dokumenti, članci |

## Tipovi inputa

### 1. Detekcija iz teksta
```python
text = " Ovaj ugovor predstavlja sporazum između strana..."
result = detector.analyze_text(text)
```

### 2. Detekcija iz naslova
```python
title = "Ugovor o prodaji"
result = detector.detect_from_title(title)
```

### 3. Detekcija iz PDF chunk-ova
```python
chunks = ["Page 1: Chapter 1...", "Page 2: Chapter 2..."]
result = detector.detect_from_chunks(chunks)
```

## Izlaz (Output format)

```python
{
    "category": "legal",           # Detektovana kategorija
    "confidence": 85.0,           # Confidence score (0-100)
    "template": {
        "name": "Legal Document Processor",
        "prompt_template": "You are a legal document analyzer...",
        "rules": {
            "difficulty": "medium",
            "question_types": ["multiple_choice", "true_false"],
            "num_questions": 10,
            "focus_areas": ["definitions", "obligations", "deadlines"]
        }
    },
    "scores": {
        "legal": 85.0,
        "technical": 10.0,
        "medical": 0.0,
        "academic": 0.0,
        "textbook": 0.0,
        "general": 15.0
    }
}
```

## Primeri korišćenja

### Primer 1: Kreiranje Quiz-a iz PDF

```python
from app.services.skills import SkillService

service = SkillService()

# Tekst iz PDF dokumenta
pdf_text = open("document.txt").read()

# Detektovan tip + template
result = service.detect_and_get_template(pdf_text)

print(f"Detektovan tip: {result['category']}")
print(f"Confidence: {result['confidence']}%")
print(f"Prompt: {result['template']['prompt_template'][:100]}...")
print(f"Rules: {result['template']['rules']}")
```

### Primer 2: Detekcija sa više chunk-ova

```python
chunks = [
    "§1. DEFINITIONS",
    "For purposes of this Agreement, 'Contractor' means...",
    "§2. SCOPE OF WORK",
    "The Contractor shall provide the following services..."
]

detector = SkillDetector()
result = detector.detect_from_chunks(chunks)

# Aggregate rezultat iz svih chunk-ova
print(f"Final category: {result['category']}")
print(f"Confidence: {result['confidence']}")
```

### Primer 3: Integracija sa Quiz Service

```python
from app.services.skills import SkillService
from app.services.quiz import QuizService

skill_service = SkillService()
quiz_service = QuizService()

# Tekst dokumenta
document_text = load_document_text(document_id)

# Detekcija tipa
skill_result = skill_service.detect_and_get_template(document_text)

# Quiz generisanje sa detektovanim skill-om
quiz_result = quiz_service.create_quiz_from_document(
    db=db,
    document_id=document_id,
    title="Quiz iz dokumenta",
    num_questions=skill_result["template"]["rules"]["num_questions"],
    subject_area=skill_result["category"]  # Koristi detektovanu kategoriju
)
```

## Dostupne funkcije

### SkillDetector
- `analyze_text(text)` - Detekcija iz teksta
- `detect_from_chunks(chunks)` - Detekcija iz chunk-ova
- `detect_from_title(title)` - Detekcija iz naslova
- `get_category_confidence(text, category)` - Confidence za specifičnu kategoriju

### SkillService
- `detect_and_get_template(text, title, chunks)` - Detekcija + template
- `get_prompt_for_document(text, title)` - Samo prompt
- `get_rules_for_document(text)` - Samo pravila
- `detect_category(text)` - Samo kategorija
- `get_detection_details(text)` - Svi detailji

### Templates
- `get_template(name)` - Template po imenu
- `get_template_by_category(category)` - Template po kategoriji
- `get_all_templates()` - Svi templates

## Napomene

- Confidence threshold je podesiv (default: 50)
- Ako confidence < threshold, vraća "general" kategoriju
- Detekcija iz chunks-ova daje bolje rezultate za duže dokumente
- Quiz generisanje koristi detektovanu kategoriju kao subject_area

## Zavisnosti

- `app.services.skills.models` - Skill modeli i keywords
- `app.services.skills.detector` - SkillDetector
- `app.services.skills.service` - SkillService
- `app.services.skills.templates` - Template sistem
- `app.services.quiz` - QuizService (za integraciju)

## Reference

- Detaljnije u `app/services/skills/` direktorijumu
- Testovi u `tests/test_skills_*.py`
- Dokumentacija: `Detaljan_Plan_ReorganizacijeIntegracijeMCPservera_skilova.md`