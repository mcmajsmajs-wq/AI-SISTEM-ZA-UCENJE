# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE — MULTI-PROVIDER
================================================================================
Servis za generisanje kvizova pomoću AI sa više provajdera:
  - Ollama  (lokalni, besplatni)
  - OpenAI  (GPT-4 / GPT-4o)
  - Claude  (Anthropic)
  + fallback chain (isti pattern kao TranslationService)

Verzija: 2.0.0
================================================================================
"""

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer
from app.db.models.document import Document, Chunk

logger = logging.getLogger(__name__)


# ============================================================
# PROMPT
# ============================================================

QUIZ_PROMPT = """You are an expert educator. Based on the following text, generate exactly {num_questions} quiz questions.

QUESTION TYPE DISTRIBUTION (strictly follow this):
- ~50% multiple_choice  — exactly 1 correct answer, 4 options
- ~30% checkbox         — 2 or more correct answers, 4 options (select ALL that apply)
- ~20% true_false       — Tačno / Netačno

CRITICAL RULES FOR OPTIONS:
1. Options MUST be COMPLETE MEANINGFUL SENTENCES or PHRASES — NEVER single letters like "A", "B", "C", "D"
2. For multiple_choice and checkbox: write 4 plausible options as full text
3. For checkbox: correct_answer MUST be exactly 2 or more comma-separated option values that EXACTLY match text in options array
4. correct_answer must EXACTLY match the text of the option(s) — case-sensitive, word-for-word
5. Options must test real understanding — distractors should be plausible but clearly wrong on close reading

EXPLANATION RULES:
- Clearly state WHY each correct answer is right (cite the text)
- For multiple_choice: briefly explain why each wrong option is incorrect
- For checkbox: explain why each correct option qualifies AND why wrong ones don't
- For true_false: explain what makes the statement true or false
- 2-5 sentences, educational tone
- Use the SAME LANGUAGE as the text

Return ONLY a valid JSON array — no markdown, no extra text:
[
  {{
    "question_text": "What is the primary purpose of the layer mode feature?",
    "question_type": "multiple_choice",
    "options": [
      "To control laser speed and power per layer",
      "To import files from external applications",
      "To set the workspace background color",
      "To manage user account settings"
    ],
    "correct_answer": "To control laser speed and power per layer",
    "explanation": "Layer modes allow assigning different speed and power settings to each layer, enabling precise control over cutting and engraving operations. The other options describe unrelated features not associated with layer modes.",
    "points": 1
  }},
  {{
    "question_text": "Is it true that open shapes cannot be filled with the fill tool?",
    "question_type": "true_false",
    "options": ["Tačno", "Netačno"],
    "correct_answer": "Tačno",
    "explanation": "Tačno — the fill tool only works on closed shapes because filling requires a fully enclosed boundary. Open paths have no enclosed area to fill.",
    "points": 1
  }},
  {{
    "question_text": "Which of the following are valid reasons to use overscanning? (select all that apply)",
    "question_type": "checkbox",
    "options": [
      "To prevent burnt edges at the start and end of each scan line",
      "To allow the laser head to accelerate before reaching the work area",
      "To increase the total file size of the project",
      "To compensate for mechanical inertia at direction changes"
    ],
    "correct_answer": "To prevent burnt edges at the start and end of each scan line,To allow the laser head to accelerate before reaching the work area,To compensate for mechanical inertia at direction changes",
    "explanation": "Overscanning extends the laser path beyond the design edges so the head reaches full speed before engraving begins, preventing burnt edges and compensating for inertia. Increasing file size is not a purpose of overscanning.",
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
        self._available: Optional[bool] = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            r = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            self._available = r.status_code == 200
        except Exception:
            self._available = False
        return self._available

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
_PROVIDER_ORDER = ["gemini", "groq", "mistral", "openai", "claude", "ollama"]

def _build_clients(
    user_openai_key: str = None,
    user_claude_key: str = None,
    user_gemini_key: str = None,
    user_groq_key: str = None,
    user_mistral_key: str = None,
) -> dict:
    """Builds client dict with optional user-level API key overrides."""
    gemini_key  = user_gemini_key  or getattr(settings, 'GEMINI_API_KEY',  '') or ''
    groq_key    = user_groq_key    or getattr(settings, 'GROQ_API_KEY',    '') or ''
    mistral_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '') or ''
    openai_key  = user_openai_key  or getattr(settings, 'OPENAI_API_KEY',  '') or ''
    claude_key  = user_claude_key  or getattr(settings, 'ANTHROPIC_API_KEY','') or ''

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
        "groq":    OpenAICompatQuizClient("groq",    "https://api.groq.com/openai/v1",                          "llama-3.1-8b-instant", groq_key),
        "mistral": OpenAICompatQuizClient("mistral", "https://api.mistral.ai/v1",                               "mistral-small-latest", mistral_key),
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
    """Generise osnovna true/false pitanja kada nijedan AI nije dostupan."""
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 30]
    questions = []
    for i, sentence in enumerate(sentences[:num_questions]):
        questions.append({
            "question_text": f"Da li je tačna sledeća tvrdnja: \"{sentence[:200]}\"?",
            "question_type": "true_false",
            "options": ["Tačno", "Netačno"],
            "correct_answer": "Tačno",
            "explanation": "Ova tvrdnja je direktno navedena u tekstu.",
            "points": 1,
            "order_index": i
        })
    return questions


def _select_chunks_for_quiz(chunks: list, max_chars: int = 10000) -> list:
    """
    Selects evenly-distributed chunks from across the document,
    up to max_chars total. This ensures the quiz covers the whole
    document, not just the first N chunks.
    """
    if not chunks:
        return []
    total = len(chunks)

    # Estimate average chunk length from up to 20 samples
    sample = chunks[::max(1, total // 20)][:20]
    avg_len = sum(len(c.translated_content or c.content) for c in sample) / len(sample)

    # How many chunks can we fit?
    target_count = max(5, int(max_chars / max(avg_len, 100)))
    step = max(1, total // target_count)

    selected = []
    total_chars = 0
    for i in range(0, total, step):
        text = chunks[i].translated_content or chunks[i].content
        if total_chars + len(text) > max_chars:
            break
        selected.append(chunks[i])
        total_chars += len(text)

    return selected


def _auto_num_questions(total_chunks: int, requested: int) -> int:
    """
    If requested > 0, use it (capped to a sane max).
    If requested == 0, calculate based on document size.
    """
    if requested > 0:
        return min(requested, 50)  # cap at 50 per generation
    # Auto: ~1 question per 10 chunks, min 5, max 50
    return min(50, max(5, total_chunks // 10))


class QuizService:
    """
    Servis za generisanje i upravljanje kvizovima.
    Podržava Ollama, OpenAI, Claude sa fallback lancem.
    """

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
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja koristeći AI.
        Args:
            text: Tekst za analizu
            num_questions: Željeni broj pitanja
            provider: Specifičan provajder (None=auto)
            user_*_key: User-ov API ključ (override globalnog)
        Returns:
            (success, questions_list, used_provider_or_error)
        """
        clients = _build_clients(
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
        )

        def get_client(p: str):
            return clients.get(p)

        # Ako je specifičan provajder zahtjevan, pokušaj samo njega
        if provider and provider in clients:
            client = get_client(provider)
            if not client or not client.is_available():
                logger.warning(f"Provajder '{provider}' nije dostupan, koristim fallback lanac")
            else:
                ok, raw, err = client.generate(text, num_questions)
                if ok:
                    questions = _parse_questions(raw)
                    if questions:
                        logger.info(f"[{provider}] Generisano {len(questions)} pitanja")
                        return True, questions, provider
                logger.warning(f"[{provider}] Greška: {err}, prelazim na fallback")

        # Fallback lanac
        order = [p for p in _PROVIDER_ORDER if p != provider]
        if provider:
            order = [provider] + order

        for p in order:
            client = get_client(p)
            if not client or not client.is_available():
                continue
            ok, raw, err = client.generate(text, num_questions)
            if ok:
                questions = _parse_questions(raw)
                if questions:
                    logger.info(f"[{p}] Generisano {len(questions)} pitanja")
                    return True, questions, p
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

        quiz = Quiz(
            document_id=document_id,
            user_id=user_id,
            title=f"Kviz: {document.title}",
            description=f"Automatski generisan kviz iz dokumenta '{document.title}'",
            time_limit=time_limit,
            passing_score=passing_score,
            status="generating",
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
            quiz.status = "error"
            db.commit()
            return False, ""

        # Auto-determine num_questions based on document size if not specified
        effective_num_questions = _auto_num_questions(len(all_chunks), num_questions)
        logger.info(f"Document has {len(all_chunks)} chunks → generating {effective_num_questions} questions")

        # Select evenly-distributed chunks (covers whole document, respects AI context limit)
        chunks = _select_chunks_for_quiz(all_chunks, max_chars=10000)
        logger.info(f"Selected {len(chunks)} of {len(all_chunks)} chunks for quiz context (evenly spread)")

        combined_text = "\n\n".join(
            c.translated_content or c.content for c in chunks
        )

        # Pokušaj da obogatiš kontekst sa RAG knowledge base
        try:
            from app.services.rag import similarity_search
            rag_chunks = similarity_search(db, f"quiz questions about: {quiz.title}", top_k=3)
            if rag_chunks:
                rag_context = "\n\n".join([c['content'] for c in rag_chunks[:3]])
                combined_text = combined_text + "\n\n=== DODATNI KONTEKST IZ BAZE ZNANJA ===\n\n" + rag_context
        except Exception:
            pass

        success, questions_data, used_provider = self.generate_questions_with_ai(
            text=combined_text,
            num_questions=effective_num_questions,
            provider=provider,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
        )

        if not success or not questions_data:
            quiz.status = "error"
            db.commit()
            return False, ""

        for q_data in questions_data:
            db.add(Question(
                quiz_id=quiz.id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation", ""),
                points=q_data.get("points", 1),
                order_index=q_data.get("order_index", 0),
            ))

        quiz.total_questions = len(questions_data)
        quiz.status = "ready"
        db.commit()
        logger.info(f"Kviz {quiz_id} spreman — {quiz.total_questions} pitanja [{used_provider}]")
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
        passed = percentage >= (quiz.passing_score if quiz else 60)

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


quiz_service = QuizService()
