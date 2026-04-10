# -*- coding: utf-8 -*-
"""
===============================================================================
SKILLS PACKAGE - FAZA 6 Skill Sistem
===============================================================================
Modularni Skill sistem za automatsku detekciju tipa dokumenata.

Struktura:
├── __init__.py         # Glavni export (settings included)
├── models.py           # Skill, SkillTemplate, DocumentType, UserSkill
├── detector.py         # SkillDetector (auto-detekcija)
├── service.py         # SkillService (glavni servis)
└── templates/
    └── __init__.py    # Sistemski šabloni

Verzija: 1.0.0 (FAZA 6 - Skill Sistem)
===============================================================================
"""

from app.services.skills.models import (
    Skill,
    SkillTemplate,
    DocumentType,
    UserSkill,
    SkillCategory,
)

from app.services.skills.templates import (
    SYSTEM_SKILL_TEMPLATES,
    DOCUMENT_TYPE_KEYWORDS,
)

from app.services.skills.detector import (
    SkillDetector,
    detect_document_type,
    detect_from_file,
)

from app.services.skills.pdf_detector import (
    PDFSkillDetector,
    detect_subject_from_text,
    detect_subject_from_chunks,
    get_prompt_for_subject,
    get_rules_for_subject,
    detect_and_prepare_quiz,
    SUBJECT_AREAS,
)

from app.services.skills.service import (
    SkillService,
    skill_service,
    get_skill_service,
)

from app.services.skills.templates import (
    get_template,
    get_template_by_category,
    get_all_templates,
    get_template_names,
    get_categories,
)

__all__ = [
    "Skill",
    "SkillTemplate",
    "DocumentType",
    "UserSkill",
    "SkillCategory",
    "SYSTEM_SKILL_TEMPLATES",
    "DOCUMENT_TYPE_KEYWORDS",
    "SkillDetector",
    "detect_document_type",
    "detect_from_file",
    "PDFSkillDetector",
    "detect_subject_from_text",
    "detect_subject_from_chunks",
    "get_prompt_for_subject",
    "get_rules_for_subject",
    "detect_and_prepare_quiz",
    "SUBJECT_AREAS",
    "SkillService",
    "skill_service",
    "get_skill_service",
    "get_template",
    "get_template_by_category",
    "get_all_templates",
    "get_template_names",
    "get_categories",
    "get_skill_templates",  # Alias for backward compatibility
]

# Alias for backward compatibility
get_skill_templates = get_all_templates
