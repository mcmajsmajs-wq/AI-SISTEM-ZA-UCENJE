# -*- coding: utf-8 -*-
"""
===============================================================================
TEXTBOOK DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

TEXTBOOK_PROMPT_TEMPLATE = """You are an educational content expert specializing in textbooks
and learning materials.

When processing this PDF:
1. Identify key concepts and definitions
2. Extract learning objectives
3. Note important formulas and equations
4. Identify examples and exercises
5. Extract chapter summaries

Quiz generation rules:
- Create questions about key concepts
- Include questions about formulas and equations
- Focus on learning objectives
- Multiple choice with 4 options
- Provide clear explanations
- Difficulty: varies (easy to medium)"""

TEXTBOOK_RULES = {
    "difficulty": "medium",
    "question_types": ["multiple_choice", "fill_blank"],
    "num_questions": 10,
    "focus_areas": ["concepts", "formulas", "examples", "exercises"],
}

TEXTBOOK_KEYWORDS = [
    "chapter",
    "exercise",
    "learning objective",
    "example",
    "formula",
    "theorem",
    "definition",
    "summary",
    "review",
    "question",
    "problem",
    "solution",
    "explanation",
    "tutorial",
]

__all__ = [
    "TEXTBOOK_PROMPT_TEMPLATE",
    "TEXTBOOK_RULES",
    "TEXTBOOK_KEYWORDS",
]
