# -*- coding: utf-8 -*-
"""
===============================================================================
LEGAL DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

LEGAL_PROMPT_TEMPLATE = """You are a legal document analyzer specialized in processing contracts,
agreements, and legal texts.

When processing this PDF:
1. Identify numbered clauses (§1, §2, etc.) and articles
2. Extract key definitions and terminology
3. Note rights and obligations of parties
4. Identify deadlines, timelines, and important dates
5. Extract penalties and consequences

Quiz generation rules:
- Focus on key definitions and terms
- Create questions about rights and obligations
- Include questions about deadlines and timelines
- Multiple choice with 4 options (A, B, C, D)
- One correct answer
- Provide brief explanation for each answer
- Difficulty: medium to hard"""

LEGAL_RULES = {
    "difficulty": "medium",
    "question_types": ["multiple_choice", "true_false"],
    "num_questions": 10,
    "focus_areas": ["definitions", "obligations", "deadlines", "penalties"],
}

LEGAL_KEYWORDS = [
    "contract",
    "agreement",
    "clause",
    "section",
    "article",
    "party",
    "obligation",
    "liability",
    "damages",
    "termination",
    "governing law",
    "jurisdiction",
    "whereas",
    "hereby",
    "exhibit",
    "schedule",
]

__all__ = [
    "LEGAL_PROMPT_TEMPLATE",
    "LEGAL_RULES",
    "LEGAL_KEYWORDS",
]
