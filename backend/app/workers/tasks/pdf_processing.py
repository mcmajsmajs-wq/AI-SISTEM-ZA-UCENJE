# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - PDF PROCESSING MODULE
================================================================================
Background task za obradu PDF fajlova.

Task: process_pdf_task

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
import logging
import uuid

from app.core.config import settings  # noqa: F401
from app.db.session import engine
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.services.storage import storage_service
from app.services.pdf import pdf_service

logger = logging.getLogger(__name__)


def get_db_session():
    """
    Kreira SQLAlchemy session za task.

    Returns:
        SQLAlchemy Session instanca
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@shared_task(bind=True, max_retries=3)
def process_pdf_task(self, document_id: str, file_id: str = None):
    """
    Task za obradu PDF fajla.
    Ekstrahuje tekst, chunk-uje i priprema za prevod.

    Args:
        document_id: ID dokumenta za obradu
        file_id: ID fajla (opcionalno, za backward compatibility)
    """
    logger.info(f"Starting PDF processing for document: {document_id}")

    db = get_db_session()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        document.status = "processing"
        db.commit()

        if file_id is None:
            file_id = document.file_id

        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise ValueError(f"File not found: {file_id}")

        file.status = "processing"
        db.commit()

        logger.info(f"Downloading file from storage: {file.storage_path}")
        file_bytes = storage_service.download_file(file.storage_path)

        file_ext = (
            file.original_filename.split(".")[-1].lower()
            if file.original_filename
            else "pdf"
        )
        file_ext = "." + file_ext

        if file_ext in [".pdf", ".PDF"]:
            logger.info(f"Processing PDF file: {file.original_filename}")
            result = pdf_service.process_pdf(
                file_bytes,
                title=file.original_filename or "document.pdf",
            )

            if not result.success:
                raise ValueError(f"PDF processing failed: {result.error}")

            for chunk_data in result.chunks:
                chunk = Chunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    content=chunk_data.content,
                    sequence_number=chunk_data.sequence_number,
                    token_count=chunk_data.token_count,
                    page_number=chunk_data.page_number,
                )
                db.add(chunk)

            document.total_pages = result.metadata.total_pages
            document.status = "completed"
            document.total_chunks = len(result.chunks)
            document.file_metadata = document.file_metadata or {}
            document.file_metadata["pdf_processing"] = {
                "success": result.success,
                "total_chunks": len(result.chunks),
                "total_pages": result.metadata.total_pages,
                "pages_text": [
                    p[:200] + "..." if len(p) > 200 else p for p in result.pages_text
                ],
            }

            file.status = "completed"
            logger.info(f"PDF processing completed: {len(result.chunks)} chunks")

        elif file_ext in [".txt", ".TXT"]:
            logger.info(f"Processing text file: {file.original_filename}")
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = file_bytes.decode("latin-1")

            chunk = Chunk(
                id=uuid.uuid4(),
                document_id=document.id,
                content=text_content,
                sequence_number=1,
                token_count=len(text_content) // 4,
            )
            db.add(chunk)
            document.total_chunks = 1
            document.status = "completed"
            file.status = "completed"

        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        db.commit()

        # Send email notification about chunks being ready
        if document.user_id:
            try:
                from app.db.models.user import User

                user = db.query(User).filter(User.id == document.user_id).first()
                if user and user.email:
                    from app.services.email_service import email_service

                    email_service.send_chunks_ready(
                        to=user.email,
                        full_name=user.full_name or "",
                        document_title=document.title or "Dokument",
                        total_chunks=document.total_chunks or 0,
                        total_pages=document.total_pages or 0,
                    )
                    logger.info(f"Email notification sent for document {document_id}")
            except Exception as email_err:
                logger.warning(f"Email notification failed (non-critical): {email_err}")

    except Exception as exc:
        logger.error(f"PDF processing failed: {exc}")

        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = document.file_metadata or {}
                document.file_metadata["processing_error"] = str(exc)
                db.commit()

            file = (
                db.query(File).filter(File.id == file_id).first() if file_id else None
            )
            if file:
                file.status = "error"
                file.file_metadata = {"error": str(exc)}
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()
