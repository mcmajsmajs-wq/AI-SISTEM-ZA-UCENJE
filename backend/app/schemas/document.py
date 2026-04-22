# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - DOCUMENTS
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class DocumentBase(BaseModel):
    """Base document model."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation model."""

    file_id: str
    source_language: Optional[str] = "en"
    target_language: Optional[str] = "sr"


class DocumentFromTextCreate(BaseModel):
    """Create document directly from text (without file upload).

    The text will be chunked and stored in the database.
    """

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(
        ..., min_length=1, description="Text content to chunk and translate"
    )
    source_language: Optional[str] = "en"
    target_language: Optional[str] = "sr"
    description: Optional[str] = None
    translate_immediately: bool = Field(
        default=False,
        description="Whether to start translation immediately after chunking",
    )
    provider: Optional[str] = Field(
        default=None,
        description="Translation provider to use (auto-detected if not specified)",
    )


class DocumentFromTextResponse(BaseModel):
    """Response for document created from text."""

    document_id: str
    title: str
    total_chunks: int
    status: str
    task_id: Optional[str] = None
    message: str


class DocumentResponse(DocumentBase):
    """Document response model."""

    id: str
    file_id: str
    user_id: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: int = 0
    translated_chunks: int = 0
    status: str = Field(
        ..., description="pending|processing|translating|completed|error|partial"
    )
    source_language: str = "en"
    target_language: str = "sr"
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    """Chunk response model."""

    id: str
    document_id: str
    sequence_number: int
    content: str
    translated_content: Optional[str] = None
    token_count: Optional[int] = None
    heading_level: int = 0
    parent_heading: Optional[str] = None
    is_translated: bool = False
    is_reviewed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class ChunkUpdate(BaseModel):
    """Chunk update model for manual corrections."""

    content: Optional[str] = None
    translated_content: Optional[str] = None
    is_reviewed: Optional[bool] = None
