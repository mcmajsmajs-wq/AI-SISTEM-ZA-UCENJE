from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(50), nullable=False)
    name = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    url = Column(Text)
    status = Column(String(20), default="pending")
    total_chunks = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_indexed = Column(DateTime(timezone=True))
    indexed_by = Column(String(50), default="manual")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section_index = Column(Integer)
    section_title = Column(String(500))
    heading_level = Column(Integer)
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_knowledge_chunks_source_id", "source_id"),
        Index("ix_knowledge_chunks_section", "source_id", "section_index"),
    )


class KnowledgeSectionSummary(Base):
    __tablename__ = "knowledge_section_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_index = Column(Integer, nullable=False)
    section_title = Column(String(500))
    heading_level = Column(Integer, default=1)
    content = Column(Text)
    summary = Column(Text)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_section_summaries_source", "source_id"),
        Index(
            "ix_section_summaries_section", "source_id", "section_index", unique=True
        ),
    )


class KnowledgeDocumentSummary(Base):
    __tablename__ = "knowledge_document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_title = Column(String(500))
    summary = Column(Text)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (Index("ix_document_summaries_source", "source_id", unique=True),)
