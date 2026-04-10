# -*- coding: utf-8 -*-
"""
===============================================================================
GENERAL DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

GENERAL_PROMPT_TEMPLATE = """You are a general document analysis expert.

When processing this PDF:
1. Identify main topics and themes
2. Extract key information
3. Note important dates and facts
4. Identify conclusions

Quiz generation rules:
- Focus on main topics
- Create questions about key facts
- Multiple choice with 4 options
- Difficulty: easy to medium"""

GENERAL_RULES = {
    "difficulty": "medium",
    "question_types": ["multiple_choice"],
    "num_questions": 8,
    "focus_areas": ["topics", "facts", "dates", "conclusions"],
}

GENERAL_KEYWORDS = [
    "introduction",
    "overview",
    "summary",
    "conclusion",
    "background",
    "overview",
    "about",
    "description",
    "information",
    "details",
]

__all__ = [
    "GENERAL_PROMPT_TEMPLATE",
    "GENERAL_RULES",
    "GENERAL_KEYWORDS",
]
