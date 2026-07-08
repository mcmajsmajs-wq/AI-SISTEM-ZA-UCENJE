import logging
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
from app.workers.tasks.pdf_export import export_pdf_task
from . import router

# ─── PDF EXPORT ENDPOINTS ────────────────────────────────────────────────

from app.workers.tasks.pdf_export import export_pdf_task  # noqa: E402


@router.post("/{document_id}/export-pdf", status_code=202)
def export_document_to_pdf(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pokrece async PDF export task za dokument."""
    from app.db.models.document import Document

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nije pronadjen")

    # Proveri da li ima chunks
    chunk_count = db.query(Chunk).filter(Chunk.document_id == document_id).count()
    if chunk_count == 0:
        raise HTTPException(status_code=400, detail="Dokument nema chunks za export")

    # Pokreni Celery task
    task = export_pdf_task.delay(document_id, current_user.id)

    # Azuriraj status u bazi
    doc.pdf_export_status = "processing"
    doc.pdf_export_task_id = task.id
    db.commit()

    return {
        "message": "PDF export task pokrenut",
        "task_id": task.id,
        "status": "processing",
        "chunks_count": chunk_count,
    }


@router.get("/pdf-status/{task_id}")
def get_pdf_export_status(
    task_id: str,
):
    """Proverava status PDF export task-a."""
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app

    task_result = AsyncResult(task_id, app=celery_app)

    result = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.failed():
        result["error"] = str(task_result.info)
    elif task_result.successful():
        result["result"] = task_result.result
    elif task_result.status == "PROGRESS":
        # PROGRESS state stores progress info in .info (meta dict)
        if task_result.info:
            result["result"] = task_result.info

    return result


@router.get("/{document_id}/pdf-download")
def download_pdf(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download generisanog PDF-a."""

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nije pronadjen")

    if doc.pdf_export_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"PDF nije spreman (status: {doc.pdf_export_status})",
        )

    # Koristi pdf_export_path iz baze za download
    storage_path = doc.pdf_export_path
    if not storage_path:
        raise HTTPException(status_code=404, detail="PDF putanja nije definisana")

    # Download iz MinIO storage-a
    from app.services.storage import storage_service

    try:
        pdf_content = storage_service.download_file(storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="PDF fajl nije pronadjen u storage-u"
        )

    from fastapi.responses import Response

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.title or "document"}.pdf"'
        },
    )
