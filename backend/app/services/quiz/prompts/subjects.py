# -*- coding: utf-8 -*-
"""
================================================================================
SUBJECT-SPECIFIC PROMPTS MODULE
================================================================================

Specijalizovani promptovi za različite oblasti (matematika, fizika, hemija, etc.)

Verzija: 1.0.0
================================================================================
"""

from typing import Dict


SUBJECT_INSTRUCTIONS: Dict[str, str] = {
    "matematika": "",
    "fizika": "",
    "hemija": "",
    "biologija": "",
    "istorija": "",
    "geografija": "",
    "jezici": "",
    "pravo": "",
    "ekonomija": "",
    "informatika": "",
    "ostalo": "",
}


def get_specialized_prompt(subject_area: str, num_questions: int, text: str) -> str:
    """
    Vraća specijalizovani prompt za oblast.

    Args:
        subject_area: Oblast dokumenta
        num_questions: Broj pitanja
        text: Tekst dokumenta (truncate za prompt)

    Returns:
        str: Specijalizovani prompt
    """
    from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT

    subject = subject_area.lower()
    instructions = SUBJECT_INSTRUCTIONS.get(subject, SUBJECT_INSTRUCTIONS["ostalo"])

    base_prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])

    return base_prompt + instructions


def get_subject_instruction(subject_area: str) -> str:
    """
    Vraća dodatne instrukcije za oblast.

    Args:
        subject_area: Oblast dokumenta

    Returns:
        str: Dodatne instrukcije
    """
    return SUBJECT_INSTRUCTIONS.get(
        subject_area.lower(), SUBJECT_INSTRUCTIONS["ostalo"]
    )


def get_all_subjects() -> list:
    """
    Vraća listu svih podržanih oblasti.

    Returns:
        list: Lista oblasti
    """
    return list(SUBJECT_INSTRUCTIONS.keys())
