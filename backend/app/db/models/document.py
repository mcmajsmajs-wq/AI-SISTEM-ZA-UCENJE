# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - DOCUMENT
================================================================================
Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Document(Base):
    """
    ================================================================================
    DOCUMENT MODEL
    ================================================================================
    Reprezentuje procesuirani dokument.
    ================================================================================
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)

    # Sadržaj
    title = Column(String(500), nullable=False)
    description = Column(Text)
    total_pages = Column(Integer)
    total_chunks = Column(Integer, default=0)

    # Status i jezik
    status = Column(
        Enum(
            "pending",
            "processing",
            "translating",
            "completed",
            "error",
            "partial",
            name="document_status",
        ),
        default="pending",
    )
    source_language = Column(String(10), default="en")
    target_language = Column(String(10), default="sr")

    # Metadata
    file_metadata = Column("metadata", JSON, default={})

    # PDF Export status
    pdf_export_id = Column(UUID(as_uuid=True), nullable=True)
    pdf_export_status = Column(
        Enum(
            "pending",
            "processing",
            "completed",
            "failed",
            name="pdf_export_status",
        ),
        nullable=True,
    )
    pdf_export_task_id = Column(String(255), nullable=True)
    pdf_export_path = Column(Text, nullable=True)  # Putanja do PDF fajla na disku

    # DOCX Export polja
    docx_export_id = Column(UUID(as_uuid=True), nullable=True)
    docx_export_status = Column(
        Enum(
            "pending",
            "processing",
            "completed",
            "failed",
            name="docx_export_status",
        ),
        nullable=True,
    )
    docx_export_path = Column(Text, nullable=True)  # Putanja do DOCX fajla u storage-u

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacije
    chunks = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )
    quiz_images = relationship(
        "QuizImage", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"


class Chunk(Base):
    """
    ================================================================================
    CHUNK MODEL
    ================================================================================
    Reprezentuje segment dokumenta (chunk).
    ================================================================================
    """

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Sadržaj
    sequence_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    translated_content = Column(Text)
    token_count = Column(Integer)

    # Struktura
    heading_level = Column(Integer, default=0)
    parent_heading = Column(String(500))

    # Status
    is_translated = Column(Integer, default=0)  # 0=False, 1=True
    is_reviewed = Column(Integer, default=0)
    used_for_quiz = Column(
        Integer, default=0
    )  # 0=False, 1=True - da li je chunk korišćen za kviz

    # Page number for image mapping
    page_number = Column(Integer, nullable=True)  # Broj stranice u PDF-u

    # Layout data za PDF rekonstrukciju (font, size, paragraph structure)
    layout_data = Column(
        JSON, nullable=True
    )  # {paragraphs: [{font, size, is_bold, alignment}], page_number: int}

    # Embeddings (ako koristite pgvector)
    # embedding = Column(Vector(1536))  # Zakomentarisano dok se ne doda pgvector

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacije
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk(id={self.id}, doc_id={self.document_id}, seq={self.sequence_number})>"
