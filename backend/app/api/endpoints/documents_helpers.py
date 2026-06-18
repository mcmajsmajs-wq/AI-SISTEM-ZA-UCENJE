# -*- coding: utf-8 -*-
"""
================================================================================
DOCUMENTS HELPERS
================================================================================
Pomoćne funkcije za documents endpoint-e.

Verzija: 1.0.0 (2026-04-23)
================================================================================
"""

from sqlalchemy.orm import Session

from app.db.models.document import Document, Chunk
from app.schemas.document import DocumentResponse, ChunkResponse


def document_to_response(doc: Document, db: Session = None) -> DocumentResponse:
    """
    Konvertuje Document model u DocumentResponse schema.

    Args:
        doc: Document model
        db: Database session (optional, za prebrojavanje chunkova)

    Returns:
        DocumentResponse
    """
    translated_count = 0
    if db is not None:
        translated_count = (
            db.query(Chunk)
            .filter(Chunk.document_id == doc.id, Chunk.is_translated == 1)
            .count()
        )
    return DocumentResponse(
        id=str(doc.id),
        file_id=str(doc.file_id) if doc.file_id else None,
        user_id=str(doc.user_id),
        title=doc.title,
        description=doc.description,
        total_pages=doc.total_pages,
        total_chunks=doc.total_chunks,
        translated_chunks=translated_count,
        status=doc.status,
        source_language=doc.source_language,
        target_language=doc.target_language,
        metadata=doc.file_metadata or {},
        created_at=doc.created_at.isoformat() if doc.created_at else None,
        updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
    )


def chunk_to_response(chunk: Chunk) -> ChunkResponse:
    """
    Konvertuje Chunk model u ChunkResponse schema.

    Args:
        chunk: Chunk model

    Returns:
        ChunkResponse
    """
    return ChunkResponse(
        id=str(chunk.id),
        document_id=str(chunk.document_id),
        sequence_number=chunk.sequence_number,
        content=chunk.content,
        translated_content=chunk.translated_content,
        token_count=chunk.token_count,
        heading_level=chunk.heading_level,
        parent_heading=chunk.parent_heading,
        is_translated=bool(chunk.is_translated),
        is_reviewed=bool(chunk.is_reviewed),
        created_at=chunk.created_at.isoformat() if chunk.created_at else None,
        updated_at=chunk.updated_at.isoformat() if chunk.updated_at else None,
    )
