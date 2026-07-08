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
from . import router

@router.get("/{document_id}/progress")
async def get_document_progress(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    GET DOCUMENT PROGRESS
    ================================================================================
    Vraća progres obrade dokumenta.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Progress information
    ================================================================================
    """
    logger.debug(f"Checking progress for document: {document_id}")

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

    total_chunks = document.total_chunks or 0
    translated_chunks = (
        db.query(Chunk)
        .filter(and_(Chunk.document_id == document.id, Chunk.is_translated == 1))
        .count()
        if total_chunks > 0
        else 0
    )

    reviewed_chunks = (
        db.query(Chunk)
        .filter(and_(Chunk.document_id == document.id, Chunk.is_reviewed == 1))
        .count()
        if total_chunks > 0
        else 0
    )

    # Read granular progress written by Celery task
    meta = document.file_metadata or {}
    proc_progress = meta.get("processing_progress", {})
    pages_done = proc_progress.get("pages_done", 0)
    pages_total = proc_progress.get("pages_total", document.total_pages or 0)
    chunks_so_far = proc_progress.get("chunks_so_far", 0)
    trans_progress = meta.get("translation_progress", {})
    # Phase-aware elapsed_seconds i last_activity_at
    if document.status == "translating":
        elapsed_seconds = trans_progress.get("elapsed_seconds", 0)
        last_activity_at = trans_progress.get("last_activity_at")
    elif document.status == "processing":
        elapsed_seconds = proc_progress.get("elapsed_seconds", 0)
        last_activity_at = proc_progress.get("last_activity_at")
    else:
        elapsed_seconds = proc_progress.get("elapsed_seconds", 0)
        last_activity_at = proc_progress.get("last_activity_at") or trans_progress.get(
            "last_activity_at"
        )

    progress_percentage = 0
    current_phase = "waiting"
    phase_label = "Čekanje na obradu"

    if document.status == "processing":
        current_phase = "extracting_text"
        if pages_total > 0 and pages_done > 0:
            phase_label = f"Ekstrakcija teksta — strana {pages_done}/{pages_total}"
            progress_percentage = int((pages_done / pages_total) * 85)  # 0-85%
        elif pages_total > 0:
            phase_label = "Pokretanje procesora PDF-a..."
            progress_percentage = 5
        else:
            phase_label = "Pokretanje procesora PDF-a..."
            progress_percentage = 5
    elif document.status == "translating":
        current_phase = "translating"
        if translated_chunks > 0:
            phase_label = f"Prevođenje — {translated_chunks}/{total_chunks} odlomaka"
        else:
            phase_label = "Pokretanje prevodioca..."
        # Use 0-100% range for translation (not 85-100%) so progress bar is meaningful
        progress_percentage = (
            int(translated_chunks / total_chunks * 100) if total_chunks > 0 else 0
        )
    elif document.status == "completed":
        current_phase = "completed"
        phase_label = "Obrada završena"
        progress_percentage = 100
    elif document.status == "error":
        current_phase = "error"
        phase_label = "Greška pri obradi"
        progress_percentage = 0
    elif document.status == "partial":
        current_phase = "partial"
        partial_info = document.file_metadata.get("partial_translation", False)
        if partial_info:
            phase_label = (
                f"Delimično prevedeno — {translated_chunks}/{total_chunks} odlomaka"
            )
            progress_percentage = (
                int(translated_chunks / total_chunks * 100) if total_chunks > 0 else 0
            )
        else:
            phase_label = "Prekid prevođenja"
            progress_percentage = 0

    return {
        "document_id": document_id,
        "status": document.status,
        "progress_percentage": progress_percentage,
        "current_phase": current_phase,
        "phase_label": phase_label,
        "total_chunks": total_chunks,
        "processed_chunks": total_chunks,
        "translated_chunks": translated_chunks,
        "reviewed_chunks": reviewed_chunks,
        "pages_done": pages_done,
        "pages_total": pages_total,
        "chunks_so_far": chunks_so_far,
        "elapsed_seconds": elapsed_seconds,
        "last_activity_at": last_activity_at,
        "message": f"Document is {document.status}",
    }


