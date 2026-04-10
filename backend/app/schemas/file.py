# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - FILES
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class FileBase(BaseModel):
    """Base file model."""
    filename: str
    mime_type: str = "application/pdf"


class FileResponse(FileBase):
    """File response model."""
    id: str
    size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="uploaded|processing|completed|error")
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """File upload response model."""
    id: str
    filename: str
    size: int
    status: str
    message: str


class FileListResponse(BaseModel):
    """File list response model (paginated)."""
    items: List[FileResponse]
    total: int
    skip: int
    limit: int
