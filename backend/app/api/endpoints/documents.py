# -*- coding: utf-8 -*-
"""
================================================================================
DOCUMENTS ENDPOINTS
================================================================================
Endpoint-i za upravljanje dokumentima i njihovom obradom.

Verzija: 1.2.1 - Stop translation + resume
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import uuid
import logging
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
from app.workers.tasks import process_pdf_task, auto_pipeline_task
from app.core.config import settings
from app.api.endpoints.documents_helpers import document_to_response, chunk_to_response

router = APIRouter()
logger = logging.getLogger(__name__)


# UKLONJENO: document_to_response() i chunk_to_response()
# Sada su u documents_helpers.py


def document_to_response(doc: Document, db=None) -> DocumentResponse:
    """Konvertuje Document model u DocumentResponse schema."""
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
    """Konvertuje Chunk model u ChunkResponse schema."""
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


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    LIST DOCUMENTS
    ================================================================================
    Vraća listu dokumenata korisnika.

    Args:
        skip: Offset za paginaciju
        limit: Limit rezultata
        status_filter: Filtriraj po statusu (optional)
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.debug(
        f"Listing documents for user {current_user.id}: skip={skip}, limit={limit}"
    )

    query = db.query(Document).filter(Document.user_id == current_user.id)

    if status_filter:
        query = query.filter(Document.status == status_filter)

    total = query.count()
    documents = (
        query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    )

    return DocumentListResponse(
        items=[document_to_response(doc, db) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CREATE DOCUMENT
    ================================================================================
    Kreira novi dokument iz postojećeg fajla.
    Pokreće procesiranje u background-u.

    Args:
        document: Podaci za kreiranje dokumenta
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.info(f"Creating document from file: {document.file_id}")

    file = (
        db.query(File)
        .filter(and_(File.id == document.file_id, File.user_id == current_user.id))
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or does not belong to user",
        )

    if file.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create document from deleted file",
        )

    existing_doc = (
        db.query(Document).filter(Document.file_id == document.file_id).first()
    )
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already exists for this file",
        )

    new_document = Document(
        user_id=current_user.id,
        file_id=file.id,
        title=document.title or file.original_filename,
        description=document.description,
        status="pending",
        source_language=document.source_language or "en",
        target_language=document.target_language or "sr",
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    task = process_pdf_task.delay(str(new_document.id), str(file.id))
    logger.info(f"Started PDF processing task: {task.id}")

    return document_to_response(new_document, db)


@router.post(
    "/from-text",
    response_model=DocumentFromTextResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_from_text(
    data: DocumentFromTextCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CREATE DOCUMENT FROM TEXT
    ================================================================================
    Kreira dokument direktno iz teksta (bez PDF fajla).
    Text se chunk-uje i čuva u bazi podataka.

    Args:
        data: Podaci sa tekstom za chunk-ovanje
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    from app.services.rag import chunk_text
    from app.workers.tasks import translate_document_task
    import hashlib

    logger.info(
        f"Creating document from text for user {current_user.email}: {data.title}"
    )

    # Generate checksum for text content
    content_checksum = hashlib.sha256(data.content.encode("utf-8")).hexdigest()

    # Kreiramo privremeni file zapis (bez fajla na disku)
    temp_file = File(
        id=uuid.uuid4(),
        user_id=current_user.id,
        original_filename=f"{data.title}.txt",
        storage_path=f"text-uploads/{current_user.id}/{uuid.uuid4()}.txt",
        file_size=len(data.content.encode("utf-8")),
        mime_type="text/plain",
        checksum=content_checksum,
        status="uploaded",
        file_metadata={"source": "from_text", "char_count": len(data.content)},
    )
    db.add(temp_file)
    db.commit()  # Commit file first so it exists for foreign key
    db.refresh(temp_file)

    # Kreiramo dokument
    new_document = Document(
        user_id=current_user.id,
        file_id=temp_file.id,
        title=data.title,
        description=data.description,
        status="pending",
        source_language=data.source_language or "en",
        target_language=data.target_language or "sr",
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # Chunk-ujemo tekst koristeći postojeću funkciju
    chunks = chunk_text(data.content, chunk_size=500, overlap=50)
    logger.info(f"Created {len(chunks)} chunks from text")

    # Čuvamo chunk-ove u bazu
    for idx, chunk_content in enumerate(chunks):
        chunk = Chunk(
            id=uuid.uuid4(),
            document_id=new_document.id,
            sequence_number=idx,
            content=chunk_content,
            token_count=len(chunk_content.split()),
            is_translated=0,
            is_reviewed=0,
        )
        db.add(chunk)

    new_document.total_chunks = len(chunks)
    new_document.status = "completed"  # Čim se chunk-uju, status je completed
    db.commit()

    task_id = None
    if data.translate_immediately:
        # Pokrećemo translaciju
        logger.info(f"Starting translation for document {new_document.id}")
        task = translate_document_task.delay(
            str(new_document.id),
            provider=data.provider,
        )
        task_id = task.id
        new_document.status = "translating"
        db.commit()

    return DocumentFromTextResponse(
        document_id=str(new_document.id),
        title=new_document.title,
        total_chunks=len(chunks),
        status=new_document.status,
        task_id=task_id,
        message=f"Document created with {len(chunks)} chunks"
        + (
            f". Translation started (task: {task_id})"
            if task_id
            else ". Translation not started."
        ),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    GET DOCUMENT
    ================================================================================
    Vraća detalje o dokumentu.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.debug(f"Fetching document: {document_id}")

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

    return document_to_response(document, db)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    DELETE DOCUMENT
    ================================================================================
    Briše dokument i sve njegove povezane zapise (chunks, quizzes, quiz_images).

    Returns:
        204: Document deleted successfully
        409: Document has related data that needs to be deleted first
    ================================================================================
    """
    logger.warning(f"Document deletion requested: {document_id}")

    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nevalidan format ID dokumenta",
        )

    document = (
        db.query(Document)
        .filter(and_(Document.id == doc_uuid, Document.user_id == current_user.id))
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dokument nije pronađen"
        )

    # Check for related data and provide smart messages
    from app.db.models.quiz import Quiz, QuizImage, QuizAttempt, Question

    # Count related data
    chunks_count = db.query(Chunk).filter(Chunk.document_id == doc_uuid).count()
    quiz_images_count = (
        db.query(QuizImage).filter(QuizImage.document_id == doc_uuid).count()
    )
    quizzes = db.query(Quiz).filter(Quiz.document_id == doc_uuid).all()
    quizzes_count = len(quizzes)

    total_questions = 0
    total_attempts = 0
    for quiz in quizzes:
        questions_count = db.query(Question).filter(Question.quiz_id == quiz.id).count()
        total_questions += questions_count
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).count()
        total_attempts += attempts

    # Build smart response message
    if chunks_count > 0 or quizzes_count > 0 or quiz_images_count > 0:
        message_parts = []
        if chunks_count > 0:
            message_parts.append(f"• {chunks_count} odlomaka")
        if quizzes_count > 0:
            message_parts.append(
                f"• {quizzes_count} kvizova ({total_questions} pitanja)"
            )
        if quiz_images_count > 0:
            message_parts.append(f"• {quiz_images_count} slika")
        if total_attempts > 0:
            message_parts.append(f"• {total_attempts} pokušaja")

        # Provide helpful message based on what needs to be deleted
        if quizzes_count > 0:
            detail_msg = (
                "⚠️ Da biste obrisali ovaj dokument, prvo morate obrisati povezane kvizove!\n\n"
                "Da li želite da automatski obrišemo sve povezane podatke?\n\n"
                "Povezani podaci:\n" + "\n".join(message_parts) + "\n\n"
                "📝 Ili možete ručno obrisati kvizove prvo, pa onda dokument."
            )
        else:
            detail_msg = (
                "⚠️ Dokument ima povezane podatke:\n" + "\n".join(message_parts) + "\n\n"
                "Pokušavamo automatski da obrišemo..."
            )

        # Try to delete, if fails provide detailed message
        try:
            # Delete in correct order due to foreign keys
            for quiz in quizzes:
                # First get all attempt IDs for this quiz
                attempts = (
                    db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).all()
                )
                attempt_ids = [a.id for a in attempts]

                # Delete quiz_answers (references questions)
                if attempt_ids:
                    from app.db.models.quiz import QuizAnswer

                    db.query(QuizAnswer).filter(
                        QuizAnswer.attempt_id.in_(attempt_ids)
                    ).delete(synchronize_session=False)

                # Delete quiz attempts
                db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz.id).delete(
                    synchronize_session=False
                )

                # Delete questions
                db.query(Question).filter(Question.quiz_id == quiz.id).delete(
                    synchronize_session=False
                )

            # Delete quizzes
            db.query(Quiz).filter(Quiz.document_id == doc_uuid).delete(
                synchronize_session=False
            )

            # Delete quiz images
            db.query(QuizImage).filter(QuizImage.document_id == doc_uuid).delete(
                synchronize_session=False
            )

            # Delete chunks
            db.query(Chunk).filter(Chunk.document_id == doc_uuid).delete(
                synchronize_session=False
            )

            # Save file_id before deleting document
            file_id = document.file_id

            # Delete document
            db.delete(document)

            # Delete file if exists
            if file_id:
                db.query(File).filter(File.id == file_id).delete(
                    synchronize_session=False
                )

            db.commit()
            logger.warning(
                f"Document {document_id} and all related data deleted successfully"
            )

            return {"message": "Dokument uspešno obrisan!", "deleted": True}

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document {document_id}: {e}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail_msg)

    # Obriši dokument
    db.delete(document)
    db.commit()

    # Obriši fajl ako postoji
    file_id = document.file_id
    if file_id:
        from app.db.models.file import File

        file = db.query(File).filter(File.id == file_id).first()
        if file:
            db.delete(file)
            db.commit()

    logger.warning(f"Document {document_id} deleted successfully")
    return {"message": "Dokument uspešno obrisan!", "deleted": True}


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
        "message": f"Translation stopped. {translated_chunks}/{total_chunks} chunks translated. Možete ponovo pokrenuti kad želite.",
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


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
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

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id)
        .order_by(Chunk.sequence_number)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [chunk_to_response(chunk) for chunk in chunks]


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


@router.post("/{document_id}/export")
async def export_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    EXPORT DOCUMENT
    ================================================================================
    Eksportuje dokument kao PDF.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        URL za download generisanog PDF-a
    ================================================================================
    """
    logger.info(f"Export requested for document: {document_id}")

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

    if document.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully processed before export",
        )

    return {
        "document_id": document_id,
        "status": "queued",
        "download_url": None,
        "message": "Export feature coming soon",
    }


# ============================================================
# PIPELINE ENDPOINTS
# ============================================================


@router.post("/{document_id}/pipeline")
async def start_pipeline(
    document_id: str,
    pipeline_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pokretanje automatskog pipeline-a za postojeći dokument.
    PDF mora biti uploadovan, dokument mora postojati.

    Pipeline: process_pdf → translate → generate_quiz

    Body (JSON):
    {
      "source_language": "en",
      "target_language": "sr",
      "translation_provider": "ollama|deepl|openai|google|claude|null",
      "quiz_provider": "ollama|openai|claude|null",
      "num_questions": 5,
      "skip_translation": false,
      "passing_score": 60
    }
    """
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    # Auto-detekcija jezika - proveri prvi chunk
    detected_lang = None
    first_chunk = db.query(Chunk).filter(Chunk.document_id == document.id).first()
    if first_chunk and first_chunk.content:
        text = first_chunk.content[:1000]  # Proveri prvih 1000 karaktera
        text_lower = text.lower()

        # Proveri da li sadrži ćirilične karaktere
        cyrillic_chars = sum(1 for c in text if "\u0400" <= c <= "\u04ff")
        latin_chars = sum(1 for c in text if "a" <= c.lower() <= "z")

        # Proveri srpske latinične karaktere
        serbian_latin_chars = sum(1 for c in text if c in "čćžšđČĆŽŠĐ")

        # Srpske reči bez specijalnih karaktera (detektuju srpski tekst koji je sacuvan kao ASCII)
        SERBIAN_WORDS = [
            "i",
            "u",
            "na",
            "za",
            "od",
            "sa",
            "su",
            "se",
            "da",
            "je",
            "ili",
            "to",
            "je",
            "samo",
            "ali",
            "tak",
            "jer",
            "pa",
            "te",
            "kao",
            "biti",
            "bitno",
            "moze",
            "sadrzi",
            "sadrzi",
            "ima",
            "jesu",
            "bila",
            "bili",
            "bilo",
            "smo",
            "ste",
            "hemijski",
            "hemija",
            "element",
            "molekul",
            "atom",
            "reakcija",
            "jedinjenje",
            "kiselina",
            "baza",
            "oksidacija",
            "redukcija",
            "supstanca",
            "rastvor",
            "matematika",
            "matematicki",
            "matematike",
            "jednacina",
            "formula",
            "resenje",
            "fizika",
            "fizicki",
            "energije",
            "sila",
            "brzina",
            "masa",
            "temperatura",
            "biologija",
            "bilogija",
            "organizam",
            "celija",
            "tkivo",
            "organ",
            "sistem",
            "istorija",
            "istorijski",
            "godina",
            "veka",
            "doba",
            "događaj",
            "dogadaj",
            "srbija",
            "beograd",
            "narod",
            "drzava",
            "drzavni",
            "vojvodina",
            "kosovo",
            "geografija",
            "drzava",
            "grad",
            "reka",
            "planina",
            "more",
            "jezero",
            "knjizevnost",
            "autor",
            "del",
            "glavni",
            "lik",
            "radnja",
            "pesnik",
            "informati",
            "racunar",
            "program",
            "algoritam",
            "podatak",
            "sistem",
            "lekcija",
            "nastav",
            "ucenik",
            "skola",
            "udzbenik",
            "gradivo",
            "poglavlje",
            "strana",
            " stran",
            "zadatak",
            "pitanje",
            "odgovor",
            "primer",
            "objasnjenje",
        ]

        # Prepoznaje srpski tekst bez specijalnih karaktera
        serbian_word_matches = sum(1 for word in SERBIAN_WORDS if word in text_lower)

        # Engleske reči koje mogu da se pojave u srpskim dokumentima
        ENGLISH_WORDS = [
            "the",
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "been",
            "being",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "their",
            "them",
            "and",
            "or",
            "but",
            "not",
            "no",
            "if",
            "then",
            "so",
            "because",
            "when",
            "which",
            "what",
            "who",
            "whom",
            "how",
            "where",
            "why",
            "chapter",
            "page",
            "figure",
            "table",
            "section",
            "introduction",
            "conclusion",
            "abstract",
            "references",
            "bibliography",
            "appendix",
        ]
        english_word_matches = sum(
            1 for word in ENGLISH_WORDS if f" {word} " in f" {text_lower} "
        )

        # Detekcija - POPRAVLJENA LOGIKA:
        # Srpski se detektuje ako:
        # 1. Ima bilo koju ćirilicu (> 0)
        # 2. Ima srpske latinične karaktere (č, ć, ž, š, đ)
        # 3. Ima dosta ćirilice (>10%) - za mešovite tekstove
        # 4. Ima dosta srpskih reči bez specijalnih karaktera (> 3)
        if cyrillic_chars > 0:
            detected_lang = "sr"
        elif serbian_latin_chars > 0:
            detected_lang = "sr"
        elif cyrillic_chars > latin_chars * 0.1:
            detected_lang = "sr"
        elif serbian_word_matches >= 3 and english_word_matches < 3:
            # Ako ima dosta srpskih reči a malo engleskih → srpski
            detected_lang = "sr"
        elif serbian_word_matches >= english_word_matches + 2:
            # Ako ima značajno više srpskih reči → srpski
            detected_lang = "sr"
        elif (
            latin_chars > 10
            and cyrillic_chars < 5
            and serbian_latin_chars < 3
            and serbian_word_matches < 3
        ):
            detected_lang = "en"

    # Koristi auto-detektovani jezik ili default
    source_language = pipeline_data.get("source_language") or detected_lang or "en"
    # Target language je uvek suprotan od source
    if not pipeline_data.get("target_language"):
        target_language = "sr" if source_language == "en" else "en"
    else:
        target_language = pipeline_data.get("target_language")
    translation_provider = pipeline_data.get("translation_provider")
    quiz_provider = pipeline_data.get("quiz_provider")
    num_questions = int(pipeline_data.get("num_questions", 5))
    skip_translation = bool(pipeline_data.get("skip_translation", False))
    passing_score = int(pipeline_data.get("passing_score", 60))

    # Reset status ako je potrebno
    if document.status == "error":
        document.status = "pending"
        db.commit()

    task = auto_pipeline_task.delay(
        document_id=str(document.id),
        source_language=source_language,
        target_language=target_language,
        translation_provider=translation_provider,
        quiz_provider=quiz_provider,
        num_questions=num_questions,
        skip_translation=skip_translation,
        passing_score=passing_score,
        user_id=str(current_user.id),
    )

    logger.info(f"Pipeline pokrenut za dokument {document_id} — Celery task {task.id}")

    return {
        "task_id": task.id,
        "document_id": document_id,
        "status": "started",
        "message": f"Pipeline pokrenut: PDF → {'→ Prevod ' if not skip_translation else ''}→ Kviz",
        "stages": [
            {"name": "PDF Processing", "skipped": document.status == "completed"},
            {
                "name": f"Prevod ({source_language}→{target_language})",
                "skipped": skip_translation or source_language == target_language,
            },
            {"name": f"Generisanje kviza ({num_questions} pitanja)", "skipped": False},
        ],
        "providers": {
            "translation": translation_provider or "auto",
            "quiz": quiz_provider or "auto",
        },
    }


@router.get("/pipeline/providers")
async def get_pipeline_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Vraća listu dostupnih AI provajdera za pipeline.
    """
    from app.services.translation import translation_service
    from app.services.quiz import quiz_service

    translation_providers = translation_service.get_available_providers()
    quiz_providers = quiz_service.get_available_providers()

    return {
        "translation_providers": translation_providers,
        "quiz_providers": quiz_providers,
    }


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
    from celery.result import AsyncResult
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


@router.get("/{document_id}/quiz-availability")
async def get_quiz_availability(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vraća dostupnost pitanja za kviz za dati dokument.

    Returns:
        - total: Ukupno generisanih pitanja za dokument
        - used: Broj pitanja koja su vec koriscena u kvizovima
        - available: Broj dostupnih pitanja za nove kvizove
    """
    from app.db.models.quiz import Quiz, Question

    doc_uuid = uuid.UUID(document_id)
    document = (
        db.query(Document)
        .filter(
            Document.id == doc_uuid,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    quizzes = db.query(Quiz).filter(Quiz.document_id == doc_uuid).all()

    total = 0
    used = 0

    for quiz in quizzes:
        questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
        total += len(questions)
        used += sum(1 for q in questions if q.used)

    available = total - used

    return {
        "total": total,
        "used": used,
        "available": available,
    }


# ─── DOCX EXPORT ENDPOINTS ────────────────────────────────────────────────

from app.workers.tasks.docx_export import export_docx_task


@router.post("/{document_id}/export-docx", status_code=202)
def export_document_to_docx(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pokrece async DOCX export task za dokument."""
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
    task = export_docx_task.delay(document_id, str(current_user.id))

    # Azuriraj status u bazi
    doc.docx_export_status = "processing"
    db.commit()

    return {
        "message": "DOCX export task pokrenut",
        "task_id": task.id,
        "status": "processing",
        "chunks_count": chunk_count,
    }


@router.get("/docx-status/{task_id}")
def get_docx_export_status(
    task_id: str,
):
    """Proverava status DOCX export task-a."""
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


@router.get("/{document_id}/docx-download")
def download_docx(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download generisanog DOCX-a."""
    from fastapi.responses import Response

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nije pronadjen")

    if doc.docx_export_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"DOCX nije spreman (status: {doc.docx_export_status})",
        )

    # Koristi docx_export_path iz baze za download
    storage_path = doc.docx_export_path
    if not storage_path:
        raise HTTPException(status_code=404, detail="DOCX putanja nije definisana")

    # Download iz MinIO storage-a
    from app.services.storage import storage_service

    try:
        docx_content = storage_service.download_file(storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="DOCX fajl nije pronadjen u storage-u"
        )

    return Response(
        content=docx_content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.title or "document"}.docx"'
        },
    )


# ─── PDF EXPORT ENDPOINTS ────────────────────────────────────────────────

from app.workers.tasks.pdf_export import export_pdf_task
from fastapi import BackgroundTasks


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
    from fastapi.responses import FileResponse
    from pathlib import Path

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
