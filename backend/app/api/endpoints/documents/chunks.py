import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.db.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    ChunkResponse,
    DocumentFromTextCreate,
    DocumentFromTextResponse,
)
from app.services.auth import get_current_user
from app.core.config import settings
from .helpers import chunk_to_response
from . import router

@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    GET DOCUMENT CHUNKS
    ================================================================================
    Vraća chunk-ove dokumenta (za review i editovanje).

    Args:
        document_id: ID dokumenta
        skip: Offset
        limit: Limit
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.debug(f"Fetching chunks for document: {document_id}")

    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    document = (
        db.query(Document)
        .filter(and_(Document.id == doc_uuid, Document.user_id == current_user.id))
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    query = db.query(Chunk).filter(Chunk.document_id == document.id)
    total = query.count()

    chunks = (
        query.order_by(Chunk.sequence_number)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "items": [chunk_to_response(chunk) for chunk in chunks],
        "total": total,
    }


@router.put("/{document_id}/chunks/{chunk_id}")
async def update_chunk(
    document_id: str,
    chunk_id: str,
    content: str = None,
    translated_content: str = None,
    is_reviewed: bool = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    UPDATE CHUNK
    ================================================================================
    Ažurira sadržaj chunk-a (ručna korekcija prevoda).

    Args:
        document_id: ID dokumenta
        chunk_id: ID chunk-a
        content: Novi sadržaj (opcionalno)
        translated_content: Novi prevedeni sadržaj (opcionalno)
        is_reviewed: Da li je pregledan (opcionalno)
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.info(f"Updating chunk {chunk_id} in document {document_id}")

    try:
        doc_uuid = uuid.UUID(document_id)
        chunk_uuid = uuid.UUID(chunk_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format"
        )

    document = (
        db.query(Document)
        .filter(and_(Document.id == doc_uuid, Document.user_id == current_user.id))
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    chunk = (
        db.query(Chunk)
        .filter(and_(Chunk.id == chunk_uuid, Chunk.document_id == document.id))
        .first()
    )

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found"
        )

    if content is not None:
        chunk.content = content

    if translated_content is not None:
        chunk.translated_content = translated_content
        chunk.is_translated = 1

    if is_reviewed is not None:
        chunk.is_reviewed = 1 if is_reviewed else 0

    db.commit()
    db.refresh(chunk)

    return {
        "chunk_id": chunk_id,
        "status": "updated",
        "message": "Chunk updated successfully",
    }


