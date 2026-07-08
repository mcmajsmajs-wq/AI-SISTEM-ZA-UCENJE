# -*- coding: utf-8 -*-
"""
Parsing, validation, and fallback question generation.
"""

import json
import logging
import random
import re
from typing import Any, List, Union

logger = logging.getLogger(__name__)


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _get_content(chunk: Any) -> str:
    translated = _get_attr(chunk, "translated_content", "")
    if translated:
        return translated
    return _get_attr(chunk, "content", "") or _get_attr(chunk, "text", "")


def _get_chunk_id(chunk: Any) -> Any:
    return _get_attr(chunk, "id")


def _is_used_for_quiz(chunk: Any) -> bool:
    val = _get_attr(chunk, "used_for_quiz", False)
    if val is False:
        val = _get_attr(chunk, "used_in_quiz", False)
    return bool(val)


def _parse_questions(raw: Union[str, list, dict]) -> List[dict]:
    if isinstance(raw, list):
        return _validate_questions(raw)
    if isinstance(raw, dict):
        for v in raw.values():
            if isinstance(v, list):
                return _validate_questions(v)
        logger.warning("Dict nema listu u vrednostima, vracam prazno")
        return []
    if not isinstance(raw, str):
        logger.warning(
            f"_parse_questions ocekuje string/list/dict, dobijen {type(raw).__name__}"
        )
        return []

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
    valid = []

    ALLOWED_DB_TYPES = {
        "multiple_choice", "checkbox", "true_false", "fill_blank",
        "calculation", "step_by_step", "chemical_equation",
        "sequencing", "categorization", "matching", "hotspot",
        "odd_one_out", "estimation", "matrix", "text_input",
    }
    TEXT_INPUT_MAP = {"text_input", "text", "short_answer", "long_answer", "essay"}

    for i, q in enumerate(data):
        if not isinstance(q, dict):
            continue

        q_type = q.get("question_type", "")

        if q_type in TEXT_INPUT_MAP and q_type != "fill_blank":
            q["question_type"] = "fill_blank"
            q_type = "fill_blank"

        if q_type in ("multiple_choice", "checkbox", "true_false"):
            if not all(
                k in q
                for k in ("question_text", "question_type", "options", "correct_answer")
            ):
                continue
            options = q.get("options", [])
            if isinstance(options, list) and options:
                single_char_options = [str(o).strip() for o in options]
                if all(len(o) == 1 and o.isalpha() for o in single_char_options):
                    logger.warning(
                        f"Pitanje {i} ima samo-slova opcije, preskačem: {options}"
                    )
                    continue

        elif q_type in ("text_input", "fill_blank"):
            if not all(
                k in q for k in ("question_text", "question_type", "correct_answer")
            ):
                logger.warning(
                    f"Pitanje {i} tipa {q_type} nema question_text ili correct_answer, preskačem"
                )
                continue

        elif q_type in (
            "sequencing", "categorization", "matching", "hotspot",
            "odd_one_out", "estimation", "matrix",
        ):
            if "question_text" not in q or "question_type" not in q:
                continue
            if "correct_answer" not in q and "extra_data" not in q:
                logger.warning(
                    f"Pitanje {i} tipa {q_type} nema correct_answer ni extra_data, preskačem"
                )
                continue

        elif q_type not in ALLOWED_DB_TYPES:
            logger.warning(
                f"Pitanje {i} ima tip '{q_type}' koji ne postoji u DB enumu, preskacem"
            )
            continue

        q.setdefault("explanation", "")
        q.setdefault("points", 1)

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
