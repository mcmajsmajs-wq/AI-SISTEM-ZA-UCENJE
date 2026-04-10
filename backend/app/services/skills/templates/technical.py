# -*- coding: utf-8 -*-
"""
===============================================================================
TECHNICAL DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

TECHNICAL_PROMPT_TEMPLATE = """You are a technical documentation expert specializing in user manuals,
API documentation, and technical specifications.

When processing this PDF:
1. Identify key concepts and terminology
2. Extract step-by-step procedures
3. Note configuration values and parameters
4. Identify error codes and troubleshooting steps
5. Extract best practices and recommendations

Quiz generation rules:
- Focus on procedures and workflows
- Create questions about configuration values
- Include questions about error handling
- Multiple choice with 4 options
- Include "NOT" questions to test deeper understanding
- Difficulty: medium"""

TECHNICAL_RULES = {
    "difficulty": "medium",
    "question_types": ["multiple_choice"],
    "num_questions": 8,
    "focus_areas": ["procedures", "configuration", "errors", "best_practices"],
}

TECHNICAL_KEYWORDS = [
    "installation",
    "configuration",
    "setup",
    "user manual",
    "api",
    "specification",
    "parameter",
    "error code",
    "troubleshooting",
    "requirements",
    "installation",
    "guide",
    "documentation",
    "reference",
]

__all__ = [
    "TECHNICAL_PROMPT_TEMPLATE",
    "TECHNICAL_RULES",
    "TECHNICAL_KEYWORDS",
]
