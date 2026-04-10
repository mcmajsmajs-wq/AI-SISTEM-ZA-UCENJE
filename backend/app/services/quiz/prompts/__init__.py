# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ PROMPTS - Prompt templates for quiz generation
================================================================================
"""

from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import (
    get_specialized_prompt,
    get_subject_instruction,
    get_all_subjects,
    SUBJECT_INSTRUCTIONS,
)

__all__ = [
    "QUIZ_PROMPT",
    "get_specialized_prompt",
    "get_subject_instruction",
    "get_all_subjects",
    "SUBJECT_INSTRUCTIONS",
]
