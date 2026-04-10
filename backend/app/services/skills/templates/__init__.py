# -*- coding: utf-8 -*-
"""
===============================================================================
SKILL TEMPLATES - Consolidated Exports
===============================================================================
Svi sistemski šabloni za različite tipove dokumenata.

Verzija: 1.0.0 (FAZA 6 - Skill Sistem)
===============================================================================
"""

from app.services.skills.templates.legal import (
    LEGAL_PROMPT_TEMPLATE,
    LEGAL_RULES,
    LEGAL_KEYWORDS,
)
from app.services.skills.templates.technical import (
    TECHNICAL_PROMPT_TEMPLATE,
    TECHNICAL_RULES,
    TECHNICAL_KEYWORDS,
)
from app.services.skills.templates.medical import (
    MEDICAL_PROMPT_TEMPLATE,
    MEDICAL_RULES,
    MEDICAL_KEYWORDS,
)
from app.services.skills.templates.academic import (
    ACADEMIC_PROMPT_TEMPLATE,
    ACADEMIC_RULES,
    ACADEMIC_KEYWORDS,
)
from app.services.skills.templates.textbook import (
    TEXTBOOK_PROMPT_TEMPLATE,
    TEXTBOOK_RULES,
    TEXTBOOK_KEYWORDS,
)
from app.services.skills.templates.general import (
    GENERAL_PROMPT_TEMPLATE,
    GENERAL_RULES,
    GENERAL_KEYWORDS,
)

SYSTEM_SKILL_TEMPLATES = {
    "legal_document": {
        "name": "Legal Document Processor",
        "description": "Analyzes legal documents with numbered clauses and definitions",
        "category": "legal",
        "prompt_template": LEGAL_PROMPT_TEMPLATE,
        "rules": LEGAL_RULES,
    },
    "technical_manual": {
        "name": "Technical Manual Processor",
        "description": "Processes technical documentation and user manuals",
        "category": "technical",
        "prompt_template": TECHNICAL_PROMPT_TEMPLATE,
        "rules": TECHNICAL_RULES,
    },
    "medical_document": {
        "name": "Medical Document Processor",
        "description": "Processes medical literature and health documents",
        "category": "medical",
        "prompt_template": MEDICAL_PROMPT_TEMPLATE,
        "rules": MEDICAL_RULES,
    },
    "academic_paper": {
        "name": "Academic Paper Processor",
        "description": "Processes research papers and academic documents",
        "category": "academic",
        "prompt_template": ACADEMIC_PROMPT_TEMPLATE,
        "rules": ACADEMIC_RULES,
    },
    "textbook": {
        "name": "Textbook Processor",
        "description": "Processes educational textbooks and learning materials",
        "category": "textbook",
        "prompt_template": TEXTBOOK_PROMPT_TEMPLATE,
        "rules": TEXTBOOK_RULES,
    },
    "general": {
        "name": "General Document Processor",
        "description": "Processes general documents and articles",
        "category": "general",
        "prompt_template": GENERAL_PROMPT_TEMPLATE,
        "rules": GENERAL_RULES,
    },
}

DOCUMENT_TYPE_KEYWORDS = {
    "legal": {"keywords": LEGAL_KEYWORDS, "category": "legal"},
    "technical": {"keywords": TECHNICAL_KEYWORDS, "category": "technical"},
    "medical": {"keywords": MEDICAL_KEYWORDS, "category": "medical"},
    "academic": {"keywords": ACADEMIC_KEYWORDS, "category": "academic"},
    "textbook": {"keywords": TEXTBOOK_KEYWORDS, "category": "textbook"},
    "general": {"keywords": GENERAL_KEYWORDS, "category": "general"},
}


def get_template(template_name: str) -> dict:
    """Vraća sistemski šablon po imenu."""
    return SYSTEM_SKILL_TEMPLATES.get(template_name)


def get_template_by_category(category: str) -> dict:
    """Vraća prvi sistemski šablon za datu kategoriju."""
    for template in SYSTEM_SKILL_TEMPLATES.values():
        if template.get("category") == category:
            return template
    return None


def get_all_templates() -> dict:
    """Vraća sve sistemske šablone."""
    return SYSTEM_SKILL_TEMPLATES.copy()


def get_template_names() -> list:
    """Vraća listu imena svih dostupnih šablona."""
    return list(SYSTEM_SKILL_TEMPLATES.keys())


def get_categories() -> list:
    """Vraća listu svih dostupnih kategorija."""
    categories = set()
    for template in SYSTEM_SKILL_TEMPLATES.values():
        categories.add(template.get("category", "general"))
    return sorted(list(categories))


__all__ = [
    "SYSTEM_SKILL_TEMPLATES",
    "DOCUMENT_TYPE_KEYWORDS",
    "get_template",
    "get_template_by_category",
    "get_all_templates",
    "get_template_names",
    "get_categories",
]
