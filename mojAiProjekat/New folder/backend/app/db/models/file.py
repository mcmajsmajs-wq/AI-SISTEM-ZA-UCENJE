# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - FILE
================================================================================
Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import Column, String, BigInteger, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class File(Base):
    """
    ================================================================================
    FILE MODEL
    ================================================================================
    Reprezentuje upload-ovani fajl.
    ================================================================================
    """
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Fajl informacije
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA256
    
    # Status
    status = Column(
        Enum("uploaded", "processing", "completed", "error", "deleted", name="file_status"),
        default="uploaded"
    )
    
    # Dodatni podaci
    file_metadata = Column("metadata", JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<File(id={self.id}, filename={self.original_filename}, status={self.status})>"
