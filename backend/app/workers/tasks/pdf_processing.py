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

from app.core.config import settings
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
                file.original_filename or "document.pdf",
                document_id,
                db,
            )

            document.status = "completed"
            document.total_chunks = result.get("total_chunks", 0)
            document.file_metadata = document.file_metadata or {}
            document.file_metadata["pdf_processing"] = result

            file.status = "completed"
            logger.info(
                f"PDF processing completed: {result.get('total_chunks', 0)} chunks"
            )

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
                char_count=len(text_content),
                token_count=len(text_content) // 4,
            )
            db.add(chunk)
            document.total_chunks = 1
            document.status = "completed"
            file.status = "completed"

        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        db.commit()

    except Exception as exc:
        logger.error(f"PDF processing failed: {exc}")

        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = document.file_metadata or {}
                document.file_metadata["processing_error"] = str(exc)
                db.commit()

            file = db.query(File).filter(File.id == file_id).first() if file_id else None
            if file:
                file.status = "error"
                file.file_metadata = {"error": str(exc)}
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()