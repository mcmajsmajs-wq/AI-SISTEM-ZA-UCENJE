# -*- coding: utf-8 -*-
"""
Skills Tool Handlers - FAZA 7
Handlers za Skills MCP alate.
"""

from typing import Any, Dict


CATEGORY_KEYWORDS = {
    "legal": [
        "law",
        "agreement",
        "contract",
        "clause",
        "section",
        "obligation",
        "termination",
        "liability",
        "damages",
        "governing law",
        "jurisdiction",
        "party",
        "parties",
        "consent",
        "notice",
        "deadline",
        "breach",
    ],
    "technical": [
        "api",
        "installation",
        "configuration",
        "setup",
        "parameter",
        "error code",
        "troubleshooting",
        "documentation",
        "specification",
        "manual",
        "guide",
        "system",
        "component",
        "serial",
        "warranty",
    ],
    "medical": [
        "symptom",
        "diagnosis",
        "treatment",
        "medication",
        "therapy",
        "patient",
        "clinical",
        "condition",
        "drug",
        "dosage",
        "contraindication",
        "side effect",
        "prognosis",
        "diagnosis",
    ],
    "academic": [
        "research",
        "methodology",
        "results",
        "discussion",
        "conclusion",
        "reference",
        "citation",
        "abstract",
        "doi",
        "hypothesis",
        "sample",
        "statistical",
        "analysis",
        "findings",
    ],
    "textbook": [
        "chapter",
        "lesson",
        "example",
        "exercise",
        "solution",
        "textbook",
        "course",
        "review",
        "test",
        "grade",
        "assignment",
    ],
    "general": ["document", "information", "content", "summary", "overview"],
}

SKILL_TEMPLATES = {
    "legal": {
        "name": "Legal Document",
        "description": "Template for legal document processing",
        "quiz_generation": "You are a legal expert creating quiz questions from legal documentation. Focus on legal terminology, obligations, rights, and procedures.",
    },
    "technical": {
        "name": "Technical Manual",
        "description": "Template for technical documentation",
        "quiz_generation": "You are a technical writer creating quiz questions from technical manuals. Focus on specifications, procedures, troubleshooting, and configuration.",
    },
    "medical": {
        "name": "Medical Document",
        "description": "Template for medical documentation",
        "quiz_generation": "You are a medical professional creating quiz questions from medical documentation. Focus on symptoms, treatments, and clinical procedures. WARNING: Include disclaimer about medical accuracy.",
    },
    "academic": {
        "name": "Academic Paper",
        "description": "Template for academic papers",
        "quiz_generation": "You are an academic creating quiz questions from research papers. Focus on methodology, findings, and conclusions.",
    },
    "textbook": {
        "name": "Textbook",
        "description": "Template for educational content",
        "quiz_generation": "You are an educator creating quiz questions from textbook material. Focus on key concepts, examples, and problem-solving.",
    },
    "general": {
        "name": "General Document",
        "description": "Template for general documents",
        "quiz_generation": "You are an educational content creator generating quiz questions from general documentation.",
    },
}


def detect_category(text: str, threshold: int = 50) -> Dict[str, Any]:
    """Detektuje kategoriju dokumenta na osnovu teksta."""
    text_lower = text.lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score * 100 / max(len(keywords), 1)

    max_category = max(scores.items(), key=lambda x: x[1])
    confidence = max_category[1] if max_category[1] > 0 else 0

    if confidence < threshold:
        max_category = ("general", 50)
        confidence = 50

    matched_keywords = [
        kw for kw in CATEGORY_KEYWORDS[max_category[0]] if kw in text_lower
    ]

    return {
        "category": max_category[0],
        "confidence": round(confidence, 2),
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "matched_keywords": matched_keywords[:10],
        "threshold_used": threshold,
    }


async def handle_skill_detect(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handler za skill_detect tool."""
    text = params["text"]
    threshold = params.get("threshold", 50)

    result = detect_category(text, threshold)
    return {"status": "ok", **result}


async def handle_skill_list() -> Dict[str, Any]:
    """Handler za skill_list tool."""
    return {"status": "ok", "categories": list(CATEGORY_KEYWORDS.keys())}


async def handle_skill_get_template(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handler za skill_get_template tool."""
    category = params["category"]
    template_type = params.get("template_type", "quiz_generation")

    if category not in SKILL_TEMPLATES:
        return {
            "status": "error",
            "message": f"Category '{category}' not found. Available: {list(SKILL_TEMPLATES.keys())}",
        }

    template = SKILL_TEMPLATES[category]
    return {
        "status": "ok",
        "category": category,
        "name": template["name"],
        "description": template["description"],
        "template": template.get(template_type, template["quiz_generation"]),
    }


async def handle_skill_list_templates() -> Dict[str, Any]:
    """Handler za skill_list_templates tool."""
    templates = []
    for category, template in SKILL_TEMPLATES.items():
        templates.append(
            {
                "category": category,
                "name": template["name"],
                "description": template["description"],
                "available_types": list(template.keys()),
            }
        )
    return {"status": "ok", "templates": templates}


async def handle_skill_get_categories(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handler za skill_get_categories tool."""
    category = params.get("category")

    if category:
        if category not in CATEGORY_KEYWORDS:
            return {"status": "error", "message": f"Category '{category}' not found"}
        return {
            "status": "ok",
            "category": category,
            "keywords": CATEGORY_KEYWORDS[category],
        }

    return {
        "status": "ok",
        "categories": {cat: kws for cat, kws in CATEGORY_KEYWORDS.items()},
    }
