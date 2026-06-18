# -*- coding: utf-8 -*-
"""
===============================================================================
SKILL SERVICE
===============================================================================
Glavni servis za upravljanje Skill sistemom.

SkillService:
- detect_and_get_template(): Detektuje tip i vraća template
- get_system_template(): Vraća sistemski template po imenu
- get_user_skills(): Vraća skill-ove korisnika
- create_skill(): Kreira novi skill
- update_skill(): Ažurira skill
- delete_skill(): Briše skill

Verzija: 1.0.0 (FAZA 6 - Skill Sistem)
===============================================================================
"""

import logging
from typing import List, Dict, Any, Optional

from app.services.skills import detector
from app.services.skills import templates as skill_templates

logger = logging.getLogger(__name__)


class SkillService:
    """
    ================================================================================
    SKILL SERVICE
    ================================================================================
    Glavni servis za upravljanje Skill sistemom.

    Obezbeđuje automatsku detekciju tipa dokumenta i primenu
    odgovarajućih prompt šablona.
    ================================================================================
    """

    def __init__(self):
        """
        Inicijalizuje SkillService.
        """
        self._detector = detector.SkillDetector()
        self._templates = skill_templates

    def detect_and_get_template(
        self, text: str, title: Optional[str] = None, chunks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Detektuje tip dokumenta i vraća odgovarajući template.

        Args:
            text: Tekst dokumenta
            title: Naslov dokumenta (opciono)
            chunks: Lista chunks-a (opciono)

        Returns:
            Dict sa:
                - template: Template podaci
                - category: Detektovana kategorija
                - confidence: Confidence score

        Primer:
            >>> service = SkillService()
            >>> result = service.detect_and_get_template(text)
            >>> print(result["category"])
            "legal"
        """
        if chunks:
            detection_result = self._detector.detect_from_chunks(chunks)
            category = detection_result["category"]
            confidence = detection_result["confidence"]
        elif text:
            detection_result = self._detector.analyze_text(text)
            category = detection_result["category"]
            confidence = detection_result["confidence"]
        elif title:
            detection_result = self._detector.detect_from_title(title)
            category = detection_result["category"]
            confidence = detection_result["confidence"]
        else:
            category = "general"
            confidence = 50

        template = self._templates.get_template_by_category(category)

        if not template:
            template = self._templates.get_template("general")

        return {"template": template, "category": category, "confidence": confidence}

    def get_system_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Vraća sistemski template po imenu.

        Args:
            template_name: Ime template-a

        Returns:
            Template dict ili None
        """
        return self._templates.get_template(template_name)

    def get_all_templates(self) -> Dict[str, Any]:
        """
        Vraća sve sistemske templates.

        Returns:
            Dict svih templates
        """
        return self._templates.get_all_templates()

    def get_template_names(self) -> List[str]:
        """
        Vraća listu imena svih templates.

        Returns:
            List imena
        """
        return self._templates.get_template_names()

    def get_categories(self) -> List[str]:
        """
        Vraća listu dostupnih kategorija.

        Returns:
            List kategorija
        """
        return self._templates.get_categories()

    def detect_category(self, text: str) -> str:
        """
        Detektuje kategoriju dokumenta.

        Args:
            text: Tekst dokumenta

        Returns:
            Kategorija
        """
        result = self._detector.analyze_text(text)
        return result["category"]

    def get_detection_details(self, text: str) -> Dict[str, Any]:
        """
        Vraća detaljne informacije o detekciji.

        Args:
            text: Tekst dokumenta

        Returns:
            Dict sa svim scores
        """
        return self._detector.analyze_text(text)

    def get_prompt_for_document(self, text: str, title: Optional[str] = None) -> str:
        """
        Vraća prompt template za dati dokument.

        Args:
            text: Tekst dokumenta
            title: Naslov dokumenta (opciono)

        Returns:
            Prompt template string
        """
        result = self.detect_and_get_template(text, title)
        return result["template"]["prompt_template"]

    def get_rules_for_document(self, text: str) -> Dict[str, Any]:
        """
        Vraća pravila za generisanje pitanja za dati dokument.

        Args:
            text: Tekst dokumenta

        Returns:
            Dict sa rules
        """
        result = self.detect_and_get_template(text)
        return result["template"].get("rules", {})


skill_service = SkillService()


def get_skill_service() -> SkillService:
    """
    Vraća globalnu SkillService instancu.

    Returns:
        SkillService
    """
    return skill_service


__all__ = [
    "SkillService",
    "skill_service",
    "get_skill_service",
]
