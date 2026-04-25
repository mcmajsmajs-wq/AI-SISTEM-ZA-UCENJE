# -*- coding: utf-8 -*-
"""
================================================================================
DOCUMENTS ENDPOINTS
================================================================================
Endpoint-i za upravljanje dokumentima i njihovom obradom.

Verzija: 1.2.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.db.session import get_db
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.db.models.user import User
from app.schemas.document import (
    DocumentCreate, 
    DocumentResponse, 
    DocumentListResponse,
    ChunkResponse,
    ChunkUpdate
)
from app.schemas.file import FileResponse
from app.services.auth import get_current_user
from app.workers.tasks import process_pdf_task
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def document_to_response(doc: Document) -> DocumentResponse:
    """Konvertuje Document model u DocumentResponse schema."""
    return DocumentResponse(
        id=str(doc.id),
        file_id=str(doc.file_id) if doc.file_id else None,
        user_id=str(doc.user_id),
        title=doc.title,
        description=doc.description,
        total_pages=doc.total_pages,
        total_chunks=doc.total_chunks,
        status=doc.status,
        source_language=doc.source_language,
        target_language=doc.target_language,
        metadata=doc.metadata or {},
        created_at=doc.created_at.isoformat() if doc.created_at else None,
        updated_at=doc.updated_at.isoformat() if doc.updated_at else None
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
        updated_at=chunk.updated_at.isoformat() if chunk.updated_at else None
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    logger.debug(f"Listing documents for user {current_user.id}: skip={skip}, limit={limit}")
    
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        items=[document_to_response(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    
    file = db.query(File).filter(
        and_(File.id == document.file_id, File.user_id == current_user.id)
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or does not belong to user"
        )
    
    if file.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create document from deleted file"
        )
    
    existing_doc = db.query(Document).filter(Document.file_id == document.file_id).first()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already exists for this file"
        )
    
    new_document = Document(
        user_id=current_user.id,
        file_id=file.id,
        title=document.title or file.original_filename,
        description=document.description,
        status="pending",
        source_language=document.source_language or "en",
        target_language=document.target_language or "sr"
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    task = process_pdf_task.delay(str(new_document.id), str(file.id))
    logger.info(f"Started PDF processing task: {task.id}")
    
    return document_to_response(new_document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document_to_response(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    DELETE DOCUMENT
    ================================================================================
    Briše dokument i sve njegove chunk-ove.
    
    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session
    ================================================================================
    """
    logger.warning(f"Document deletion requested: {document_id}")
    
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    db.delete(document)
    db.commit()
    
    logger.info(f"Document deleted: {document_id}")
    return None


@router.post("/{document_id}/process")
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already being processed"
        )
    
    if not document.file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no associated file"
        )
    
    document.status = "pending"
    db.commit()
    
    task = process_pdf_task.delay(str(document.id), str(document.file_id))
    
    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "queued",
        "message": "Document processing queued"
    }


@router.post("/{document_id}/translate")
async def translate_document(
    document_id: str,
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    logger.info(f"Translation requested for document: {document_id}, provider: {provider}")
    
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status not in ["completed", "translating"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed before translation"
        )
    
    from app.workers.tasks import translate_document_task
    task = translate_document_task.delay(str(document.id), provider)
    
    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "queued",
        "provider": provider or "auto",
        "message": f"Translation queued using {provider or 'auto-selected'} provider"
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
    ================================================================================
    """
    from app.services.translation import translation_service
    
    providers = translation_service.get_available_providers()
    
    return {
        "providers": providers,
        "default_order": settings.TRANSLATION_FALLBACK_ORDER
    }


@router.post("/{document_id}/estimate-translation")
async def estimate_translation(
    document_id: str,
    provider: str = "deepl",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    chunks = db.query(Chunk).filter(Chunk.document_id == document.id).all()
    texts = [chunk.content for chunk in chunks]
    
    from app.services.translation import translation_service
    estimate = translation_service.estimate_cost(texts, provider)
    
    return {
        "document_id": document_id,
        "estimate": estimate
    }


@router.get("/{document_id}/progress")
async def get_document_progress(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    total_chunks = document.total_chunks or 0
    translated_chunks = db.query(Chunk).filter(
        and_(Chunk.document_id == document.id, Chunk.is_translated == 1)
    ).count() if total_chunks > 0 else 0
    
    reviewed_chunks = db.query(Chunk).filter(
        and_(Chunk.document_id == document.id, Chunk.is_reviewed == 1)
    ).count() if total_chunks > 0 else 0
    
    progress_percentage = 0
    current_phase = "waiting"
    
    if document.status == "processing":
        current_phase = "extracting_text"
        progress_percentage = 50
    elif document.status == "translating":
        current_phase = "translating"
        progress_percentage = 50 + (translated_chunks / total_chunks * 50) if total_chunks > 0 else 50
    elif document.status == "completed":
        current_phase = "completed"
        progress_percentage = 100
    elif document.status == "error":
        current_phase = "error"
        progress_percentage = 0
    
    return {
        "document_id": document_id,
        "status": document.status,
        "progress_percentage": int(progress_percentage),
        "current_phase": current_phase,
        "total_chunks": total_chunks,
        "processed_chunks": total_chunks,
        "translated_chunks": translated_chunks,
        "reviewed_chunks": reviewed_chunks,
        "message": f"Document is {document.status}"
    }


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    chunks = db.query(Chunk).filter(
        Chunk.document_id == document.id
    ).order_by(Chunk.sequence_number).offset(skip).limit(limit).all()
    
    return [chunk_to_response(chunk) for chunk in chunks]


@router.put("/{document_id}/chunks/{chunk_id}")
async def update_chunk(
    document_id: str,
    chunk_id: str,
    content: str = None,
    translated_content: str = None,
    is_reviewed: bool = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    chunk = db.query(Chunk).filter(
        and_(Chunk.id == chunk_uuid, Chunk.document_id == document.id)
    ).first()
    
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found"
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
        "message": "Chunk updated successfully"
    }


@router.post("/{document_id}/export")
async def export_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    document = db.query(Document).filter(
        and_(Document.id == doc_uuid, Document.user_id == current_user.id)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully processed before export"
        )
    
    return {
        "document_id": document_id,
        "status": "queued",
        "download_url": None,
        "message": "Export feature coming soon"
    }
