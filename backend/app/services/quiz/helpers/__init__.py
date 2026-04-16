# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ HELPERS - Parsing, Validation, Fallback
================================================================================

Verzija: 1.0.0
================================================================================
"""

import json
import logging
import random
import re
from typing import List, Any, Union

logger = logging.getLogger(__name__)


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """
    Unified attribute access for both dict and object types.

    Args:
        obj: Object or dict
        attr: Attribute name
        default: Default value if not found

    Returns:
        Value of the attribute or default
    """
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _get_content(chunk: Any) -> str:
    """Get content from chunk (supports dict with 'text' key or object with 'content' attr)."""
    return _get_attr(chunk, "content", "") or _get_attr(chunk, "text", "")


def _get_chunk_id(chunk: Any) -> Any:
    """Get id from chunk."""
    return _get_attr(chunk, "id")


def _is_used_for_quiz(chunk: Any) -> bool:
    """Check if chunk is used for quiz (supports 'used_for_quiz' or 'used_in_quiz')."""
    val = _get_attr(chunk, "used_for_quiz", False)
    if val is False:
        val = _get_attr(chunk, "used_in_quiz", False)
    return bool(val)


def _parse_questions(raw: str) -> List[dict]:
    """
    Parsira JSON array iz AI odgovora.

    Args:
        raw: Raw string odgovor od AI providera

    Returns:
        List[dict]: Lista parsiranih pitanja
    """
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
    """
    Validira i čisti pitanja koja dolaze od AI providera.

    Podržava sve tipove pitanja uključujući nove (2026-04-06):
    - multiple_choice, checkbox, true_false ( postojeći)
    - sequencing, categorization, matching, hotspot, odd_one_out, estimation, matrix (novi)

    Args:
        data: Lista pitanja od AI

    Returns:
        List[dict]: Lista validiranih pitanja
    """
    valid = []

    for i, q in enumerate(data):
        if not isinstance(q, dict):
            continue

        q_type = q.get("question_type", "")

        # Validacija za različite tipove pitanja
        if q_type in ("multiple_choice", "checkbox", "true_false"):
            # Postojeći tipovi - zahtevaju options i correct_answer
            if not all(
                k in q
                for k in ("question_text", "question_type", "options", "correct_answer")
            ):
                continue

            # Provera za single-letter opcije (AI možda nije pratio instrukcije)
            options = q.get("options", [])
            if isinstance(options, list) and options:
                single_char_options = [str(o).strip() for o in options]
                if all(len(o) == 1 and o.isalpha() for o in single_char_options):
                    logger.warning(
                        f"Pitanje {i} ima samo-slova opcije, preskačem: {options}"
                    )
                    continue

        elif q_type in (
            "sequencing",
            "categorization",
            "matching",
            "hotspot",
            "odd_one_out",
            "estimation",
            "matrix",
        ):
            # Novi tipovi - koriste extra_data umesto options
            if "question_text" not in q or "question_type" not in q:
                continue
            # Provera da postoji ili correct_answer ili extra_data
            if "correct_answer" not in q and "extra_data" not in q:
                logger.warning(
                    f"Pitanje {i} tipa {q_type} nema correct_answer ni extra_data, preskačem"
                )
                continue

        else:
            # Nepoznat tip - preskoči
            logger.warning(f"Pitanje {i} ima nepoznati tip: {q_type}, preskačem")
            continue

        # Postavljanje podrazumevanih vrednosti
        q.setdefault("explanation", "")
        q.setdefault("points", 1)

        # Specijalna validacija za checkbox
        if q.get("question_type") == "checkbox":
            correct = q.get("correct_answer", "")
            correct_parts = [p.strip() for p in correct.split(",") if p.strip()]
            if len(correct_parts) < 2:
                logger.warning(
                    f"Pitanje {i} je checkbox ali ima samo 1 tačan odgovor, skidam na multiple_choice"
                )
                q["question_type"] = "multiple_choice"
                q["correct_answer"] = correct_parts[0] if correct_parts else correct
            else:
                if q.get("points", 1) < 2:
                    q["points"] = 2

        q["order_index"] = i
        valid.append(q)

    return valid


def _fallback_questions(text: str, num_questions: int) -> List[dict]:
    """
    Generiše osnovna pitanja kada nijedan AI nije dostupan.

    Args:
        text: Tekst dokumenta
        num_questions: Broj pitanja za generisanje

    Returns:
        List[dict]: Lista fallback pitanja
    """
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 15]
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

        questions.append(
            {
                "question_text": question_text,
                "question_type": "true_false",
                "options": ["Тачно", "Нетачно"],
                "correct_answer": correct,
                "explanation": explanation,
                "points": 1,
                "order_index": i,
            }
        )

    return questions


LOW_QUALITY_PATTERNS = [
    "this page intentionally",
    "left blank",
    "copyright",
    "all rights reserved",
    "this material is copyright",
    "no part of this publication",
    "notice to reader",
    "notice to readers",
    "preface",
    "acknowledg",
    "table of contents",
    "index",
    "figure",
    "second edition",
    "third edition",
    "first edition",
    "fourth edition",
    "updated edition",
    "revised edition",
    "edition notice",
    "about the author",
    "author biography",
    "back cover",
    "front cover",
    "cover page",
    "title page",
    "dedication",
    "epigraph",
    "страница намерно",
    "празна страница",
    "сва права задржана",
    "copyright ©",
    "напомене",
    "биљешке",
    "садржај",
    "казало",
    "предговор",
    "захвалнице",
    "кључне речи",
    "abstract",
    "sažetak",
]


def is_chunk_quality(chunk_text: str) -> bool:
    """
    Proverava da li je chunk kvalitetan za quiz.

    Args:
        chunk_text: Tekst chunk-a

    Returns:
        bool: True ako je chunk kvalitetan
    """
    text_lower = chunk_text.lower()

    for pattern in LOW_QUALITY_PATTERNS:
        if pattern in text_lower:
            return False

    if len(chunk_text.strip()) < 50:
        return False

    return True


def select_chunks_for_quiz(chunks: list, max_chars: int = 10000) -> list:
    """
    Bira ravnomerno raspoređene chunk-ove iz dokumenta.

    Args:
        chunks: Lista Chunk SQLAlchemy objekata (NE dictionary!)
        max_chars: Maksimalan broj karaktera

    Returns:
        List: Lista odabranih chunk-ova (Chunk objekata)
    """
    if not chunks:
        return []

    quality_chunks = [c for c in chunks if is_chunk_quality(_get_content(c))]
    if not quality_chunks:
        quality_chunks = chunks

    total_chars = sum(len(_get_content(c)) for c in quality_chunks)
    if total_chars <= max_chars:
        return quality_chunks

    result = []
    current_chars = 0

    num_chunks = len(quality_chunks)
    step = max(1, num_chunks // 10)

    indices = list(range(0, num_chunks, step))

    for idx in indices:
        chunk = quality_chunks[idx]
        text = _get_content(chunk) or ""
        if current_chars + len(text) > max_chars:
            remaining = max_chars - current_chars
            if remaining > 200:
                if isinstance(chunk, dict):
                    chunk["text"] = text[:remaining]
                else:
                    chunk.content = text[:remaining]
            break
        result.append(chunk)
        current_chars += len(text)

    return result


def get_images_for_chunks(chunks: list, quiz_images: list) -> dict:
    """
    Mapira slike na chunk-ove.

    Args:
        chunks: Lista Chunk SQLAlchemy objekata
        quiz_images: Lista slika za quiz (dictionaries sa chunk_id)

    Returns:
        dict: Mapping slika na chunk-ove
    """
    chunk_images = {}

    for chunk in chunks:
        chunk_id = _get_chunk_id(chunk)
        if not chunk_id:
            continue

        matching = [img for img in quiz_images if img.get("chunk_id") == chunk_id]

        if matching:
            chunk_images[chunk_id] = matching

    return chunk_images


def get_quiz_usage_stats(chunks: list) -> dict:
    """
    Vraća statistiku korišćenja chunk-ova za quiz.

    Args:
        chunks: Lista Chunk SQLAlchemy objekata

    Returns:
        dict: Statistika
    """
    total = len(chunks)
    used = sum(1 for c in chunks if _is_used_for_quiz(c))
    unused = total - used

    return {
        "total": total,
        "used_in_quiz": used,
        "unused": unused,
        "usage_percentage": round((used / total * 100) if total > 0 else 0, 1),
    }


def mark_chunks_as_used(chunk_ids: list, db):
    """
    Označava chunk-ove kao korišćene u quiz-u.

    Args:
        chunk_ids: Lista ID-jeva chunk-ova
        db: Database session
    """
    from app.db.models.document import Chunk

    if not chunk_ids:
        return

    db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).update(
        {"used_for_quiz": 1},  # 1 = True, 0 = False
        synchronize_session=False,
    )
    db.commit()


# Re-export new modules for backward compatibility
from app.services.quiz.helpers.subject_detection import (
    detect_subject_area,
    get_subject_keywords,
    get_all_subjects as subject_detection_get_all_subjects,
    SUBJECT_KEYWORDS,
)

from app.services.quiz.helpers.document_structure import (
    detect_document_structure,
    get_structure_based_prompt,
    get_structure_keywords,
    get_all_structures as document_structure_get_all_structures,
    STRUCTURE_PATTERNS,
)

from app.services.quiz.helpers.progress import (
    update_quiz_progress,
    get_quiz_progress,
    delete_quiz_progress,
    set_quiz_cache,
    get_quiz_cache,
    clear_quiz_cache,
)

__all__ = [
    # Existing
    "_parse_questions",
    "_validate_questions",
    "_fallback_questions",
    "is_chunk_quality",
    "select_chunks_for_quiz",
    "get_images_for_chunks",
    "get_quiz_usage_stats",
    "mark_chunks_as_used",
    # Backward compatibility aliases
    "parse_quiz_response",  # Alias for _parse_questions
    # New - subject detection
    "detect_subject_area",
    "get_subject_keywords",
    "SUBJECT_KEYWORDS",
    # New - document structure
    "detect_document_structure",
    "get_structure_based_prompt",
    "get_structure_keywords",
    "STRUCTURE_PATTERNS",
    # New - progress
    "update_quiz_progress",
    "get_quiz_progress",
    "delete_quiz_progress",
    "set_quiz_cache",
    "get_quiz_cache",
    "clear_quiz_cache",
]

# Backward compatibility - add aliases
parse_quiz_response = _parse_questions
