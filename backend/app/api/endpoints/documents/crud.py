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
from .helpers import document_to_response
from . import router

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


