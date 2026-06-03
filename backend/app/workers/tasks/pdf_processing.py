# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - PDF PROCESSING MODULE
================================================================================
Background task za obradu PDF fajlova.

Task: process_pdf_task

Verzija: 2.1.0 (ZAŠTITA - cuvaj prevedene chunks)
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
import logging
import time
import uuid
from datetime import datetime, timezone

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
def process_pdf_task(
    self, document_id: str, file_id: str = None, force_reprocess: bool = False
):
    """
    Task za obradu PDF fajla.
    Ekstrahuje tekst, chunk-uje i priprema za prevod.

    ZAŠTITA: Cuv prevedene chunks prilikom reprocessovanja!

    Args:
        document_id: ID dokumenta za obradu
        file_id: ID fajla (opcionalno, za backward compatibility)
        force_reprocess: Ako True, brise sve chunks (ukljucujuci prevedene)
    """
    logger.info(
        f"Starting PDF processing for document: {document_id}, force={force_reprocess}"
    )

    db = get_db_session()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Proveri postojece chunks - cuvaj prevedene!
        existing_chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()

        # Mapiraj translated_content postojecih chunks po sequence_number
        # Ovo je KLJUCNO za cuvanje prevoda!
        translated_map = {}
        has_translations = False

        if existing_chunks:
            for chunk in existing_chunks:
                if chunk.translated_content and chunk.translated_content.strip():
                    translated_map[chunk.sequence_number] = chunk.translated_content
                    has_translations = True

            if has_translations:
                logger.info(
                    f"Document {document_id} has {len(translated_map)} translated chunks. "
                    f"These will be preserved during reprocessing!"
                )

        # BRISANJE STARIH CHUNKS - ali cuvaj prevedene u map!
        if existing_chunks and not force_reprocess:
            # Samo obelezi stare chunks za brisanje ali NE BRISI prevedene
            for chunk in existing_chunks:
                if chunk.sequence_number not in translated_map:
                    db.delete(chunk)
            logger.info(
                f"Deleted {len(existing_chunks) - len(translated_map)} non-translated chunks"
            )
        elif existing_chunks and force_reprocess:
            # Ako je force_reprocess, obavesti i obrisi SVE
            logger.warning(
                f"FORCE REPROCESS: Deleting ALL {len(existing_chunks)} chunks "
                f"({len(translated_map)} had translations - WILL BE LOST!)"
            )
            for chunk in existing_chunks:
                db.delete(chunk)
            translated_map = {}  # Resetuj jer su obrisani

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

            start_time = time.time()

            def progress_callback(pages_done, pages_total, chunks_so_far):
                try:
                    document.file_metadata = document.file_metadata or {}
                    document.file_metadata["processing_progress"] = {
                        "pages_done": pages_done,
                        "pages_total": pages_total,
                        "chunks_so_far": chunks_so_far,
                        "elapsed_seconds": int(time.time() - start_time),
                        "last_activity_at": datetime.now(timezone.utc).isoformat(),
                    }
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")

            result = pdf_service.process_pdf(
                file_bytes,
                title=file.original_filename or "document.pdf",
                progress_callback=progress_callback,
            )

            if not result.success:
                raise ValueError(f"PDF processing failed: {result.error}")

            # Kreiraj novi chunks - ali vrati prevedeni sadrzaj ako postoji!
            chunks_created = 0
            chunks_with_translation = 0

            for chunk_data in result.chunks:
                chunk = Chunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    content=chunk_data.content,
                    sequence_number=chunk_data.sequence_number,
                    token_count=chunk_data.token_count,
                    page_number=chunk_data.page_number,
                    heading_level=getattr(chunk_data, "heading_level", 0),
                    parent_heading=getattr(chunk_data, "parent_heading", ""),
                    layout_data=getattr(chunk_data, "layout_data", None),
                )

                # VRATI PREVEDENI SADRZAJ AKO POSTOJI!
                if chunk.sequence_number in translated_map:
                    chunk.translated_content = translated_map[chunk.sequence_number]
                    chunk.is_translated = 1
                    chunks_with_translation += 1
                    logger.debug(
                        f"Restored translation for chunk {chunk.sequence_number}"
                    )

                db.add(chunk)
                chunks_created += 1

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
                "preserved_translations": chunks_with_translation,
            }

            file.status = "completed"
            logger.info(
                f"PDF processing completed: {chunks_created} chunks, "
                f"{chunks_with_translation} translations preserved"
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
