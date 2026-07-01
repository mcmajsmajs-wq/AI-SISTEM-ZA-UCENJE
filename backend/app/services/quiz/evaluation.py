# -*- coding: utf-8 -*-
"""
Answer evaluation logic for quiz questions.

Extracted from QuizService for cleaner separation of concerns.
"""

import json
import logging
import re

from app.utils.cyrillic import transliterate_text

logger = logging.getLogger(__name__)


def _transliterate_text(text: str) -> str:
    return transliterate_text(text)


def _check_text_input_answer_static(
    user_answer: str, correct_answer: str, extra_data: dict = None
) -> bool:
    if not user_answer or not correct_answer:
        return False

    user_answer = user_answer.strip()
    correct_answer = correct_answer.strip()

    case_insensitive = True
    exact_word = False
    fuzzy = False
    transliterate_opt = True

    if extra_data:
        case_insensitive = extra_data.get("case_insensitive", True)
        exact_word = extra_data.get("exact_word", False)
        fuzzy = extra_data.get("fuzzy", False)
        transliterate_opt = extra_data.get("transliterate", True)

    if transliterate_opt:
        user_answer = _transliterate_text(user_answer)
        correct_answer = _transliterate_text(correct_answer)

    if case_insensitive:
        user_answer = user_answer.lower()
        correct_answer = correct_answer.lower()

    if exact_word:
        return user_answer == correct_answer

    if fuzzy:
        user_words = set(user_answer.split())
        correct_words = set(correct_answer.split())
        matching = len(user_words & correct_words) / max(len(correct_words), 1)
        return matching >= 0.8

    return user_answer == correct_answer


def _check_fill_blank_answer_static(
    user_answer: str, correct_answer: str, extra_data: dict = None
) -> bool:
    if not user_answer or not correct_answer:
        return False

    user_answer = user_answer.strip()
    correct_answers = [
        a.strip() for a in re.split(r"[,|]", correct_answer) if a.strip()
    ]

    if not correct_answers:
        return False

    case_insensitive = True
    if extra_data:
        case_insensitive = extra_data.get("case_insensitive", True)

    user_answer = _transliterate_text(user_answer)
    if case_insensitive:
        user_answer = user_answer.lower()

    for correct in correct_answers:
        correct_processed = _transliterate_text(correct)
        if case_insensitive:
            correct_processed = correct_processed.lower()
        if user_answer == correct_processed:
            return True

    return False


def _check_answer_static(
    q_type: str, user_answer: str, correct_answer: str, extra_data: dict = None
) -> bool:
    user_answer = (user_answer or "").strip().lower()
    correct_answer = (correct_answer or "").strip().lower()

    if q_type in ("multiple_choice", "true_false", "calculation"):
        return user_answer == correct_answer

    elif q_type == "checkbox":
        correct_answer = correct_answer.strip("[]")
        correct_parts = set(
            p.strip().lower() for p in correct_answer.split(",") if p.strip()
        )
        user_parts = set(p.strip().lower() for p in user_answer.split(",") if p.strip())
        return correct_parts == user_parts

    elif q_type == "sequencing":
        correct_indices = [i.strip() for i in correct_answer.split(",")]
        user_indices = [i.strip() for i in user_answer.split(",")]
        return correct_indices == user_indices

    elif q_type == "categorization":
        try:
            correct_map = json.loads(correct_answer)
            user_map = json.loads(user_answer)
            return correct_map == user_map
        except Exception:
            return False

    elif q_type == "matching":
        try:
            correct_pairs = json.loads(correct_answer)
            user_pairs = json.loads(user_answer)
            return set(correct_pairs) == set(user_pairs)
        except Exception:
            return False

    elif q_type == "estimation":
        try:
            user_num = float(user_answer)
            correct_num = float(correct_answer)
            tolerance = float(extra_data.get("tolerance", 10)) if extra_data else 10
            return abs(user_num - correct_num) <= tolerance
        except Exception:
            return False

    elif q_type == "matrix":
        try:
            correct_answers = json.loads(correct_answer)
            user_answers = json.loads(user_answer)
            return correct_answers == user_answers
        except Exception:
            return False

    elif q_type == "matching":
        try:
            correct_pairs = json.loads(correct_answer)
            user_pairs = json.loads(user_answer)
            return set(correct_pairs) == set(user_pairs)
        except Exception:
            return False

    elif q_type == "odd_one_out":
        correct_items = [i.strip().lower() for i in correct_answer.split(",")]
        return user_answer.strip().lower() in correct_items

    elif q_type == "estimation":
        try:
            user_num = float(user_answer)
            correct_num = float(correct_answer)
            tolerance = float(extra_data.get("tolerance", 10)) if extra_data else 10
            return abs(user_num - correct_num) <= tolerance
        except Exception:
            return False

    elif q_type == "matrix":
        try:
            correct_answers = json.loads(correct_answer)
            user_answers = json.loads(user_answer)
            return correct_answers == user_answers
        except Exception:
            return False

    elif q_type == "hotspot":
        return user_answer == correct_answer

    elif q_type in ("text_input", "fill_blank"):
        return _check_text_input_answer_static(user_answer, correct_answer, extra_data)

    return False
