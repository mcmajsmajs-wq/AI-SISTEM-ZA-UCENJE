# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
Quiz Service - Multi-Provider AI Quiz Generation

Verzija: 2.0.0
Autor: Branko Suznjevic

Funkcionalnosti:
  - Ollama (lokalni, besplatni)
  - OpenAI (GPT-4 / GPT-4o)
  - Claude (Anthropic)
  - Gemini (Google)
  - DeepSeek
  - Groq
  - Mistral
  + fallback chain
================================================================================
"""

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import signal

import httpx
import redis as redis_client
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer
from app.db.models.document import Document, Chunk

logger = logging.getLogger(__name__)


def _get_redis():
    """Get Redis connection for progress tracking."""
    try:
        return redis_client.from_url(settings.REDIS_CONNECTION_URL, decode_responses=True)
    except Exception:
        return None


def update_quiz_progress(quiz_id: str, current: int, total: int):
    """Update quiz progress in Redis - completely separate from DB."""
    import redis as redis_lib
    try:
        r = redis_lib.Redis.from_url(settings.REDIS_CONNECTION_URL, decode_responses=True)
        r.hset(f"quiz_progress:{quiz_id}", mapping={
            "current": str(current),
            "total": str(total)
        })
        r.expire(f"quiz_progress:{quiz_id}", 3600)
        r.close()
    except Exception as e:
        logger.debug(f"Redis progress update failed: {e}")


def get_quiz_progress(quiz_id: str) -> tuple:
    """Get quiz progress from Redis. Returns (current, total)."""
    try:
        r = _get_redis()
        if r:
            data = r.hgetall(f"quiz_progress:{quiz_id}")
            if data:
                return int(data.get("current", 0)), int(data.get("total", 0))
    except Exception:
        pass
    return 0, 0

logger = logging.getLogger(__name__)


# ============================================================
# PROMPT
# ============================================================

QUIZ_PROMPT = """You are an expert educator and assessment designer. Based on the following text, generate exactly {num_questions} high-quality quiz questions that test deep understanding.

STRICT FILTERING RULES - IGNORE the following content COMPLETELY:
1. "This page intentionally left blank" and similar blank page notices
2. Copyright notices, edition notices (e.g., "Second Edition", "Third Edition", "First Edition")
3. "Notice to Readers", "Notice to Reader" or similar disclaimers
4. Table of Contents, Prefaces, Acknowledgments, Introductions
5. Figure captions, image descriptions, "Figure X:" without substantive content
6. Page numbers, headers, footers, running titles
7. Very short content (< 100 characters)
8. Generic statements without specific information
9. Notes sections, footnotes, endnotes, "Notes:" sections
10. Cover pages, back covers, front matter, back matter
11. "About the Author", author biography pages
12. Index pages, glossaries
13. Any page that is mostly references or citations
14. OCR noise, garbled text, unreadable characters

ONLY create questions from:
- Actual substantive content with specific facts, concepts, definitions
- Step-by-step processes or procedures with detailed steps
- Specific examples with concrete details
- Definitions of key terms with explanations
- Data, statistics, research findings with numbers
- Cause-effect relationships explained in text
- Detailed explanations of concepts
- Historical events with dates and details

IMPORTANT - QUESTION TYPES:
- 60% multiple_choice — 1 correct answer, 4 plausible options
- 25% checkbox — 2-4 correct answers, 4 options (select ALL that apply)  
- 15% true_false — balanced mix of TRUE and FALSE statements

CRITICAL: TRUE/FALSE BALANCE
- For TRUE/FALSE questions: Exactly 50% should be TRUE, 50% FALSE
- Create false statements by: negating a fact, changing a number/date, reversing cause-effect, stating opposite
- NEVER make all true/false questions have the same answer!

QUESTION QUALITY - Make questions ANALYTICAL and THOUGHT-PROVOKING:
- NOT: "Koji je glavni grad Mesopotamije?" (simple recall)
- YES: "Zašto su gradovi Mesopotamije nastajali na rekama? Objasni geografski i ekonomski razlog."
- NOT: "Šta je hram?" (definition only)
- YES: "Čemu su služili zikgurati u drevnoj Mesopotamiji i kako se njihova funkcija razlikovala od običnih hramova?"

Options must be:
- Complete meaningful sentences (not single letters/words)
- Plausible but clearly distinguishable
- Testing real understanding, not just memorization
- For false statements in true_false: make them plausible but wrong

============================================================
CRITICAL: EXPLANATIONS MUST BE EDUCATIONAL AND DETAILED!
============================================================

FOR MATHEMATICS (especially important!):
- Show the STEP-BY-STEP CALCULATION process
- Include the FORMULA used for the solution
- Explain the MATHEMATICAL LOGIC and reasoning
- For example, if question is about triangle area: "Површина троугла се рачуна као половина производа основице и висине: P = (a * h) / 2. За a=6 и h=4, добијамо P = (6 * 4) / 2 = 12cm²"

For geometry:
- Always include which formula was used
- Show the substitution of values
- Explain WHY that formula applies

For algebra:
- Show the equation setup
- Explain each step of solving
- Include verification/check

For word problems:
- Explain HOW you identified what to calculate
- Show the logic from text to formula

GENERAL EXPLANATION RULES:
- Each explanation MUST be 3-7 SENTENCES
- Start with WHAT the correct answer is
- Then explain WHY it's correct
- Include the relevant FORMULA or CONCEPT if applicable
- For incorrect options: explain specifically why EACH one is wrong
- NEVER just say "because it's in the text" - EXPLAIN THE REASONING

BAD explanation examples (DO NOT USE):
- "Тачно је зато што пише у тексту" ❌
- "Одговор је тачан" ❌

GOOD explanation examples (USE THESE):
- "Тачан одговор је 24cm². Површина правоугаоника рачуна се као производ страница: P = a * b = 6 * 4 = 24cm². Други одговори су погрешни јер користе погрешну формулу или погрешно израчунавају." ✅
- "Нетачно. Збир углова у троуглу увек износи 180° без обзира на облик троугла. Ово следи из Теореме о збиру углова троугла." ✅
- "Одговор А је тачан. Користимо Питагорину теорему: a² + b² = c². За a=3 и b=4: 9 + 16 = 25, па је c = 5." ✅

LANGUAGE: Use the SAME LANGUAGE as the input text (Serbian Cyrillic: Ћ, Њ, Љ, Ш, Ч, Ж, etc.)

Return ONLY valid JSON array:
[
  {{
    "question_text": "Питање на српском језику?",
    "question_type": "multiple_choice",
    "options": [
      "Тачан одговор са рачуницом",
      "Погрешан одговор 1",
      "Погрешан одговор 2", 
      "Погрешан одговор 3"
    ],
    "correct_answer": "Тачан одговор са рачуницом",
    "explanation": "Тачан одговор је [A]. Користимо формулу [формула]. Заменом вредности добијамо [израчунавање]. Други одговори су погрешни јер [објашњење зашто].",
    "points": 1
  }},
  {{
    "question_text": "Да ли је следећа тврдња тачна: 'Зигурати су били трговачки центри'?",
    "question_type": "true_false", 
    "options": ["Тачно", "Нетачно"],
    "correct_answer": "Нетачно",
    "explanation": "Нетачно. Зигурати су били храмови посвећени богу Луни, а не трговачки центри. Они су служили као религијски објекти и астрономске осматрачнице.",
    "points": 1
  }},
  {{
    "question_text": "Које од следећих су биле карактеристике старог Египта?",
    "question_type": "checkbox",
    "options": [
      "Фараон као божански владар",
      "Пирамиде као гробнице",
      "Демократски систем владавине",
      "Развијена трговина и занати"
    ],
    "correct_answer": "Фараон као божански владар,Пирамиде као гробнице,Развијена трговина и занати",
    "explanation": "Египат није имао демократски систем. Фараон је био божански владар са апсолутном влашћу, градили су грандиозне пирамиде као краљевске гробнице, и имали су развијену трговину дуж Нила и занате.",
    "points": 2
  }}
]

Text:
{text}
"""


# ============================================================
# BASE CLIENT
# ============================================================

class BaseQuizClient(ABC):
    @abstractmethod
    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """Vraca (success, raw_json_string, error)."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


# ============================================================
# OLLAMA CLIENT
# ============================================================

class OllamaQuizClient(BaseQuizClient):
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        # Always check fresh - don't cache availability
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
                    json={"model": self.model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.3}}
                )
                r.raise_for_status()
                return True, r.json().get("response", ""), ""
        except Exception as e:
            return False, "", str(e)


# ============================================================
# OPENAI CLIENT
# ============================================================

class OpenAIQuizClient(BaseQuizClient):
    SYSTEM = "You are an expert educator that creates quiz questions. Always respond with valid JSON only."

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.timeout = getattr(settings, "OPENAI_TIMEOUT", 120)

    @property
    def provider_name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.SYSTEM},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "response_format": {"type": "json_object"} if "gpt-4" in self.model else None
                    }
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)


# ============================================================
# CLAUDE CLIENT
# ============================================================

class ClaudeQuizClient(BaseQuizClient):
    SYSTEM = "You are an expert educator that creates quiz questions. Always respond with valid JSON only — no markdown, no extra text."

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.timeout = getattr(settings, "CLAUDE_TIMEOUT", 120)

    @property
    def provider_name(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "system": self.SYSTEM,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                r.raise_for_status()
                content = r.json()["content"][0]["text"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)


# ============================================================
# QUIZ SERVICE (orchestrator)
# ============================================================

# ============================================================
# OPENAI-COMPATIBLE CLIENT (Gemini, Groq, Mistral)
# ============================================================

class OpenAICompatQuizClient(BaseQuizClient):
    SYSTEM = "You are an expert educator that creates quiz questions. Always respond with valid JSON only — no markdown, no extra text."

    def __init__(self, name: str, base_url: str, model: str, api_key: str = ""):
        self._name = name
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = 120

    @property
    def provider_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.SYSTEM},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    }
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)


# Redosled pokušaja: prvi dostupan pobedi
_PROVIDER_ORDER = ["groq", "openai", "claude", "gemini", "mistral", "deepseek", "ollama"]

def _build_clients(
    user_openai_key: str = None,
    user_claude_key: str = None,
    user_gemini_key: str = None,
    user_groq_key: str = None,
    user_mistral_key: str = None,
    user_deepseek_key: str = None,
) -> dict:
    """Builds client dict with optional user-level API key overrides.
    
    Priority:
    1. User's own API key (from user settings)
    2. System API key from settings (SYSTEM_GROQ_API_KEY, etc.)
    3. Default API key from settings (GROQ_API_KEY, etc.)
    """
    # Prioritet: 1. Korisnikov ključ, 2. Default ključ iz .env
    gemini_key  = user_gemini_key  or getattr(settings, 'GEMINI_API_KEY',  '') or ''
    groq_key    = user_groq_key    or getattr(settings, 'GROQ_API_KEY',    '') or ''
    mistral_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '') or ''
    openai_key  = user_openai_key  or getattr(settings, 'OPENAI_API_KEY',  '') or ''
    claude_key  = user_claude_key  or getattr(settings, 'ANTHROPIC_API_KEY','') or ''
    deepseek_key = user_deepseek_key or getattr(settings, 'DEEPSEEK_API_KEY', '') or ''

    ollama = OllamaQuizClient()
    openai = OpenAIQuizClient()
    if user_openai_key:
        openai.api_key = user_openai_key
    claude = ClaudeQuizClient()
    if user_claude_key:
        claude.api_key = user_claude_key

    return {
        "ollama":  ollama,
        "openai":  openai,
        "claude":  claude,
        "gemini":  OpenAICompatQuizClient("gemini",  "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash",    gemini_key),
        "groq":    OpenAICompatQuizClient("groq",    "https://api.groq.com/openai/v1",                          "llama-3.3-70b-versatile", groq_key),
        "mistral": OpenAICompatQuizClient("mistral","https://api.mistral.ai/v1",                               "mistral-small-latest",   mistral_key),
        "deepseek": OpenAICompatQuizClient("deepseek","https://api.deepseek.com/v1",                           "deepseek-chat",      deepseek_key),
    }

_CLIENTS: dict = _build_clients()


def _get_available_providers() -> List[dict]:
    """Lista svih provajdera i njihove dostupnosti."""
    return [
        {"id": k, "available": v.is_available(), "type": "local" if k == "ollama" else "online"}
        for k, v in _CLIENTS.items()
    ]


def _parse_questions(raw: str) -> List[dict]:
    """Parsira JSON array iz AI odgovora."""
    # Probaj direktno
    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return _validate_questions(data)
        # OpenAI json_object wraps it
        for v in data.values():
            if isinstance(v, list):
                return _validate_questions(v)
    except json.JSONDecodeError:
        pass
    # Izvuci array iz teksta
    match = re.search(r'\[.*\]', raw, re.DOTALL)
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
        # Reject single-letter placeholder options (AI ignored the instructions)
        options = q.get("options", [])
        if isinstance(options, list) and options:
            if all(len(str(o).strip()) <= 1 for o in options):
                logger.warning(f"Pitanje {i} ima samo-slova opcije, preskačem: {options}")
                continue
        q.setdefault("explanation", "")
        q.setdefault("points", 1)
        # Ensure checkbox has at least 2 correct answers and points >= 2
        if q.get("question_type") == "checkbox":
            correct = q.get("correct_answer", "")
            correct_parts = [p.strip() for p in correct.split(",") if p.strip()]
            if len(correct_parts) < 2:
                logger.warning(f"Pitanje {i} je checkbox ali ima samo 1 tačan odgovor, skidam na multiple_choice")
                q["question_type"] = "multiple_choice"
                q["correct_answer"] = correct_parts[0] if correct_parts else correct
            else:
                # Ensure checkbox scores at least 2 points
                if q.get("points", 1) < 2:
                    q["points"] = 2
        q["order_index"] = i
        valid.append(q)
    return valid


def _fallback_questions(text: str, num_questions: int) -> List[dict]:
    """Generise osnovna pitanja kada nijedan AI nije dostupan."""
    import random
    
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 30]
    questions = []
    
    for i, sentence in enumerate(sentences[:num_questions]):
        # Randomize between true and false for variety
        is_true = random.choice([True, False])
        
        if is_true:
            question_text = f"Да ли је тачна следећа тврдња: \"{sentence[:150]}\"?"
            correct = "Тачно"
            explanation = "Ова тврдња је директно наведена у тексту."
        else:
            # Create a false statement by simple negation (for fallback only)
            question_text = f"Да ли је тачна следећа тврдња: \"{sentence[:150]}\"?"
            correct = "Нетачно"
            explanation = "Ова тврдња не одговара садржају текста."
        
        questions.append({
            "question_text": question_text,
            "question_type": "true_false",
            "options": ["Тачно", "Нетачно"],
            "correct_answer": correct,
            "explanation": explanation,
            "points": 1,
            "order_index": i
        })
    return questions


def _select_chunks_for_quiz(chunks: list, max_chars: int = 10000) -> list:
    """
    Selects evenly-distributed chunks from across the document,
    up to max_chars total. This ensures the quiz covers the whole
    document, not just the first N chunks.
    
    Also filters out low-quality chunks (TOC, blank pages, notices, etc.)
    """
    if not chunks:
        return []
    
    # Extended list of patterns that indicate low-quality content
    LOW_QUALITY_PATTERNS = [
        # English
        'this page intentionally',
        'left blank',
        'copyright',
        'all rights reserved',
        'this material is copyright',
        'no part of this publication',
        'notice to reader',
        'notice to readers',
        'preface',
        'acknowledg',
        'table of contents',
        'index',
        'figure',
        'second edition',
        'third edition',
        'first edition',
        'fourth edition',
        'updated edition',
        'revised edition',
        'edition notice',
        'about the author',
        'author biography',
        'back cover',
        'front cover',
        'cover page',
        'title page',
        'dedication',
        'epigraph',
        # Serbian - Metadata pages
        'страница намерно',
        'празна страница',
        'сва права задржана',
        'copyright ©',
        'напомене',
        'биљешке',
        'садржај',
        'казало',
        'предговор',
        'захвалнице',
        'издање',
        'прво издање',
        'друго издање',
        'треће издање',
        # Serbian - Book metadata (new)
        'увод',
        'уводна реч',
        'реч аутора',
        'реч издавача',
        'приказак',
        'кола',
        'категорија',
        'ваодич',
        'садржина',
        'литература',
        'библиографиј',
        'регистар',
        'именник',
        'појмовник',
        'глосар',
        'задаци',
        'мисли',
        'штампа',
        'тираж',
        'издавач',
        'аутор',
        'рецензент',
        'уредник',
        'илустрациј',
        'лектура',
        'коректура',
        'дизајн',
        'прелом',
        'министарство просвете',
        'одобрило је',
        'решење број',
        ' фондациј',
        'кавчић',
        'диофант',
        'математички клуб',
        # Serbian - MORE metadata patterns (CRITICAL)
        'др-војислав',
        'војислав-андрић',
        'маријана-стефановић',
        'ђорђе-голубовић',
        'вељко-ћировић',
        'рецензенти',
        'главни-уредник',
        'предметни-уредник',
        'главни уредник',
        'предметни уредник',
        'иллустрације',
        'прелом',
        'за издавача',
        'isbn',
        'фитд',
        'сирупдаће',
        'обнављање градива',
        'иницијални тест',
        'сажитак',
        'питалице',
        'предлог задатака',
        'предлог теста',
        'предлог контролне',
        'подсетник',
        'пример',
        'решење задатака',
        'решења',
        'индекс појмова',
        'литература',
        'реч аутора',
        'физичко тело',
        'математичко тврђење',
        'дефиниција',
        'теорема',
        'задатак',
        'пример',
        'примена',
        # More patterns that indicate cover/copyright pages
        'чит',
        'за издавача',
        'тираж',
        'штампа –',
        'птр',
        'земун',
        'ваљево',
        'лукина',
        'кавчић',
        'алек',
        'фондација',
    ]
    
    def is_quality_chunk(chunk) -> bool:
        """Check if chunk has meaningful content for quiz generation."""
        text = (chunk.translated_content or chunk.content or '').lower()
        
        # Skip very short chunks
        if len(text) < 100:
            return False
        
        # Skip chunks with mostly numbers/page numbers
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars < 50:
            return False
        
        # Skip chunks matching low-quality patterns (stricter - no length exception)
        for pattern in LOW_QUALITY_PATTERNS:
            if pattern in text:
                return False
        
        return True
    
    # Filter chunks: only unused chunks + quality check
    quality_chunks = [c for c in chunks if is_quality_chunk(c) and (getattr(c, 'used_for_quiz', 0) or 0) == 0]
    
    # Log warning if we filtered too much
    if len(quality_chunks) < 3:
        logger.warning(f"Only {len(quality_chunks)} quality chunks found, using them anyway (might result in fewer questions)")
        # Still use the filtered chunks, don't fall back to all chunks
    
    # If still no chunks after filtering, return empty
    if not quality_chunks:
        logger.warning("No quality chunks found for quiz generation")
        return []
    
    total = len(quality_chunks)

    # Estimate average chunk length from up to 20 samples
    sample = quality_chunks[::max(1, total // 20)][:20]
    avg_len = sum(len(c.translated_content or c.content) for c in sample) / len(sample)

    # How many chunks can we fit?
    target_count = max(5, int(max_chars / max(avg_len, 100)))
    
    # RANDOMIZATION: Shuffle chunks so each quiz gets different content
    # Use random start offset to cover different parts of the document
    import random
    random_offset = random.randint(0, total - 1)  # Random starting point
    rotated_chunks = quality_chunks[random_offset:] + quality_chunks[:random_offset]
    
    # Now select evenly from the rotated list (this gives different chunks each time)
    step = max(1, total // target_count)

    selected = []
    total_chars = 0
    for i in range(0, total, step):
        chunk = rotated_chunks[i % total]  # Wrap around using modulo
        text = chunk.translated_content or chunk.content
        if total_chars + len(text) > max_chars:
            break
        selected.append(chunk)
        total_chars += len(text)

    # Shuffle final selection for variety in the quiz
    random.shuffle(selected)

    return selected


def get_images_for_chunks(chunks: list, quiz_images: list) -> dict:
    """
    Map images to chunks based on page number.
    Returns dict: chunk_index -> list of images
    """
    logger.warning(f"DEBUG get_images_for_chunks: received {len(chunks)} chunks, {len(quiz_images)} images")
    
    if not quiz_images:
        logger.warning("DEBUG: No quiz_images provided!")
        return {}
    
    # Build page -> images mapping
    page_to_images = {}
    for img in quiz_images:
        page_num = getattr(img, 'page_number', None)
        if page_num:
            if page_num not in page_to_images:
                page_to_images[page_num] = []
            page_to_images[page_num].append(img)
    
    logger.warning(f"DEBUG: page_to_images has {len(page_to_images)} entries: {list(page_to_images.keys())[:10]}")
    
    # Map chunks to their images
    chunk_to_images = {}
    for idx, chunk in enumerate(chunks):
        chunk_page = getattr(chunk, 'page_number', None)
        if chunk_page and chunk_page in page_to_images:
            chunk_to_images[idx] = page_to_images[chunk_page]
    
    # If no page-based mapping, assign random images from the document
    if not chunk_to_images and quiz_images:
        import random
        random.shuffle(quiz_images)
        for idx in range(min(len(chunks), len(quiz_images))):
            chunk_to_images[idx] = [quiz_images[idx % len(quiz_images)]]
        logger.warning(f"DEBUG: Assigned random images to {len(chunk_to_images)} chunks")
    
    logger.warning(f"DEBUG: chunk_to_images mapped {len(chunk_to_images)} chunks to images")
    return chunk_to_images


def get_quiz_usage_stats(chunks: list) -> dict:
    """
    Vraća statistiku o iskorišćenosti chunk-ova za kviz.
    """
    total = len(chunks)
    used = sum(1 for c in chunks if (getattr(c, 'used_for_quiz', 0) or 0) == 1)
    unused = total - used
    return {
        "total_chunks": total,
        "used_chunks": used,
        "unused_chunks": unused,
        "can_generate_new": unused > 0
    }


def mark_chunks_as_used(chunk_ids: list, db):
    """
    Označava chunk-ove kao korišćene za kviz.
    """
    if not chunk_ids:
        return
    try:
        from app.db.models.document import Chunk
        db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).update(
            {"used_for_quiz": 1},
            synchronize_session=False
        )
        db.commit()
        logger.info(f"Marked {len(chunk_ids)} chunks as used for quiz")
    except Exception as e:
        logger.error(f"Error marking chunks as used: {e}")
        db.rollback()


def _auto_num_questions(total_chunks: int, requested: int) -> int:
    """
    If requested > 0, use it (capped to a sane max).
    If requested == 0, calculate based on document size.
    """
    # Ensure requested is an integer
    try:
        requested = int(requested) if requested else 0
    except (ValueError, TypeError):
        requested = 0
    
    if requested > 0:
        return min(requested, 50)  # cap at 50 per generation
    # Auto: ~1 question per 10 chunks, min 5, max 50
    return min(50, max(5, total_chunks // 10))


class QuizService:
    """
    Servis za generisanje i upravljanje kvizovima.
    Podržava Ollama, OpenAI, Claude sa fallback lancem.
    """

    def _get_image_for_vision(self, img, storage, timeout: int = 5) -> Tuple[str, str]:
        """
        Hibridni pristup: prvo probaj MinIO URL, pa fallback na base64.
        
        Returns:
            (image_content, content_type)
            - image_content: ili URL ili base64 string
            - content_type: "url" ili "base64"
        """
        import httpx
        import base64
        
        try:
            # 1. Probaj MinIO public URL
            public_url = storage.get_public_url(img.storage_path)
            logger.info(f"Trying MinIO URL: {public_url[:80]}...")
            
            # Testiraj da li URL radi (kratki timeout)
            response = httpx.get(public_url, timeout=timeout)
            if response.status_code == 200:
                logger.info("MinIO URL accessible - using URL mode")
                return public_url, "url"
            else:
                logger.warning(f"MinIO URL returned {response.status_code} - falling back to base64")
                
        except Exception as e:
            logger.warning(f"MinIO URL failed: {e} - falling back to base64")
        
        # 2. Fallback: preuzmi sliku i enkoduj kao base64
        try:
            from app.services.storage_cloud import CloudStorageService
            storage = CloudStorageService()
            
            # Preuzmi sliku iz MinIO
            import io
            from botocore.exceptions import ClientError
            
            try:
                response = storage.client.get_object(
                    Bucket=storage.bucket_name,
                    Key=img.storage_path
                )
                image_data = response['Body'].read()
                
                # Enkoduj kao base64
                b64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Odredi mime type iz storage_path
                path_lower = img.storage_path.lower()
                if path_lower.endswith('.png'):
                    mime_type = 'image/png'
                elif path_lower.endswith('.gif'):
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'
                
                logger.info(f"Using base64 mode (image size: {len(image_data)} bytes)")
                return f"data:{mime_type};base64,{b64_image}", "base64"
                
            except ClientError as e:
                logger.error(f"Failed to download image from MinIO: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Base64 fallback also failed: {e}")
            raise

    def _generate_vision_questions_for_images(
        self,
        images: list,
        num_questions: int = 5,
        subject_area: str = None,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja gdje SVAKO PITANJE dolazi iz TAČNE SLIKE.
        
        Hibridni pristup:
        1. Probaj MinIO public URL (brži)
        2. Fallback na base64 (uvek radi)
        
        Returns:
            (success, questions_list sa image_url i image_caption, used_provider)
        """
        import httpx
        from app.services.storage_cloud import CloudStorageService
        
        if not images:
            return False, [], "no_images"
        
        # Select images to process
        selected_images = images[:min(num_questions, len(images))]
        storage = CloudStorageService()
        
        # Subject-specific prompts
        subject_prompts = {
            "matematika": "Ova slika prikazuje matematički koncept, zadatak ili grafikon. Kreiraj pitanje koje testira razumevanje prikazanog matematičkog sadržaja.",
            "fizika": "Ova slika prikazuje fizikalni eksperiment, dijagram ili koncept. Kreiraj pitanje koje testira razumevanje prikazanog fizikalnog sadržaja.",
            "hemija": "Ova slika prikazuje hemijski eksperiment, strukturu molekula ili dijagram. Kreiraj pitanje koje testira razumevanje prikazanog hemijskog sadržaja.",
            "biologija": "Ova slika prikazuje biološki organizam, proces ili dijagram. Kreiraj pitanje koje testira razumevanje prikazanog biološkog sadržaja.",
            "istorija": "Ova slika prikazuje istorijski događaj, ličnost, artefakt ili mapu. Kreiraj pitanje koje testira znanje o prikazanom istorijskom sadržaju.",
        }
        
        subject_instruction = subject_prompts.get(subject_area, "Ova slika je iz udžbenika. Kreiraj pitanje koje testira razumevanje prikazanog sadržaja.")
        
        # Vision-capable providers in order of preference
        providers = []
        
        # Mistral Vision (prioritet - ima dobar vision model)
        mistral_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '') or ''
        if mistral_key:
            providers.append(("mistral", mistral_key))
        
        # Claude Vision
        claude_key = user_claude_key or getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
        if claude_key:
            providers.append(("claude", claude_key))
        
        # DeepSeek VL Vision
        deepseek_key = user_deepseek_key or getattr(settings, 'DEEPSEEK_API_KEY', '') or ''
        if deepseek_key:
            providers.append(("deepseek", deepseek_key))
        
        # Groq Vision (Llama 3.2 Vision)
        groq_key = user_groq_key or getattr(settings, 'GROQ_API_KEY', '') or ''
        if groq_key:
            providers.append(("groq", groq_key))
        
        # OpenAI GPT-4o Vision
        openai_key = user_openai_key or getattr(settings, 'OPENAI_API_KEY', '') or ''
        if openai_key:
            providers.append(("openai", openai_key))
        
        # Gemini Vision
        gemini_key = user_gemini_key or getattr(settings, 'GEMINI_API_KEY', '') or ''
        if gemini_key:
            providers.append(("gemini", gemini_key))
        
        if not providers:
            logger.warning("No Vision-capable API keys available")
            return False, [], "no_vision_keys"
        
        questions = []
        
        # Process each image one by one
        for idx, img in enumerate(selected_images):
            logger.info(f"Processing image {idx+1}/{len(selected_images)}: {img.storage_path}")
            
            # Get image using hybrid approach (URL first, then base64 fallback)
            try:
                image_content, content_type = self._get_image_for_vision(img, storage)
                logger.info(f"Using {content_type} mode for image {idx+1}")
            except Exception as e:
                logger.warning(f"Failed to get image {idx+1}: {e}")
                continue
            
            # Single image prompt
            single_prompt = f"""Analiziraj ovu sliku iz udžbenika i kreiraj JEDNO kviz pitanje o njenom sadržaju.

{subject_instruction}

PITANJE MORA BITI O SADRŽAJU SLIKE - ne generiši pitanje koje nije povezano sa onim što vidiš na slici!

Vrati SAMO JSON objekat (bez markdown formatiranja):
{{
  "question_text": "Pitanje o sadržaju slike na srpskom jeziku",
  "question_type": "multiple_choice",
  "options": ["A) Tačan odgovor", "B) Pogrešan odgovor 1", "C) Pogrešan odgovor 2", "D) Pogrešan odgovor 3"],
  "correct_answer": "A) Tačan odgovor",
  "explanation": "Objašnjenje zašto je ovaj odgovor tačan a drugi nisu",
  "points": 1
}}

VAŽNO: 
- Pitanje mora biti o onome što stvarno vidiš na slici
- Ako slika prikazuje dijagram, pitaj o podacima iz dijagrama
- Ako slika prikazuje eksperiment, pitaj o njegovim karakteristikama
- Ako slika prikazuje mapu, pitaj o geografskim podacima
"""
            
            question_data = None
            
            # Try each Vision provider
            for provider_name, api_key in providers:
                try:
                    if provider_name == "openai":
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        
                        # Format image content based on type
                        if content_type == "base64":
                            image_block = {"type": "image_url", "image_url": {"url": image_content}}
                        else:
                            image_block = {"type": "image_url", "image_url": {"url": image_content}}
                        
                        payload = {
                            "model": "gpt-4o",
                            "messages": [
                                {"role": "user", "content": [
                                    {"type": "text", "text": single_prompt},
                                    image_block
                                ]}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                        
                        response = httpx.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['choices'][0]['message']['content']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1} (stranica {getattr(img, 'page_number', '?')})"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"OpenAI Vision: Generated question for image {idx+1}")
                                break
                                
                    elif provider_name == "gemini":
                        headers = {"Content-Type": "application/json"}
                        # Convert URL to base64 for Gemini (or use URL directly)
                        payload = {
                            "contents": [{
                                "parts": [
                                    {"text": single_prompt},
                                    {"image_url": {"url": image_content}}
                                ]
                            }]
                        }
                        # Note: Gemini has different API format
                        response = httpx.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={api_key}",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['candidates'][0]['content']['parts'][0]['text']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1}"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"Gemini Vision: Generated question for image {idx+1}")
                                break
                                
                    elif provider_name == "claude":
                        # Claude Vision - koristi claude-3-sonnet-20240229 ili noviji
                        import base64
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 1000,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": single_prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "url",
                                            "url": image_content
                                        }
                                    }
                                ]
                            }]
                        }
                        
                        response = httpx.post(
                            "https://api.anthropic.com/v1/messages",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['content'][0]['text']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1}"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"Claude Vision: Generated question for image {idx+1}")
                                break
                                
                    elif provider_name == "deepseek":
                        # DeepSeek VL Vision
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "deepseek-chat",
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": single_prompt},
                                    {"type": "image_url", "image_url": {"url": image_content}}
                                ]
                            }],
                            "max_tokens": 1000
                        }
                        
                        response = httpx.post(
                            "https://api.deepseek.com/v1/chat/completions",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['choices'][0]['message']['content']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1}"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"DeepSeek Vision: Generated question for image {idx+1}")
                                break
                                
                    elif provider_name == "groq":
                        # Groq Vision - koristi llama-3.2-90b-vision-preview
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "llama-3.2-90b-vision-preview",
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": single_prompt},
                                    {"type": "image_url", "image_url": {"url": image_content}}
                                ]
                            }],
                            "max_tokens": 1000
                        }
                        
                        response = httpx.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['choices'][0]['message']['content']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1}"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"Groq Vision: Generated question for image {idx+1}")
                                break
                                
                    elif provider_name == "mistral":
                        # Mistral Vision - koristi pixtral-large-2411 (dedicated vision model)
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "pixtral-large-2411",
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": single_prompt},
                                    {"type": "image_url", "image_url": {"url": image_content}}
                                ]
                            }],
                            "max_tokens": 1000
                        }
                        
                        response = httpx.post(
                            "https://api.mistral.ai/v1/chat/completions",
                            headers=headers, json=payload, timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            content = response.json()['choices'][0]['message']['content']
                            import re, json
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                question_data = json.loads(match.group())
                                question_data["image_url"] = image_content
                                question_data["image_caption"] = getattr(img, 'caption', None) or f"Slika {idx+1}"
                                question_data["order_index"] = idx
                                questions.append(question_data)
                                logger.info(f"Mistral Vision: Generated question for image {idx+1}")
                                break
                        else:
                            logger.warning(f"Mistral returned {response.status_code}: {response.text[:200]}")
                                
                except Exception as e:
                    logger.warning(f"{provider_name} Vision failed for image {idx+1}: {e}")
                    continue
            
            if not question_data:
                logger.warning(f"No Vision provider succeeded for image {idx+1}")
        
        if questions:
            return True, questions, "vision_ai"
        return False, [], "vision_failed"

    def _generate_text_questions_with_optional_images(
        self,
        chunks: list,
        quiz_images: list,
        num_questions: int = 5,
        subject_area: str = None,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja iz TEKSTA, gde AI ODMA SAM odlučuje da li da doda sliku.
        
        Ovo je hibridni pristup:
        1. AI generiše pitanje iz TEKSTA (chunks)
        2. AI dobija informacije o slicama (koja slika je na kojoj stranici)
        3. AI SAM odlučuje da li je slika relevantna za to pitanje
        4. U JSON odgovoru, AI vraća "image_page": N ako je slika relevantna
        
        Args:
            chunks: Lista Chunk objekata (sa page_number)
            quiz_images: Lista QuizImage objekata (sa page_number)
            num_questions: Željeni broj pitanja
            subject_area: Oblast dokumenta
        
        Returns:
            (success, questions_list sa image_url ako je relevantno, used_provider)
        """
        import base64
        import httpx
        from app.services.storage_cloud import CloudStorageService
        
        subject_instructions = {
            "matematika": """
IMPORTANT - MATHEMATICS QUESTIONS:
- 40% CALCULATION: Step-by-step math problems with formulas
- 35% MULTIPLE_CHOICE: Problem solving with explanation
- 25% TRUE_FALSE: Only for definitions/concepts, NEVER for calculations
NEVER create True/False for calculation problems!
Explanations MUST include the formula used and step-by-step calculation.
""",
            "fizika": """
IMPORTANT - PHYSICS QUESTIONS:
- 40% CALCULATION: Physics problems with formulas and units
- 35% MULTIPLE_CHOICE: Concepts and definitions
- 25% TRUE_FALSE: Physical laws and facts
Always include UNITS in explanations!
""",
            "hemija": """
IMPORTANT - CHEMISTRY QUESTIONS:
- 30% MULTIPLE_CHOICE: Chemical reactions, compounds, elements
- 25% CHEMICAL_EQUATION: Complete the reaction
- 20% CALCULATION: Molar mass, concentrations
- 25% TRUE_FALSE: Chemical facts
Include chemical formulas in explanations!
""",
            "biologija": """
IMPORTANT - BIOLOGY QUESTIONS:
- 50% MULTIPLE_CHOICE: Cell biology, organisms, systems
- 30% CHECKBOX: Select all that apply (structures, functions)
- 20% TRUE_FALSE: Biological facts and processes
Focus on: ćelija, organeli, sistemi, procesi, genetika
""",
            "istorija": """
IMPORTANT - HISTORY QUESTIONS:
- 50% MULTIPLE_CHOICE: Historical events, dates, people
- 30% CHRONOLOGY: Order of events
- 20% TRUE_FALSE: Historical facts
Focus on: datumi, događaji, ličnosti, periodi
""",
            "geografija": """
IMPORTANT - GEOGRAPHY QUESTIONS:
- 50% MULTIPLE_CHOICE: Countries, capitals, geography facts
- 30% MAP: Location-based questions
- 20% TRUE_FALSE: Geographic facts
Focus on: države, gradovi, reljef, klima, resursi
""",
            "informatika": """
IMPORTANT - COMPUTER SCIENCE QUESTIONS:
- 40% MULTIPLE_CHOICE: Programming, algorithms, concepts
- 30% CODE_COMPLETION: Find the error or complete the code
- 30% TRUE_FALSE: Technical facts
Focus on: algoritmi, programiranje, mreže, baze podataka
""",
        }
        
        subject_instruction = subject_instructions.get(subject_area, "")
        
        if not chunks:
            return False, [], "no_chunks"
        
        # Build image context for AI
        # Map page_number -> image_info
        page_to_image = {}
        for img in quiz_images:
            page_num = getattr(img, 'page_number', None)
            if page_num:
                if page_num not in page_to_image:
                    page_to_image[page_num] = img
        
        # Prepare chunks for AI - with image info
        chunks_with_images = []
        for i, chunk in enumerate(chunks):
            page_num = getattr(chunk, 'page_number', None)
            text = (chunk.translated_content or chunk.content or '')[:1000]  # First 1000 chars
            
            image_info = ""
            has_image = False
            if page_num and page_num in page_to_image:
                img = page_to_image[page_num]
                image_info = f"[PODEŠENO ZA STRANICU {page_num} - AKO JE SLIKA RELEVANTNA ZA PITANJE, VRATI 'image_page': {page_num}]"
                has_image = True
            
            chunks_with_images.append({
                'index': i,
                'page': page_num,
                'text': text,
                'has_image': has_image,
                'image_info': image_info
            })
        
        # Select chunks to use (up to num_questions)
        selected_chunks = chunks_with_images[:min(num_questions, len(chunks_with_images))]
        
        # Build the prompt with image context
        subject_instruction = subject_instructions.get(subject_area, "")
        
        # Create chunk descriptions with image info
        chunk_descriptions = []
        for i, chunk_info in enumerate(selected_chunks):
            img_note = f" [SLIKA NA STRANICI {chunk_info['page']} - dodaj u JSON 'image_page': {chunk_info['page']} ako je relevantna]" if chunk_info['has_image'] else ""
            chunk_descriptions.append(f"--- TEKST {i+1} (stranica {chunk_info['page']}){img_note} ---\n{chunk_info['text'][:800]}")
        
        chunks_text = "\n\n".join(chunk_descriptions)
        
        smart_prompt = f"""Analiziraj tekst iz udžbenika i kreiraj kviz pitanja.

{subject_instruction}

{chunks_text}

INSTUKCIJE ZA FORMAT ODGOVORA:
- Za SVAKO pitanje, u JSON-u vrati:
  {{
    "question_text": "Pitanje na srpskom jeziku",
    "question_type": "multiple_choice",
    "options": ["A) Opcija A", "B) Opcija B", "C) Opcija C", "D) Opcija D"],
    "correct_answer": "A) Opcija A",
    "explanation": "Objašnjenje",
    "points": 1,
    "source_chunk": N,
    "image_page": N ILI null
  }}

- POLJE "image_page":
  - Ako tekst pominje sliku, dijagram, grafikon ILI je pitanje vezano za vizuelni sadržaj → vrati broj stranice (npr. 5)
  - Ako pitanje NIJE vezano za sliku → vrati null

PRIMER:
- Tekst o pH skali + slika na stranici 3 → "image_page": 3
- Tekst o hemijskoj reakciji → "image_page": null
- Tekst o mitohondriji + slika na stranici 15 → "image_page": 15
- Tekst o definiciji → "image_page": null

VRATI {len(selected_chunks)} PITANJA u JSON nizu."""

        # Get image URLs for all pages
        page_to_image_url = {}
        if quiz_images:
            try:
                storage = CloudStorageService()
                for img in quiz_images:
                    page_num = getattr(img, 'page_number', None)
                    if page_num and page_num not in page_to_image_url:
                        try:
                            image_content, _ = self._get_image_for_vision(img, storage)
                            page_to_image_url[page_num] = image_content
                        except:
                            pass
            except:
                pass

        # Try providers
        providers_to_try = []
        
        # Mistral
        mistral_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '') or ''
        if mistral_key:
            providers_to_try.append(("mistral", mistral_key))
        
        # OpenAI
        openai_key = user_openai_key or getattr(settings, 'OPENAI_API_KEY', '') or ''
        if openai_key:
            providers_to_try.append(("openai", openai_key))
        
        # Groq
        groq_key = user_groq_key or getattr(settings, 'GROQ_API_KEY', '') or ''
        if groq_key:
            providers_to_try.append(("groq", groq_key))
        
        # Claude
        claude_key = user_claude_key or getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
        if claude_key:
            providers_to_try.append(("claude", claude_key))
        
        # DeepSeek
        deepseek_key = user_deepseek_key or getattr(settings, 'DEEPSEEK_API_KEY', '') or ''
        if deepseek_key:
            providers_to_try.append(("deepseek", deepseek_key))
        
        if not providers_to_try:
            return False, [], "no_api_keys"
        
        questions = []
        
        for provider_name, api_key in providers_to_try:
            try:
                if provider_name == "openai":
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": smart_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 3000
                    }
                    response = httpx.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers, json=payload, timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        content = response.json()['choices'][0]['message']['content']
                        import re, json
                        match = re.search(r'\[.*\]', content, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            for i, q in enumerate(data):
                                q["image_url"] = None
                                if q.get("image_page") and q["image_page"] in page_to_image_url:
                                    q["image_url"] = page_to_image_url[q["image_page"]]
                                    q["image_caption"] = f"Slika sa stranice {q['image_page']}"
                                q["order_index"] = i
                                questions.append(q)
                            return True, questions, "openai_text"
                
                elif provider_name == "mistral":
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "mistral-large-latest",
                        "messages": [{"role": "user", "content": smart_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 3000
                    }
                    response = httpx.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers=headers, json=payload, timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        content = response.json()['choices'][0]['message']['content']
                        import re, json
                        match = re.search(r'\[.*\]', content, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            for i, q in enumerate(data):
                                q["image_url"] = None
                                if q.get("image_page") and q["image_page"] in page_to_image_url:
                                    q["image_url"] = page_to_image_url[q["image_page"]]
                                    q["image_caption"] = f"Slika sa stranice {q['image_page']}"
                                q["order_index"] = i
                                questions.append(q)
                            return True, questions, "mistral_text"
                
                elif provider_name == "groq":
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "mixtral-8x7b-32768",
                        "messages": [{"role": "user", "content": smart_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 3000
                    }
                    response = httpx.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers, json=payload, timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        content = response.json()['choices'][0]['message']['content']
                        import re, json
                        match = re.search(r'\[.*\]', content, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            for i, q in enumerate(data):
                                q["image_url"] = None
                                if q.get("image_page") and q["image_page"] in page_to_image_url:
                                    q["image_url"] = page_to_image_url[q["image_page"]]
                                    q["image_caption"] = f"Slika sa stranice {q['image_page']}"
                                q["order_index"] = i
                                questions.append(q)
                            return True, questions, "groq_text"
                
            except Exception as e:
                logger.warning(f"{provider_name} text generation failed: {e}")
                continue
        
        if questions:
            return True, questions, "text_with_images"
        return False, [], "text_generation_failed"

    def _generate_questions_from_images(
        self,
        images: list,
        num_questions: int = 5,
        provider: Optional[str] = None,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja iz slika koristeći AI Vision.
        
        Args:
            images: Lista QuizImage objekata
            num_questions: Željeni broj pitanja
            provider: Specifičan provajder
        
        Returns:
            (success, questions_list, used_provider_or_error)
        """
        import base64
        import httpx
        
        # Select up to num_questions images to analyze
        selected_images = images[:min(num_questions, len(images))]
        
        # Build the vision prompt
        vision_prompt = """Analiziraj ove slike iz udžbenika i kreiraj kviz pitanja.
Za svaku sliku kreiraj jedno pitanje sa 4 opcije (A, B, C, D) i tačnim odgovorom.

Vrati JSON niz u formatu:
[
  {
    "question_text": "Pitanje bazirano na slici",
    "question_type": "multiple_choice",
    "options": ["A) Opcija A", "B) Opcija B", "C) Opcija C", "D) Opcija D"],
    "correct_answer": "A) Opcija A",
    "explanation": "Objašnjenje zašto je odgovor tačan",
    "points": 1
  }
]

Fokusiraj se na:
- Istoriju: datumi, događaji, ličnosti, uzroci i posledice
- Geografiju: države, glavni gradovi, karakteristike regiona
- Biologiju: organizmi, procesi, strukture
- Opšte znanje: činjenice prikazane na slici

 Kreiraj """ + str(len(selected_images)) + """ pitanja."""
        
        # Try using Groq first (fastest)
        groq_key = user_groq_key or getattr(settings, 'GROQ_API_KEY', '') or ''
        
        if groq_key:
            try:
                # For Groq, we need to use a vision-capable model
                # Note: Groq may not have vision yet, so we might need to fallback
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                
                # Try with Llama Vision or fallback
                payload = {
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt}
                            ]
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                # For now, return failure to try other providers
                # Real implementation would send actual images
                logger.warning("Groq Vision not fully implemented yet")
                
            except Exception as e:
                logger.warning(f"Groq Vision failed: {e}")
        
        # Try with OpenAI GPT-4V
        openai_key = user_openai_key or getattr(settings, 'OPENAI_API_KEY', '') or ''
        logger.warning(f"OpenAI key available: {bool(openai_key)}, length: {len(openai_key) if openai_key else 0}")
        
        if openai_key:
            try:
                logger.warning("Starting OpenAI Vision API call...")
                
                # Get public URL for images
                from app.services.storage_cloud import CloudStorageService
                storage = CloudStorageService()
                
                # Prepare messages with image URLs
                content = [{"type": "text", "text": vision_prompt}]
                
                # Add public image URLs to the prompt
                for img in selected_images:
                    if hasattr(img, 'storage_path') and img.storage_path:
                        # Get permanent public URL
                        public_url = storage.get_public_url(img.storage_path)
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": public_url}
                        })
                        logger.info(f"Using public URL for vision: {public_url[:50]}...")
                
                logger.warning(f"Prepared {len(content)} content items (1 text + {len(content)-1} images)")
                
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120.0
                )
                logger.warning(f"OpenAI response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Parse JSON from response
                    import json
                    import re
                    
                    # Extract JSON array from response
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        questions = json.loads(match.group())
                        if questions:
                            # Add order_index
                            for i, q in enumerate(questions):
                                q['order_index'] = i
                            logger.info(f"OpenAI Vision generated {len(questions)} questions")
                            return True, questions, "openai"
                else:
                    logger.warning(f"OpenAI Vision failed with status {response.status_code}: {response.text[:200]}")
                            
            except Exception as e:
                logger.warning(f"OpenAI Vision failed: {e}")
        
        # Try with Mistral Vision
        mistral_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '') or ''
        
        if mistral_key:
            try:
                logger.warning("Starting Mistral Vision API call...")
                
                from app.services.storage_cloud import CloudStorageService
                import base64
                import httpx
                
                storage = CloudStorageService()
                
                # Prepare messages with base64 encoded images
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt}
                        ]
                    }
                ]
                
                # Download and encode images as base64 for Mistral
                for img in selected_images:
                    if hasattr(img, 'storage_path') and img.storage_path:
                        try:
                            # Get the image from MinIO
                            image_data = storage.client.get_object(
                                Bucket=storage.bucket_name,
                                Key=img.storage_path
                            )
                            image_bytes = image_data.read()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            # Determine mime type
                            import imghdr
                            ext = img.storage_path.split('.')[-1].lower() if '.' in img.storage_path else 'jpg'
                            mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
                            
                            messages[0]["content"].append({
                                "type": "image_url",
                                "image_url": f"data:{mime_type};base64,{image_base64}"
                            })
                            logger.info(f"Encoded image: {img.storage_path[:30]}...")
                        except Exception as img_err:
                            logger.warning(f"Failed to encode image: {img_err}")
                
                headers = {
                    "Authorization": f"Bearer {mistral_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "pixtral-large-latest",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                response = httpx.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120.0
                )
                logger.warning(f"Mistral response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    import json
                    import re
                    
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        questions = json.loads(match.group())
                        if questions:
                            for i, q in enumerate(questions):
                                q['order_index'] = i
                            logger.info(f"Mistral Vision generated {len(questions)} questions")
                            return True, questions, "mistral"
                else:
                    logger.warning(f"Mistral Vision failed with status {response.status_code}: {response.text[:200]}")
                    
            except Exception as e:
                logger.warning(f"Mistral Vision failed: {e}")
        
        # Try with Claude Vision
        claude_key = user_claude_key or getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
        
        if claude_key:
            try:
                # Prepare image URLs for Claude
                image_urls = []
                for img in selected_images:
                    if hasattr(img, 'image_url') and img.image_url:
                        image_urls.append(img.image_url)
                
                if not image_urls:
                    return False, [], "no_image_urls"
                
                # Claude requires images to be base64 encoded or use URL
                # For simplicity, we'll try with text prompt only
                headers = {
                    "x-api-key": claude_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                
                # Build content with text and image references
                content = [{"type": "text", "text": vision_prompt}]
                
                payload = {
                    "model": "claude-3-opus-20240229",
                    "max_tokens": 2000,
                    "messages": [
                        {"role": "user", "content": content}
                    ]
                }
                
                # Note: Claude vision requires specific format, simplified for now
                logger.warning("Claude Vision not fully implemented")
                
            except Exception as e:
                logger.warning(f"Claude Vision failed: {e}")
        
        # If all vision fails, return simple text-based fallback
        return False, [], "vision_not_available"

    def generate_questions_with_ai(
        self,
        text: str,
        num_questions: int = 5,
        provider: Optional[str] = None,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
        quiz_images: list = None,
        chunk_image_map: dict = None,
        subject_area: str = None,
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja koristeći AI.
        Args:
            text: Tekst za analizu
            num_questions: Željeni broj pitanja
            provider: Specifičan provajder (None=auto)
            user_*_key: User-ov API ključ (override globalnog)
            subject_area: Oblast dokumenta (matematika, fizika, hemija...)
        Returns:
            (success, questions_list, used_provider_or_error)
        """
        
        # Detect subject area if not provided
        if not subject_area:
            logger.info("Detecting subject area...")
            subject_area = detect_subject_area(text)
            logger.info(f"Detected subject area: {subject_area}")
        
        # Get specialized prompt for this subject
        prompt = get_specialized_prompt(subject_area, num_questions, text)
        
        clients = _build_clients(
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
        )

        def get_client(p: str):
            return clients.get(p)

        # Create wrapper that uses our custom prompt
        def generate_with_prompt(client, text_to_use: str, num: int):
            return client.generate(prompt, num)

        # Ako je specifičan provajder zahtjevan, pokušaj samo njega
        if provider and provider in clients:
            client = get_client(provider)
            if not client or not client.is_available():
                logger.warning(f"Provajder '{provider}' nije dostupan, koristim fallback lanac")
            else:
                ok, raw, err = generate_with_prompt(client, text, num_questions)
                if ok:
                    questions = _parse_questions(raw)
                    if questions:
                        logger.info(f"[{provider}] Generisano {len(questions)} pitanja za oblast: {subject_area}")
                        return True, questions, provider
                    logger.warning(f"[{provider}] AI vratio prazan odgovor, prelazim na fallback")
                logger.warning(f"[{provider}] Greška: {err}, prelazim na fallback")

        # Fallback lanac
        order = [p for p in _PROVIDER_ORDER if p != provider]
        if provider:
            order = [provider] + order

        for p in order:
            client = get_client(p)
            if not client or not client.is_available():
                continue
            ok, raw, err = generate_with_prompt(client, text, num_questions)
            if ok:
                logger.info(f"[{p}] AI odgovor: {raw[:200]}...")
                questions = _parse_questions(raw)
                if questions:
                    logger.info(f"[{p}] Generisano {len(questions)} pitanja za oblast: {subject_area}")
                    return True, questions, p
                logger.warning(f"[{p}] AI vratio prazan odgovor, probam sledeci")
            logger.warning(f"[{p}] Nije uspelo: {err}")

        # Poslednje utočiste — fallback pitanja
        logger.warning("Svi AI provajderi zakazali, koristim fallback pitanja")
        fallback = _fallback_questions(text, num_questions)
        return True, fallback, "fallback"

    def create_quiz_from_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
        num_questions: int = 5,
        time_limit: Optional[int] = None,
        passing_score: int = 60,
    ) -> Quiz:
        """Kreira Quiz zapis (status=generating), task generiše pitanja asinhrono."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Dokument nije pronađen: {document_id}")
        
        # Calculate expected questions for progress tracking
        expected = num_questions if num_questions > 0 else 10
        
        quiz = Quiz(
            document_id=document_id,
            user_id=user_id,
            title=f"Kviz: {document.title}",
            description=f"Automatski generisan kviz iz dokumenta '{document.title}'",
            time_limit=time_limit,
            passing_score=passing_score,
            status="generating",
            target_questions=expected,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz

    def populate_quiz_questions(
        self,
        db: Session,
        quiz_id: str,
        document_id: str,
        num_questions: int = 5,
        provider: Optional[str] = None,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Generiše pitanja i sačuva ih.
        Vraća (success, used_provider).
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return False, ""

        # Fetch ALL chunks, then sample evenly across the document
        all_chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.sequence_number)
            .all()
        )
        if not all_chunks:
            logger.warning(f"Document {document_id} has NO chunks at all, checking for images...")
            
            # Get images for this document
            from app.db.models.quiz import QuizImage
            all_images = db.query(QuizImage).all()
            doc_images = [img for img in all_images if str(img.document_id) == str(document_id)]
            
            if doc_images:
                logger.warning(f"Found {len(doc_images)} images, using AI Vision to generate questions...")
                
                # Try to generate questions from images using AI Vision
                vision_success, vision_questions, vision_error = self._generate_questions_from_images(
                    doc_images, 
                    num_questions,
                    provider=provider,
                    user_openai_key=user_openai_key,
                    user_claude_key=user_claude_key,
                    user_gemini_key=user_gemini_key,
                    user_groq_key=user_groq_key,
                    user_mistral_key=user_mistral_key,
                    user_deepseek_key=user_deepseek_key,
                )
                
                if vision_success and vision_questions:
                    logger.info(f"AI Vision generated {len(vision_questions)} questions from images")
                    quiz_images = doc_images
                    
                    # Get public URL for images
                    from app.services.storage_cloud import CloudStorageService
                    storage = CloudStorageService()
                    
                    # Assign images to questions and convert to permanent URLs
                    for i, q_data in enumerate(vision_questions):
                        if i < len(quiz_images):
                            img_url = quiz_images[i].image_url
                            # Convert to permanent public URL if it's a presigned URL
                            if img_url and ('X-Amz-' in img_url or img_url.startswith('/minio/')):
                                url_path = img_url.split('?')[0] if '?' in img_url else img_url
                                url_path = url_path.replace('/minio/', '')
                                if '/' in url_path:
                                    storage_path = url_path.split('/', 1)[1]
                                    img_url = storage.get_public_url(storage_path)
                            q_data["image_url"] = img_url
                            q_data["image_caption"] = quiz_images[i].caption or f"Slika {i+1}"
                    
                    questions_data = vision_questions
                    
                    detected_subject = "opšte znanje"
                    title_lower = document.title.lower() if document.title else ""
                    if "matematika" in title_lower or "matem" in title_lower:
                        detected_subject = "matematika"
                    elif "fizika" in title_lower or "fizik" in title_lower:
                        detected_subject = "fizika"
                    elif "hemija" in title_lower or "hemij" in title_lower:
                        detected_subject = "hemija"
                    elif "biologija" in title_lower or "biolog" in title_lower:
                        detected_subject = "biologija"
                    elif "istorija" in title_lower or "istor" in title_lower:
                        detected_subject = "istorija"
                    elif "geografija" in title_lower or "geograf" in title_lower:
                        detected_subject = "geografija"
                    elif "informatika" in title_lower or "informati" in title_lower:
                        detected_subject = "informatika"
                    elif "srpski" in title_lower or "jezik" in title_lower:
                        detected_subject = "srpski jezik"
                    elif "engleski" in title_lower or "english" in title_lower:
                        detected_subject = "engleski jezik"
                    
                    # Add questions to database
                    for idx, q_data in enumerate(questions_data):
                        try:
                            db.add(Question(
                                quiz_id=quiz.id,
                                question_text=q_data["question_text"],
                                question_type=q_data["question_type"],
                                options=q_data["options"],
                                correct_answer=q_data["correct_answer"],
                                explanation=q_data.get("explanation", ""),
                                points=q_data.get("points", 1),
                                order_index=q_data.get("order_index", 0),
                                image_url=q_data.get("image_url"),
                                image_caption=q_data.get("image_caption"),
                            ))
                            update_quiz_progress(str(quiz.id), idx + 1, len(questions_data))
                        except Exception as q_err:
                            logger.error(f"Error adding question {idx}: {q_err}")
                    
                    quiz.total_questions = len(questions_data)
                    quiz.target_questions = len(questions_data)
                    quiz.status = "ready"
                    quiz.subject_area = detected_subject
                    quiz.description = f"Automatski generisan kviz iz slika dokumenta. Коришћен AI Vision за генерисање питања."
                    db.commit()
                    update_quiz_progress(str(quiz.id), len(questions_data), len(questions_data))
                    return True, "success"
                else:
                    # AI Vision also failed
                    quiz.status = "error"
                    quiz.description = f"⚠️ Документ садржи само слике без текста. AI Vision није успео да генерише питања: {vision_error}"
                    db.commit()
                    return False, f"vision_failed: {vision_error}"
            else:
                # No chunks AND no images
                quiz.status = "error"
                quiz.description = f"⚠️ Нема довољно квалитетних одломака за генерисање квиза. Документ можда садржи само слике или врло кратак текст."
                db.commit()
                return False, "no_quality_chunks"

        # Auto-determine num_questions based on document size if not specified
        effective_num_questions = _auto_num_questions(len(all_chunks), num_questions)
        logger.info(f"Document has {len(all_chunks)} chunks → generating {effective_num_questions} questions")

        # Check available unused chunks
        unused_chunks = [c for c in all_chunks if (getattr(c, 'used_for_quiz', 0) or 0) == 0]
        unused_count = len(unused_chunks)
        total_count = len(all_chunks)
        
        logger.info(f"Chunk usage: {unused_count}/{total_count} unused chunks available")
        
        # Store for later use
        initial_unused_count = unused_count
        
        # If no unused chunks, return error with info
        if unused_count == 0:
            quiz.status = "error"
            quiz.description = f"⚠️ Сви одломци из документа су већ искоришћени за генерисање квизова! Можете одговарати на претходно креиране квизове или креирати нове из других докумената."
            db.commit()
            logger.warning(f"Document {document_id} has all chunks exhausted for quiz generation")
            return False, "all_chunks_exhausted"

        # Select evenly-distributed chunks (covers whole document, respects AI context limit)
        chunks = _select_chunks_for_quiz(all_chunks, max_chars=10000)
        
        # FALLBACK: If no chunks but have images, use AI Vision to generate questions from images
        if not chunks:
            logger.warning(f"Document {document_id} has no text chunks, checking for images...")
            
            # Get images for this document - properly filter by document_id
            from app.db.models.quiz import QuizImage
            doc_images = db.query(QuizImage).filter(
                QuizImage.document_id == document_id
            ).all()
            
            if doc_images:
                logger.warning(f"Found {len(doc_images)} images, using AI Vision to generate questions...")
                
                # Detect subject area from images using AI
                detected_subject = "matematika"  # Default
                try:
                    # Sample a few images to detect subject
                    sample_images = doc_images[:3]
                    # For now, use keyword detection from the title
                    title_lower = document.title.lower() if document.title else ""
                    if "matematika" in title_lower or "matem" in title_lower:
                        detected_subject = "matematika"
                    elif "fizika" in title_lower or "fizik" in title_lower:
                        detected_subject = "fizika"
                    elif "hemija" in title_lower or "hemij" in title_lower:
                        detected_subject = "hemija"
                    elif "biologija" in title_lower or "biolog" in title_lower:
                        detected_subject = "biologija"
                    elif "istorija" in title_lower or "istor" in title_lower:
                        detected_subject = "istorija"
                    elif "geografija" in title_lower or "geograf" in title_lower:
                        detected_subject = "geografija"
                    logger.info(f"Detected subject from document title: {detected_subject}")
                except Exception as e:
                    logger.warning(f"Could not detect subject from title: {e}")
                
                # Try to generate questions from images using AI Vision
                vision_success, vision_questions, vision_error = self._generate_questions_from_images(
                    doc_images, 
                    num_questions,
                    provider=provider,
                    user_openai_key=user_openai_key,
                    user_claude_key=user_claude_key,
                    user_gemini_key=user_gemini_key,
                    user_groq_key=user_groq_key,
                    user_mistral_key=user_mistral_key,
                    user_deepseek_key=user_deepseek_key,
                )
                
                if vision_success and vision_questions:
                    logger.info(f"AI Vision generated {len(vision_questions)} questions from images")
                    quiz_images = doc_images
                    
                    # Get public URL for images
                    from app.services.storage_cloud import CloudStorageService
                    storage = CloudStorageService()
                    
                    # Assign images to questions and convert to permanent URLs
                    for i, q_data in enumerate(vision_questions):
                        if i < len(quiz_images):
                            img_url = quiz_images[i].image_url
                            # Convert to permanent public URL if it's a presigned URL
                            if img_url and ('X-Amz-' in img_url or img_url.startswith('/minio/')):
                                url_path = img_url.split('?')[0] if '?' in img_url else img_url
                                url_path = url_path.replace('/minio/', '')
                                if '/' in url_path:
                                    storage_path = url_path.split('/', 1)[1]
                                    img_url = storage.get_public_url(storage_path)
                            q_data["image_url"] = img_url
                            q_data["image_caption"] = quiz_images[i].caption or f"Slika {i+1}"
                    
                    questions_data = vision_questions
                    # detected_subject already set from document title above
                    
                    # Add questions to database
                    for idx, q_data in enumerate(questions_data):
                        try:
                            db.add(Question(
                                quiz_id=quiz.id,
                                question_text=q_data["question_text"],
                                question_type=q_data["question_type"],
                                options=q_data["options"],
                                correct_answer=q_data["correct_answer"],
                                explanation=q_data.get("explanation", ""),
                                points=q_data.get("points", 1),
                                order_index=q_data.get("order_index", 0),
                                image_url=q_data.get("image_url"),
                                image_caption=q_data.get("image_caption"),
                            ))
                            update_quiz_progress(str(quiz.id), idx + 1, len(questions_data))
                        except Exception as q_err:
                            logger.error(f"Error adding question {idx}: {q_err}")
                    
                    quiz.total_questions = len(questions_data)
                    quiz.target_questions = len(questions_data)
                    quiz.status = "ready"
                    quiz.subject_area = detected_subject
                    quiz.description = f"Automatski generisan kviz iz slika dokumenta. Коришћен AI Vision за генерисање питања."
                    db.commit()
                    update_quiz_progress(str(quiz.id), len(questions_data), len(questions_data))
                    return True, "success"
                else:
                    # AI Vision also failed
                    quiz.status = "error"
                    quiz.description = f"⚠️ Документ садржи само слике без текста. AI Vision није успео да генерише питања: {vision_error}"
                    db.commit()
                    return False, f"vision_failed: {vision_error}"
            else:
                # No chunks AND no images
                quiz.status = "error"
                quiz.description = f"⚠️ Нема довољно квалитетних одломака за генерисање квиза. Документ можда садржи само слике или врло кратак текст."
                db.commit()
                return False, "no_quality_chunks"
        
        # Track which chunk IDs were used
        used_chunk_ids = [c.id for c in chunks]
        
        logger.info(f"Selected {len(chunks)} of {len(all_chunks)} chunks for quiz context (evenly spread)")

        combined_text = "\n\n".join(
            c.translated_content or c.content for c in chunks
        )

        # Detect subject area using AI
        logger.info("Detecting subject area for quiz...")
        detected_subject = detect_subject_area(combined_text)
        logger.info(f"Detected subject area: {detected_subject}")
        
        # Update quiz with detected subject area
        quiz.subject_area = detected_subject

        # Pokušaj da obogatiš kontekst sa RAG knowledge base
        try:
            from app.services.rag import similarity_search
            rag_chunks = similarity_search(db, f"quiz questions about: {quiz.title}", top_k=3)
            if rag_chunks:
                rag_context = "\n\n".join([c['content'] for c in rag_chunks[:3]])
                combined_text = combined_text + "\n\n=== DODATNI KONTEKST IZ BAZE ZNANJA ===\n\n" + rag_context
        except Exception:
            pass

        # Fetch images from document for quiz questions
        quiz_images = []
        try:
            # IMPORTANT: Rollback any failed transaction before new queries
            db.rollback()
            
            from app.db.models.quiz import QuizImage
            
            # Get ALL images first, then filter in Python (most reliable)
            all_images = db.query(QuizImage).all()
            doc_id_str = str(document_id)
            
            logger.warning(f"DEBUG: Total images in DB: {len(all_images)}")
            logger.warning(f"DEBUG: Looking for doc_id: '{doc_id_str}'")
            
            # Debug: show first few image document_ids
            if all_images:
                sample_ids = [str(img.document_id) for img in all_images[:3]]
                logger.warning(f"DEBUG: Sample image doc_ids: {sample_ids}")
            
            quiz_images = [img for img in all_images if str(img.document_id) == doc_id_str]
            
            logger.warning(f"DEBUG: Found {len(quiz_images)} quiz_images for doc {doc_id_str}")
            
        except Exception as e:
            logger.warning(f"Could not fetch quiz images: {e}")

        # ============================================================
        # HIBRIDNI TEKSTUALNI PRISTUP (PRIORITET)
        # ============================================================
        # 1. AI generise pitanje iz TEKSTA (chunks)
        # 2. AI ODMAH odlucuje da li je slika relevantna za to pitanje
        # 3. Ako pitanje pominje sliku/dijagram → ukljuci image_url
        # 4. Ako nije vezano za sliku → null
        
        if chunks and len(chunks) >= 2:
            logger.info(f"Using HYBRID TEXT generation with optional images")
            logger.info(f"  - Chunks: {len(chunks)}")
            logger.info(f"  - Images: {len(quiz_images) if quiz_images else 0}")
            
            text_success, text_questions, text_error = self._generate_text_questions_with_optional_images(
                chunks=chunks,
                quiz_images=quiz_images or [],
                num_questions=effective_num_questions,
                subject_area=detected_subject,
                user_openai_key=user_openai_key,
                user_claude_key=user_claude_key,
                user_gemini_key=user_gemini_key,
                user_deepseek_key=user_deepseek_key,
                user_groq_key=user_groq_key,
                user_mistral_key=user_mistral_key,
            )
            
            if text_success and text_questions:
                logger.info(f"Hybrid text generation generated {len(text_questions)} questions!")
                
                # Build page_to_image_url mapping for linking images to questions
                page_to_image_url = {}
                if quiz_images:
                    try:
                        from app.services.storage_cloud import CloudStorageService
                        storage = CloudStorageService()
                        for img in quiz_images:
                            page_num = getattr(img, 'page_number', None)
                            if page_num and page_num not in page_to_image_url:
                                # Use storage_path (which is correct) instead of image_url
                                storage_path = getattr(img, 'storage_path', None) or ""
                                if storage_path:
                                    try:
                                        img_url = storage.get_public_url(storage_path)
                                    except Exception as url_err:
                                        logger.warning(f"Could not get public URL for {storage_path}: {url_err}")
                                        img_url = None
                                else:
                                    img_url = None
                                page_to_image_url[page_num] = img_url
                    except Exception as img_err:
                        logger.warning(f"Could not get image URLs: {img_err}")
                
                for idx, q_data in enumerate(text_questions):
                    try:
                        image_url = None
                        image_caption = None
                        
                        # Check if AI said this question needs an image
                        image_page = q_data.get("image_page")
                        if image_page and image_page in page_to_image_url:
                            image_url = page_to_image_url[image_page]
                            image_caption = f"Stranica {image_page}"
                        
                        db.add(Question(
                            quiz_id=quiz.id,
                            question_text=q_data["question_text"],
                            question_type=q_data.get("question_type", "multiple_choice"),
                            options=q_data["options"],
                            correct_answer=q_data["correct_answer"],
                            explanation=q_data.get("explanation", ""),
                            points=q_data.get("points", 1),
                            order_index=q_data.get("order_index", idx),
                            image_url=image_url,
                            image_caption=image_caption,
                        ))
                        update_quiz_progress(str(quiz.id), idx + 1, len(text_questions))
                    except Exception as q_err:
                        logger.error(f"Error adding question {idx}: {q_err}")
                
                quiz.total_questions = len(text_questions)
                quiz.target_questions = len(text_questions)
                quiz.status = "ready"
                quiz.description = f"Automatski generisan kviz iz teksta - slike su ukljucene gde su relevantne za pitanje."
                db.commit()
                update_quiz_progress(str(quiz.id), len(text_questions), len(text_questions))
                
                if used_chunk_ids:
                    mark_chunks_as_used(used_chunk_ids, db)
                
                logger.info(f"Quiz {quiz.id} completed with hybrid text-based generation")
                return True, "success"
            else:
                logger.warning(f"Hybrid text generation failed ({text_error}), falling back to legacy approach")
        
        # ============================================================
        # FALLBACK: Legacy text-based generation
        # ============================================================
        
        # Re-set subject area after rollback (it was lost due to rollback)
        quiz.subject_area = detected_subject

        # Get page-based image mapping for chunks
        chunk_image_map = get_images_for_chunks(chunks, quiz_images)
        logger.warning(f"DEBUG: chunk_image_map has {len(chunk_image_map)} entries")
        
        # Pass chunks info to AI for better context
        chunk_context_for_ai = []
        for idx, chunk in enumerate(chunks):
            chunk_info = {
                'text': (chunk.translated_content or chunk.content)[:500],  # First 500 chars
                'page': getattr(chunk, 'page_number', None),
                'images': [img.image_url for img in chunk_image_map.get(idx, [])]
            }
            chunk_context_for_ai.append(chunk_info)

        success, questions_data, used_provider = self.generate_questions_with_ai(
            text=combined_text,
            num_questions=effective_num_questions,
            provider=provider,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
            quiz_images=quiz_images,
            chunk_image_map=chunk_image_map,
            subject_area=detected_subject,
        )

        if not success or not questions_data:
            quiz.status = "error"
            db.commit()
            return False, ""

        # Assign images to questions based on page numbers (chunk -> image mapping)
        # This ensures the correct image appears with its related text
        if chunk_image_map and len(questions_data) > 0:
            for i, q_data in enumerate(questions_data):
                if i in chunk_image_map and chunk_image_map[i]:
                    # Get first image for this chunk/page
                    img = chunk_image_map[i][0]
                    questions_data[i]["image_url"] = img.image_url
                    questions_data[i]["image_caption"] = img.caption or f"Slika sa stranice {img.page_number}"
                    logger.info(f"Assigned image from page {img.page_number} to question {i+1}")

        for idx, q_data in enumerate(questions_data):
            try:
                db.add(Question(
                    quiz_id=quiz.id,
                    question_text=q_data["question_text"],
                    question_type=q_data["question_type"],
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation", ""),
                    points=q_data.get("points", 1),
                    order_index=q_data.get("order_index", 0),
                    image_url=q_data.get("image_url"),
                    image_caption=q_data.get("image_caption"),
                    exact_word=q_data.get("exact_word"),
                    alternative_words=q_data.get("alternative_words"),
                    case_insensitive=q_data.get("case_insensitive", True),
                    formula=q_data.get("formula"),
                    steps=q_data.get("steps"),
                ))
                # Update progress in Redis after each question
                update_quiz_progress(str(quiz.id), idx + 1, len(questions_data))
            except Exception as q_err:
                logger.error(f"Error adding question {idx}: {q_err}")

        quiz.total_questions = len(questions_data)
        quiz.target_questions = len(questions_data)  # Mark as complete - no more expected
        quiz.status = "ready"
        
        # Try to commit everything at once
        try:
            db.commit()
            # Update final progress in Redis
            update_quiz_progress(str(quiz.id), len(questions_data), len(questions_data))
            
            # Mark chunks as used AFTER successful commit
            if used_chunk_ids:
                mark_chunks_as_used(used_chunk_ids, db)
            
            # Update description with remaining chunks info
            if 'initial_unused_count' in dir():
                remaining = initial_unused_count - len(used_chunk_ids)
                if remaining >= 0:
                    doc = db.query(Document).filter(Document.id == document_id).first()
                    doc_title = doc.title if doc else "документ"
                    quiz.description = f"Automatski generisan kviz из документа '{doc_title}'. Преостало одломака за нове квизове: {remaining}"
                    db.commit()
            
            logger.info(f"Quiz {quiz_id} saved: {len(questions_data)} questions")
        except Exception as commit_err:
            logger.error(f"First commit error: {commit_err}")
            # Try to recover by creating questions one by one
            db.rollback()
            db.begin()
            for q_data in questions_data:
                try:
                    q = Question(
                        quiz_id=quiz.id,
                        question_text=q_data["question_text"],
                        question_type=q_data["question_type"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data.get("explanation", ""),
                        points=q_data.get("points", 1),
                        order_index=q_data.get("order_index", 0),
                        image_url=q_data.get("image_url"),
                        image_caption=q_data.get("image_caption"),
                        exact_word=q_data.get("exact_word"),
                        alternative_words=q_data.get("alternative_words"),
                        case_insensitive=q_data.get("case_insensitive", True),
                        formula=q_data.get("formula"),
                        steps=q_data.get("steps"),
                    )
                    db.add(q)
                    db.flush()
                except Exception as single_err:
                    logger.error(f"Error adding single question: {single_err}")
            try:
                db.query(Quiz).filter(Quiz.id == quiz.id).update(
                    {"status": "ready", "total_questions": len(questions_data), "target_questions": len(questions_data)}
                )
                db.commit()
                
                # Mark chunks as used in recovery path too
                if used_chunk_ids:
                    mark_chunks_as_used(used_chunk_ids, db)
                
                logger.info(f"Quiz {quiz_id} saved (recovery): {len(questions_data)} questions")
            except Exception as err_final:
                logger.error(f"Final commit error: {err_final}")
        
        logger.info(f"Kviz {quiz_id} spreman — {len(questions_data)} pitanja [{used_provider}]")
        return True, used_provider

    def submit_attempt(
        self,
        db: Session,
        quiz_id: str,
        user_id: str,
        attempt_id: str,
        answers: List[dict],
    ) -> QuizAttempt:
        """Evaluira odgovore i zatvara attempt."""
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt:
            raise ValueError("Pokušaj nije pronađen")

        questions = {str(q.id): q for q in db.query(Question).filter(Question.quiz_id == quiz_id).all()}
        total_points = sum(q.points for q in questions.values())
        earned = 0

        for ans in answers:
            q = questions.get(ans["question_id"])
            if not q:
                continue
            is_correct = self._check_answer(q, ans["user_answer"].strip())
            pts = q.points if is_correct else 0
            earned += pts
            db.add(QuizAnswer(
                attempt_id=attempt_id,
                question_id=q.id,
                user_answer=ans["user_answer"].strip(),
                is_correct=is_correct,
                points_earned=pts,
            ))

        percentage = (earned / total_points * 100) if total_points > 0 else 0
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        # Handle None passing_score - default to 60
        passing = quiz.passing_score if quiz and quiz.passing_score is not None else 60
        passed = percentage >= passing

        from datetime import datetime, timezone
        attempt.score = earned
        attempt.total_points = total_points
        attempt.percentage = round(percentage, 1)
        attempt.passed = passed
        attempt.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(attempt)
        return attempt

    def _check_answer(self, question: Question, user_answer: str) -> bool:
        if question.question_type == "checkbox":
            correct_set = {v.strip() for v in question.correct_answer.split(",")}
            user_set = {v.strip() for v in user_answer.split(",")}
            return correct_set == user_set
        elif question.question_type == "fill_blank":
            # For fill_blank, check exact_word or alternative_words
            user_answer_clean = user_answer.strip()
            if question.case_insensitive:
                user_answer_clean = user_answer_clean.lower()
                if question.exact_word and user_answer_clean == question.exact_word.lower():
                    return True
                if question.alternative_words:
                    alt_words = question.alternative_words if isinstance(question.alternative_words, list) else []
                    return user_answer_clean in [w.lower() for w in alt_words]
            else:
                if question.exact_word and user_answer_clean == question.exact_word:
                    return True
                if question.alternative_words:
                    alt_words = question.alternative_words if isinstance(question.alternative_words, list) else []
                    return user_answer_clean in alt_words
            # Fallback to exact match
            return user_answer_clean.lower() == question.correct_answer.strip().lower()
        return user_answer.lower() == question.correct_answer.strip().lower()

    @staticmethod
    def _check_answer_static(question_type: str, user_answer: str, correct_answer: str) -> bool:
        """Statička verzija za testiranje bez Question objekta."""
        if question_type == "checkbox":
            correct_set = {v.strip() for v in correct_answer.split(",")}
            user_set = {v.strip() for v in user_answer.split(",")}
            return correct_set == user_set
        return user_answer.lower().strip() == correct_answer.lower().strip()

    def get_available_providers(self) -> List[dict]:
        return _get_available_providers()


# ============================================================
# SUBJECT AREA DETECTION & SPECIALIZED PROMPTS
# ============================================================

SUBJECT_KEYWORDS = {
    "matematika": ["izračunaj", "jednačina", "površina", "zapremina", "trougao", "kvadrat", "formula", "x", "reši", "zadatak", "izraz", "jednakost", "pravougaonik", "krug", "kocka", "lopta", "piramida", "valjak", "procenat", "razlomak", "decimalni", "koren", "stepen", "logaritam", "sistem jednačina", "nejednačina", "funkcija", "grafik", "ugao", "simetrala", "pitagora", "израчунај", "једначина", "површина", "запремина", "троугао", "квадрат", "формула", "реши", "задатак", "израз", "једнакост", "правоугаоник", "круг", "коцка", "лопта", "пирамида", "ваљак", "проценат", "разломак", "децинални", "корен", "степен", "логаритам", "систем једначина", "неједначина", "функција", "график", "угао", "симетрала", "питагора", "рачунај", "сабирање", "одузимање", "множење", "дељење", "једнакост", "неједнакост"],
    "fizika": ["sila", "brzina", "energija", "talas", "električni", "magnetni", "newton", "joule", "metar", "sekunda", "kg", "fizikalni", "mehanika", "optika", "termodinamika", "kinetika", "potencijal", "naboj", "struja", "napon", "otpor", "magnetno polje", "elektromagnet", "frekvencija", "talasna dužina", "amplituda", "сила", "брзина", "енергија", "талас", "електрични", "магнетни", "Њутн", "Метар", "Секунда", "физика", "механика", "оптика", "термодинамика", "кинетика", "потенцијал", "набој", "струја", "напон", "отпор", "магнетно поље", "електромagnet", "фреквенција", "таласна дужина", "амплитуда", "гравитација", "маса", "време", "брзина", "убрзање", "сила", "потисак", "трење"],
    "hemija": ["reakcija", "jedinjenje", "atom", "molekul", "hemijska", "oksidacija", "kisik", "vodonik", "ugljenik", "kemijski", "element", "periodni sistem", "metal", "nemetal", "kiselina", "baza", "so", "oksid", "redukcija", "elektroliza", "organska", "neorganska", "supstanca", "rastvor", "koncentracija", "реакција", "једињење", "атом", "молекул", "хемијска", "оксидација", "кисеоник", "водоник", "угљеник", "хемијски", "елемент", "периодни систем", "метал", "неметал", "киселина", "база", "со", "оксид", "редукција", "електролиза", "органска", "неорганска", "супстанца", "раствор", "концентрација", "хемија", "јон", "молекул", "атомско језгро", "електрон", "протон", "неутрон", "период", "група", "халид", "сулфид", "нитрат", "карбонат"],
    "biologija": ["ćelija", "organizam", "gen", "enzim", "metabolizam", "dna", "rna", "biljka", "životinja", "bakterija", "virus", "fotosinteza", "respiracija", "digestija", "cirkulacija", "nervni sistem", "imuni sistem", "hormon", "ćelija", "tkivo", "organ", "sistem", "mutacija", "evolucija", "nasleđе", "ћелија", "организам", "ген", "ензим", "метаболизам", "ДНК", "РНК", "биљка", "животиња", "бактерија", "вирус", "фотосинтеза", "респирација", "дигестија", "циркулација", "нервни систем", "имуни систем", "хормон", "ткиво", "орган", "систем", "мутација", "еволуција", "наслеђе", "биологија", "ћелијска мембрана", "цитоплазма", "језгро", "митохондрија", "рибозом", "лишћ", "корен", "стабло", "цвет", "плод"],
    "istorija": ["godina", "vek", "rat", "vladar", "događaj", "istorijski", "pre", "posle", "godine", "stoljeće", "monarhija", "republika", "imperija", "vojna", "mir", "revolucija", "nezavisnost", "grad", "država", "narod", "kultura", "civilizacija", "праисторија", "антика", "средњи век", "нови век", "година", "век", "рат", "владар", "догађај", "историјски", "монархија", "република", "империја", "војна", "мир", "револуција", "независност", "град", "држава", "народ", "култура", "цивилизација", "историја", "антички", "средњевековни", "модерни", "праисторијски", "пећински", "пирамида", "храм", "палата", "црква", "манастир"],
    "geografija": ["država", "grad", "reka", "planina", "more", "kontinenti", "obala", "ostrvo", "jezero", "geografski", "klima", "vegetacija", "stanovništvo", "privreda", "reljef", "pustinje", "tropski", "umereni", "polarni", "ekvator", "tropski", "meridian", "paralela", "држава", "град", "река", "планина", "море", "континенти", "обала", "острво", "језеро", "географски", "клима", "вегетација", "становништо", "привреда", "рељеф", "пустиње", "тропски", "умерени", "поларни", "екватор", "меридијан", "паралела", "географиjа", "континент", "атмосфера", "хидросфера", "литосфера", "биосфера", "климат", "време", "температура", "падавине", "ветар"],
    "jezici": ["reč", "rečenica", "gramatika", "glagol", "imenica", "prevedi", "translation", "verb", "noun", "adjectiv", "prilog", "predlog", "veznik", "uzvik", "padež", "rod", "broj", "lice", "nastavak", "prefiks", "sufiks", "koren", "glas", "pismo", "alfabet", "jezik", "dijalekat", "реч", "реченица", "граматика", "глагол", "именица", "преведи", "превод", "глагол", "именица", "прилог", "предлог", "везник", "узвик", "падеж", "род", "број", "лице", "наставак", "префикс", "суфикс", "корен", "глас", "писмо", "алфабет", "језик", "дијалекат", "латиница", "ћирилица", "словенски", "германски", "романски"],
    "pravo": ["zakon", "član", "propis", "prekršaj", "krivični", "sud", "paragraf", "pravo", "krivično", "građansko", "upravno", "ustav", "parlament", "vlada", "izvršna", "zakonodavna", "sudska", "presuda", "tužba", "odbrana", "svjedok", "dokaz", "rok", "postupak", "закон", "члан", "пропис", "прекршај", "кривични", "суд", "параграф", "право", "кривично", "грађанско", "управно", "устав", "парламент", "влада", "извршна", "законодавна", "судска", "пресуда", "тужба", "одбрана", "сведок", "доказ", "рок", "поступак", "право", "судови", "законодавство", "извршна власт", "судска власт"],
    "ekonomija": ["cena", "trošak", "prihod", "profit", "investicija", "tržište", "novac", "banka", "kredit", "inflacija", "deflacija", "BDP", "nezaposlenost", "ponuda", "potražnja", "robna", "uslužna", "privreda", "preduzeće", "preduzetnik", "dividenda", "akcija", "obveznica", "devize", "devizni", "цена", "трошак", "приход", "профит", "инвестиција", "тржиште", "новац", "банка", "кредит", "инфлација", "дефлација", "БДП", "незапосленост", "понуда", "потражња", "робна", "услужна", "привреда", "предузеће", "предузетник", "дивиденда", "акција", "обvezница", "девизе", "девизни", "економија", "макроекономија", "микроекономија", "тржишна економија"],
    "informatika": ["program", "kod", "algoritam", "funkcija", "varijabla", "loop", "computer", "software", "hardware", "internet", "mreža", "baza podataka", "sql", "python", "java", "programiranje", "debug", "kompajliranje", "izvršavanje", "memorija", "procesor", "operativni sistem", "fajl", "folder", "програм", "код", "алгоритам", "функција", "варијабла", "петља", "рачунар", "софтвер", "хардвер", "интернет", "мрежа", "база података", "програмирање", "дебуг", "компајлирање", "извршавање", "меморија", "процесор", "оперативни систем", "фајл", "фолдер", "информатика", "рачунарство", "дигитални", "бинарни", "систем"],
}


def detect_subject_area(text: str, num_samples: int = 20) -> str:
    """
    Detektuje oblast dokumenta na osnovu teksta.
    Koristi ključne reči + AI za precizniju detekciju.
    """
    text_lower = text.lower()
    
    # Count keyword matches for each subject
    subject_scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        subject_scores[subject] = score
    
    # Get the subject with highest score
    if max(subject_scores.values()) > 0:
        detected = max(subject_scores.items(), key=lambda x: x[1])
        logger.info(f"Subject detected by keywords: {detected[0]} (score: {detected[1]})")
        return detected[0]
    
    # If no keywords matched, use AI for detection
    return _detect_subject_with_ai(text[:3000])


def _detect_subject_with_ai(text: str) -> str:
    """AI-based subject area detection when keywords don't match."""
    prompt = f"""Analiziraj sledeći tekst i odredi kojoj predmetnoj oblasti pripada.
    
Moguće oblasti: matematika, fizika, hemija, biologija, istorija, geografija, jezici, pravo, ekonomija, informatika, medicina, muzika, likovna, ostalo

Tekst:
{text[:2000]}

Odgovori samo sa jednom rečju - nazivom oblasti. Ne piši ništa drugo."""

    clients = _build_clients()
    
    for provider in ["openai", "groq", "claude", "ollama"]:
        client = clients.get(provider)
        if not client or not client.is_available():
            continue
        try:
            with httpx.Client(timeout=30) as c:
                if provider == "ollama":
                    r = c.post(
                        f"{settings.OLLAMA_HOST}/api/generate",
                        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}
                    )
                    response = r.json().get("response", "").strip().lower()
                else:
                    # For OpenAI-compatible APIs
                    api_key = ""
                    if provider == "openai":
                        api_key = settings.OPENAI_API_KEY
                    elif provider == "groq":
                        api_key = settings.GROQ_API_KEY
                    elif provider == "claude":
                        continue  # Claude needs different format
                    
                    r = c.post(
                        f"https://api.{provider}.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "gpt-4o" if provider == "openai" else "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50
                        }
                    )
                    response = r.json()["choices"][0]["message"]["content"].strip().lower()
                
                # Extract just the subject name
                for subject in SUBJECT_KEYWORDS.keys():
                    if subject in response:
                        logger.info(f"Subject detected by AI ({provider}): {subject}")
                        return subject
        except Exception as e:
            logger.warning(f"AI subject detection failed for {provider}: {e}")
            continue
    
    return "ostalo"


STRUCTURE_PATTERNS = {
    "test": ["тест", "test", "предлог", "провера", "испит", "контролни", "задатак за оцену", "test knowledge", "exam", "quiz", "assessment"],
    "zadaci": ["задаци", "zadaci", "вежба", "exercise", "problem", "задатак", "practice", "problems", "exercises"],
    "primer": ["пример", "primer", "solved", "решени", "пример решени", "example", "solution", "решење"],
    "resenje": ["решења", "resenja", "solutions", "answers", "resenje zadataka", "key", "answers to problems"],
    "podsetnik": ["подсетник", "podsetnik", "напомена", " напомене", "reminder", "review", "summary", "резиме", "сажетак"],
    "obnavljanje": ["обнављање", "obnavljanje", "повторење", "repeat", "recap", "review chapter"],
    "pitanja": ["питања", "pitanja", "questions", "питалице", "pitanja za ponavljanje"],
}


def detect_document_structure(text: str) -> dict:
    """
    Detektuje strukturu dokumenta na osnovu teksta.
    Vraca recnik sa strukturom i brojem pojavljivanja.
    """
    text_lower = text.lower()
    structure_counts = {}
    
    for structure, patterns in STRUCTURE_PATTERNS.items():
        count = sum(1 for pattern in patterns if pattern in text_lower)
        if count > 0:
            structure_counts[structure] = count
    
    if not structure_counts:
        return {"tip": "opšti", "detalji": {}}
    
    dominant = max(structure_counts.items(), key=lambda x: x[1])
    
    result = {"tip": dominant[0], "detalji": structure_counts}
    
    logger.info(f"Document structure detected: {result}")
    return result


def get_structure_based_prompt(structure: dict, subject_area: str) -> str:
    """
    Vraca dodatne instrukcije za prompt na osnovu strukture dokumenta.
    """
    tip = structure.get("tip", "opšti")
    
    structure_prompts = {
        "test": """
Fokusiraj se na pitanja koja se koriste u testovima:
- Višestruki izbor (A, B, V, G, D)
- Pitanja sa jednim tačnim odgovorom
- Kratka i koncizna pitanja
- Fokus na činjenice i definicije
""",
        "zadaci": """
Fokusiraj se na problemske zadatke:
- Računski zadaci sa koracima
- Objašnjenje postupka rešavanja
- Primena formula
- Realni primeri iz konteksta
""",
        "primer": """
Fokusiraj se na objašnjenja i primere:
- Pitanja koja testiraju razumevanje primera
- "Šta ako" scenariji
- Poređenje sa drugim pristupima
- Kritička analiza primera
""",
        "resenje": """
Izbegavaj detalje koja su već data u rešenjima.
Kreiraj nova pitanja koja testiraju primenu znanja.
""",
        "podsetnik": """
Kreiraj pitanja koja sumiraju ključne koncepte.
Fokus na definicije i formule.
""",
        "obnavljanje": """
Kreiraj pitanja za ponavljanje i utvrđivanje gradiva.
Kombinuj različite koncepte.
""",
        "pitanja": """
Kreiraj raznovrsna pitanja koja pokrivaju celo gradivo.
Kombinuj različite tipove pitanja.
""",
    }
    
    return structure_prompts.get(tip, "")


def get_specialized_prompt(subject_area: str, num_questions: int, text: str) -> str:
    """
    Vraća optimizovani prompt za specifičnu oblast.
    """
    base_rules = """
STRICT FILTERING RULES - IGNORE the following content COMPLETELY:
1. "This page intentionally left blank" and similar blank page notices
2. Copyright notices, edition notices
3. "Notice to Readers", "Notice to Reader"
4. Table of Contents, Prefaces, Acknowledgments, Introductions
5. Figure captions, image descriptions
6. Page numbers, headers, footers
7. Very short content (< 100 characters)
8. Generic statements without specific information
9. Notes sections, footnotes
10. Cover pages, back covers
11. "About the Author"
12. OCR noise, garbled text
"""
    
    # Subject-specific instructions
    subject_instructions = {
        "matematika": f"""
IMPORTANT - MATHEMATICS QUESTIONS:
- 40% CALCULATION: Step-by-step math problems with formulas
  Example: "Kolika je površina pravougaonika ako su stranice a=5cm i b=3cm?"
  Options: A) 15 cm², B) 8 cm², C) 16 cm², D) 12 cm²
  Explanation MUST show: formula → substitution → calculation → result

- 35% MULTIPLE_CHOICE: Problem solving with explanation
- 25% TRUE_FALSE: Only for definitions/concepts, NEVER for calculations

NEVER create True/False for calculation problems!
Explanations MUST include the formula used and step-by-step calculation.
""",
        
        "fizika": f"""
IMPORTANT - PHYSICS QUESTIONS:
- 40% CALCULATION: Physics problems with formulas and units
  Example: "Kolika je kinetička energija tela mase 2kg koje se kreće brzinom 3m/s?"
  Options: A) 9J, B) 6J, C) 12J, D) 3J
  Explanation: E = mv²/2 = 2×9/2 = 9J

- 35% MULTIPLE_CHOICE: Concepts and definitions
- 25% TRUE_FALSE: Physical laws and facts

Always include UNITS in explanations!
""",
        
        "hemija": f"""
IMPORTANT - CHEMISTRY QUESTIONS:
- 30% MULTIPLE_CHOICE: Chemical reactions, compounds, elements
- 25% CHEMICAL_EQUATION: Complete the reaction
  Example: "Dopuni jednačinu: 2H₂ + O₂ → ?"
  Options: A) 2H₂O, B) H₂O, C) H₂O₂, D) O₂
- 20% CALCULATION: Molar mass, concentrations
- 25% TRUE_FALSE: Chemical facts

Include chemical formulas in explanations!
""",
        
        "biologija": f"""
IMPORTANT - BIOLOGY QUESTIONS:
- 50% MULTIPLE_CHOICE: Cell biology, organisms, systems
- 30% CHECKBOX: Select all that apply (structures, functions)
- 20% TRUE_FALSE: Biological facts and processes

Focus on: ćelija, organeli, sistemi, procesi, genetika
""",
        
        "istorija": f"""
IMPORTANT - HISTORY QUESTIONS:
- 60% MULTIPLE_CHOICE: Events, dates, causes, consequences
  Include: DATUMI, uzroci, posledice, ličnosti
- 40% TRUE_FALSE: Historical facts
  Example: "Da li je tačno: Car Dušan je vladao Srbijom u 14. veku?"

Focus on: datumi, događaji, vladari, civilizacije
""",
        
        "geografija": f"""
IMPORTANT - GEOGRAPHY QUESTIONS:
- 60% MULTIPLE_CHOICE: Countries, capitals, features
  Include: glavni gradovi, karakteristike, lokacije
- 40% TRUE_FALSE: Geographic facts

Focus on: države, glavni gradovi, reke, planine, mora
""",
        
        "jezici": f"""
IMPORTANT - LANGUAGE QUESTIONS:
- 30% FILL_BLANK: Complete the sentence with missing word
  Format: "The cat ___ on the mat."
  Include in JSON: exact_word: "sits", case_insensitive: true
  Options: A) sits, B) runs, C) sleeps, D) eats
  
- 40% MULTIPLE_CHOICE: Vocabulary and grammar
- 30% TRANSLATION: Translate from/to target language

For FILL_BLANK questions, structure:
{{
  "question_text": "The cat ___ on the mat.",
  "question_type": "fill_blank",
  "options": ["sits", "runs", "sleeps", "eats"],
  "correct_answer": "sits",
  "exact_word": "sits",
  "alternative_words": ["is sitting"],
  "case_insensitive": true,
  "explanation": "Glagol 'sit' u present simple trećem licu jednine dobija nastavak -s: sits"
}}
""",
        
        "pravo": f"""
IMPORTANT - LAW QUESTIONS:
- 60% MULTIPLE_CHOICE: Articles, regulations, concepts
- 40% TRUE_FALSE: Legal definitions and facts

Focus on: zakoni, članovi, propisi, definicije
""",
        
        "ekonomija": f"""
IMPORTANT - ECONOMICS QUESTIONS:
- 50% MULTIPLE_CHOICE: Market, prices, economy concepts
- 30% CALCULATION: Simple economics calculations (percentage, profit)
- 20% TRUE_FALSE: Economic facts

Focus on: cena, profit, tržište, novac, investicije
""",
        
        "informatika": f"""
IMPORTANT - IT/COMPUTER SCIENCE QUESTIONS:
- 50% MULTIPLE_CHOICE: Programming, algorithms, concepts
- 30% CODE_ANALYSIS: What does this code do?
- 20% TRUE_FALSE: Technical facts

Focus on: algoritmi, programiranje, mreže, baze podataka
"""
    }
    
    # Get subject-specific instructions or use default
    instructions = subject_instructions.get(subject_area, "")
    
    # Build the final prompt
    prompt = f"""You are an expert educator and assessment designer for {subject_area.upper()}. 
Based on the following text, generate exactly {num_questions} high-quality quiz questions.

{base_rules}

{instructions}

QUESTION TYPES DISTRIBUTION:
- Use the percentages specified in the subject instructions above
- Adjust to fit the actual content in the text
- NEVER use True/False for calculation problems!

EXPLANATION RULES:
- Each explanation MUST be 3-7 SENTENCES
- Start with WHAT the correct answer is
- Then explain WHY it's correct
- For calculations: include formula and step-by-step
- Include relevant facts/concepts

Return ONLY valid JSON array:
[
  {{
    "question_text": "Питање на српском језику?",
    "question_type": "multiple_choice",
    "options": ["Тачан одговор", "Погрешан 1", "Погрешан 2", "Погрешан 3"],
    "correct_answer": "Тачан одговор",
    "explanation": "Објашњење...",
    "points": 1
  }},
  {{
    "question_text": "Колика је вредност: 3 + 5 = ?",
    "question_type": "calculation",
    "options": ["8", "7", "9", "6"],
    "correct_answer": "8",
    "explanation": "Збир бројева 3 и 5 је 8. Користимо сабирање: 3 + 5 = 8",
    "points": 1
  }},
  {{
    "question_text": "The cat ___ on the mat.",
    "question_type": "fill_blank",
    "options": ["sits", "runs", "sleeps", "eats"],
    "correct_answer": "sits",
    "exact_word": "sits",
    "alternative_words": ["is sitting"],
    "case_insensitive": true,
    "explanation": "Glagol 'sit' u present simple trećem licu jednine dobija nastavak -s"
  }}
]

Text:
{text[:12000]}
"""
    return prompt


quiz_service = QuizService()
