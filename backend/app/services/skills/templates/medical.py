# -*- coding: utf-8 -*-
"""
===============================================================================
MEDICAL DOCUMENT TEMPLATE
===============================================================================

Verzija: 1.0.0
===============================================================================
"""

MEDICAL_PROMPT_TEMPLATE = """You are a medical documentation expert specializing in healthcare
literature, clinical studies, and medical guides.

When processing this PDF:
1. Identify medical terminology and definitions
2. Extract symptoms and diagnosis information
3. Note treatment protocols and medications
4. Identify contraindications and side effects
5. Extract preventive measures

Quiz generation rules:
- Focus on accurate medical terminology
- Create questions about symptoms and treatments
- Include questions about drug interactions
- Multiple choice with 4 options
- Difficulty: hard (requires precise answers)"""

MEDICAL_RULES = {
    "difficulty": "hard",
    "question_types": ["multiple_choice", "true_false"],
    "num_questions": 12,
    "focus_areas": ["terminology", "symptoms", "treatments", "contraindications"],
}

MEDICAL_KEYWORDS = [
    "diagnosis",
    "treatment",
    "symptom",
    "medication",
    "contraindication",
    "patient",
    "clinical",
    "therapy",
    "prognosis",
    "etiology",
    "pathophysiology",
    "disease",
    "disorder",
    "syndrome",
    "condition",
]

__all__ = [
    "MEDICAL_PROMPT_TEMPLATE",
    "MEDICAL_RULES",
    "MEDICAL_KEYWORDS",
]
