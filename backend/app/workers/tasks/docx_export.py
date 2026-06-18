# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TASK - DOCX EXPORT
================================================================================
Background task za generisanje DOCX fajla od prevedenih chunkova.
Koristi se za dokumente sa velikim brojem chunkova (1000+).
Verzija: 1.0.0 (FAZA 14)
================================================================================
"""

import logging

from celery import Task

from app.db.session import engine
from app.workers.celery_app import celery_app
from app.db.models.document import Document, Chunk
from app.services.docx_export_service import DOCXExportService

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
def export_docx_task(
    self, document_id: str, user_id: str, include_original: bool = False
):
    """
    Celery task za generisanje DOCX-a u pozadini.

    Args:
        document_id: ID dokumenta
        user_id: ID korisnika (za proveru permisija)
        include_original: Da li uključiti originalni tekst

    Returns:
        dict sa statusom i putanjom do fajla u MinIO-u
    """

    def progress_callback(current: int, total: int, message: str):
        self.update_state(
            state="PROGRESS",
            meta={
                "current": current,
                "total": 100,
                "status": message,
                "phase": "docx_generation",
            },
        )

    self.update_state(
        state="PROGRESS",
        meta={
            "current": 0,
            "total": 100,
            "status": "Započinjanje DOCX exporta...",
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
                "status": f"Pronađeno {len(chunks)} chunkova. Generisanje DOCX-a...",
            },
        )

        # 3. Priprema podataka za DOCX service (uključujući strukturu)
        chunk_dicts = [
            {
                "original_text": c.content,
                "translated_text": c.translated_content
                if c.translated_content
                else c.content,
                "heading_level": c.heading_level or 0,
                "parent_heading": c.parent_heading,
                "sequence_number": c.sequence_number,
            }
            for c in chunks
        ]

        # 4. Generisanje DOCX-a
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 40,
                "total": 100,
                "status": "Generisanje DOCX sadržaja...",
            },
        )

        docx_service = DOCXExportService(progress_callback=progress_callback)

        docx_bytes = docx_service.generate(
            title=document.title,
            chunks=chunk_dicts,
            include_original=include_original,
        )

        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Čuvanje DOCX fajla..."},
        )

        # 5. Upload DOCX u MinIO storage
        import uuid

        safe_title = "".join(
            c if c.isalnum() or c in "-_ " else "_" for c in document.title
        )[:60]
        filename = f"{safe_title}_prevod.docx"

        # Upload u storage (MinIO)
        from io import BytesIO
        from app.services.storage import storage_service

        docx_file_obj = BytesIO(docx_bytes)
        upload_result = storage_service.upload_file(
            file_content=docx_file_obj,
            filename=filename,
            user_id=str(document.user_id),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        # Čuvamo storage_path kao docx_export_path
        file_id = str(uuid.uuid4())
        storage_path = upload_result.get("storage_path", f"docx_exports/{file_id}.docx")

        # 6. Ažuriranje dokumenta
        document.docx_export_id = file_id
        document.docx_export_path = storage_path
        document.docx_export_status = "completed"
        db.commit()

        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "DOCX uspešno generisan!"},
        )

        return {
            "status": "completed",
            "file_id": file_id,
            "filename": filename,
            "document_id": document_id,
            "chunks_count": len(chunks),
        }

    except Exception as e:
        logger.error(f"Greška pri DOCX exportu: {e}")
        try:
            document.docx_export_status = "failed"
            db.commit()
        except Exception:
            pass

        self.update_state(state="FAILURE", meta={"status": f"Greška: {str(e)}"})
        raise

    finally:
        db.close()
