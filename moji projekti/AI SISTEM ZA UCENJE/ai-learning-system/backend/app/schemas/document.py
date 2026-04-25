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


class DocumentResponse(DocumentBase):
    """Document response model."""
    id: str
    file_id: str
    user_id: Optional[str] = None
    total_pages: Optional[int] = None
    total_chunks: int = 0
    status: str = Field(..., description="pending|processing|translating|completed|error")
    source_language: str = "en"
    target_language: str = "sr"
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChunkUpdate(BaseModel):
    """Chunk update model for manual corrections."""
    content: Optional[str] = None
    translated_content: Optional[str] = None
    is_reviewed: Optional[bool] = None

