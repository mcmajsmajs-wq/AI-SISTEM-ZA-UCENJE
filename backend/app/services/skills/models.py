# -*- coding: utf-8 -*-
"""
===============================================================================
SKILLS MODELS - Database Models
===============================================================================
Database modeli za Skill sistem.

Models:
- Skill: Korisnički definisani skill (prompt template)
- SkillTemplate: Sistemski šabloni
- DocumentType: Tipovi dokumenata za auto-detekciju

Verzija: 1.0.0 (FAZA 6 - Skill Sistem)
===============================================================================
"""

from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SkillCategory(str, PyEnum):
    """Kategorije skill-ova."""

    LEGAL = "legal"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    ACADEMIC = "academic"
    TEXTBOOK = "textbook"
    GENERAL = "general"


class Skill(Base):
    """
    Skill - definicija prompt šablona za tip dokumenta.
    """

    __tablename__ = "skills"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    name = Column(String(100), nullable=False)
    description = Column(Text)

    category = Column(String(50), nullable=False)
    prompt_template = Column(Text, nullable=False)

    rules = Column(
        JSON,
        default=lambda: {
            "difficulty": "medium",
            "question_types": ["multiple_choice"],
            "num_questions": 10,
            "focus_areas": [],
        },
    )

    allowed_tools = Column(JSON, default=list)

    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="skills")

    def __repr__(self):
        return f"<Skill {self.name} ({self.category})>"


class SkillTemplate(Base):
    """
    SkillTemplate - sistemski šabloni.
    """

    __tablename__ = "skill_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)

    prompt_template = Column(Text, nullable=False)

    document_types = Column(JSON, default=list)

    category = Column(String(50), nullable=False)

    rules = Column(JSON, default=dict)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SkillTemplate {self.name}>"


class DocumentType(Base):
    """
    DocumentType - tipovi dokumenata za auto-detekciju.
    """

    __tablename__ = "document_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)

    keywords = Column(JSON, default=list)
    patterns = Column(JSON, default=list)

    category = Column(String(50), nullable=False)
    description = Column(Text)

    skill_id = Column(PGUUID(as_uuid=True), ForeignKey("skills.id"), nullable=True)

    confidence_threshold = Column(Integer, default=70)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<DocumentType {self.name}>"


class UserSkill(Base):
    """
    UserSkill - veza korisnika i skill-a.
    """

    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    skill_id = Column(
        PGUUID(as_uuid=True), ForeignKey("skills.id"), nullable=False, index=True
    )

    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    is_favorite = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FileSkillCategory(str, PyEnum):
    """Kategorije file skill-ova."""

    TRANSLATE = "translate"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"


class FileSkill(Base):
    """
    FileSkill - šabloni za obradu fajlova (translate, pdf, docx, xlsx).

    Ovo su Anthropic-style skills koji se primenjuju kad korisnik
    klikne dugme "Prevedi" ili "Exportuj u PDF/Word".
    """

    __tablename__ = "file_skills"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(20), nullable=False)

    description = Column(Text)
    prompt_template = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FileSkill {self.name} ({self.category})>"


__all__ = [
    "Skill",
    "SkillTemplate",
    "DocumentType",
    "UserSkill",
    "SkillCategory",
    "FileSkill",
    "FileSkillCategory",
]
