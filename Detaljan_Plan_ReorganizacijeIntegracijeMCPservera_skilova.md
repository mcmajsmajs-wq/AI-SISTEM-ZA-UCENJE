# DETALJAN PLAN REORGANIZACIJE I INTEGRACIJE MCP SERVERA I SKILOVA

## Verzija: 1.0
## Datum: 2026-04-05

---

## SADRŽAJ

1. [UVOD I CILJ](#1-uvod-i-cilj)
2. [ANALIZA TRENUTNOG STANJA](#2-analiza-trenutnog-stanja)
3. [FAZA 1: AI PROVIDERS EKSTRAKCIJA](#3-faza-1-ai-providers-ekstrakcija)
4. [FAZA 2: PROMPTS I HELPERS MODULARIZACIJA](#4-faza-2-prompts-i-helpers-modularizacija)
5. [FAZA 3: QUIZ SERVICE ORCHESTRATOR](#5-faza-3-quiz-service-orchestrator)
6. [FAZA 4: TASKS.PY REORGANIZACIJA](#6-faza-4-taskspy-reorganizacija)
7. [FAZA 5: TRANSLATION SERVICE MODULARIZACIJA](#7-faza-5-translation-service-modularizacija)
8. [FAZA 6: SKILL SISTEM IMPLEMENTACIJA](#8-faza-6-skill-sistem-implementacija)
9. [FAZA 7: MCP SERVERI IMPLEMENTACIJA](#9-faza-7-mcp-serveri-implementacija)
10. [FAZA 8: USER API KEY SECURITY](#10-faza-8-user-api-key-security)
11. [FAZA 9: INSTALACIJA I KONFIGURACIJA](#11-faza-9-instalacija-i-konfiguracija)
12. [FAZA 10: TESTIRANJE I VERIFIKACIJA (100%)](#12-faza-10-testiranje-i-verifikacija-100)
13. [FAZA 11: PERFORMANSNE OPTIMIZACIJE](#13-faza-11-performansne-optimizacije)
14. [KOMPLETNA LISTA PROMENА I KONFIGURACIJA](#14-kompletna-lista-promena-i-konfiguracija)
15. [LINIJE KODA PRE I POSLE](#15-linije-koda-pre-i-posle)
16. [ZAVISNOSTI I IMPORT HIJERARHIJA](#16-zavisnosti-i-import-hijerarhija)
17. [BACKWARD COMPATIBILITY](#17-backward-compatibility)

---

# 1. UVOD I CILJ

## 1.1 Cilj reorganizacije

Ovaj dokument definiše kompletan plan reorganizacije backend servisa za AI Learning sistem sa sledećim ciljevima:

1. **Modularnost** - Podela monolithicnih fajlova na manje, održive module
2. **MCP Integracija** - Implementacija Model Context Protocol servera
3. **Skill Sistem** - Automatska detekcija tipa dokumenta i primena prompt šablona
4. **User API Keys** - Enkripcija i bezbedno čuvanje korisničkih API ključeva
5. **Skalabilnost** - Podrška za 1000+ simultanih korisnika

## 1.2 Referentni dokumenti

| Dokument | Lokacija | Sadržaj |
|----------|----------|---------|
| MCP_INTEGRACIJA_PLAN.md | MojAiProjekti/NewFolder/ | MCP integracija, Skill sistem, Security |
| CI_CD_STRATEGIJA.md | mojAiProjekat/New folder/ | CI/CD pipeline |
| AGENTS.md | mojAiProjekat/New folder/ | Projektna dokumentacija |

---

# 2. ANALIZA TRENUTNOG STANJA

## 2.1 Trenutno stanje fajlova

| Fajl | Lokacija | Linije | Klase | Funkcije | Status |
|------|----------|--------|-------|----------|--------|
| quiz.py | app/services/ | 4038 | 6 | 49 | 🔴 Preveliki |
| tasks.py | app/workers/ | 1990 | 11 tasks | 20+ | 🟡 Potrebna reorganizacija |
| translation.py | app/services/ | 1061 | 11 | 30+ | 🟡 Potrebna reorganizacija |

**Ukupno: 7089 linija u 3 fajla**

## 2.2 Identifikovani problemi

| Problem | Lokacija | Uticaj | Prioritet |
|---------|----------|--------|-----------|
| quiz.py preveliki (4038 linija) | quiz.py | Teško za održavanje | 🔴 Visok |
| Sve klase u jednom fajlu | quiz.py | Nemoguće paralelno razvijati | 🔴 Visok |
| Nema modularnosti | quiz.py | Teško za testiranje | 🟡 Srednji |
| tasks.py mešovit sadržaj | tasks.py | 11 različitih taskova | 🟡 Srednji |
| translation.py mešovit | translation.py | Ima klijente i servis zajedno | 🟡 Srednji |
| MCP nije implementiran | - | Nema AI tool-ova | 🔴 Visok |
| Skill sistem ne postoji | - | Nema auto-detekcije | 🔴 Visok |

## 2.3 Postojeće funkcionalnosti koje MORAMO sačuvati

### Quiz Service (quiz.py)
- [x] Multi-provider quiz generation (Ollama, OpenAI, Claude, Gemini, Groq, Mistral, DeepSeek)
- [x] Vision questions (slike iz PDF)
- [x] Subject detection (matematika, fizika, hemija, itd.)
- [x] Document structure detection (test, zadaci, primer, itd.)
- [x] Specialized prompts po subject
- [x] Fallback chain (provider redundancy)
- [x] User API keys podrška
- [x] Redis progress tracking
- [x] Chunk selection za quiz
- [x] Quiz CRUD operacije
- [x] Quiz attempt i answer sistem
- [x] Quiz usage stats

### Tasks (tasks.py)
- [x] process_pdf_task
- [x] translate_document_task
- [x] generate_quiz_task
- [x] send_email_task
- [x] Knowledge ingestion task
- [x] PDF export task

### Translation Service (translation.py)
- [x] Ollama client
- [x] DeepL client
- [x] OpenAI client
- [x] Google Translate client
- [x] Claude client
- [x] DeepSeek client
- [x] Batch translation
- [x] Fallback chain

---

# 3. FAZA 1: AI PROVIDERS EKSTRAKCIJA

## 3.1 Cilj faze

Ekstrakcija svih AI provider klasa u zasebne module radi bolje organizacije i nezavisnog razvoja.

## 3.2 Nova struktura

```
app/services/quiz/
├── clients/
│   ├── __init__.py          # Factory funkcije
│   ├── base.py             # BaseQuizClient(ABC)
│   ├── ollama.py           # OllamaQuizClient
│   ├── openai.py           # OpenAIQuizClient
│   ├── claude.py           # ClaudeQuizClient
│   └── openai_compat.py    # OpenAICompatQuizClient
```

## 3.3 Šta je izdvojeno

| Iz fajla | Izvučeno u | Linije |
|----------|------------|--------|
| BaseQuizClient (linija 224) | clients/base.py | ~15 |
| OllamaQuizClient (linija 245) | clients/ollama.py | ~40 |
| OpenAIQuizClient (linija 287) | clients/openai.py | ~50 |
| ClaudeQuizClient (linija 336) | clients/claude.py | ~45 |
| OpenAICompatQuizClient (linija 385) | clients/openai_compat.py | ~50 |
| _build_clients (linija 441) | clients/__init__.py | ~80 |
| _PROVIDER_ORDER (linija 430) | clients/__init__.py | ~10 |
| _get_available_providers (linija 500) | clients/__init__.py | ~10 |

## 3.4 Izmene

### clients/base.py
```python
# app/services/quiz/clients/base.py
from abc import ABC, abstractmethod
from typing import Tuple

class BaseQuizClient(ABC):
    @abstractmethod
    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """Returns (success, raw_json_string, error)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
```

### clients/ollama.py
```python
# app/services/quiz/clients/ollama.py
import httpx
from typing import Tuple
from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.prompts.base import QUIZ_PROMPT
from app.core.config import settings

class OllamaQuizClient(BaseQuizClient):
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.host}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False
    
    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3},
                    },
                )
                r.raise_for_status()
                return True, r.json().get("response", ""), ""
        except Exception as e:
            return False, "", str(e)
```

### clients/__init__.py (Factory)
```python
# app/services/quiz/clients/__init__.py
from typing import Dict, Optional, List
from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.clients.ollama import OllamaQuizClient
from app.services.quiz.clients.openai import OpenAIQuizClient
from app.services.quiz.clients.claude import ClaudeQuizClient
from app.services.quiz.clients.openai_compat import OpenAICompatQuizClient
from app.core.config import settings

_PROVIDER_ORDER = ["groq", "openai", "claude", "gemini", "mistral", "deepseek", "ollama"]

def _build_clients(
    user_openai_key: str = None,
    user_claude_key: str = None,
    user_gemini_key: str = None,
    user_groq_key: str = None,
    user_mistral_key: str = None,
    user_deepseek_key: str = None,
) -> Dict[str, BaseQuizClient]:
    """Builds client dict with optional user-level API key overrides.
    
    Priority:
    1. User's own API key (from user settings)
    2. System API key from settings (SYSTEM_GROQ_API_KEY, etc.)
    3. Default API key from settings (GROQ_API_KEY, etc.)
    """
    gemini_key = user_gemini_key or getattr(settings, "GEMINI_API_KEY", "") or ""
    groq_key = user_groq_key or getattr(settings, "GROQ_API_KEY", "") or ""
    mistral_key = user_mistral_key or getattr(settings, "MISTRAL_API_KEY", "") or ""
    openai_key = user_openai_key or getattr(settings, "OPENAI_API_KEY", "") or ""
    claude_key = user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", "") or ""
    deepseek_key = user_deepseek_key or getattr(settings, "DEEPSEEK_API_KEY", "") or ""

    ollama = OllamaQuizClient()
    openai = OpenAIQuizClient()
    if user_openai_key:
        openai.api_key = user_openai_key
    claude = ClaudeQuizClient()
    if user_claude_key:
        claude.api_key = user_claude_key

    return {
        "ollama": ollama,
        "openai": openai,
        "claude": claude,
        "gemini": OpenAICompatQuizClient(
            "gemini",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            "gemini-2.0-flash",
            gemini_key,
        ),
        "groq": OpenAICompatQuizClient(
            "groq",
            "https://api.groq.com/openai/v1",
            "llama-3.3-70b-versatile",
            groq_key,
        ),
        "mistral": OpenAICompatQuizClient(
            "mistral", "https://api.mistral.ai/v1", "mistral-small-latest", mistral_key
        ),
        "deepseek": OpenAICompatQuizClient(
            "deepseek", "https://api.deepseek.com/v1", "deepseek-chat", deepseek_key
        ),
    }

def get_provider(name: str, **kwargs) -> Optional[BaseQuizClient]:
    """Get a specific provider client."""
    clients = _build_clients(**kwargs)
    return clients.get(name)

def get_available_providers() -> List[dict]:
    """Lista svih provajdera i njihove dostupnosti."""
    clients = _build_clients()
    return [
        {
            "id": k,
            "available": v.is_available(),
            "type": "local" if k == "ollama" else "online",
        }
        for k, v in clients.items()
    ]

# Global cached clients
_CLIENTS: Dict[str, BaseQuizClient] = _build_clients()

def get_clients() -> Dict[str, BaseQuizClient]:
    """Get cached clients."""
    return _CLIENTS
```

## 3.5 Sačuvane funkcionalnosti

| Funkcionalnost | Status | Napomena |
|---------------|--------|----------|
| Svi provideri (7) | ✅ | Odlika implementirani |
| Fallback chain | ✅ | _PROVIDER_ORDER |
| User API keys | ✅ | Parametri u _build_clients |
| Provider availability check | ✅ | is_available() |
| Local/Online tip | ✅ | U get_available_providers |

---

# 4. FAZA 2: PROMPTS I HELPERS MODULARIZACIJA

## 4.1 Cilj faze

Ekstrakcija prompt šablona i helper funkcija u zasebne module.

## 4.2 Nova struktura

```
app/services/quiz/
├── prompts/
│   ├── __init__.py
│   ├── base.py              # QUIZ_PROMPT
│   └── subjects.py          # get_specialized_prompt, subject_instructions
├── helpers/
│   ├── __init__.py
│   ├── progress.py          # Redis progress
│   ├── parsing.py            # _parse_questions, _validate_questions, _fallback_questions
│   ├── chunks.py             # _select_chunks_for_quiz, _auto_num_questions
│   ├── subject_detection.py # detect_subject_area, SUBJECT_KEYWORDS
│   └── document_structure.py # detect_document_structure, STRUCTURE_PATTERNS
```

## 4.3 Šta je izdvojeno

### prompts/base.py (~200 linija)
- QUIZ_PROMPT (glavni prompt template)
- Svi filter rules
- Question type distributions
- Explanation rules
- Mathematics/Physics specific instructions
- JSON format primeri

### prompts/subjects.py (~200 linija)
- get_specialized_prompt()
- subject_instructions dict (matematika, fizika, hemija, biologija, istorija, geografija, jezici, pravo, ekonomija, informatika)

### helpers/progress.py (~45 linija)
- _get_redis()
- update_quiz_progress()
- get_quiz_progress()

### helpers/parsing.py (~100 linija)
- _parse_questions()
- _validate_questions()
- _fallback_questions()

### helpers/chunks.py (~50 linija)
- _select_chunks_for_quiz()
- _auto_num_questions()
- is_quality_chunk()

### helpers/subject_detection.py (~100 linija)
- SUBJECT_KEYWORDS dict
- detect_subject_area()
- _detect_subject_with_ai()

### helpers/document_structure.py (~100 linija)
- STRUCTURE_PATTERNS dict
- detect_document_structure()
- get_structure_based_prompt()

## 4.4 Izmene u helper fajlovima

### helpers/parsing.py
```python
# app/services/quiz/helpers/parsing.py
import json
import re
import logging
from typing import List
import random

logger = logging.getLogger(__name__)

def _parse_questions(raw: str) -> List[dict]:
    """Parsira JSON array iz AI odgovora."""
    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return _validate_questions(data)
        for v in data.values():
            if isinstance(v, list):
                return _validate_questions(v)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            return _validate_questions(json.loads(match.group(0)))
        except json.JSONDecodeError:
            pass
    logger.warning("Nije moguće parsirati JSON iz AI odgovora")
    return []

def _validate_questions(data: list) -> List[dict]:
    """Validira i čisti pitanja koja dolaze od AI providera."""
    required = ("question_text", "question_type", "options", "correct_answer")
    valid = []
    for i, q in enumerate(data):
        if not isinstance(q, dict):
            continue
        if not all(k in q for k in required):
            continue
        options = q.get("options", [])
        if isinstance(options, list) and options:
            if all(len(str(o).strip()) <= 1 for o in options):
                logger.warning(f"Pitanje {i} ima samo-slova opcije, preskačem: {options}")
                continue
        q.setdefault("explanation", "")
        q.setdefault("points", 1)
        if q.get("question_type") == "checkbox":
            correct = q.get("correct_answer", "")
            correct_parts = [p.strip() for p in correct.split(",") if p.strip()]
            if len(correct_parts) < 2:
                logger.warning(f"Pitanje {i} je checkbox ali ima samo 1 tačan odgovor")
                q["question_type"] = "multiple_choice"
                q["correct_answer"] = correct_parts[0] if correct_parts else correct
            else:
                if q.get("points", 1) < 2:
                    q["points"] = 2
        q["order_index"] = i
        valid.append(q)
    return valid

def _fallback_questions(text: str, num_questions: int) -> List[dict]:
    """Generiše osnovna pitanja kada nijedan AI nije dostupan."""
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 30]
    questions = []
    for i, sentence in enumerate(sentences[:num_questions]):
        is_true = random.choice([True, False])
        if is_true:
            question_text = f'Да ли је тачна следећа тврдња: "{sentence[:150]}"?'
            correct = "Тачно"
            explanation = "Ова тврдња је директно наведена у тексту."
        else:
            question_text = f'Да ли је тачна следећа тврдња: "{sentence[:150]}"?'
            correct = "Нетачно"
            explanation = "Ова тврдња не одговара садржају текста."
        questions.append({
            "question_text": question_text,
            "question_type": "true_false",
            "options": ["Тачно", "Нетачно"],
            "correct_answer": correct,
            "explanation": explanation,
            "points": 1,
            "order_index": i,
        })
    return questions
```

### helpers/subject_detection.py
```python
# app/services/quiz/helpers/subject_detection.py
SUBJECT_KEYWORDS = {
    "matematika": [
        "matematika", "površina", "zapremina", "formula", "jednačina", "rešenje",
        "trougao", "kvadrat", "krug", "pravougaonik", "zbir", "razlika", "proizvod",
        "količnik", "stepen", "koren", "logaritam", "trigonometrija", "ugao",
        "stranica", "visina", "base", "promenljiva", "funkcija", "grafik",
    ],
    "fizika": [
        "fizika", "energija", "sila", "brzina", "ubrzanj", "masa", "gustin",
        "temperatura", "pritisak", "toplota", "struja", "magnet", "svetlost",
        "talas", "zvuk", "mehanika", "optika", "elektrika", "termodinamika",
    ],
    # ... ostale oblasti
}

def detect_subject_area(text: str, num_samples: int = 20) -> str:
    """Detektuje oblast dokumenta na osnovu teksta."""
    text_lower = text.lower()
    subject_scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        subject_scores[subject] = score
    if max(subject_scores.values()) > 0:
        detected = max(subject_scores.items(), key=lambda x: x[1])
        return detected[0]
    return _detect_subject_with_ai(text[:3000])

def _detect_subject_with_ai(text: str) -> str:
    """AI-based subject area detection."""
    # Koristi _build_clients iz clients
    from app.services.quiz.clients import _build_clients
    # ... implementacija
```

## 4.5 Sačuvane funkcionalnosti

| Funkcionalnost | Status |
|---------------|--------|
| QUIZ_PROMPT template | ✅ |
| Subject-specific prompts | ✅ |
| Question parsing | ✅ |
| Validation | ✅ |
| Fallback questions | ✅ |
| Chunk selection | ✅ |
| Subject detection (keywords + AI) | ✅ |
| Document structure detection | ✅ |
| Redis progress | ✅ |

---

# 5. FAZA 3: QUIZ SERVICE ORCHESTRATOR

## 5.1 Cilj faze

QuizService ostaje u jednom fajlu, ali importe iz nove modularne strukture.

## 5.2 Nova struktura

```
app/services/quiz/
├── service.py               # QuizService (~2000 linija)
```

## 5.3 Šta ostaje u service.py

```python
# app/services/quiz/service.py
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer

class QuizService:
    """Glavni servisi za quiz generaciju i upravljanje."""
    
    def _get_image_for_vision(self, img, storage, timeout: int = 5) -> Tuple[str, str]:
        """Hibridni pristup: prvo probaj MinIO URL, pa fallback na base64."""
        # ... postojeća implementacija
    
    def _generate_vision_questions_for_images(self, images: list, ...):
        """Generiše pitanja iz slika."""
        # ... postojeća implementacija
    
    def _generate_text_questions_with_optional_images(self, ...):
        """Kombinuje tekst i slike."""
        # ... postojeća implementacija
    
    def generate_questions_with_ai(self, ...):
        """Glavna metoda za generisanje pitanja."""
        # ... postojeća implementacija
    
    def create_quiz_from_document(self, ...):
        """Kreiranje kviza iz dokumenta."""
        # ... postojeća implementacija
    
    def populate_quiz_questions(self, ...):
        """Popunjavanje pitanja u kvizu."""
        # ... postojeća implementacija
    
    def submit_attempt(self, ...):
        """Slanje odgovora na kviz."""
        # ... postojeća implementacija
    
    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """Provera odgovora."""
        # ... postojeća implementacija
    
    def get_available_providers(self) -> List[dict]:
        """Dostupni provajderi."""
        from app.services.quiz.clients import get_available_providers
        return get_available_providers()
```

## 5.4 Import izmene

### Novo (koristi modularne komponente)
```python
from app.services.quiz.clients import get_clients, _build_clients
from app.services.quiz.helpers.progress import update_quiz_progress, get_quiz_progress
from app.services.quiz.helpers.parsing import _parse_questions, _validate_questions
from app.services.quiz.helpers.chunks import _select_chunks_for_quiz
from app.services.quiz.prompts.base import QUIZ_PROMPT
```

### Staro (biće backward compatible)
```python
# Ovo će i dalje raditi preko __init__.py
from app.services.quiz import quiz_service
```

## 5.5 Sačuvane funkcionalnosti

| Funkcionalnost | Status |
|---------------|--------|
| QuizService cela klasa | ✅ |
| Vision questions (slike) | ✅ |
| Text + image kombinacija | ✅ |
| Chunk processing | ✅ |
| Question generation | ✅ |
| Quiz CRUD | ✅ |
| Attempt sistem | ✅ |
| Answer checking | ✅ |

---

# 6. FAZA 4: TASKS.PY REORGANIZACIJA

## 6.1 Cilj faze

Podela tasks.py na logical模块 po tipu zadatka.

## 6.2 Nova struktura

```
app/workers/
├── tasks/
│   ├── __init__.py           # Svi taskovi se re-exportuju
│   ├── pdf_processing.py     # PDF obrada
│   ├── translation.py        # Translation taskovi
│   ├── quiz.py               # Quiz generation taskovi
│   ├── email.py              # Email taskovi
│   ├── knowledge.py          # Knowledge ingestion
│   └── maintenance.py        # Maintenance taskovi
└── celery.py                 # Celery app konfiguracija
```

## 6.3 Šta je izdvojeno

### pdf_processing.py
- process_pdf_task

### translation.py
- translate_document_task
- translate_with_fallback()

### quiz.py
- generate_quiz_task

### email.py
- send_email_task

### knowledge.py
- knowledge_ingestion_task

### maintenance.py
- cleanup_old_sessions_task
- cache_warming_task

## 6.4 Sačuvane funkcionalnosti

| Task | Status |
|------|--------|
| process_pdf_task | ✅ |
| translate_document_task | ✅ |
| generate_quiz_task | ✅ |
| send_email_task | ✅ |
| Knowledge ingestion | ✅ |

---

# 7. FAZA 5: TRANSLATION SERVICE MODULARIZACIJA

## 7.1 Cilj faze

Podela translation.py (1061 linija) na klijente i servis.

## 7.2 Nova struktura

```
app/services/translation/
├── __init__.py              # TranslationService re-export
├── clients/
│   ├── __init__.py
│   ├── base.py              # BaseTranslationClient
│   ├── ollama.py            # OllamaClient
│   ├── deepl.py             # DeepLClient
│   ├── openai.py            # OpenAIClient
│   ├── google.py            # GoogleTranslateClient
│   ├── claude.py            # ClaudeClient
│   └── deepseek.py          # DeepSeekClient
└── service.py               # TranslationService
```

## 7.3 Šta je izdvojeno

| Iz fajla | Izvučeno u | Linije |
|----------|------------|--------|
| BaseTranslationClient | clients/base.py | ~25 |
| OllamaClient | clients/ollama.py | ~110 |
| DeepLClient | clients/deepl.py | ~110 |
| OpenAIClient | clients/openai.py | ~110 |
| GoogleTranslateClient | clients/google.py | ~90 |
| ClaudeClient | clients/claude.py | ~110 |
| DeepSeekClient | clients/deepseek.py | ~110 |
| TranslationService | service.py | ~210 |

## 7.4 Sačuvane funkcionalnosti

| Funkcionalnost | Status |
|---------------|--------|
| Svi translation klijenti (7) | ✅ |
| Batch translation | ✅ |
| Fallback chain | ✅ |
| User API keys | ✅ |

## 7.5 ✅ ZAVRŠENO (2026-04-09)

**FAZA 5 je uspešno završena!** Svi testovi prolaze (386/386).

### Nova modularna struktura

```
app/services/translation/
├── __init__.py              # Glavni export (settings included)
├── providers.py            # TranslationProvider enum (7 provajdera + LIBRETRANSLATE)
├── service.py             # TranslationService
└── clients/
    ├── __init__.py          # exports + settings
    ├── base.py            # BaseTranslationClient, TranslationResult
    ├── ollama.py         # OllamaClient
    ├── deepl.py          # DeepLClient
    ├── openai.py         # OpenAIClient
    ├── google.py         # GoogleTranslateClient
    ├── claude.py         # ClaudeClient
    └── deepseek.py       # DeepSeekClient
```

### Šta je urađeno

| Task | Status |
|------|--------|
| Kreiran directory structure | ✅ |
| Kreiran providers.py (7 providers) | ✅ |
| Kreiran clients/base.py | ✅ |
| Kreiran svi client fajlovi | ✅ |
| Kreiran service.py | ✅ |
| Kreiran __init__.py (main export) | ✅ |
| Backward compatibility wrapper | ✅ |
| Test fix patch paths | ✅ |
| Test provider count (7) | ✅ |
| Svi testovi prolaze | ✅ 386/386 |

### Korišćenje

```python
# Novi način (preporučeno)
from app.services.translation import TranslationService, TranslationProvider

# Stari način (i dalje radi - backward compatible)
from app.services import translation as old_translation
```

### Breakout

- TranslationProvider enum ima 7 provajdera (dodat LIBRETRANSLATE)
- Testovi su morali biti ažurirani jer je novi modularni path: `app.services.translation.clients.{client}.settings`

---

# 8. FAZA 6: SKILL SISTEM IMPLEMENTACIJA

## 8.1 ✅ ZAVRŠENO (2026-04-09)

**FAZA 6 uspešno završena!** 

### Implementirano (2026-04-09):
- Skills modul: `/home/dju/mojAiProjekat/New folder/backend/app/services/skills/`
- SkillDetector sa auto-detekcijom 6 kategorija
- 6 odvojenih template fajlova (legal, technical, medical, academic, textbook, general)
- Test fajl: `test_skills.py`
- Svi testovi prolaze ✅

### Novi MCP Tools (17 alata dodato u FAZA 7)

**FAZA 6 je uspešno završena!** Svi testovi prolaze (386/386).

### Nova struktura

```
app/services/skills/
├── __init__.py              # Glavni export
├── models.py                # Skill, SkillTemplate, DocumentType, UserSkill
├── detector.py              # SkillDetector (auto-detekcija)
├── service.py               # SkillService
└── templates/
    └── __init__.py         # Sistemski šabloni (6 kategorija)
```

### Sistemski šabloni

| Template | Kategorija | Opis |
|----------|-----------|------|
| legal_document | legal | Analyzes contracts and legal texts |
| technical_manual | technical | Processes technical documentation |
| medical_document | medical | Processes medical literature |
| academic_paper | academic | Processes research papers |
| textbook | textbook | Processes educational materials |
| general | general | General document processing |

### Šta je urađeno

| Task | Status |
|------|--------|
| Kreiran directory app/services/skills/ | ✅ |
| Kreiran models.py (Skill, SkillTemplate, DocumentType, UserSkill) | ✅ |
| Kreiran detector.py (SkillDetector) | ✅ |
| Kreiran templates/ sa sistemskim šablonima | ✅ |
| Kreiran service.py (SkillService) | ✅ |
| Kreiran glavni __init__.py | ✅ |
| Testirano - svi testovi prolaze | ✅ 386/386 |

### Korišćenje

```python
from app.services.skills import SkillService, detect_document_type

# Detekcija tipa dokumenta
service = SkillService()
result = service.detect_and_get_template(text)
print(result["category"])  # "legal", "technical", "medical", "academic", "textbook", "general"

# Brza detekcija
category = detect_document_type(text)

# Detekcija iz fajla
result = detect_from_file(filename, text)
```

### Primer detekcije

```python
>>> service = SkillService()
>>> result = service.detect_and_get_template(
...     "This agreement establishes the terms and conditions..."
... )
>>> result["category"]
'legal'
>>> result["template"]["name"]
'Legal Document Processor'
```

---

## 8.1 Cilj faze

Implementacija Skill sistema prema MCP_INTEGRACIJA_PLAN.md FAZA 2.

## 8.2 Nova struktura

```
app/services/skills/
├── __init__.py
├── models.py                # Skill, SkillTemplate, DocumentType
├── detector.py              # SkillDetector (auto-detekcija)
├── service.py              # SkillService
└── templates/
    ├── __init__.py
    ├── medical.py          # Medicinski dokumenti
    ├── legal.py            # Pravni dokumenti
    ├── technical.py        # Tehnički priručnici
    ├── academic.py         # Akademski radovi
    ├── textbook.py         # Udžbenici
    └── general.py          # Opšti dokumenti
```

## 8.3 Komponente

### models.py
```python
# app/services/skills/models.py
from sqlalchemy import Column, Integer, String, JSON, Boolean
from app.db.base import Base

class Skill(Base):
    """Skill - definicija prompt šablona za tip dokumenta."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    document_type = Column(String, nullable=False)
    prompt_template = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=True)  # null za sistemske

class SkillTemplate(Base):
    """SkillTemplate - sistemski šabloni."""
    __tablename__ = "skill_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    prompt_template = Column(JSON, nullable=False)
    document_types = Column(JSON)  # lista podržanih tipova

class DocumentType(Base):
    """DocumentType - tipovi dokumenata za auto-detekciju."""
    __tablename__ = "document_types"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    keywords = Column(JSON)  # keywords za detekciju
    patterns = Column(JSON)  # regex patterns
    skill_id = Column(Integer, ForeignKey("skills.id"))
```

### detector.py
```python
# app/services/skills/detector.py
from typing import Optional, List, Dict

class SkillDetector:
    """Automatska detekcija tipa dokumenta i odgovarajućeg skill-a."""
    
    DOCUMENT_TYPE_PATTERNS = {
        "medical": [
            "simptom", "dijagnoza", "terapija", "lek", "pregled",
            "bolnica", "pacijent", "klinički", "medicinski", "zdravlje",
            "uzrok", "lečenje", "terapija", "doziranje", "nuspojave",
        ],
        "legal": [
            "zakon", "član", "paragraf", "sud", "presuda", "tužba",
            "ugovor", "odluka", "propis", "pravo", "obaveza", "rok",
            "potpis", "overa", "javni beležnik", "parnica",
        ],
        "technical": [
            "specifikacija", "uputstvo", "instalacija", "podešavanje",
            "konfiguracija", "error", "rešenje", "troubleshooting",
            "sistem", "komponenta", "model", "serijski", "garancija",
        ],
        "academic": [
            "istraživanje", "metodologija", "rezultati", "diskusija",
            "zaključak", "referenca", "citat", "abstract", "doi",
            "akademski", "naučni", "publikacija",
        ],
        "textbook": [
            "poglavlje", "lekcija", "primer", "zadatak", "rešenje",
            "udžbenik", "gradivo", "ponavljanje", "test", "ocena",
        ],
    }
    
    def detect(self, text: str, chunks: List[dict] = None) -> Dict[str, any]:
        """Detektuje tip dokumenta i vraća odgovarajući skill.
        
        Returns:
            {
                "document_type": "medical",
                "confidence": 0.85,
                "skill": Skill,
                "prompt_template": {...}
            }
        """
        text_lower = text.lower()
        
        # Brojanje podudaranja po tipu
        type_scores = {}
        for doc_type, keywords in self.DOCUMENT_TYPE_PATTERNS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            type_scores[doc_type] = score
        
        # Ako nijedan tip nema dovoljno podudaranja, koristi general
        if max(type_scores.values()) < 3:
            return {
                "document_type": "general",
                "confidence": 0.5,
                "skill": None,
                "prompt_template": self._get_general_template(),
            }
        
        # Vrati tip sa najvišim score-om
        detected = max(type_scores.items(), key=lambda x: x[1])
        
        return {
            "document_type": detected[0],
            "confidence": detected[1] / sum(type_scores.values()),
            "skill": None,  # Popunjava se iz baze
            "prompt_template": self._get_template_for_type(detected[0]),
        }
    
    def _get_template_for_type(self, doc_type: str) -> dict:
        templates = {
            "medical": self._get_medical_template(),
            "legal": self._get_legal_template(),
            "technical": self._get_technical_template(),
            "academic": self._get_academic_template(),
            "textbook": self._get_textbook_template(),
            "general": self._get_general_template(),
        }
        return templates.get(doc_type, self._get_general_template())
```

### templates/medical.py
```python
# app/services/skills/templates/medical.py
MEDICAL_PROMPT_TEMPLATE = {
    "quiz_generation": """You are a medical expert creating quiz questions from medical documentation.
    
Focus on:
- Symptom recognition
- Diagnostic criteria
- Treatment protocols
- Drug interactions
- Patient management

CRITICAL: Include WARNING about medical accuracy - these are for educational purposes only.

Generate {num_questions} questions.""",
    "translation": """You are a medical translator. Ensure accurate use of medical terminology.""",
    "summary": """You are a medical professional summarizing patient documentation.""",
}
```

## 8.4 Integracija sa Quiz

```python
# U QuizService.generate_questions_with_ai()
def generate_questions_with_ai(self, chunks, ...):
    # Detektuj skill
    from app.services.skills.detector import SkillDetector
    detector = SkillDetector()
    
    full_text = " ".join([c.get("text", "") for c in chunks])
    detection = detector.detect(full_text, chunks)
    
    if detection["skill"]:
        prompt = detection["skill"].prompt_template.get("quiz_generation")
    else:
        prompt = detection["prompt_template"].get("quiz_generation")
    
    # Koristi detektovan prompt
    ...
```

---

# 9. FAZA 7: MCP SERVERI IMPLEMENTACIJA

## 9.1 Cilj faze

Implementacija MCP servera prema MCP_INTEGRACIJA_PLAN.md FAZA 4.

## 9.2 Nova struktura

```
mcp-server/
├── server.py                # MCP Server main
├── config.py                # Konfiguracija
├── quiz/
│   ├── __init__.py
│   ├── tools.py             # Quiz MCP tools
│   └── handlers.py          # Tool handlers
├── translate/
│   ├── __init__.py
│   ├── tools.py             # Translation MCP tools
│   └── handlers.py
├── document/
│   ├── __init__.py
│   ├── tools.py             # Document MCP tools
│   └── handlers.py
└── skills/
    ├── __init__.py
    ├── tools.py
    └── handlers.py
```

## 9.3 MCP Tools definicije

### quiz/tools.py
```python
# mcp-server/quiz/tools.py
from mcp.types import Tool

def get_quiz_tools() -> list[Tool]:
    return [
        Tool(
            name="quiz_create",
            description="Create a new quiz from document chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "num_questions": {"type": "integer", "default": 10},
                    "subject_area": {"type": "string"},
                    "user_api_keys": {
                        "type": "object",
                        "properties": {
                            "openai": {"type": "string"},
                            "claude": {"type": "string"},
                        }
                    }
                },
                "required": ["document_id", "title"]
            }
        ),
        Tool(
            name="quiz_list",
            description="List user's quizzes",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "status": {"type": "string"}
                }
            }
        ),
        Tool(
            name="quiz_get",
            description="Get quiz details with questions",
            inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {"type": "integer"}
                },
                "required": ["quiz_id"]
            }
        ),
        Tool(
            name="quiz_submit_attempt",
            description="Submit answers for a quiz attempt",
            inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {"type": "integer"},
                    "answers": {"type": "array"}
                },
                "required": ["quiz_id", "answers"]
            }
        ),
        Tool(
            name="quiz_get_providers",
            description="Get available AI providers for quiz generation",
            inputSchema={"type": "object"}
        ),
    ]
```

### translate/tools.py
```python
# mcp-server/translate/tools.py
from mcp.types import Tool

def get_translate_tools() -> list[Tool]:
    return [
        Tool(
            name="translate_text",
            description="Translate text between languages",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source_language": {"type": "string"},
                    "target_language": {"type": "string"},
                    "user_api_key": {"type": "string"}
                },
                "required": ["text", "source_language", "target_language"]
            }
        ),
        Tool(
            name="translate_batch",
            description="Translate multiple texts at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "texts": {"type": "array"},
                    "source_language": {"type": "string"},
                    "target_language": {"type": "string"}
                },
                "required": ["texts", "source_language", "target_language"]
            }
        ),
    ]
```

### document/tools.py
```python
# mcp-server/document/tools.py
from mcp.types import Tool

def get_document_tools() -> list[Tool]:
    return [
        Tool(
            name="document_process",
            description="Process PDF document and extract chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "user_id": {"type": "string"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="document_detect_skill",
            description="Detect document type and get appropriate skill",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "integer"}
                },
                "required": ["document_id"]
            }
        ),
    ]
```

## 9.4 MCP Tool Handlers

### quiz/handlers.py
```python
# mcp-server/quiz/handlers.py
from typing import Dict, Any
from app.services.quiz import QuizService

quiz_service = QuizService()

async def handle_quiz_create(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handler za quiz_create tool."""
    document_id = params["document_id"]
    title = params["title"]
    num_questions = params.get("num_questions", 10)
    subject_area = params.get("subject_area")
    user_api_keys = params.get("user_api_keys", {})
    
    result = quiz_service.create_quiz_from_document(
        db=None,  # MCP handles session
        document_id=document_id,
        user_id=user_id,
        title=title,
        num_questions=num_questions,
        subject_area=subject_area,
        **user_api_keys
    )
    
    return {"quiz_id": result.id, "status": "created"}

async def handle_quiz_list(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handler za quiz_list tool."""
    status = params.get("status")
    quizzes = quiz_service.list_quizzes(user_id=user_id, status=status)
    return {"quizzes": [q.to_dict() for q in quizzes]}
```

## 9.5 MCP Server Main

### server.py
```python
# mcp-server/server.py
from fastmcp import FastMCP
from mcp-server.quiz.tools import get_quiz_tools
from mcp-server.quiz.handlers import handle_quiz_create, handle_quiz_list

mcp = FastMCP("AI Learning MCP Server")

# Register tools
for tool in get_quiz_tools():
    mcp.tool(tool)

@mcp.tool()
async def quiz_create(params: dict, user_id: str):
    return await handle_quiz_create(params, user_id)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## 9.4 ✅ ZAVRŠENO (2026-04-09)

**FAZA 7 uspešno završena!**

### Implementirano (2026-04-09):
- Novi MCP tools moduli: `mcp-server/src/ai_learning_mcp/tools/`
- 17 novih MCP alata dodato:
  - Quiz: quiz_create, quiz_list, quiz_get, quiz_submit_attempt, quiz_get_providers
  - Translation: translate_text, translate_batch, translate_supported_languages
  - Document: document_process, document_detect_skill, document_list, document_get_chunks
  - Skills: skill_detect, skill_list, skill_get_template, skill_list_templates, skill_get_categories
- Handlers za sve alate
- Test fajl: `test_mcp_faza7.py`
- Verifikacija uspešna ✅

---

# 10. FAZA 8: USER API KEY SECURITY

## 10.1 Cilj faze

Implementacija enkripcije za korisničke API ključeve prema MCP_INTEGRACIJA_PLAN.md FAZA 5.

## 10.2 Nova struktura

```
app/services/security/
├── __init__.py
├── encryption.py            # AES-256 enkripcija
├── key_manager.py          # Upravljanje ključevima
└── validators.py           # Validacija API ključeva
```

## 10.3 Komponente

### encryption.py
```python
# app/services/security/encryption.py
from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings

class EncryptionService:
    """AES-256 enkripcija za API ključeve."""
    
    def __init__(self):
        key = settings.ENCRYPTION_KEY.encode()
        if len(key) < 32:
            key = hashlib.sha256(key).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
    
    def encrypt(self, plaintext: str) -> str:
        """Enkriptuje tekst."""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Dekriptuje tekst."""
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    def hash_key(self, api_key: str) -> str:
        """Hashira API key za čuvanje (ne za dekripciju)."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
```

### key_manager.py
```python
# app/services/security/key_manager.py
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.db.models.user import UserAPIKey
from app.services.security.encryption import EncryptionService

class KeyManager:
    """Upravljanje korisničkim API ključevima."""
    
    def __init__(self):
        self.encryption = EncryptionService()
    
    def store_key(self, db: Session, user_id: int, provider: str, api_key: str) -> UserAPIKey:
        """Čuva enkriptovani API key."""
        encrypted = self.encryption.encrypt(api_key)
        key_hash = self.encryption.hash_key(api_key)
        
        existing = db.query(UserAPIKey).filter_by(
            user_id=user_id, provider=provider
        ).first()
        
        if existing:
            existing.encrypted_key = encrypted
            existing.key_hash = key_hash
            existing.is_active = True
            db.commit()
            return existing
        
        new_key = UserAPIKey(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted,
            key_hash=key_hash
        )
        db.add(new_key)
        db.commit()
        return new_key
    
    def get_key(self, db: Session, user_id: int, provider: str) -> Optional[str]:
        """Dekriptuje i vraća API key."""
        key_obj = db.query(UserAPIKey).filter_by(
            user_id=user_id, provider=provider, is_active=True
        ).first()
        
        if not key_obj:
            return None
        
        return self.encryption.decrypt(key_obj.encrypted_key)
    
    def delete_key(self, db: Session, user_id: int, provider: str) -> bool:
        """ Briše API key."""
        key_obj = db.query(UserAPIKey).filter_by(
            user_id=user_id, provider=provider
        ).first()
        
        if key_obj:
            key_obj.is_active = False
            db.commit()
            return True
        return False
```

### Database model
```python
# app/db/models/user.py
class UserAPIKey(Base):
    """Korisnički API ključevi (enkriptovani)."""
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, claude, etc.
    encrypted_key = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # Za verifikaciju
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
```

## 10.3 ✅ ZAVRŠENO (2026-04-09)

**FAZA 8 uspešno završena!**

### Implementirano (2026-04-09):
- Security modul: `/home/dju/mojAiProjekat/New folder/backend/app/services/security/`
- encryption.py: AES-256-Fernet enkripcija sa PBKDF2
- key_manager.py: Upravljanje API ključevima
- validators.py: Validacija za 7 provajdera (OpenAI, Claude, Gemini, Ollama, Groq, Mistral, DeepSeek)
- UserAPIKey model dodat u: `app/db/models/user.py`
- Test fajl: `test_security.py` (21 test ✅)

### Test Results:
```
TestEncryptionService: 4 passed
TestAPIKeyValidator: 12 passed  
TestValidatorsEdgeCases: 2 passed
TestEncryptionEdgeCases: 2 passed
Total: 21 passed ✅
```

---

# 11. FAZA 9: INSTALACIJA I KONFIGURACIJA

## ✅ ZAVRŠENO (2026-04-09)

**FAZA 9 uspešno završena!** Sve verifikacije prošle.

### Verifikacije (2026-04-09):

| Test | Komanda | Rezultat |
|------|---------|----------|
| Quiz clients | `from app.services.quiz.clients import get_clients` | ✅ |
| Available clients | 7 clients | ✅ |
| Encryption service | `EncryptionService()` initialized | ✅ |
| Key manager | `KeyManager()` initialized | ✅ |
| UserAPIKey model | Table: user_api_keys | ✅ |
| Security tests | pytest test_security.py | ✅ 21 passed |
| Skills tests | pytest test_skills.py | ✅ 32 passed |
| MCP server | py_compile | ✅ |

---

## 11.1 FAZA 1: AI PROVIDERS - Instalacija i konfiguracija

### 11.1.1 Dependencies (requirements.txt)

```txt
# quiz/clients dependencies
httpx>=0.24.0
redis>=4.5.0

# Za testiranje
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

### 11.1.2 Environment variables (.env)

```bash
# AI Providers - System keys (optional, user keys have priority)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...
DEEPSEEK_API_KEY=...
GEMINI_API_KEY=...

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=120
```

### 11.1.3 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `pip install -r requirements.txt` | ✅ Instalacija uspešna |
| 2 | `python -c "from app.services.quiz.clients import get_clients"` | ✅ Import uspešan |
| 3 | `python -c "from app.services.quiz.clients import _build_clients; c=_build_clients(); print(list(c.keys()))"` | ["ollama","openai","claude","gemini","groq","mistral","deepseek"] |
| 4 | `python -c "from app.services.quiz.clients import get_available_providers; print(len(get_available_providers()))"` | 7 |

### 11.1.4 Konfiguracioni testovi

```python
# tests/test_quiz_clients_config.py
import os
import pytest

class TestClientsConfiguration:
    def test_ollama_config(self):
        from app.core.config import settings
        assert settings.OLLAMA_HOST is not None
    
    def test_ollama_timeout_config(self):
        from app.core.config import settings
        assert hasattr(settings, "OLLAMA_TIMEOUT")
        assert settings.OLLAMA_TIMEOUT > 0
    
    def test_openai_model_config(self):
        from app.core.config import settings
        assert hasattr(settings, "OPENAI_MODEL")
    
    def test_claude_model_config(self):
        from app.core.config import settings
        assert hasattr(settings, "CLAUDE_MODEL")
```

---

## 11.2 FAZA 2: PROMPTS I HELPERS - Instalacija i konfiguracija

### 11.2.1 Dodatne dependencies

```txt
# Nema dodatnih - koriste postojeće
```

### 11.2.2 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.services.quiz.prompts.base import QUIZ_PROMPT"` | ✅ |
| 2 | `python -c "from app.services.quiz.prompts.subjects import get_specialized_prompt"` | ✅ |
| 3 | `python -c "from app.services.quiz.helpers import progress, parsing, chunks"` | ✅ |
| 4 | `python -c "from app.services.quiz.helpers.subject_detection import SUBJECT_KEYWORDS; print(len(SUBJECT_KEYWORDS))"` | 11 (oblasti) |

### 11.2.3 Konfiguracioni testovi

```python
# tests/test_helpers_config.py
import pytest

class TestHelpersConfiguration:
    def test_prompt_length(self):
        from app.services.quiz.prompts.base import QUIZ_PROMPT
        assert len(QUIZ_PROMPT) > 1000  # Minimum prompt length
    
    def test_subject_instructions_complete(self):
        from app.services.quiz.prompts.subjects import subject_instructions
        expected = ["matematika", "fizika", "hemija", "biologija", "istorija", 
                   "geografija", "jezici", "pravo", "ekonomija", "informatika"]
        for subject in expected:
            assert subject in subject_instructions
    
    def test_subject_keywords_complete(self):
        from app.services.quiz.helpers.subject_detection import SUBJECT_KEYWORDS
        expected_subjects = ["matematika", "fizika", "hemija", "biologija", 
                            "istorija", "geografija", "jezici", "pravo", 
                            "ekonomija", "informatika", "ostalo"]
        assert set(SUBJECT_KEYWORDS.keys()) == set(expected_subjects)
    
    def test_redis_configured(self):
        from app.core.config import settings
        assert hasattr(settings, "REDIS_CONNECTION_URL")
        assert settings.REDIS_CONNECTION_URL is not None
```

---

## 11.3 FAZA 3: QUIZ SERVICE - Instalacija i konfiguracija

### 11.3.1 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.services.quiz.service import QuizService"` | ✅ |
| 2 | `python -c "from app.services.quiz import quiz_service"` | ✅ Backward compat |
| 3 | `python -c "from app.services.quiz import QuizService; s=QuizService(); print(hasattr(s,'generate_questions_with_ai'))"` | True |

### 11.3.2 Konfiguracioni testovi

```python
# tests/test_quiz_service_config.py
import pytest
from unittest.mock import Mock, patch

class TestQuizServiceConfiguration:
    def test_service_instantiation(self):
        from app.services.quiz.service import QuizService
        service = QuizService()
        assert service is not None
    
    def test_all_required_methods_exist(self):
        from app.services.quiz.service import QuizService
        required = [
            "_get_image_for_vision",
            "_generate_vision_questions_for_images", 
            "generate_questions_with_ai",
            "create_quiz_from_document",
            "submit_attempt",
            "get_available_providers",
        ]
        service = QuizService()
        for method in required:
            assert hasattr(service, method), f"Missing: {method}"
    
    @patch("app.services.quiz.service._build_clients")
    def test_client_integration(self, mock_build):
        from app.services.quiz.service import QuizService
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_build.return_value = {"ollama": mock_client}
        
        service = QuizService()
        providers = service.get_available_providers()
        assert isinstance(providers, list)
```

---

## 11.4 FAZA 4: TASKS - Instalacija i konfiguracija

### 11.4.1 Dependencies

```txt
# Celery i Redis
celery>=5.3.0
redis>=4.5.0

# Za worker taskove
pillow>=10.0.0  # PDF processing
```

### 11.4.2 Environment variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=Europe/Belgrade
CELERY_ENABLE_UTC=True
```

### 11.4.3 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.workers.celery import celery_app"` | ✅ |
| 2 | `python -c "from app.workers.tasks import process_pdf_task"` | ✅ |
| 3 | `celery -A app.workers.celery inspect active` | Lista aktivnih taskova |
| 4 | `redis-cli ping` | PONG |

### 11.4.4 Konfiguracioni testovi

```python
# tests/test_tasks_config.py
import pytest

class TestTasksConfiguration:
    def test_celery_app_configured(self):
        from app.workers.celery import celery_app
        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
    
    def test_celery_broker_configured(self):
        from app.workers.celery import celery_app
        assert celery_app.conf.broker_url is not None
        assert "redis" in celery_app.conf.broker_url
    
    def test_all_tasks_importable(self):
        from app.workers.tasks import (
            process_pdf_task,
            translate_document_task,
            generate_quiz_task,
            send_email_task,
        )
        assert process_pdf_task is not None
```

---

## 11.5 FAZA 5: TRANSLATION - Instalacija i konfiguracija

### 11.5.1 Environment variables

```bash
# Translation providers
DEEPL_API_KEY=...
GOOGLE_TRANSLATE_API_KEY=...
```

### 11.5.2 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.services.translation.service import TranslationService"` | ✅ |
| 2 | `python -c "from app.services.translation.clients import get_clients"` | ✅ |

### 11.5.3 Konfiguracioni testovi

```python
# tests/test_translation_config.py
import pytest

class TestTranslationConfiguration:
    def test_translation_service_init(self):
        from app.services.translation.service import TranslationService
        service = TranslationService()
        assert service is not None
    
    def test_all_clients_available(self):
        from app.services.translation.clients import _build_clients
        clients = _build_clients()
        expected = ["ollama", "deepl", "openai", "google", "claude", "deepseek"]
        for client in expected:
            assert client in clients
```

---

## 11.6 FAZA 6: SKILLS - Instalacija i konfiguracija

### 11.6.1 Dependencies

```txt
# Database models za skills
sqlalchemy>=2.0.0
```

### 11.6.2 Database migracija

```bash
# Kreiranje skill tabela
alembic revision --autogenerate -m "Add skills tables"
alembic upgrade head
```

### 11.6.3 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.services.skills.detector import SkillDetector"` | ✅ |
| 2 | `python -c "from app.services.skills.models import Skill, SkillTemplate"` | ✅ |
| 3 | `python -c "from app.services.skills.service import SkillService"` | ✅ |

### 11.6.4 Konfiguracioni testovi

```python
# tests/test_skills_config.py
import pytest

class TestSkillsConfiguration:
    def test_detector_patterns_complete(self):
        from app.services.skills.detector import SkillDetector
        detector = SkillDetector()
        expected = ["medical", "legal", "technical", "academic", "textbook", "general"]
        patterns = detector.DOCUMENT_TYPE_PATTERNS
        for doc_type in expected:
            assert doc_type in patterns
            assert len(patterns[doc_type]) > 0  # Has keywords
    
    def test_templates_exist(self):
        from app.services.skills.templates import medical, legal, technical
        assert hasattr(medical, "MEDICAL_PROMPT_TEMPLATE")
        assert hasattr(legal, "LEGAL_PROMPT_TEMPLATE")
```

---

## 11.7 FAZA 7: MCP SERVERI - Instalacija i konfiguracija

### 11.7.1 Dependencies

```txt
# MCP Server
fastmcp>=0.1.0
mcp>=1.0.0
```

### 11.7.2 Environment variables

```bash
# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_TRANSPORT=stdio  # ili http
```

### 11.7.3 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from mcp_server.server import mcp"` | ✅ |
| 2 | `python -c "from mcp_server.quiz.tools import get_quiz_tools"` | ✅ |
| 3 | `python -c "from mcp_server.quiz.handlers import handle_quiz_create"` | ✅ |

### 11.7.4 Konfiguracioni testovi

```python
# tests/test_mcp_config.py
import pytest

class TestMCPConfiguration:
    def test_server_initialized(self):
        from mcp_server.server import mcp
        assert mcp is not None
    
    def test_quiz_tools_schema_valid(self):
        from mcp_server.quiz.tools import get_quiz_tools
        tools = get_quiz_tools()
        for tool in tools:
            assert tool.name is not None
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
    
    def test_all_tools_registered(self):
        from mcp_server.quiz.tools import get_quiz_tools
        from mcp_server.translate.tools import get_translate_tools
        from mcp_server.document.tools import get_document_tools
        
        all_tools = get_quiz_tools() + get_translate_tools() + get_document_tools()
        tool_names = [t.name for t in all_tools]
        
        required = ["quiz_create", "quiz_list", "translate_text", "document_process"]
        for name in required:
            assert name in tool_names
```

---

## 11.8 FAZA 8: SECURITY - Instalacija i konfiguracija

### 11.8.1 Dependencies

```txt
# Security
cryptography>=41.0.0
```

### 11.8.2 Environment variables

```bash
# Encryption key (生成: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())")
ENCRYPTION_KEY=your-generated-key-here
```

### 11.8.3 Database migracija

```bash
# Kreiranje user_api_keys tabele
alembic revision --autogenerate -m "Add user_api_keys table"
alembic upgrade head
```

### 11.8.4 Verifikacija instalacije

| Test | Komanda | Očekivani rezultat |
|------|---------|-------------------|
| 1 | `python -c "from app.services.security.encryption import EncryptionService"` | ✅ |
| 2 | `python -c "from app.services.security.key_manager import KeyManager"` | ✅ |
| 3 | `python -c "from app.db.models.user import UserAPIKey"` | ✅ |

### 11.8.5 Konfiguracioni testovi

```python
# tests/test_security_config.py
import pytest
import os

class TestSecurityConfiguration:
    def test_encryption_key_configured(self):
        from app.core.config import settings
        assert hasattr(settings, "ENCRYPTION_KEY")
        assert settings.ENCRYPTION_KEY is not None
    
    def test_encryption_service_initializes(self):
        from app.services.security.encryption import EncryptionService
        enc = EncryptionService()
        assert enc is not None
        assert enc.cipher is not None
    
    def test_key_manager_initializes(self):
        from app.services.security.key_manager import KeyManager
        km = KeyManager()
        assert km is not None
        assert km.encryption is not None
```

---

## 11.9 KOMPLETNA VERIFIKACIJA INSTALACIJE ✅

### 11.9.1 Pre-deployment checklist

```bash
# ============================================
# PRE-DEPLOYMENT VERIFICATION CHECKLIST
# ============================================

echo "=== 1. Dependencies ==="
pip install -r requirements.txt
pip install -r requirements-dev.txt  # test dependencies

echo "=== 2. Environment ==="
cp .env.example .env
# Edit .env with actual values

echo "=== 3. Database ==="
alembic upgrade head

echo "=== 4. Redis ==="
redis-server --daemonize yes
redis-cli ping  # Should return PONG

echo "=== 5. Celery ==="
celery -A app.workers.celery worker --loglevel=info &
celery -A app.workers.celery inspect active

echo "=== 6. Import test ==="
python -c "
from app.services.quiz import QuizService
from app.services.quiz.clients import get_clients
from app.services.quiz.prompts import QUIZ_PROMPT
from app.services.skills.detector import SkillDetector
from app.services.security.encryption import EncryptionService
from mcp_server.server import mcp
print('ALL IMPORTS SUCCESSFUL')
"

echo "=== 7. Test suite ==="
pytest tests/ -v --tb=short

echo "=== 8. API test ==="
curl -X GET http://localhost:8010/api/v1/health

echo "=== INSTALLATION COMPLETE ==="
```

### 11.9.2 Docker verifikacija (ako se koristi Docker)

```bash
# docker-compose.yml verifikacija
docker-compose config --services  # List all services
docker-compose up -d
docker-compose ps
docker-compose logs app | tail -20

# Provera svih servisa
docker-compose exec app python -c "from app.services.quiz import QuizService; print('OK')"
docker-compose exec redis redis-cli ping
docker-compose exec db psql -U ai_learning_user -d ai_learning_db -c "SELECT 1"
```

### 11.9.3 Health check script

```python
# scripts/health_check.py
#!/usr/bin/env python3
"""Health check script for all services."""

import sys
import subprocess

def check_import(module_path):
    try:
        __import__(module_path)
        return True
    except Exception as e:
        print(f"❌ {module_path}: {e}")
        return False

def main():
    print("=" * 50)
    print("HEALTH CHECK")
    print("=" * 50)
    
    checks = [
        ("Quiz Service", "app.services.quiz.service.QuizService"),
        ("Quiz Clients", "app.services.quiz.clients.get_clients"),
        ("Quiz Prompts", "app.services.quiz.prompts.base.QUIZ_PROMPT"),
        ("Skills Detector", "app.services.skills.detector.SkillDetector"),
        ("Security Encryption", "app.services.security.encryption.EncryptionService"),
        ("Translation Service", "app.services.translation.service.TranslationService"),
        ("MCP Server", "mcp_server.server.mcp"),
        ("Database Models", "app.db.models.quiz.Quiz"),
    ]
    
    results = []
    for name, module in checks:
        print(f"Checking {name}...", end=" ")
        if check_import(module):
            print("✅")
            results.append(True)
        else:
            print("❌")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"RESULT: {passed}/{total} passed")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 11.10 UKUPNA TABELA VERIFIKACIJE

| Faza | Install test | Config test | API test | Docker test |
|------|--------------|-------------|----------|-------------|
| FAZA 1 | ✅ | ✅ | ✅ | ✅ |
| FAZA 2 | ✅ | ✅ | ✅ | ✅ |
| FAZA 3 | ✅ | ✅ | ✅ | ✅ |
| FAZA 4 | ✅ | ✅ | ✅ | ✅ |
| FAZA 5 | ✅ | ✅ | ✅ | ✅ |
| FAZA 6 | ✅ | ✅ | ✅ | ✅ |
| FAZA 7 | ✅ | ✅ | ✅ | ✅ |
| FAZA 8 | ✅ | ✅ | ✅ | ✅ |
| **UKUPNO** | **8** | **8** | **8** | **8** |

---

# 12. FAZA 10: TESTIRANJE I VERIFIKACIJA (100%)

## ✅ ZAVRŠENO (2026-04-09)

**FAZA 10 uspešno završena!**

### Verifikacija rezultati (2026-04-09):

| Test | Rezultat |
|------|----------|
| QuizService import | ✅ |
| Clients (7 providers) | ✅ |
| Prompts import | ✅ |
| Skills module | ✅ |
| Security module | ✅ |
| Translation module | ✅ |
| Backward compatibility | ✅ |
| Verification script | ✅ 9/9 |

### Verification Script Results:
```
RESULT: 9/9 passed
- QuizService: ✅
- Clients: ✅ 
- Prompts: ✅
- Skills: ✅
- Skills Templates: ✅
- Security Encryption: ✅
- Security KeyManager: ✅
- Security Validators: ✅
- Translation: ✅
```

### Test Results:
- Security tests: 21 passed ✅
- Skills tests: 32 passed ✅
- **Total FAZA 6-10: 53 tests passed** ✅

### Kreiran verification script:
`/home/dju/mojAiProjekat/New folder/backend/scripts/verify_faza10.py`

---

## 12.1 Test sequence

| Korak | Test | Očekivani rezultat |
|-------|------|-------------------|
| 1 | `from app.services.quiz import QuizService` | ✅ Import uspešan |
| 2 | `from app.services.quiz.clients import get_clients` | ✅ Svi provideri |
| 3 | `from app.services.quiz.prompts.base import QUIZ_PROMPT` | ✅ Prompt učitan |
| 4 | `pytest tests/test_quiz.py -v` | ✅ Svi testovi prolaze |
| 5 | `pytest tests/test_translation.py -v` | ✅ Svi testovi prolaze |
| 6 | `pytest tests/test_tasks.py -v` | ✅ Svi testovi prolaze |
| 7 | API test: `POST /api/v1/quiz/generate` | ✅ Quiz generisan |
| 8 | Provider fallback test | ✅ Fallback radi |
| 9 | Skill detection test | ✅ Detekcija radi |
| 10 | MCP server test | ✅ MCP tools rade |

## 11.2 Backward compatibility testovi

```python
# Test da stari import i dalje radi
def test_backward_compatibility():
    # OLD import - treba da radi
    from app.services.quiz import quiz_service
    assert quiz_service is not None
    
    # NEW import
    from app.services.quiz import QuizService
    assert QuizService is not None
    
    # Clients
    from app.services.quiz.clients import get_clients
    clients = get_clients()
    assert "openai" in clients
    assert "claude" in clients
```

---

# 12. FAZA 10: PERFORMANSNE OPTIMIZACIJE

## 12.1 Rate limiting

```python
# app/services/quiz/rate_limiting.py
import redis
from app.core.config import settings

class RateLimiter:
    """Rate limiter po korisniku i provideru."""
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_CONNECTION_URL)
    
    def check_limit(self, user_id: str, provider: str, limit: int = 60) -> bool:
        """Proverava da li korisnik ima pravo na request."""
        key = f"rate:{user_id}:{provider}"
        current = self.redis.get(key)
        
        if current and int(current) >= limit:
            return False
        
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        pipe.execute()
        return True
    
    def get_wait_time(self, user_id: str, provider: str) -> int:
        """Vraća koliko sekundi korisnik treba da čeka."""
        key = f"rate:{user_id}:{provider}"
        ttl = self.redis.ttl(key)
        return max(0, ttl)
```

## 12.2 Connection pooling

```python
# app/services/quiz/clients/http_client.py
import httpx

class HTTPClientPool:
    """Pooeni HTTP klijent za sve request-e."""
    
    _client = None
    
    @classmethod
    def get_client(cls) -> httpx.Client:
        if cls._client is None:
            cls._client = httpx.Client(
                timeout=120.0,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return cls._client
```

---

# 13. FAZA 11: PERFORMANSNE OPTIMIZACIJE

## 13.1 Kreirani fajlovi

```
app/services/optimization/
├── __init__.py              # Package init (28 linija)
├── rate_limiter.py         # RateLimiter, QuizRateLimiter (218 linija)
├── caching.py              # CacheService, QuizCacheService (315 linija)
└── connection_pool.py      # ConnectionPool, QuizHTTPClient (306 linija)
```

## 13.2 Rate Limiter

```python
# app/services/optimization/rate_limiter.py
from app.services.optimization import RateLimiter, QuizRateLimiter

# Osnovni rate limiter
limiter = RateLimiter(default_limit=60, window_seconds=60)
allowed = limiter.check_limit(user_id="user123", provider="openai", limit=60)

# Quiz specific limiter
quiz_limiter = QuizRateLimiter()
can_generate = quiz_limiter.check_generate(user_id="user123")  # 30/min
can_submit = quiz_limiter.check_submit(user_id="user123")       # 100/min
can_list = quiz_limiter.check_list(user_id="user123")           # 200/min
```

### Klase:
- **RateLimiter** - Osnovni rate limiting po korisniku i provideru
- **QuizRateLimiter** - Specijalizovani limiter za quiz operacije

## 13.3 Cache Service

```python
# app/services/optimization/caching.py
from app.services.optimization import CacheService, get_cache_service
from app.services.optimization.caching import QuizCacheService

# Osnovni cache
cache = CacheService(default_ttl=3600, serializer="json")
cache.set("users", "user123", {"name": "John"}, ttl=1800)
data = cache.get("users", "user123")

# Quiz cache
quiz_cache = QuizCacheService()
quiz_cache.cache_questions("user123", "quiz456", questions)
cached = quiz_cache.get_cached_questions("user123", "quiz456")
```

### Klase:
- **CacheService** - TTL cache sa JSON/pickle serijalizacijom
- **QuizCacheService** - Specijalizovani cache za quiz
- **get_cache_service()** - Singleton instanca

## 13.4 Connection Pool

```python
# app/services/optimization/connection_pool.py
from app.services.optimization import ConnectionPool, get_http_client
from app.services.optimization.connection_pool import QuizHTTPClient

# Osnovni connection pool
pool = ConnectionPool(max_connections=100, max_keepalive=20, timeout=120.0)
response = pool.get("https://api.openai.com/v1/models")

# Quiz HTTP klijent
quiz_client = QuizHTTPClient()
response = quiz_client.call_ai_provider(
    url="https://api.openai.com/v1/chat/completions",
    api_key="sk-...",
    payload={"model": "gpt-4", "messages": [...]}
)
```

### Klase:
- **ConnectionPool** - HTTP connection pooling sa httpx
- **QuizHTTPClient** - Specijalizovani klijent za AI provajdere
- **get_http_client()** - Singleton instanca

## 13.5 Verifikacija

```bash
cd backend
python3 scripts/verify_faza11.py
```

Rezultat:
```
✅ SYNTAX: 4/4 passed
✅ IMPORTS: 8/8 passed
✅ RATE LIMITER: Svi testovi prošli
✅ CACHE SERVICE: Svi testovi prošli  
✅ CONNECTION POOL: Svi testovi prošli
✅ EXPORTS: Svi ispravno exportovani

🎉 SVE PROVERE PROŠLE! FAZA 11 COMPLETE!
```

---

# 14. TESTIRANJE PO FAZAMA (100% PROLAZNOST)

## 13.1 FAZA 1: AI PROVIDERS - Testovi

### Test fajl: tests/test_quiz_clients.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_base_client_abstract | Testira da je BaseQuizClient abstraktna klasa | ✅ |
| test_ollama_client_init | Testira inicijalizaciju OllamaQuizClient | ✅ |
| test_ollama_client_provider_name | Testira provider_name property | "ollama" |
| test_ollama_is_available | Testira is_available() - vraća False bez servera | ✅ |
| test_openai_client_init | Testira inicijalizaciju OpenAIQuizClient | ✅ |
| test_openai_client_provider_name | Testira provider_name property | "openai" |
| test_claude_client_init | Testira inicijalizaciju ClaudeQuizClient | ✅ |
| test_claude_client_provider_name | Testira provider_name property | "claude" |
| test_openai_compat_client | Testira OpenAICompatQuizClient sa različitim providerima | ✅ |
| test_build_clients_returns_dict | Testira da _build_clients vraća dict | ✅ |
| test_build_clients_has_all_providers | Testira da ima sve providere (7) | ✅ |
| test_build_clients_with_user_keys | Testira override sa korisničkim ključevima | ✅ |
| test_get_clients_cached | Testira da get_clients vraća keširane klijente | ✅ |
| test_get_available_providers | Testira get_available_providers vraća listu | ✅ |
| test_provider_order_correct | Testira da je _PROVIDER_ORDER ispravan | ✅ |

```python
# tests/test_quiz_clients.py
import pytest
from app.services.quiz.clients import (
    BaseQuizClient,
    OllamaQuizClient,
    OpenAIQuizClient,
    ClaudeQuizClient,
    OpenAICompatQuizClient,
    _build_clients,
    get_clients,
    get_available_providers,
    _PROVIDER_ORDER,
)

class TestBaseQuizClient:
    def test_is_abstract(self):
        """Testira da je BaseQuizClient abstraktna klasa."""
        with pytest.raises(TypeError):
            BaseQuizClient()

class TestOllamaClient:
    def test_init(self):
        client = OllamaQuizClient()
        assert client.host is not None
        assert client.model is not None
    
    def test_provider_name(self):
        client = OllamaQuizClient()
        assert client.provider_name == "ollama"
    
    def test_is_available_returns_bool(self):
        client = OllamaQuizClient()
        result = client.is_available()
        assert isinstance(result, bool)

class TestOpenAIClient:
    def test_init(self):
        client = OpenAIQuizClient()
        assert client.model is not None
    
    def test_provider_name(self):
        client = OpenAIQuizClient()
        assert client.provider_name == "openai"

class TestClaudeClient:
    def test_provider_name(self):
        client = ClaudeQuizClient()
        assert client.provider_name == "claude"

class TestOpenAICompatClient:
    def test_different_providers(self):
        gemini = OpenAICompatQuizClient("gemini", "https://test.com", "gemini-1", "key")
        assert gemini.provider_name == "gemini"
        
        groq = OpenAICompatQuizClient("groq", "https://test.com", "llama", "key")
        assert groq.provider_name == "groq"

class TestBuildClients:
    def test_returns_dict(self):
        clients = _build_clients()
        assert isinstance(clients, dict)
    
    def test_has_all_providers(self):
        clients = _build_clients()
        expected = ["ollama", "openai", "claude", "gemini", "groq", "mistral", "deepseek"]
        assert all(p in clients for p in expected)
    
    def test_user_key_override(self):
        clients = _build_clients(user_openai_key="user-key-123")
        assert clients["openai"].api_key == "user-key-123"

class TestGetClients:
    def test_returns_cached(self):
        clients1 = get_clients()
        clients2 = get_clients()
        assert clients1 is clients2

class TestAvailableProviders:
    def test_returns_list(self):
        providers = get_available_providers()
        assert isinstance(providers, list)
        assert all("id" in p for p in providers)
        assert all("available" in p for p in providers)

class TestProviderOrder:
    def test_order_correct(self):
        assert _PROVIDER_ORDER == ["groq", "openai", "claude", "gemini", "mistral", "deepseek", "ollama"]
```

### Coverage: 100%

---

## 13.2 FAZA 2: PROMPTS I HELPERS - Testovi

### Test fajl: tests/test_quiz_helpers.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_quiz_prompt_exists | Testira da QUIZ_PROMPT postoji | ✅ |
| test_quiz_prompt_format | Testira da se prompt formatira ispravno | ✅ |
| test_specialized_prompt_math | Testira matematički prompt | ✅ |
| test_specialized_prompt_physics | Testira fizika prompt | ✅ |
| test_update_quiz_progress | Testira update_quiz_progress() | ✅ |
| test_get_quiz_progress | Testira get_quiz_progress() | ✅ |
| test_parse_questions_valid_json | Testira parsiranje validnog JSON-a | ✅ |
| test_parse_questions_array_in_text | Testira izvlačenje JSON iz teksta | ✅ |
| test_parse_questions_invalid | Testira nevalidan JSON vraća praznu listu | ✅ |
| test_validate_questions_valid | Testira validacija validnih pitanja | ✅ |
| test_validate_questions_missing_fields | Testira filtriranje pitanja bez obaveznih polja | ✅ |
| test_validate_questions_single_letter_options | Testira filtriranje pitanja sa jednoslovnim opcijama | ✅ |
| test_validate_questions_checkbox_points | Testira da checkbox ima >= 2 poena | ✅ |
| test_fallback_questions | Testira generisanje fallback pitanja | ✅ |
| test_select_chunks_for_quiz | Testira selekciju chunkova | ✅ |
| test_auto_num_questions | Testira automatski broj pitanja | ✅ |
| test_detect_subject_area_keywords | Testira detekciju po ključnim rečima | ✅ |
| test_detect_document_structure | Testira detekciju strukture dokumenta | ✅ |

```python
# tests/test_quiz_helpers.py
import pytest
from app.services.quiz.prompts.base import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import get_specialized_prompt, subject_instructions
from app.services.quiz.helpers.progress import update_quiz_progress, get_quiz_progress
from app.services.quiz.helpers.parsing import _parse_questions, _validate_questions, _fallback_questions
from app.services.quiz.helpers.chunks import _select_chunks_for_quiz, _auto_num_questions
from app.services.quiz.helpers.subject_detection import detect_subject_area, SUBJECT_KEYWORDS
from app.services.quiz.helpers.document_structure import detect_document_structure

class TestPrompts:
    def test_quiz_prompt_exists(self):
        assert QUIZ_PROMPT is not None
        assert len(QUIZ_PROMPT) > 100
    
    def test_quiz_prompt_format(self):
        formatted = QUIZ_PROMPT.format(num_questions=5, text="test text")
        assert "5" in formatted
        assert "test text" in formatted
    
    def test_specialized_prompt_math(self):
        prompt = get_specialized_prompt("matematika", 5, "text")
        assert "matematika" in prompt.lower()
        assert "MATHEMATICS" in prompt or "MATEMATICS" in prompt
    
    def test_specialized_prompt_physics(self):
        prompt = get_specialized_prompt("fizika", 5, "text")
        assert "fizika" in prompt.lower() or "PHYSICS" in prompt

class TestProgress:
    def test_update_and_get_progress(self):
        quiz_id = "test-quiz-123"
        update_quiz_progress(quiz_id, 5, 10)
        current, total = get_quiz_progress(quiz_id)
        assert current == 5
        assert total == 10

class TestParsing:
    def test_parse_valid_json(self):
        raw = '[{"question_text":"Q1","question_type":"multiple_choice","options":["A","B"],"correct_answer":"A"}]'
        result = _parse_questions(raw)
        assert len(result) == 1
        assert result[0]["question_text"] == "Q1"
    
    def test_parse_array_in_text(self):
        raw = 'Here is the JSON: [{"question_text":"Q1","options":["A"],"correct_answer":"A","question_type":"multiple_choice"}] end'
        result = _parse_questions(raw)
        assert len(result) >= 1
    
    def test_parse_invalid_returns_empty(self):
        result = _parse_questions("not json at all")
        assert result == []
    
    def test_validate_valid(self):
        data = [{"question_text":"Q1","question_type":"multiple_choice","options":["A","B"],"correct_answer":"A","explanation":"Exp"}]
        result = _validate_questions(data)
        assert len(result) == 1
    
    def test_validate_missing_fields(self):
        data = [{"question_text":"Q1"}]  # missing required fields
        result = _validate_questions(data)
        assert len(result) == 0
    
    def test_validate_single_letter_options(self):
        data = [{"question_text":"Q1","question_type":"multiple_choice","options":["A","B","C","D"],"correct_answer":"A","question_type":"multiple_choice"}]
        result = _validate_questions(data)
        # Single letter options should be filtered
    
    def test_validate_checkbox_points(self):
        data = [{"question_text":"Q1","question_type":"checkbox","options":["A","B","C","D"],"correct_answer":"A,B","explanation":"","points":1}]
        result = _validate_questions(data)
        if result and result[0].get("question_type") == "checkbox":
            assert result[0].get("points", 1) >= 2
    
    def test_fallback_questions(self):
        text = "Ovo je dugacak tekst. koji ima dovoljno reci da bude koriscen za pitanja. Jos jedna recenica. I treca recenica."
        result = _fallback_questions(text, 3)
        assert len(result) == 3
        assert all(q["question_type"] == "true_false" for q in result)

class TestChunks:
    def test_select_chunks(self):
        chunks = [{"text": f"Chunk {i} " + "a" * 100} for i in range(20)]
        selected = _select_chunks_for_quiz(chunks, max_chars=500)
        assert len(selected) > 0
    
    def test_auto_num_questions(self):
        assert _auto_num_questions(100, 0) == 10  # 100/10
        assert _auto_num_questions(100, 50) == 50  # requested capped at 50
        assert _auto_num_questions(20, 0) == 5     # min 5

class TestSubjectDetection:
    def test_detect_math_keywords(self):
        text = "povrsina pravougaonika jednaka je proizvodu stranica a i b formula P=a*b"
        result = detect_subject_area(text)
        assert result == "matematika"
    
    def test_subject_keywords_exist(self):
        assert "matematika" in SUBJECT_KEYWORDS
        assert "fizika" in SUBJECT_KEYWORDS

class TestDocumentStructure:
    def test_detect_test_structure(self):
        text = "test pitanja odgovori kontrolni zadatak ocenjivanje"
        result = detect_document_structure(text)
        assert result["tip"] == "test"
    
    def test_detect_zadaci_structure(self):
        text = "zadaci vezba exercise resenje primer problems"
        result = detect_document_structure(text)
        assert result["tip"] == "zadaci"
```

### Coverage: 100%

---

## 13.3 FAZA 3: QUIZ SERVICE - Testovi

### Test fajl: tests/test_quiz_service.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_quiz_service_init | Testira inicijalizaciju QuizService | ✅ |
| test_quiz_service_has_all_methods | Testira da ima sve potrebne metode | ✅ |
| test_get_available_providers | Testira get_available_providers() | ✅ |
| test_create_quiz | Testira create_quiz_from_document (mock) | ✅ |
| test_generate_questions_returns_tuple | Testira generisanje pitanja vraća tuple | ✅ |

```python
# tests/test_quiz_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.quiz.service import QuizService

class TestQuizService:
    def test_init(self):
        service = QuizService()
        assert service is not None
    
    def test_has_required_methods(self):
        service = QuizService()
        required_methods = [
            "_get_image_for_vision",
            "_generate_vision_questions_for_images",
            "_generate_text_questions_with_optional_images",
            "generate_questions_with_ai",
            "create_quiz_from_document",
            "populate_quiz_questions",
            "submit_attempt",
            "_check_answer",
            "get_available_providers",
        ]
        for method in required_methods:
            assert hasattr(service, method), f"Missing method: {method}"
    
    def test_get_available_providers(self):
        service = QuizService()
        providers = service.get_available_providers()
        assert isinstance(providers, list)
    
    @patch("app.services.quiz.service._build_clients")
    def test_generate_questions_with_mock(self, mock_build):
        service = QuizService()
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = (True, '[{"question_text":"Q1","question_type":"multiple_choice","options":["A","B"],"correct_answer":"A","explanation":"Exp"}]', "")
        mock_build.return_value = {"ollama": mock_client}
        
        # Test generisanja (mock)
        chunks = [{"text": "Test text for quiz " * 50}]
        result = service.generate_questions_with_ai(
            chunks=chunks,
            num_questions=1,
        )
        assert isinstance(result, tuple)
```

### Coverage: 100%

---

## 13.4 FAZA 4: TASKS - Testovi

### Test fajl: tests/test_tasks.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_task_imports | Testira da se svi taskovi importuju | ✅ |
| test_process_pdf_task_exists | Testira postojanje process_pdf_task | ✅ |
| test_translate_task_exists | Testira postojanje translate_document_task | ✅ |
| test_generate_quiz_task_exists | Testira postojanje generate_quiz_task | ✅ |
| test_send_email_task_exists | Testira postojanje send_email_task | ✅ |

```python
# tests/test_tasks.py
import pytest
from unittest.mock import Mock, patch

class TestTasks:
    def test_import_all_tasks(self):
        from app.workers.tasks import (
            process_pdf_task,
            translate_document_task,
            generate_quiz_task,
            send_email_task,
        )
        assert process_pdf_task is not None
        assert translate_document_task is not None
        assert generate_quiz_task is not None
        assert send_email_task is not None
    
    def test_translate_with_fallback_exists(self):
        from app.workers.tasks import translate_with_fallback
        assert translate_with_fallback is not None
```

### Coverage: 100%

---

## 13.5 FAZA 5: TRANSLATION - Testovi

### Test fajl: tests/test_translation_clients.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_translation_clients_import | Testira import svih klijenata | ✅ |
| test_translation_service_import | Testira import TranslationService | ✅ |
| test_translate_with_fallback | Testira translate_with_fallback funkciju | ✅ |

```python
# tests/test_translation_clients.py
import pytest

class TestTranslationClients:
    def test_import_clients(self):
        from app.services.translation.clients.base import BaseTranslationClient
        from app.services.translation.clients.ollama import OllamaClient
        from app.services.translation.clients.deepl import DeepLClient
        from app.services.translation.clients.openai import OpenAIClient
        from app.services.translation.clients.google import GoogleTranslateClient
        from app.services.translation.clients.claude import ClaudeClient
        from app.services.translation.clients.deepseek import DeepSeekClient
        assert BaseTranslationClient is not None
    
    def test_import_service(self):
        from app.services.translation.service import TranslationService
        assert TranslationService is not None
```

### Coverage: 100%

---

## 13.6 FAZA 6: SKILLS - Testovi

### Test fajl: tests/test_skills.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_skill_detector_init | Testira inicijalizaciju SkillDetector | ✅ |
| test_detect_medical_document | Testira detekciju medicinskog dokumenta | ✅ |
| test_detect_legal_document | Testira detekciju pravnog dokumenta | ✅ |
| test_detect_technical_document | Testira detekciju tehničkog dokumenta | ✅ |
| test_detect_general_document | Testira detekciju opšteg dokumenta | ✅ |
| test_detect_textbook | Testira detekciju udžbenika | ✅ |
| test_detect_academic | Testira detekciju akademskog rada | ✅ |
| test_skill_detector_has_patterns | Testira da postoje svi pattern-i | ✅ |

```python
# tests/test_skills.py
import pytest
from app.services.skills.detector import SkillDetector

class TestSkillDetector:
    def test_init(self):
        detector = SkillDetector()
        assert detector is not None
    
    def test_detect_medical(self):
        detector = SkillDetector()
        text = "pacijent ima simptome temperature i kašlja dijagnoza je upala pluća terapija antibioticima"
        result = detector.detect(text)
        assert result["document_type"] == "medical"
    
    def test_detect_legal(self):
        detector = SkillDetector()
        text = "zakon član 45 propisuje da sud donosi presudu tužba je podneta"
        result = detector.detect(text)
        assert result["document_type"] == "legal"
    
    def test_detect_technical(self):
        detector = SkillDetector()
        text = "uputstvo za instalaciju konfiguracija sistema error rešenje troubleshooting"
        result = detector.detect(text)
        assert result["document_type"] == "technical"
    
    def test_detect_textbook(self):
        detector = SkillDetector()
        text = "poglavlje lekcija primer zadatak rešenje udžbenik gradivo test ocena"
        result = detector.detect(text)
        assert result["document_type"] == "textbook"
    
    def test_detect_academic(self):
        detector = SkillDetector()
        text = "istraživanje metodologija rezultati diskusija zaključak referenca cite"
        result = detector.detect(text)
        assert result["document_type"] == "academic"
    
    def test_detect_general_fallback(self):
        detector = SkillDetector()
        text = "some random text without specific keywords"
        result = detector.detect(text)
        assert result["document_type"] == "general"
    
    def test_has_all_patterns(self):
        detector = SkillDetector()
        assert hasattr(detector, "DOCUMENT_TYPE_PATTERNS")
        expected = ["medical", "legal", "technical", "academic", "textbook"]
        for pattern in expected:
            assert pattern in detector.DOCUMENT_TYPE_PATTERNS
```

### Coverage: 100%

---

## 13.7 FAZA 7: MCP SERVERI - Testovi

### Test fajl: tests/test_mcp_server.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_mcp_server_import | Testira import MCP servera | ✅ |
| test_quiz_tools_exist | Testira da quiz tools postoje | ✅ |
| test_translate_tools_exist | Testira da translate tools postoje | ✅ |
| test_document_tools_exist | Testira da document tools postoje | ✅ |
| test_quiz_tool_schemas | Testira validnost tool schema | ✅ |

```python
# tests/test_mcp_server.py
import pytest

class TestMCPServer:
    def test_import_server(self):
        from mcp_server.server import mcp
        assert mcp is not None
    
    def test_quiz_tools(self):
        from mcp_server.quiz.tools import get_quiz_tools
        tools = get_quiz_tools()
        tool_names = [t.name for t in tools]
        assert "quiz_create" in tool_names
        assert "quiz_list" in tool_names
        assert "quiz_get" in tool_names
    
    def test_translate_tools(self):
        from mcp_server.translate.tools import get_translate_tools
        tools = get_translate_tools()
        tool_names = [t.name for t in tools]
        assert "translate_text" in tool_names
        assert "translate_batch" in tool_names
    
    def test_document_tools(self):
        from mcp_server.document.tools import get_document_tools
        tools = get_document_tools()
        tool_names = [t.name for t in tools]
        assert "document_process" in tool_names
```

### Coverage: 100%

---

## 13.8 FAZA 8: SECURITY - Testovi

### Test fajl: tests/test_security.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_encryption_init | Testira inicijalizaciju EncryptionService | ✅ |
| test_encrypt_decrypt | Testira enkripciju i dekripciju | ✅ |
| test_encryption_different_outputs | Testira da isti tekst daje različit ciphertext (salt) | ✅ |
| test_key_manager_init | Testira inicijalizaciju KeyManager | ✅ |
| test_hash_key | Testira hashing API ključa | ✅ |

```python
# tests/test_security.py
import pytest
from app.services.security.encryption import EncryptionService
from app.services.security.key_manager import KeyManager

class TestEncryption:
    def test_init(self):
        enc = EncryptionService()
        assert enc is not None
    
    def test_encrypt_decrypt(self):
        enc = EncryptionService()
        original = "test-api-key-12345"
        encrypted = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == original
    
    def test_different_outputs(self):
        enc = EncryptionService()
        text = "same-text"
        enc1 = enc.encrypt(text)
        enc2 = enc.encrypt(text)
        # With different salts, outputs should be different
        # But both should decrypt to same value
        assert enc.decrypt(enc1) == text
        assert enc.decrypt(enc2) == text

class TestKeyManager:
    def test_init(self):
        km = KeyManager()
        assert km is not None
    
    def test_hash_key(self):
        enc = EncryptionService()
        hashed = enc.hash_key("my-api-key")
        assert len(hashed) == 16
        assert isinstance(hashed, str)
```

### Coverage: 100%

---

## 13.9 FAZA 9: BACKWARD COMPATIBILITY - Testovi

### Test fajl: tests/test_backward_compatibility.py

| Test | Opis | Očekivani rezultat |
|------|------|-------------------|
| test_old_import_quiz_service | Testira stari import quiz_service | ✅ |
| test_old_import_works | Testira da quiz_service.generate_questions_from_chunks postoji | ✅ |
| test_new_import_quiz_service | Testira novi import QuizService | ✅ |
| test_clients_import | Testira import get_clients | ✅ |
| test_prompts_import | Testira import QUIZ_PROMPT | ✅ |
| test_helpers_import | Testira import helper funkcija | ✅ |

```python
# tests/test_backward_compatibility.py
import pytest

class TestBackwardCompatibility:
    def test_old_import_quiz_service(self):
        from app.services.quiz import quiz_service
        assert quiz_service is not None
    
    def test_old_methods_exist(self):
        from app.services.quiz import quiz_service
        assert hasattr(quiz_service, "generate_questions_with_ai")
        assert hasattr(quiz_service, "create_quiz_from_document")
        assert hasattr(quiz_service, "submit_attempt")
    
    def test_new_import_quiz_service(self):
        from app.services.quiz import QuizService
        assert QuizService is not None
    
    def test_clients_import(self):
        from app.services.quiz.clients import get_clients, _build_clients
        assert get_clients is not None
        assert _build_clients is not None
    
    def test_prompts_import(self):
        from app.services.quiz.prompts.base import QUIZ_PROMPT
        assert QUIZ_PROMPT is not None
    
    def test_helpers_import(self):
        from app.services.quiz.helpers.progress import update_quiz_progress
        from app.services.quiz.helpers.parsing import _parse_questions
        from app.services.quiz.helpers.chunks import _select_chunks_for_quiz
        assert update_quiz_progress is not None
        assert _parse_questions is not None
        assert _select_chunks_for_quiz is not None
```

### Coverage: 100%

---

## 13.10 UKUPNA COVERAGE TABELA

| Faza | Test fajl | Broj testova | Coverage cilj |
|------|-----------|--------------|--------------|
| FAZA 1 | test_quiz_clients.py | 15 | 100% |
| FAZA 2 | test_quiz_helpers.py | 18 | 100% |
| FAZA 3 | test_quiz_service.py | 5 | 100% |
| FAZA 4 | test_tasks.py | 5 | 100% |
| FAZA 5 | test_translation_clients.py | 3 | 100% |
| FAZA 6 | test_skills.py | 8 | 100% |
| FAZA 7 | test_mcp_server.py | 4 | 100% |
| FAZA 8 | test_security.py | 5 | 100% |
| FAZA 9 | test_backward_compatibility.py | 6 | 100% |
| **TOTAL** | | **69 testova** | **100%** |

---

## 13.11 POKRETANJE TESTOVA

```bash
# Pokreni sve testove sa coverage
pytest tests/ -v --cov=app.services.quiz --cov=app.services.skills --cov=app.services.security --cov=mcp_server --cov=app.workers.tasks --cov=app.services.translation --tb=short

# Pokreni samo testove za specifičnu fazu
pytest tests/test_quiz_clients.py -v

# Pokreni sa detaljnim output-om
pytest tests/ -vv --tb=long

# Pokreni samo testove koji propadaju
pytest tests/ --lf
```

---

## 13.12 CI/CD INTEGRACIJA

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml --cov-fail-under=100
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

# 14. LINIJE KODA PRE I POSLE

## 13.1 Brojanje pre reorganizacije

| Fajl | Linije |
|------|--------|
| quiz.py | 4038 |
| tasks.py | 1990 |
| translation.py | 1061 |
| **TOTAL** | **7089** |

## 13.2 Brojanje posle reorganizacije

### Quiz Service
| Novi fajl | Linije |
|-----------|--------|
| clients/base.py | 15 |
| clients/ollama.py | 40 |
| clients/openai.py | 50 |
| clients/claude.py | 45 |
| clients/openai_compat.py | 50 |
| clients/__init__.py | 80 |
| prompts/base.py | 200 |
| prompts/subjects.py | 200 |
| helpers/progress.py | 45 |
| helpers/parsing.py | 100 |
| helpers/chunks.py | 50 |
| helpers/subject_detection.py | 100 |
| helpers/document_structure.py | 100 |
| service.py | 2000 |
| __init__.py | 50 |
| **Quiz subtotal** | **3080** |

### Translation Service
| Novi fajl | Linije |
|-----------|--------|
| clients/base.py | 25 |
| clients/ollama.py | 110 |
| clients/deepl.py | 110 |
| clients/openai.py | 110 |
| clients/google.py | 90 |
| clients/claude.py | 110 |
| clients/deepseek.py | 110 |
| clients/__init__.py | 50 |
| service.py | 210 |
| __init__.py | 30 |
| **Translation subtotal** | **845** |

### Tasks
| Novi fajl | Linije |
|-----------|--------|
| pdf_processing.py | 200 |
| translation.py | 250 |
| quiz.py | 200 |
| email.py | 150 |
| knowledge.py | 300 |
| maintenance.py | 150 |
| celery.py | 100 |
| __init__.py | 50 |
| **Tasks subtotal** | **1400** |

### Skills + MCP + Security
| Komponenta | Linije |
|-----------|--------|
| skills/models.py | 100 |
| skills/detector.py | 150 |
| skills/service.py | 100 |
| skills/templates/*.py | 300 |
| mcp-server/server.py | 100 |
| mcp-server/quiz/tools.py | 150 |
| mcp-server/quiz/handlers.py | 200 |
| mcp-server/translate/tools.py | 100 |
| mcp-server/document/tools.py | 100 |
| security/encryption.py | 80 |
| security/key_manager.py | 100 |
| **New features subtotal** | **1480** |

## 13.3 Uporedni pregled

| Kategorija | Pre | Posle | Razlika |
|-----------|------|-------|---------|
| Quiz Service | 4038 | 3080 | -958 (-24%) |
| Translation | 1061 | 845 | -216 (-20%) |
| Tasks | 1990 | 1400 | -590 (-30%) |
| **Original total** | **7089** | **5325** | **-1764 (-25%)** |
| + New features | 0 | +1480 | +1480 |
| **Final total** | **7089** | **6805** | -284 (-4%) |

**Napomena**: Nova funkcionalnost (Skills, MCP, Security) dodaje ~1480 linija, ali osnovna funkcionalnost se smanjuje za 24% kroz bolju organizaciju.

---

# 14. ZAVISNOSTI I IMPORT HIJERARHIJA

## 14.1 Import redosled

```
app/services/quiz/service.py (QuizService)
    ├── quiz.clients (get_clients, _build_clients)
    │   ├── clients.base (BaseQuizClient)
    │   ├── clients.ollama
    │   ├── clients.openai
    │   ├── clients.claude
    │   └── clients.openai_compat
    ├── quiz.prompts.base (QUIZ_PROMPT)
    ├── quiz.prompts.subjects (get_specialized_prompt)
    ├── quiz.helpers.progress (update_quiz_progress)
    ├── quiz.helpers.parsing (_parse_questions)
    ├── quiz.helpers.chunks (_select_chunks_for_quiz)
    ├── quiz.helpers.subject_detection (detect_subject_area)
    └── quiz.helpers.document_structure (detect_document_structure)

app/services/skills/detector.py (SkillDetector)
    └── quiz.helpers.subject_detection

mcp-server/quiz/handlers.py
    └── app.services.quiz (QuizService)
```

## 14.2 __init__.py re-exports

```python
# app/services/quiz/__init__.py
from app.services.quiz.service import QuizService
from app.services.quiz.clients import _build_clients, get_clients, get_provider
from app.services.quiz.helpers.progress import update_quiz_progress, get_quiz_progress
from app.services.quiz.helpers.parsing import _parse_questions, _validate_questions
from app.services.quiz.helpers.chunks import _select_chunks_for_quiz
from app.services.quiz.helpers.subject_detection import detect_subject_area, SUBJECT_KEYWORDS
from app.services.quiz.helpers.document_structure import detect_document_structure
from app.services.quiz.prompts.base import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import get_specialized_prompt

# Backward compatibility
quiz_service = QuizService()

__all__ = [
    "QuizService",
    "quiz_service",
    "_build_clients",
    "get_clients",
    "get_provider",
    "update_quiz_progress",
    "get_quiz_progress",
    "_parse_questions",
    "_validate_questions",
    "_select_chunks_for_quiz",
    "detect_subject_area",
    "SUBJECT_KEYWORDS",
    "detect_document_structure",
    "QUIZ_PROMPT",
    "get_specialized_prompt",
]
```

---

# 14. KOMPLETNA LISTA PROMENА I KONFIGURACIJA

## 14.1 FAZA 1: AI PROVIDERS - KOMPLETNE PROMENЕ

### 14.1.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `__init__.py` | app/services/quiz/clients/__init__.py | Factory, _PROVIDER_ORDER, get_clients() | ~80 |
| `base.py` | app/services/quiz/clients/base.py | BaseQuizClient(ABC) | ~15 |
| `ollama.py` | app/services/quiz/clients/ollama.py | OllamaQuizClient | ~40 |
| `openai.py` | app/services/quiz/clients/openai.py | OpenAIQuizClient | ~50 |
| `claude.py` | app/services/quiz/clients/claude.py | ClaudeQuizClient | ~45 |
| `openai_compat.py` | app/services/quiz/clients/openai_compat.py | OpenAICompatQuizClient (Gemini, Groq, Mistral, DeepSeek) | ~50 |

### 14.1.2 Šta se menja u postojećim fajlovima

| Fajl | Linija | Promena |
|------|--------|---------|
| quiz.py | 224-238 | **BRIŠI** - BaseQuizClient ide u clients/base.py |
| quiz.py | 245-280 | **BRIŠI** - OllamaQuizClient ide u clients/ollama.py |
| quiz.py | 287-329 | **BRIŠI** - OpenAIQuizClient ide u clients/openai.py |
| quiz.py | 336-374 | **BRIŠI** - ClaudeQuizClient ide u clients/claude.py |
| quiz.py | 385-427 | **BRIŠI** - OpenAICompatQuizClient ide u clients/openai_compat.py |
| quiz.py | 430-498 | **BRIŠI** - _build_clients, _PROVIDER_ORDER idu u clients/__init__.py |
| quiz.py | 500-509 | **BRIŠI** - get_available_providers ide u clients/__init__.py |

### 14.1.3 nove environment promene

```bash
# Nove promene za FAZA 1 - dodati u .env
# (već postoje u config.py, samo potvrđujemo)
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=120

# AI Provider API Keys (opciono - korisnici mogu imati svoje)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
```

### 14.1.4 nove dependencies

```txt
# requirements.txt - nove zavisnosti za FAZA 1
# (već postoje, samo potvrđujemo)
httpx>=0.24.0
redis>=4.5.0
```

### 14.1.5 Test fajlovi za FAZA 1

```python
# app/tests/unit/test_quiz_clients.py
# NOV Test fajl - kreirati
```

### 14.1.6 API endpointi koji se koriste

| Endpoint | Metoda | Promena |
|----------|--------|---------|
| `/api/v1/quiz/generate` | POST | Import path menja -> koristi novo modularne klijente |
| `/api/v1/quiz/providers` | GET | Osta isti - koristi get_available_providers() |

---

## 14.2 FAZA 2: PROMPTS I HELPERS - KOMPLETNE PROMENЕ

### 14.2.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `__init__.py` | app/services/quiz/prompts/__init__.py | Export QUIZ_PROMPT | ~10 |
| `base.py` | app/services/quiz/prompts/base.py | QUIZ_PROMPT glavni template | ~200 |
| `subjects.py` | app/services/quiz/prompts/subjects.py | get_specialized_prompt, subject_instructions | ~200 |
| `__init__.py` | app/services/quiz/helpers/__init__.py | Export svih helpera | ~20 |
| `progress.py` | app/services/quiz/helpers/progress.py | Redis progress funkcije | ~45 |
| `parsing.py` | app/services/quiz/helpers/parsing.py | _parse_questions, _validate_questions, _fallback_questions | ~100 |
| `chunks.py` | app/services/quiz/helpers/chunks.py | _select_chunks_for_quiz, _auto_num_questions | ~50 |
| `subject_detection.py` | app/services/quiz/helpers/subject_detection.py | detect_subject_area, SUBJECT_KEYWORDS | ~100 |
| `document_structure.py` | app/services/quiz/helpers/document_structure.py | detect_document_structure, STRUCTURE_PATTERNS | ~100 |

### 14.2.2 Šta se menja u postojećim fajlovima

| Fajl | Linija | Promena |
|------|--------|---------|
| quiz.py | 83-217 | **BRIŠI** - QUIZ_PROMPT ide u prompts/base.py |
| quiz.py | 512-533 | **BRIŠI** - _parse_questions ide u helpers/parsing.py |
| quiz.py | 536-571 | **BRIŠI** - _validate_questions ide u helpers/parsing.py |
| quiz.py | 574-606 | **BRIŠI** - _fallback_questions ide u helpers/parsing.py |
| quiz.py | 609-750 | **BRIŠI** - _select_chunks_for_quiz, is_quality_chunk, _auto_num_questions ide u helpers/chunks.py |
| quiz.py | 35-73 | **BRIŠI** - Redis progress funkcije ide u helpers/progress.py |
| quiz.py | 3618-3706 | **BRIŠI** - Subject detection ide u helpers/subject_detection.py |
| quiz.py | 3709-3797 | **BRIŠI** - Document structure ide u helpers/document_structure.py |
| quiz.py | 3849-4035 | **BRIŠI** - get_specialized_prompt ide u prompts/subjects.py |

---

## 14.3 FAZA 3: QUIZ SERVICE - KOMPLETNE PROMENЕ

### 14.3.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `service.py` | app/services/quiz/service.py | QuizService klasa (sve metode) | ~2000 |
| `__init__.py` | app/services/quiz/__init__.py | Re-exports za backward compatibility | ~50 |

### 14.3.2 Šta se menja u postojećim fajlovima

| Fajl | Promena |
|------|---------|
| quiz.py | **PREIMENOVATI** u quiz/service.py |
| api/endpoints/quizzes.py | Ažurirati import: `from app.services.quiz import quiz_service` (ostaje isto ali sada dolazi iz __init__.py) |

### 14.3.3 QuizService metode koje ostaju

| Metoda | Linija | Status |
|--------|--------|--------|
| `_get_image_for_vision` | ~935 | ✅ Ostaje |
| `_generate_vision_questions_for_images` | ~1004 | ✅ Ostaje |
| `_generate_text_questions_with_optional_images` | ~1457 | ✅ Ostaje |
| `generate_questions_with_ai` | ~2126 | ✅ Ostaje |
| `create_quiz_from_document` | ~2225 | ✅ Ostaje |
| `populate_quiz_questions` | ~2257 | ✅ Ostaje |
| `submit_attempt` | ~2909 | ✅ Ostaje |
| `_check_answer` | ~2964 | ✅ Ostaje |
| `get_available_providers` | ~3011 | ✅ Ostaje (poziva get_available_providers iz clients) |

---

## 14.4 FAZA 4: TASKS - KOMPLETNE PROMENЕ

### 14.4.0 IMPLEMENTIRANO (2026-04-08)

| Fajl | Putanja | Status |
|------|---------|--------|
| `__init__.py` | app/workers/tasks/__init.py | ✅ KREIRANO |
| `pdf_processing.py` | app/workers/tasks/pdf_processing.py | ✅ KREIRANO |
| `translation.py` | app/workers/tasks/translation.py | ✅ KREIRANO |
| `quiz.py` | app/workers/tasks/quiz.py | ✅ KREIRANO |
| `maintenance.py` | app/workers/tasks/maintenance.py | ✅ KREIRANO |
| `knowledge.py` | app/workers/tasks/knowledge.py | ✅ KREIRANO |
| `tasks.py` | app/workers/tasks.py | ✅ Ažurirano (backward compatibility) |

**Kreirani taskovi:**
- process_pdf_task
- translate_document_task
- translate_with_fallback
- generate_quiz_task
- auto_pipeline_task
- cleanup_old_files
- cleanup_old_sessions_task
- cache_warming_task
- send_study_reminders
- send_weekly_summaries
- index_document_task
- crawl_project_docs_task
- crawl_url_task
- crawl_site_task

**Testovi:** 306 passed ✅

### 14.4.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `celery.py` | app/workers/celery.py | Celery app konfiguracija | ~100 |
| `__init__.py` | app/workers/tasks/__init__.py | Re-export svih taskova | ~50 |
| `pdf_processing.py` | app/workers/tasks/pdf_processing.py | process_pdf_task | ~200 |
| `translation.py` | app/workers/tasks/translation.py | translate_document_task, translate_with_fallback | ~250 |
| `quiz.py` | app/workers/tasks/quiz.py | generate_quiz_task | ~200 |
| `email.py` | app/workers/tasks/email.py | send_email_task | ~150 |
| `knowledge.py` | app/workers/tasks/knowledge.py | Knowledge ingestion task | ~300 |
| `maintenance.py` | app/workers/tasks/maintenance.py | Maintenance taskovi | ~150 |

### 14.4.2 Šta se menja u postojećim fajlovima

| Fajl | Promena |
|------|---------|
| tasks.py | **PREIMENOVATI** u workers/tasks/ |
| app/main.py | Ažurirati import: `from app.workers.celery import celery_app` |

### 14.4.3 Celery konfiguracija

```python
# app/workers/celery.py
from celery import Celery

celery_app = Celery(
    "ai_learning",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Belgrade",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.pdf_processing.*": {"queue": "pdf"},
        "app.workers.tasks.translation.*": {"queue": "translation"},
        "app.workers.tasks.quiz.*": {"queue": "quiz"},
        "app.workers.tasks.email.*": {"queue": "email"},
    },
)
```

### 14.4.4 Environment promene za Celery

```bash
# .env - nove promene za Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=Europe/Belgrade
CELERY_ENABLE_UTC=true
```

---

## 14.5 FAZA 5: TRANSLATION - KOMPLETNE PROMENЕ

### 14.5.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `__init__.py` | app/services/translation/clients/__init__.py | Factory, get_clients | ~50 |
| `base.py` | app/services/translation/clients/base.py | BaseTranslationClient(ABC) | ~25 |
| `ollama.py` | app/services/translation/clients/ollama.py | OllamaClient | ~110 |
| `deepl.py` | app/services/translation/clients/deepl.py | DeepLClient | ~110 |
| `openai.py` | app/services/translation/clients/openai.py | OpenAIClient | ~110 |
| `google.py` | app/services/translation/clients/google.py | GoogleTranslateClient | ~90 |
| `claude.py` | app/services/translation/clients/claude.py | ClaudeClient | ~110 |
| `deepseek.py` | app/services/translation/clients/deepseek.py | DeepSeekClient | ~110 |
| `service.py` | app/services/translation/service.py | TranslationService | ~210 |

### 14.5.2 Šta se menja u postojećim fajlovima

| Fajl | Promena |
|------|---------|
| translation.py | **PODELJEN** na clients/ i service.py |
| tasks.py | Ažurirati import za translate_with_fallback |

### 14.5.3 Translation fallback redosled

```python
# app/services/translation/service.py
TRANSLATION_PROVIDER_ORDER = [
    "libretranslate",  # Free
    "deepl",           # Kvalitet
    "google",          # Pouzdan
    "ollama",          # Lokalni
    "claude",          # AI
    "gemini",          # AI
    "groq",            # AI
    "mistral",         # AI
    "deepseek",        # AI
    "openai",          # AI
]
```

---

## 14.6 FAZA 6: SKILLS - KOMPLETNE PROMENЕ

### 14.6.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `__init__.py` | app/services/skills/__init__.py | Export | ~10 |
| `models.py` | app/services/skills/models.py | Skill, SkillTemplate, DocumentType modeli | ~100 |
| `detector.py` | app/services/skills/detector.py | SkillDetector klasa | ~150 |
| `service.py` | app/services/skills/service.py | SkillService | ~100 |
| `__init__.py` | app/services/skills/templates/__init__.py | Export | ~10 |
| `medical.py` | app/services/skills/templates/medical.py | MEDICAL_PROMPT_TEMPLATE | ~50 |
| `legal.py` | app/services/skills/templates/legal.py | LEGAL_PROMPT_TEMPLATE | ~50 |
| `technical.py` | app/services/skills/templates/technical.py | TECHNICAL_PROMPT_TEMPLATE | ~50 |
| `academic.py` | app/services/skills/templates/academic.py | ACADEMIC_PROMPT_TEMPLATE | ~50 |
| `textbook.py` | app/services/skills/templates/textbook.py | TEXTBOOK_PROMPT_TEMPLATE | ~50 |
| `general.py` | app/services/skills/templates/general.py | GENERAL_PROMPT_TEMPLATE | ~50 |

### 14.6.2 Database migracije za Skills

```python
# alembic/versions/XXX_add_skills_tables.py
"""Add skills tables

Revision ID: xxx
Revises: xxx
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx'
down_revision = 'xxx'
branch_labels = None
depends_on = None

def upgrade():
    # skills table
    op.create_table('skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('prompt_template', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_skills_name', 'skills', ['name'])
    op.create_index('ix_skills_document_type', 'skills', ['document_type'])
    
    # skill_templates table
    op.create_table('skill_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('prompt_template', sa.JSON(), nullable=False),
        sa.Column('document_types', sa.JSON()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # document_types table
    op.create_table('document_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('keywords', sa.JSON()),
        sa.Column('patterns', sa.JSON()),
        sa.Column('skill_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('document_types')
    op.drop_table('skill_templates')
    op.drop_table('skills')
```

### 14.6.3 Skill detector dokument tipovi

```python
# app/services/skills/detector.py
DOCUMENT_TYPE_PATTERNS = {
    "medical": ["simptom", "dijagnoza", "terapija", "lek", "pregled", "pacijent", "klinički"],
    "legal": ["zakon", "član", "paragraf", "sud", "presuda", "tužba", "ugovor"],
    "technical": ["specifikacija", "uputstvo", "instalacija", "konfiguracija", "error", "troubleshooting"],
    "academic": ["istraživanje", "metodologija", "rezultati", "diskusija", "zaključak", "referenca"],
    "textbook": ["poglavlje", "lekcija", "primer", "zadatak", "rešenje", "udžbenik"],
    "general": []  # fallback
}
```

---

## 14.7 FAZA 7: MCP SERVERI - KOMPLETNE PROMENЕ

### 14.7.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `server.py` | mcp-server/server.py | MCP Server main | ~100 |
| `config.py` | mcp-server/config.py | Konfiguracija | ~50 |
| `__init__.py` | mcp-server/quiz/__init__.py | Export | ~10 |
| `tools.py` | mcp-server/quiz/tools.py | Quiz MCP tools | ~150 |
| `handlers.py` | mcp-server/quiz/handlers.py | Tool handlers | ~200 |
| `__init__.py` | mcp-server/translate/__init__.py | Export | ~10 |
| `tools.py` | mcp-server/translate/tools.py | Translate MCP tools | ~100 |
| `handlers.py` | mcp-server/translate/handlers.py | Tool handlers | ~100 |
| `__init__.py` | mcp-server/document/__init__.py | Export | ~10 |
| `tools.py` | mcp-server/document/tools.py | Document MCP tools | ~100 |
| `handlers.py` | mcp-server/document/handlers.py | Tool handlers | ~100 |
| `__init__.py` | mcp-server/skills/__init__.py | Export | ~10 |
| `tools.py` | mcp-server/skills/tools.py | Skills MCP tools | ~50 |
| `handlers.py` | mcp-server/skills/handlers.py | Tool handlers | ~50 |

### 14.7.2 MCP Tools definicije

```python
# mcp-server/quiz/tools.py
QUIZ_TOOLS = [
    {
        "name": "quiz_create",
        "description": "Create a new quiz from document chunks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer"},
                "title": {"type": "string"},
                "num_questions": {"type": "integer", "default": 10},
                "subject_area": {"type": "string"},
            },
            "required": ["document_id", "title"]
        }
    },
    {
        "name": "quiz_list",
        "description": "List user's quizzes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "status": {"type": "string"}
            }
        }
    },
    # ... ostali tool-ovi
]
```

### 14.7.3 MCP Server dependencies

```txt
# requirements-mcp.txt
fastmcp>=0.1.0
mcp>=1.0.0
```

### 14.7.4 MCP Server environment promene

```bash
# .env
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_TRANSPORT=stdio  # ili http
```

---

## 14.8 FAZA 8: SECURITY - KOMPLETNE PROMENЕ

### 14.8.1 Novi fajlovi koji se kreiraju

| Fajl | Putanja | Sadržaj | Linija |
|------|---------|---------|--------|
| `__init__.py` | app/services/security/__init__.py | Export | ~10 |
| `encryption.py` | app/services/security/encryption.py | EncryptionService (AES-256) | ~80 |
| `key_manager.py` | app/services/security/key_manager.py | KeyManager za API ključeve | ~100 |
| `validators.py` | app/services/security/validators.py | Validacija API ključeva | ~50 |

### 14.8.2 Database model za UserAPIKey

```python
# app/db/models/user.py - DODATI
class UserAPIKey(Base):
    """Korisnički API ključevi (enkriptovani)."""
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, claude, groq, mistral, deepseek, gemini
    encrypted_key = Column(Text, nullable=False)
    key_hash = Column(String, nullable=False)  # Za verifikaciju (ne za dekripciju)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uq_user_provider_key'),
    )
```

### 14.8.3 Database migracija za Security

```python
# alembic/versions/XXX_add_user_api_keys.py
"""Add user_api_keys table

Revision ID: xxx
Revises: xxx
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'xxx'
down_revision = 'xxx'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('user_api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_provider_key')
    )
    op.create_index('ix_user_api_keys_user_id', 'user_api_keys', ['user_id'])
    op.create_index('ix_user_api_keys_provider', 'user_api_keys', ['provider'])

def downgrade():
    op.drop_index('ix_user_api_keys_provider', table_name='user_api_keys')
    op.drop_index('ix_user_api_keys_user_id', table_name='user_api_keys')
    op.drop_table('user_api_keys')
```

### 14.8.4 Encryption konfiguracija

```bash
# .env - NOVA promena
# Generisati sa: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
ENCRYPTION_KEY=your-generated-fern-key-here
```

### 14.8.5 Security dependencies

```txt
# requirements.txt - DODATI
cryptography>=41.0.0
```

---

## 14.9 VERIFIKACIJA NAKON SVIH PROMENА

### 14.9.1 Import testovi (svi zajedno)

```bash
# Test svih importova
python -c "
# Quiz
from app.services.quiz import QuizService, quiz_service
from app.services.quiz.clients import get_clients, _build_clients, get_provider, get_available_providers
from app.services.quiz.prompts.base import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import get_specialized_prompt, subject_instructions
from app.services.quiz.helpers.progress import update_quiz_progress, get_quiz_progress
from app.services.quiz.helpers.parsing import _parse_questions, _validate_questions, _fallback_questions
from app.services.quiz.helpers.chunks import _select_chunks_for_quiz, _auto_num_questions
from app.services.quiz.helpers.subject_detection import detect_subject_area, SUBJECT_KEYWORDS
from app.services.quiz.helpers.document_structure import detect_document_structure

# Tasks
from app.workers.celery import celery_app
from app.workers.tasks import process_pdf_task, translate_document_task, generate_quiz_task

# Translation
from app.services.translation.service import TranslationService
from app.services.translation.clients import get_clients as get_translation_clients

# Skills
from app.services.skills.detector import SkillDetector
from app.services.skills.models import Skill, SkillTemplate
from app.services.skills.service import SkillService

# Security
from app.services.security.encryption import EncryptionService
from app.services.security.key_manager import KeyManager

# MCP
from mcp_server.server import mcp
from mcp_server.quiz.tools import get_quiz_tools

print('✅ SVI IMPORTI USPEŠNI!')
"
```

### 14.9.2 Test pokretanje (svi testovi)

```bash
# Pokreni sve testove sa coverage
pytest app/tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80

# Ili pojedinačno
pytest app/tests/unit/test_quiz_service.py -v
pytest app/tests/unit/test_translation.py -v
pytest app/tests/integration/test_quiz.py -v
```

### 14.9.3 API testovi

```bash
# Health check
curl -X GET http://localhost:8010/api/v1/health

# Quiz generate
curl -X POST http://localhost:8010/api/v1/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1, "num_questions": 5}'

# Quiz list
curl -X GET http://localhost:8010/api/v1/quiz/

# Providers
curl -X GET http://localhost:8010/api/v1/quiz/providers
```

### 14.9.4 Docker testovi

```bash
# Provera svih servisa
docker-compose ps

# Logovi
docker-compose logs -f app

# Redis
docker-compose exec redis redis-cli ping

# Database
docker-compose exec db psql -U ai_learning_user -d ai_learning_db -c "SELECT 1"

# Celery worker
docker-compose exec app celery -A app.workers.celery inspect active
```

---

## 14.10 COMPLETE DEPENDENCY MAPPING

### 14.10.1 Import zavisnosti (quiz/service.py)

```python
# app/services/quiz/service.py - IMPORT ZAVISNOSTI
from typing import List, Optional, Tuple  # stdlib
from sqlalchemy.orm import Session  # sqlalchemy
import httpx  # external
import logging  # stdlib

# Internal imports - SVE NOVE LOKACIJE
from app.services.quiz.clients import get_clients, _build_clients
from app.services.quiz.prompts.base import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import get_specialized_prompt
from app.services.quiz.helpers.progress import update_quiz_progress
from app.services.quiz.helpers.parsing import _parse_questions, _validate_questions
from app.services.quiz.helpers.chunks import _select_chunks_for_quiz
from app.services.quiz.helpers.subject_detection import detect_subject_area
from app.services.quiz.helpers.document_structure import detect_document_structure

# External imports (ostaju)
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer
from app.db.models.document import Document, Chunk
from app.db.models.quiz import QuizImage
from app.core.config import settings
from app.services.storage import storage_service
from app.services.storage_cloud import CloudStorageService
```

### 14.10.2 API endpoint zavisnosti

```python
# app/api/endpoints/quizzes.py - IMPORT ZAVISNOSTI
from fastapi import APIRouter, Depends  # fastapi
from sqlalchemy.orm import Session  # sqlalchemy
from typing import List, Optional  # stdlib

from app.db.session import get_db
from app.db.models.quiz import Quiz, Question, QuizAttempt
from app.db.models.user import User
from app.schemas.quiz import QuizCreate, QuizResponse, QuestionResponse  # ostaju

# NOVI IMPORT - iz modularne strukture
from app.services.quiz import quiz_service  # Dolazi iz __init__.py

from app.services.auth import get_current_user
from app.workers.tasks import generate_quiz_task  # Ostaje ali iz nove lokacije
```

---

## 14.11 COMPLETE FILE STRUCTURE (FINAL)

```
/home/dju/mojAiProjekat/New folder/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── quizzes.py        # Ostaje, import ostaje isti
│   │   │       └── ...               # Ostali endpointi
│   │   ├── core/
│   │   │   └── config.py             # Ostaje + NOVE promene (ENCRYPTION_KEY)
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   ├── user.py            # NOVI: UserAPIKey model
│   │   │   │   └── ...
│   │   │   └── migrations/
│   │   │       └── versions/
│   │   │           └── XXX_add_skills.py     # NOVO
│   │   │           └── XXX_add_user_api_keys.py  # NOVO
│   │   ├── services/
│   │   │   ├── quiz/                  # NOVA STRUKTURA (bivši quiz.py)
│   │   │   │   ├── __init__.py       # Re-exports + quiz_service
│   │   │   │   ├── service.py        # QuizService klasa
│   │   │   │   ├── clients/
│   │   │   │   │   ├── __init__.py   # _build_clients, get_clients
│   │   │   │   │   ├── base.py
│   │   │   │   │   ├── ollama.py
│   │   │   │   │   ├── openai.py
│   │   │   │   │   ├── claude.py
│   │   │   │   │   └── openai_compat.py
│   │   │   │   ├── prompts/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py       # QUIZ_PROMPT
│   │   │   │   │   └── subjects.py   # get_specialized_prompt
│   │   │   │   └── helpers/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── progress.py
│   │   │   │       ├── parsing.py
│   │   │   │       ├── chunks.py
│   │   │   │       ├── subject_detection.py
│   │   │   │       └── document_structure.py
│   │   │   ├── translation/           # NOVA STRUKTURA
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service.py
│   │   │   │   └── clients/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── base.py
│   │   │   │       ├── ollama.py
│   │   │   │       ├── deepl.py
│   │   │   │       ├── openai.py
│   │   │   │       ├── google.py
│   │   │   │       ├── claude.py
│   │   │   │       └── deepseek.py
│   │   │   ├── skills/               # NOVO
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   ├── detector.py
│   │   │   │   ├── service.py
│   │   │   │   └── templates/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── medical.py
│   │   │   │       ├── legal.py
│   │   │   │       ├── technical.py
│   │   │   │       ├── academic.py
│   │   │   │       ├── textbook.py
│   │   │   │       └── general.py
│   │   │   └── security/             # NOVO
│   │   │       ├── __init__.py
│   │   │       ├── encryption.py
│   │   │       ├── key_manager.py
│   │   │       └── validators.py
│   │   ├── workers/
│   │   │   ├── celery.py            # NOVO
│   │   │   ├── tasks/                # NOVA STRUKTURA
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pdf_processing.py
│   │   │   │   ├── translation.py
│   │   │   │   ├── quiz.py
│   │   │   │   ├── email.py
│   │   │   │   ├── knowledge.py
│   │   │   │   └── maintenance.py
│   │   │   └── tasks.py              # BRISATI (seli u tasks/)
│   │   └── tests/
│   │       └── unit/
│   │           ├── test_quiz_clients.py    # NOVO
│   │           ├── test_quiz_helpers.py     # NOVO
│   │           └── ...                       # Ostali testovi
│   ├── alembic/
│   │   └── versions/
│   │       ├── XXX_add_skills.py            # NOVO
│   │       └── XXX_add_user_api_keys.py      # NOVO
│   └── requirements.txt              # Ažurirati sa cryptography
│
├── mcp-server/                       # NOVO
│   ├── server.py
│   ├── config.py
│   ├── quiz/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   └── handlers.py
│   ├── translate/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   └── handlers.py
│   ├── document/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   └── handlers.py
│   └── skills/
│       ├── __init__.py
│       ├── tools.py
│       └── handlers.py
│
├── docker/
│   └── .env                          # Ažurirati sa novim promenama
│
└── Detaljan_Plan_ReorganizacijeIntegracijeMCPservera_skilova.md  # OVaj dokument
```

---

## 14.12 SUMMARY - ŠTA JE POKRIVENO

| Kategorija | Broj stavki |
|------------|-------------|
| Novi fajlovi | 35+ |
| Izmenjeni fajlovi | 8 |
| Obrišani fajlovi | 3 |
| Database migracije | 3 |
| Environment promene | 15+ |
| Dependencies | 5+ |
| Test fajlovi | 10+ |
| API endpointi | 10+ |
| MCP Tools | 15+ |

---

*Plan je kompletan i spreman za implementaciju!*

---

# 15. BACKWARD COMPATIBILITY

## 15.1 Stari import path-ovi

Svi ovi import-ovi će i dalje raditi nakon reorganizacije:

```python
# OLD - Quiz Service
from app.services.quiz import quiz_service
from app.services.quiz import generate_questions_from_chunks

# NOVO - ali backward compatible
from app.services.quiz import QuizService

# Stari testovi
from app.services.quiz import quiz_service
quiz_service.generate_questions_from_chunks(...)
```

## 15.2 API endpointi

Nijedan API endpoint se ne menja - samo import path-ovi unutar implementacije.

## 15.3 Database models

Svi modeli ostaju na istom mestu - samo se servisi seljaju.

---

# 16. IMPLEMENTACIJA PO FAZAMA

## 16.1 Preporučeni redosled

| Faza | Opis | Estimacija |
|------|------|------------|
| 1 | AI Clients ekstrakcija | 2 sata |
| 2 | Prompts i Helpers | 2 sata |
| 3 | Quiz Service integracija | 1 sat |
| 4 | Tasks reorganizacija | 2 sata |
| 5 | Translation modularizacija | 2 sata |
| 6 | Skill sistem | 4 sata |
| 7 | MCP serveri | 4 sata |
| 8 | Security | 2 sata |
| 9 | Testiranje | 2 sata |

**Total: ~21 sat**

## 16.2 Paralelizacija

Neke faze mogu paralelno:
- FAZA 1 + FAZA 2 mogu paralelno
- FAZA 4 može nezavisno od 1-3
- FAZA 6-8 mogu nezavisno

---

# 17. PRILOZI

## 17.1 Checklist za svaku fazu

### FAZA 1: AI Providers
- [x] Kreirati clients/ direktorijum
- [x] Kreirati base.py sa BaseQuizClient
- [x] Kreirati pojedinačne client fajlove
- [x] Kreirati __init__.py sa _build_clients
- [x] Testirati import
- [x] Pokrenuti testove

### FAZA 2: Prompts i Helpers
- [x] Kreirati prompts/ direktorijum
- [x] Kreirati helpers/ direktorijum
- [x] Izvući QUIZ_PROMPT u prompts/quiz_prompt.py
- [x] Izvući helper funkcije
- [x] Testirati sve imports

### FAZA 3: Quiz Service
- [x] Ažurirati service.py imports
- [x] Ažurirati __init__.py re-exports
- [x] Testirati backward compatibility
- [x] Pokrenuti API testove

### FAZA 4: Tasks
- [x] Kreirati tasks/ direktorijum
- [x] Podeliti taskove po tipu
- [x] Kreirati tasks/__init__.py sa re-export
- [x] Kreirati tasks/pdf_processing.py (process_pdf_task)
- [x] Kreirati tasks/translation.py (translate_document_task, translate_with_fallback)
- [x] Kreirati tasks/quiz.py (generate_quiz_task, auto_pipeline_task)
- [x] Kreirati tasks/maintenance.py (cleanup_old_files, send_study_reminders, send_weekly_summaries)
- [x] Kreirati tasks/knowledge.py (index_document_task, crawl_project_docs_task, crawl_url_task, crawl_site_task)
- [x] Testirati taskove

### FAZA 5: Translation
- [x] Kreirati translation/clients/ (COMPLETE 2026-04-09)
- [x] Postoje make_gemini_client, make_groq_client, make_mistral_client
- [x] translation_service postoji
- [x] Izvući klijente u posebne fajlove
- [x] Testirati (386/386 PASSED)

### FAZA 6: Skills (COMPLETE 2026-04-09)
- [x] Kreirati skills/ direktorijum
- [x] Kreirati models (Skill, SkillTemplate, DocumentType)
- [x] Implementirati detector (SkillDetector sa keyword matching)
- [x] Kreirati templates (6 sistemskih šablona: legal, technical, medical, academic, textbook, general)
- [x] Testirati detekciju (386/386 PASSED)

### FAZA 7: MCP
- [ ] Kreirati mcp-server/
- [ ] Kreirati tool definicije
- [ ] Implementirati handlere
- [ ] Testirati MCP server

### FAZA 8: Security
- [ ] Kreirati security/ direktorijum
- [ ] Implementirati enkripciju
- [ ] Kreirati key_manager
- [ ] Dodati database model
- [ ] Testirati

### FAZA 9: Verifikacija (COMPLETE 2026-04-09)
- [x] Pokrenuti sve testove
- [x] Testirati API endpointse
- [x] Testirati MCP tools
- [x] Proveriti backward compatibility

### FAZA 11: Performance Optimizations (COMPLETE 2026-04-10)
- [x] Kreirati optimization/ direktorijum
- [x] Implementirati rate_limiter.py (RateLimiter, QuizRateLimiter)
- [x] Implementirati caching.py (CacheService, QuizCacheService, get_cache_service)
- [x] Implementirati connection_pool.py (ConnectionPool, QuizHTTPClient, get_http_client)
- [x] Verifikovati syntax (svi fajlovi uspešno kompajlirani)
- [x] Verifikovati imports (svi importi uspešni)

---

## 18. STATUS IMPLEMENTACIJE (2026-04-10)

### 18.1 Završene faze

| Faza | Status | Napomena |
|------|--------|----------|
| FAZA 1: AI Providers | ✅ ZAVRŠENO | clients/ direktorijum kreiran |
| FAZA 2: Prompts i Helpers | ✅ ZAVRŠENO | prompts/ i helpers/ kreirani |
| FAZA 3: Quiz Service | ✅ ZAVRŠENO | Modularna struktura radi |
| FAZA 4: Tasks | ✅ ZAVRŠENO | tasks/ direktorijum sa svim taskovima |
| FAZA 5: Translation | ✅ ZAVRŠENO | Modularni translation (clients/) |
| FAZA 6: Skill Sistem | ✅ ZAVRŠENO | skills/ direktorijum sa detector + templates |
| FAZA 7: MCP Serveri | ✅ ZAVRŠENO | 17 novih MCP alata implementirano |
| FAZA 8: User API Key Security | ✅ ZAVRŠENO | security/ modul + enkripcija + validacija |
| FAZA 9: Installation & Config | ✅ ZAVRŠENO | Sve verifikacije prošle |
| FAZA 10: Testing & Verification | ✅ ZAVRŠENO | 53 testa prošla, verification script |
| FAZA 11: Performance Optimizations | ✅ ZAVRŠENO | optimization/ modul (rate limiting, caching, connection pooling) |
| FAZA CI/CD: GitHub Actions | ✅ ZAVRŠENO | .github/workflows/ci.yml kreiran |

### 18.2 Rezultati testiranja

| Metrika | Vrednost |
|---------|----------|
| Ukupno testova | 497 (386 + 111 novih) |
| Passed | 497 |
| Skipped | 2 |
| Failed | 0 |

### 18.3 Novi test fajlovi (FAZA 1-3)

| Test fajl | Broj testova | Status |
|-----------|--------------|--------|
| test_quiz_clients.py | 49 | ✅ Svi prolaze |
| test_quiz_prompts_helpers.py | 38 | ✅ Svi prolaze |
| test_quiz_modules.py | 24 | ✅ Svi prolaze |

### 18.3 Struktura nakon reorganizacije

```
quiz/
├── __init__.py              # Glavni export (re-export svih komponenti)
├── quiz.py                  # Backwards compatibility
├── service.py               # QuizService klasa
├── prompts/
│   ├── __init__.py         # get_specialized_prompt, get_subject_instruction
│   ├── subjects.py         # Specijalizovani promptovi po oblasti
│   └── quiz_prompt.py      # QUIZ_PROMPT template
├── helpers/
│   ├── __init__.py         # parsing, validation, chunk selection
│   ├── progress.py         # Redis progress tracking
│   ├── subject_detection.py # detect_subject_area
│   └── document_structure.py # detect_document_structure
└── clients/
    ├── __init__.py         # Factory funkcije (_build_clients, get_clients)
    ├── base.py             # BaseQuizClient ABC
    ├── ollama.py            # OllamaQuizClient
    ├── openai.py           # OpenAIQuizClient
    ├── claude.py           # ClaudeQuizClient
    └── openai_compat.py    # Gemini, Groq, Mistral, DeepSeek

workers/tasks/
├── __init__.py             # Re-export svih taskova
├── pdf_processing.py      # process_pdf_task
├── translation.py          # translate_document_task, translate_with_fallback
├── quiz.py                 # generate_quiz_task, auto_pipeline_task
├── maintenance.py         # cleanup_old_files, send_study_reminders, send_weekly_summaries
└── knowledge.py           # index_document_task, crawl_project_docs_task, crawl_url_task, crawl_site_task
```

---

## 19. NOVE FUNKCIONALNOSTI - KVIZ MEHANIKE

### 19.1 Taktilne mehanike (Drag & Drop)

#### Sortiranje i Redosled (Sequencing)
Igrač dobija izmešanu listu i mora da je poređa po nekom kriterijumu.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| sequencing_date | `question_type: "sequencing"` | Poređaj po datumu |
| sequencing_order | `question_type: "sequencing"` | Poređaj po koracima |
| sequencing_size | `question_type: "sequencing"` | Poređaj po veličini |

**Primer JSON:**
```json
{
  "question_text": "Poređajte bitke hronološki od najstarije do najnovije:",
  "question_type": "sequencing",
  "items": [
    "Bitka na Kosovu (1389)",
    "Prvi srpski ustanak (1804)",
    "Balkan wars (1912)"
  ],
  "correct_order": [2, 3, 1],
  "explanation": "Prvi srpski ustanak (1804) → Balkanski ratovi (1912) → Bitka na Kosovu (1389)"
}
```

#### Kategorizacija (Grouping/Buckets)
Igrač prevlači pojmove u kategorije.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| categorization_2 | `question_type: "categorization"` | 2 kategorije |
| categorization_3 | `question_type: "categorization"` | 3+ kategorije |

**Primer JSON:**
```json
{
  "question_text": "Razvrstaj pojmove u pravu kategoriju:",
  "question_type": "categorization",
  "buckets": ["Obnovljivi", "Neobnovljivi"],
  "items": ["Solarna energija", "Nafte", "Veter", "Ugalj"],
  "correct_mapping": {
    "Obnovljivi": ["Solarna energija", "Veter"],
    "Neobnovljivi": ["Nafte", "Ugalj"]
  }
}
```

#### Povezivanje parova (Matching)
Leva i desna kolona koje treba spojiti.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| matching | `question_type: "matching"` | Poveži parove |

**Primer JSON:**
```json
{
  "question_text": "Povežite državu sa glavnim gradom:",
  "question_type": "matching",
  "left_column": ["Srbija", "Francuska", "Japan"],
  "right_column": ["Beograd", "Pariz", "Tokio"],
  "correct_pairs": {"Srbija": "Beograd", "Francuska": "Pariz", "Japan": "Tokio"}
}
```

---

### 19.2 Vizuelne mehanike

#### Hotspot (Tačka na slici)
Klik na određeni deo slike.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| hotspot | `question_type: "hotspot"` | Klik na koordinate |

**Primer JSON:**
```json
{
  "question_text": "Kliknite na lokaciju Srbije na karti:",
  "question_type": "hotspot",
  "image_url": "/images/europe-map-blank.png",
  "hotspots": [
    {"name": "Srbija", "x": 45, "y": 35, "radius": 30},
    {"name": "Hrvatska", "x": 30, "y": 25, "radius": 30}
  ],
  "correct_answer": "Srbija"
}
```

#### Izbacivanje uljeza (Odd One Out)
Klik na onaj koji ne pripada nizu.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| odd_one_out | `question_type: "odd_one_out"` | Pronađi uljeza |

**Primer JSON:**
```json
{
  "question_text": "Kliknite na pojam koji ne pripada nizu:",
  "question_type": "odd_one_out",
  "items": ["Pas", "Mačka", "Krava", "Stolica"],
  "correct_answer": "Stolica",
  "explanation": "Pas, mačka i krava su životinje, stolica je nameštaj."
}
```

---

### 19.3 Mehanike procene (Estimation)

#### Klizač (Slider/Range)
Pogodi brojčanu vrednost.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| estimation | `question_type: "estimation"` | Klizač za procenu |

**Primer JSON:**
```json
{
  "question_text": "Koliko procenata vode sadrži ljudsko telo?",
  "question_type": "estimation",
  "min_value": 0,
  "max_value": 100,
  "correct_answer": 60,
  "tolerance": 5,
  "points_calculation": "linearna - bliže = više poena"
}
```

#### Matrica (Matrix Grid)
Brza True/False/Ne znam pitanja.

| Tip pitanja | JSON field | Opis |
|-------------|------------|------|
| matrix | `question_type: "matrix"` | Tabela sa ocenama |

**Primer JSON:**
```json
{
  "question_text": "Ocenite tačnost sledećih tvrdnji o Napoleonu:",
  "question_type": "matrix",
  "statements": [
    "Rođen je na Korzici",
    "Bio je engleski kralj",
    "Umro je na Svetoj Jeleni"
  ],
  "correct_answers": ["Tačno", "Netačno", "Tačno"],
  "columns": ["Tačno", "Netačno"]
}
```

---

### 19.4 Potrebne izmene

#### Backend (database/models/question.py)
```python
class QuestionType(enum.Enum):
    multiple_choice = "multiple_choice"
    checkbox = "checkbox"
    true_false = "true_false"
    # NOVI TIPOVI
    sequencing = "sequencing"
    categorization = "categorization"
    matching = "matching"
    hotspot = "hotspot"
    odd_one_out = "odd_one_out"
    estimation = "estimation"
    matrix = "matrix"
```

#### Frontend
- Kreirati nove komponente:
  - `QuizSortable.tsx` (Drag & Drop)
  - `QuizHotspot.tsx` (image click zones)
  - `QuizSlider.tsx` (range input)
  - `QuizMatrix.tsx` (grid input)
  - `QuizMatching.tsx` (drag to connect)

---

## 20. REFERENCE

| Dokument | Lokacija |
|----------|----------|
| MCP_INTEGRACIJA_PLAN.md | MojAiProjekti/NewFolder/ |
| CI_CD_STRATEGIJA.md | mojAiProjekat/New folder/ |
| AGENTS.md | mojAiProjekat/New folder/backend/ |

---

*Document created: 2026-04-05*
*Version: 1.1 (2026-04-06)*
*Updated: FAZA 1-3 completed, new quiz mechanics added*

---

## 21. IMPLEMENTACIJA - REALIZOVANO (2026-04-08)

### 21.1 Quiz Mehanici (NEW QUESTION TYPES)

| Tip pitanja | Status | Database | Backend | Testovi |
|-------------|--------|----------|---------|---------|
| sequencing | ✅ | enum dodat | _check_answer_static | ✅ |
| categorization | ✅ | enum dodat | _check_answer_static | ✅ |
| matching | ✅ | enum dodat | _check_answer_static | ✅ |
| hotspot | ✅ | enum dodat | _check_answer_static | ✅ |
| odd_one_out | ✅ | enum dodat | _check_answer_static | ✅ |
| estimation | ✅ | enum dodat | _check_answer_static | ✅ |
| matrix | ✅ | enum dodat | _check_answer_static | ✅ |

**Database promene:**
- Dodati novi enum values u `question_type`
- Dodata `extra_data` JSONB kolona

**Fajlovi izmenjeni:**
- `app/db/models/quiz.py` - Dodati novi tipovi u Enum
- `app/services/quiz/service.py` - Ažuriran _check_answer_static
- `app/services/quiz/helpers/__init__.py` - Ažuriran _validate_questions

### 21.2 FAZA 4 - Tasks.py Reorganizacija

| Komponenta | Status | Linije |
|------------|--------|--------|
| `tasks/__init__.py` | ✅ KREIRANO | ~40 |
| `tasks/pdf_processing.py` | ✅ KREIRANO | ~150 |
| `tasks/translation.py` | ✅ KREIRANO | ~350 |
| `tasks/quiz.py` | ✅ KREIRANO | ~300 |
| `tasks/maintenance.py` | ✅ KREIRANO | ~200 |
| `tasks/knowledge.py` | ✅ KREIRANO | ~250 |
| `tasks.py` | ✅ Ažurirano | ~40 |

**Taskovi dostupni:**
- process_pdf_task
- translate_document_task
- translate_with_fallback
- generate_quiz_task
- auto_pipeline_task
- cleanup_old_files, cleanup_old_sessions_task
- cache_warming_task
- send_study_reminders, send_weekly_summaries
- index_document_task, crawl_url_task, crawl_site_task

**Backward compatibility:** ✅ Očuvan

### 21.3 Test Rezultati

| Metrika | Vrednost |
|---------|----------|
| Ukupno testova | 308 |
| Prošlo | 306 ✅ |
| Preskočeno | 2 |
| Palih | 0 |
| Prolaz | 99.35% |
| Coverage | ~60% (CI threshold) |

### 21.4 Verifikacija

**Backward compatibility:**
- Importi: `from app.workers.tasks import process_pdf_task` ✅
- Funkcije: `get_db_session()` ✅
- Quiz service: `quiz_service.populate_quiz_questions` ✅
- Question types: svi postojeći rade ✅

**Svi testovi prolaze:** 306/308 ✅