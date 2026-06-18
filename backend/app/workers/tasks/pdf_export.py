# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TASK - PDF EXPORT
================================================================================
Background task za generisanje PDF fajla od prevedenih chunkova.
Koristi se za dokumente sa velikim brojem chunkova (1000+).
Verzija: 1.1.0 (FAZA 14+) - Dodato cuvanje u files tabelu
================================================================================
"""

import logging
import uuid
import hashlib

from celery import Task

from app.db.session import engine
from app.workers.celery_app import celery_app
from app.db.models.document import Document, Chunk
from app.db.models.file import File
from app.services.pdf_export_service import PDFExportService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Task sa database session management-om."""

    _db_session = None

    def after_return(self, *args, **kwargs):
        if self._db_session is not None:
            self._db_session.close()

    @property
    def db_session(self):
        if self._db_session is None:
            from sqlalchemy.orm import sessionmaker

            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self._db_session = SessionLocal()
        return self._db_session


def get_db_session():
    """Kreira novu SQLAlchemy session."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, base=DatabaseTask)
def export_pdf_task(
    self, document_id: str, user_id: str, include_original: bool = False
):
    """
    Celery task za generisanje PDF-a u pozadini.

    Args:
        document_id: ID dokumenta
        user_id: ID korisnika (za proveru permisija)
        include_original: Da li uključiti originalni tekst

    Returns:
        dict sa statusom i putanjom do fajla u MinIO-u
    """

    def progress_callback(current: int, total: int, message: str):
        """Callback for progress updates from PDF service."""
        self.update_state(
            state="PROGRESS",
            meta={
                "current": current,
                "total": 100,
                "status": message,
                "phase": "pdf_generation",
            },
        )

    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": 100,
            "status": "Započinjanje PDF exporta...",
            "phase": "start",
        },
    )

    db = get_db_session()

    try:
        # 1. Provera dokumenta
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Učitavanje dokumenta..."},
        )

        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )

        if not document:
            raise Exception("Dokument nije pronađen ili nemate pristup")

        # 2. Učitavanje chunkova
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Učitavanje chunkova..."},
        )

        chunks = (
            db.query(Chunk)
            .filter(
                Chunk.document_id == document_id,
            )
            .order_by(Chunk.sequence_number)
            .all()
        )

        if not chunks:
            raise Exception("Dokument nema segmenata")

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 30,
                "total": 100,
                "status": f"Pronađeno {len(chunks)} chunkova. Generisanje PDF-a...",
            },
        )

        # 3. Priprema podataka za PDF service (uključujući strukturu)
        chunk_dicts = [
            {
                "original_text": c.content,
                "translated_text": c.translated_content
                if c.translated_content
                else c.content,
                "heading_level": c.heading_level,
                "parent_heading": c.parent_heading,
                "sequence_number": c.sequence_number,
                "page_number": c.page_number,
                "layout_data": c.layout_data,
            }
            for c in chunks
        ]

        # 4. Generisanje PDF-a
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 40,
                "total": 100,
                "status": "Generisanje PDF sadržaja...",
                "phase": "generating",
            },
        )

        pdf_service = PDFExportService(progress_callback=progress_callback)

        from app.services.skills.file_skills import get_file_skill

        try:
            get_file_skill().get_pdf_prompt()
        except Exception:
            pass

        pdf_bytes = pdf_service.generate(
            title=document.title,
            chunks=chunk_dicts,
            target_language=document.target_language or "sr",
            include_original=include_original,
            author="AI Sistem za učenje",
        )

        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Čuvanje PDF fajla..."},
        )

        # 5. Upload PDF - koristi storage service i sacuvaj u files tabelu
        safe_title = "".join(
            c if c.isalnum() or c in "-_ " else "_" for c in document.title
        )[:60]
        filename = f"{safe_title}_prevod.pdf"

        # Upload u storage (MinIO/S3)
        from io import BytesIO
        from app.services.storage import storage_service

        pdf_file_obj = BytesIO(pdf_bytes)
        upload_result = storage_service.upload_file(
            file_content=pdf_file_obj,
            filename=filename,
            user_id=str(document.user_id),
            content_type="application/pdf",
        )

        storage_path = upload_result.get("storage_path", "")
        checksum = upload_result.get("checksum", hashlib.sha256(pdf_bytes).hexdigest())

        # 5b. Kreiraj File zapis u bazi
        file_id = str(uuid.uuid4())
        db_file = File(
            id=uuid.UUID(file_id),
            user_id=document.user_id,
            original_filename=filename,
            storage_path=storage_path,
            file_size=len(pdf_bytes),
            mime_type="application/pdf",
            checksum=checksum,
            status="uploaded",
        )
        db.add(db_file)
        logger.info(f"Kreiran File zapis: {file_id} za PDF export")

        # 6. Azuriranje dokumenta
        document.pdf_export_id = file_id
        document.pdf_export_path = storage_path
        document.pdf_export_status = "completed"
        db.commit()

        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "PDF uspešno generisan!"},
        )

        return {
            "status": "completed",
            "file_id": file_id,
            "filename": filename,
            "document_id": document_id,
            "chunks_count": len(chunks),
        }

    except Exception as e:
        logger.error(f"Greška pri PDF exportu: {e}")
        try:
            document.pdf_export_status = "failed"
            db.commit()
        except Exception:
            pass

        self.update_state(state="FAILURE", meta={"status": f"Greška: {str(e)}"})
        raise

    finally:
        db.close()
