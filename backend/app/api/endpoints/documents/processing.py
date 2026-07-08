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
from app.workers.tasks import process_pdf_task
from . import router

@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    PROCESS DOCUMENT
    ================================================================================
    Pokreće obradu dokumenta (PDF parsing, chunking).

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Task ID za praćenje progresa
    ================================================================================
    """
    logger.info(f"Processing document: {document_id}")

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

    if document.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already being processed",
        )

    if not document.file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no associated file",
        )

    document.status = "pending"
    db.commit()

    task = process_pdf_task.delay(str(document.id), str(document.file_id))

    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "queued",
        "message": "Document processing queued",
    }


