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

@router.post("/{document_id}/translate")
async def translate_document(
    document_id: str,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    TRANSLATE DOCUMENT
    ================================================================================
    Pokreće AI prevod dokumenta.

    Args:
        document_id: ID dokumenta
        provider: Provajder za prevod (ollama, deepl, openai, google, claude)
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Task ID za praćenje progresa
    ================================================================================
    """
    logger.info(
        f"Translation requested for document: {document_id}, provider: {provider}"
    )

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

    if document.status not in ["completed", "translating", "partial"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed before translation",
        )

    from app.workers.tasks import translate_document_task

    # Update status to translating before queueing
    document.status = "translating"
    db.commit()

    task = translate_document_task.delay(str(document.id), provider)

    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "queued",
        "provider": provider or "auto",
        "message": f"Translation queued using {provider or 'auto-selected'} provider",
    }


@router.get("/{document_id}/translation/progress")
async def get_translation_progress(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    GET TRANSLATION PROGRESS
    ================================================================================
    Vraća progress translacije u realnom vremenu.
    Ovo uključuje checkpoint informacije za resume.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Progress object sa translated/total chunk-ova i checkpoint
    ================================================================================
    """
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

    # Calculate progress
    total_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).count()

    translated_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id, Chunk.is_translated == 1)
        .count()
    )

    percent = (
        round((translated_chunks / total_chunks * 100), 1) if total_chunks > 0 else 0
    )

    # Get checkpoint data
    checkpoint = (
        document.file_metadata.get("translation_checkpoint", {})
        if document.file_metadata
        else {}
    )

    return {
        "document_id": document_id,
        "status": document.status,
        "translated_chunks": translated_chunks,
        "total_chunks": total_chunks,
        "percentage": percent,
        "can_resume": document.status == "partial" and translated_chunks < total_chunks,
        "checkpoint": {
            "last_chunk_index": checkpoint.get("last_chunk_index", 0),
            "last_translated_count": checkpoint.get(
                "last_translated_count", translated_chunks
            ),
            "last_updated": checkpoint.get("last_updated", None),
        }
        if checkpoint
        else None,
        "progress": document.file_metadata.get("translation_progress", {})
        if document.file_metadata
        else None,
    }


@router.post("/{document_id}/translation/resume")
async def resume_translation(
    document_id: str,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    RESUME TRANSLATION
    ================================================================================
    Nastavlja prekinutu translaciju od checkpoint-a.

    Args:
        document_id: ID dokumenta
        provider: Provajder za prevod (optional)
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Task ID za praćenje
    ================================================================================
    """
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

    # Check if document is in valid state for resume
    if document.status not in ["completed", "translating", "partial"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed first",
        )

    # Check translation progress
    translated_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id, Chunk.is_translated == 1)
        .count()
    )

    total_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).count()

    if translated_chunks >= total_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Svi chunk-ovi su vec prevedeni",
        )

    # Clear old checkpoint to force fresh start
    if document.file_metadata:
        document.file_metadata.pop("translation_checkpoint", None)

    # Start translation task (will resume from checkpoint)
    from app.workers.tasks import translate_document_task

    task = translate_document_task.delay(str(document.id), provider)

    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "resuming",
        "translated_chunks": translated_chunks,
        "remaining_chunks": total_chunks - translated_chunks,
        "provider": provider or "auto",
        "message": f"Translation resume started from chunk {translated_chunks}",
    }


@router.delete("/{document_id}/translation")
async def stop_translation(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    STOP TRANSLATION
    ================================================================================
    Zaustavlja aktivnu translaciju i cuva checkpoint.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        Status poruka
    ================================================================================
    """
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

    # Get current progress before cancelling
    translated_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id, Chunk.is_translated == 1)
        .count()
    )

    total_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).count()

    # Mark document as partial (allows resume)
    document.status = "partial"

    # Save checkpoint for resume
    document.file_metadata = document.file_metadata or {}
    document.file_metadata["translation_checkpoint"] = {
        "last_chunk_index": translated_chunks,
        "last_translated_count": translated_chunks,
        "stopped_by_user": True,
        "stopped_at": datetime.utcnow().isoformat() + "Z",
    }
    document.file_metadata["translation_progress"] = {
        "translated_chunks": translated_chunks,
        "total_chunks": total_chunks,
        "status": "stopped_by_user",
        "last_activity_at": datetime.utcnow().isoformat() + "Z",
    }
    db.commit()

    # Try to revoke any pending/active Celery tasks for this document
    try:
        from celery import Celery
        from app.core.config import settings

        # Create a new Celery instance to connect to Redis
        celery = Celery("ai_learning_system")
        celery.config_from_object(settings.CELERY_CONFIG)

        # Revoke all tasks (terminate=True kills active ones too)
        celery.control.revoke(terminate=True)
        logger.info(f"Translation tasks revoked for document {document_id}")
    except Exception as e:
        logger.warning(f"Could not revoke Celery tasks: {e}")

    return {
        "document_id": document_id,
        "status": "stopped",
        "translated_chunks": translated_chunks,
        "total_chunks": total_chunks,
        "can_resume": translated_chunks < total_chunks,
        "message": f"Translation stopped. {translated_chunks}/{total_chunks} chunks translated. "
        "Možete ponovo pokrenuti kad želite.",
    }


@router.get("/translation/providers")
async def get_translation_providers():
    """
    ================================================================================
    GET TRANSLATION PROVIDERS
    ================================================================================
    Vraća listu dostupnih AI provajdera za prevod.

    Returns:
        Lista dostupnih provajdera sa statusom
    """
    from app.services.translation import translation_service

    providers = translation_service.get_available_providers()

    return {
        "providers": providers,
        "default_order": settings.TRANSLATION_FALLBACK_ORDER,
    }


@router.get("/translation/validate")
async def validate_translation_provider(
    provider: str = None,
    current_user: User = Depends(get_current_user),
):
    """
    ================================================================================
    VALIDATE TRANSLATION PROVIDER
    ================================================================================
    Proverava da li je API ključ i model validni za zadati provider.
    Vraća jasne poruke za korisnika.

    Args:
        provider: Ime providera (openai, claude, deepl, etc.)
        current_user: Trenutni korisnik

    Returns:
        Validation result sa porukom za korisnika
    """
    from app.services.translation import translation_service
    from app.services.translation.translation_validator import (
        validate_translation_provider as validate,
    )

    # Ako nije dat provider, vrati sve dostupne
    if not provider:
        # Vrati listu svih providera sa statusom
        results = []
        for prov in translation_service._clients.keys():
            client = translation_service._clients.get(prov)
            if client:
                api_key = getattr(client, "api_key", None)
                model = getattr(client, "model", None)
                validation = validate(prov, api_key=api_key, model=model)
                results.append(
                    {
                        "provider": prov,
                        "status": validation.status,
                        "user_message": validation.user_message,
                        "is_ok": validation.is_ok,
                    }
                )

        return {
            "providers": results,
            "message": "Svi dostupni provideri",
        }

    # Validiraj specificiran provider
    if provider.lower() not in translation_service._clients:
        return {
            "provider": provider,
            "status": "error",
            "user_message": f"Provider '{provider}' nije podržan.",
            "is_ok": False,
        }

    client = translation_service._clients[provider.lower()]
    api_key = getattr(client, "api_key", None)
    model = getattr(client, "model", None)

    validation = validate(provider, api_key=api_key, model=model)

    return {
        "provider": provider,
        "status": validation.status,
        "user_message": validation.user_message,
        "details": validation.details,
        "is_ok": validation.is_ok,
    }


@router.post("/{document_id}/estimate-translation")
async def estimate_translation(
    document_id: str,
    provider: str = "deepl",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    ESTIMATE TRANSLATION COST
    ================================================================================
    Estimira cenu prevoda dokumenta.

    Args:
        document_id: ID dokumenta
        provider: Provajder za estimaciju

    Returns:
        Estimacija cene i vremena
    ================================================================================
    """
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

    chunks = db.query(Chunk).filter(Chunk.document_id == document.id).all()
    texts = [chunk.content for chunk in chunks]

    from app.services.translation import translation_service

    estimate = translation_service.estimate_cost(texts, provider)

    return {"document_id": document_id, "estimate": estimate}


