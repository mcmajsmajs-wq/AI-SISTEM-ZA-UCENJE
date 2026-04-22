# -*- coding: utf-8 -*-
"""
================================================================================
FILE SKILLS SERVICE
================================================================================
Servis za dohvatanje file skill prompts (translate, pdf, docx, xlsx).

Ovo su Anthropic-style skill sabloni koji se koriste kad korisnik
klikne dugme "Prevedi" ili "Exportuj u PDF/Word".

Verzija: 1.0.0 (FAZA 13 - File Skills)
================================================================================
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.skills.models import FileSkill, FileSkillCategory

logger = logging.getLogger(__name__)


class FileSkillService:
    """
    ================================================================================
    FILE SKILL SERVICE
    ================================================================================
    Servis za rad sa file skillovima.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_skill(self, category: str) -> Optional[FileSkill]:
        """
        Dohvata skill po kategoriji.

        Args:
            category: Kategorija skill-a (translate, pdf, docx, xlsx)

        Returns:
            FileSkill ili None ako ne postoji
        """
        return (
            self.db.query(FileSkill)
            .filter(FileSkill.category == category, FileSkill.is_active == True)
            .first()
        )

    def get_skill_prompt(self, category: str) -> Optional[str]:
        """
        Dohvata prompt template za skill.

        Args:
            category: Kategorija skill-a

        Returns:
            Prompt string ili None
        """
        skill = self.get_skill(category)
        return skill.prompt_template if skill else None

    def get_all_skills(self) -> List[FileSkill]:
        """
        Dohvata sve aktivne skill-ove.

        Returns:
            Lista FileSkill objekata
        """
        return self.db.query(FileSkill).filter(FileSkill.is_active == True).all()

    def get_translate_prompt(self) -> str:
        """Dohvata translate skill prompt."""
        return self.get_skill_prompt(FileSkillCategory.TRANSLATE) or ""

    def get_pdf_prompt(self) -> str:
        """Dohvata PDF export skill prompt."""
        return self.get_skill_prompt(FileSkillCategory.PDF) or ""

    def get_docx_prompt(self) -> str:
        """Dohvata DOCX export skill prompt."""
        return self.get_skill_prompt(FileSkillCategory.DOCX) or ""


def get_file_skill_service(db: Session = None) -> FileSkillService:
    """Factory funkcija za FileSkillService."""
    if db is None:
        db = next(get_db())
    return FileSkillService(db)


file_skill_service: Optional[FileSkillService] = None


def get_file_skill() -> FileSkillService:
    """Get global FileSkillService instance."""
    global file_skill_service
    if file_skill_service is None:
        file_skill_service = get_file_skill_service()
    return file_skill_service
