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
        Enum("pending", "processing", "translating", "completed", "error", name="document_status"),
        default="pending"
    )
    source_language = Column(String(10), default="en")
    target_language = Column(String(10), default="sr")
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacije
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
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
    
    # Embeddings (ako koristite pgvector)
    # embedding = Column(Vector(1536))  # Zakomentarisano dok se ne doda pgvector
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacije
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, doc_id={self.document_id}, seq={self.sequence_number})>"
