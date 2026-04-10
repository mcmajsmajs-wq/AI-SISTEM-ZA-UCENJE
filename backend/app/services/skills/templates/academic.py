# -*- coding: utf-8 -*-
"""
===============================================================================
ACADEMIC DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

ACADEMIC_PROMPT_TEMPLATE = """You are an academic research expert specializing in scholarly papers
and research publications.

When processing this PDF:
1. Identify research methodology
2. Extract key findings and conclusions
3. Note statistical methods and sample sizes
4. Identify research gaps and future directions
5. Extract relevant citations

Quiz generation rules:
- Focus on methodology and findings
- Create questions about statistical methods
- Include questions about sample sizes and conclusions
- Multiple choice with 4 options
- Difficulty: hard"""

ACADEMIC_RULES = {
    "difficulty": "hard",
    "question_types": ["multiple_choice"],
    "num_questions": 10,
    "focus_areas": ["methodology", "findings", "statistics", "conclusions"],
}

ACADEMIC_KEYWORDS = [
    "abstract",
    "methodology",
    "results",
    "discussion",
    "conclusion",
    "references",
    "sample size",
    "statistical",
    "hypothesis",
    "research",
    "study",
    "analysis",
    "data",
    "findings",
    "literature",
]

__all__ = [
    "ACADEMIC_PROMPT_TEMPLATE",
    "ACADEMIC_RULES",
    "ACADEMIC_KEYWORDS",
]
