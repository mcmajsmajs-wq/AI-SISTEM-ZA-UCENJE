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
from . import router

@router.get("/{document_id}/export/pdf")
async def export_document_pdf(
    document_id: str,
    include_original: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pokreće asinhrono generisanje PDF-a i vraća task_id za praćenje statusa.
    """
    from app.workers.tasks import export_pdf_task

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    # Provera da li već postoji gotov PDF
    if document.pdf_export_id and document.pdf_export_status == "completed":
        return {
            "status": "completed",
            "task_id": None,
            "file_id": document.pdf_export_id,
            "message": "PDF je već generisan. Koristite /api/v1/files/{file_id} za preuzimanje.",
        }

    # Provera da li je task u toku
    if document.pdf_export_status == "processing":
        return {
            "status": "processing",
            "task_id": document.pdf_export_task_id,
            "message": "PDF se već generiše...",
        }

    # Pokretanje Celery task-a
    task = export_pdf_task.delay(
        document_id=document_id,
        user_id=str(current_user.id),
        include_original=include_original,
    )

    # Čuvanje task_id-a u dokumentu
    document.pdf_export_task_id = task.id
    document.pdf_export_status = "processing"
    db.commit()

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "PDF export je pokrenut. Poll-ujte /api/v1/documents/{document_id}/export/pdf/status/{task_id}",
    }


@router.get("/{document_id}/export/pdf/status/{task_id}")
async def check_pdf_export_status(
    document_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Proverava status PDF export task-a.
    """
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    task = AsyncResult(task_id, app=celery_app)

    if task.state == "PENDING":
        return {
            "status": "processing",
            "task_id": task_id,
            "info": "Task čeka na izvršavanje...",
        }
    elif task.state == "PROGRESS":
        return {"status": "processing", "task_id": task_id, "info": task.info}
    elif task.state == "SUCCESS":
        result = task.result
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "file_id": result.get("file_id"),
            "filename": result.get("filename"),
        }
    elif task.state == "FAILURE":
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(task.info) if task.info else "Nepoznata greška",
        }
    else:
        return {"status": task.state.lower(), "task_id": task_id}


@router.get("/{document_id}/export/docx")
async def export_document_docx_legacy(
    document_id: str,
    include_original: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generiše i preuzima Word dokument od prevedenih chunkova.
    OVO JE LEGACY ENDPOINT - koristi /export-docx za async verziju
    """
    from fastapi.responses import Response
    from app.services.docx_export_service import docx_export_service

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id,
            Chunk.translated_content.isnot(None),
        )
        .order_by(Chunk.sequence_number)
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Dokument nema prevedenih segmenata. Pokrenite prevod pre eksporta.",
        )

    # Sada UKLJUČUJEMO heading_level!
    chunk_dicts = [
        {
            "original_text": c.content,
            "translated_text": c.translated_content,
            "heading_level": c.heading_level or 0,
            "parent_heading": c.parent_heading,
        }
        for c in chunks
    ]

    docx_bytes = docx_export_service.generate(
        title=document.title,
        chunks=chunk_dicts,
        include_original=include_original,
    )

    safe_title = "".join(
        c if c.isalnum() or c in "-_ " else "_" for c in document.title
    )[:60]
    filename = f"{safe_title}_prevod.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{document_id}/export/xlsx")
async def export_document_xlsx(
    document_id: str,
    include_original: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generiše i preuzima Excel dokument od prevedenih chunkova.
    """
    from fastapi.responses import Response
    from app.services.xlsx_export_service import xlsx_export_service

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id,
            Chunk.translated_content.isnot(None),
        )
        .order_by(Chunk.sequence_number)
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Dokument nema prevedenih segmenata. Pokrenite prevod pre eksporta.",
        )

    chunk_dicts = [
        {"original_text": c.content, "translated_text": c.translated_content}
        for c in chunks
    ]

    xlsx_bytes = xlsx_export_service.generate(
        title=document.title,
        chunks=chunk_dicts,
        include_original=include_original,
    )

    safe_title = "".join(
        c if c.isalnum() or c in "-_ " else "_" for c in document.title
    )[:60]
    filename = f"{safe_title}_prevod.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{document_id}/export/pptx")
async def export_document_pptx(
    document_id: str,
    include_original: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generiše i preuzima PowerPoint prezentaciju od prevedenih chunkova.
    """
    from fastapi.responses import Response
    from app.services.pptx_export_service import pptx_export_service

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document_id,
            Chunk.translated_content.isnot(None),
        )
        .order_by(Chunk.sequence_number)
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="Dokument nema prevedenih segmenata. Pokrenite prevod pre eksporta.",
        )

    chunk_dicts = [
        {"original_text": c.content, "translated_text": c.translated_content}
        for c in chunks
    ]

    pptx_bytes = pptx_export_service.generate(
        title=document.title,
        chunks=chunk_dicts,
        include_original=include_original,
    )

    safe_title = "".join(
        c if c.isalnum() or c in "-_ " else "_" for c in document.title
    )[:60]
    filename = f"{safe_title}_prevod.pptx"

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


