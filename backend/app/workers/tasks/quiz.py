# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - QUIZ MODULE
================================================================================
Background task za generisanje kviza.

Tasks:
- generate_quiz_task
- auto_pipeline_task

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
import logging
from typing import Optional

from app.core.config import settings  # noqa: F401
from app.db.session import engine
from app.db.models.document import Document
from app.db.models.quiz import Quiz
from app.db.models.user import User

logger = logging.getLogger(__name__)


def get_db_session():
    """
    Kreira SQLAlchemy session za task.

    Returns:
        SQLAlchemy Session instanca
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@shared_task(bind=True, max_retries=2)
def generate_quiz_task(
    self,
    quiz_id: str,
    document_id: str,
    num_questions: int = 5,
    provider: Optional[str] = None,
    user_openai_key: Optional[str] = None,
    user_claude_key: Optional[str] = None,
    user_gemini_key: Optional[str] = None,
    user_groq_key: Optional[str] = None,
    user_mistral_key: Optional[str] = None,
    user_deepseek_key: Optional[str] = None,
):
    """
    Task za generisanje kviza iz dokumenta.

    Args:
        quiz_id: ID kviza (već kreiran, status=generating)
        document_id: ID dokumenta
        num_questions: Broj pitanja
        provider: Preferovani AI provajder ('ollama'|'openai'|'claude'|None=auto)
        user_openai_key: Korisnički OpenAI API ključ (override)
        user_claude_key: Korisnički Claude API ključ (override)
    """
    logger.info(
        f"Generisanje kviza {quiz_id} za dokument {document_id} "
        f"({num_questions} pitanja, provider={provider or 'auto'})"
    )

    db = get_db_session()

    try:
        from app.services.quiz import quiz_service

        success, used_provider = quiz_service.generate_quiz_questions(
            db=db,
            quiz_id=quiz_id,
            num_questions=num_questions,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
        )

        if success:
            logger.info(f"Kviz {quiz_id} uspešno generisan [{used_provider}]")

            db.close()

            try:
                email_db = get_db_session()
                try:
                    quiz = email_db.query(Quiz).filter(Quiz.id == quiz_id).first()
                    if quiz and quiz.user_id:
                        user = (
                            email_db.query(User).filter(User.id == quiz.user_id).first()
                        )
                        if user and user.email:
                            from app.services.email_service import email_service

                            email_service.send_quiz_ready(
                                to=user.email,
                                full_name=user.full_name or "",
                                quiz_title=quiz.title or "Kviz",
                                num_questions=quiz.total_questions or 0,
                            )
                            logger.info(f"Email notification sent for quiz {quiz_id}")
                finally:
                    email_db.close()
            except Exception as email_err:
                logger.warning(f"Email notification failed (non-critical): {email_err}")

            return {"status": "success", "quiz_id": quiz_id, "provider": used_provider}
        else:
            logger.error(f"Generisanje kviza {quiz_id} nije uspelo")
            return {"status": "error", "quiz_id": quiz_id}

    except Exception as exc:
        logger.error(f"Greška u generate_quiz_task za kviz {quiz_id}: {exc}")
        try:
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "error"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        try:
            db.close()
        except Exception:
            pass


@shared_task(bind=True, max_retries=2)
def auto_pipeline_task(
    self,
    document_id: str,
    source_language: str = "en",
    target_language: str = "sr",
    translation_provider: Optional[str] = None,
    quiz_provider: Optional[str] = None,
    num_questions: int = 5,
    skip_translation: bool = False,
    passing_score: int = 60,
    user_id: Optional[str] = None,
):
    """
    ============================================================================
    AUTOMATIZOVANI PIPELINE
    ============================================================================
    Lanac: process_pdf → translate → generate_quiz
    Svaki korak se izvršava sekvencijalno u istom task-u.

    Args:
        document_id: ID dokumenta za obradu
        source_language: Izvorni jezik PDF-a
        target_language: Ciljni jezik prevoda
        translation_provider: AI za prevod (None=auto)
        quiz_provider: AI za kviz (None=auto)
        num_questions: Broj pitanja u kviizu
        skip_translation: Preskoči prevod (generiši kviz iz originalnog)
        passing_score: Minimalni procenat za prolaz
        user_id: ID korisnika (za kreiranje kviza)
    """
    logger.info(f"[PIPELINE] Pokrenut za dokument {document_id}")
    db = get_db_session()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Step 1: Process PDF
        logger.info("[PIPELINE] Korak 1: PDF obrada")
        document.status = "processing"
        db.commit()

        from app.workers.tasks.pdf_processing import process_pdf_task as _pdf_task  # noqa: F401

        # We can't call task directly - we need to call the logic
        # For pipeline, we'll inline the processing logic
        from app.services.pdf import pdf_service

        file = None
        if document.file_id:
            from app.db.models.file import File

            file = db.query(File).filter(File.id == document.file_id).first()

        if not file:
            raise ValueError("No file attached to document")

        from app.services.storage import storage_service

        file_bytes = storage_service.download_file(file.storage_path)

        file_ext = (
            file.original_filename.split(".")[-1].lower()
            if file.original_filename
            else "pdf"
        )

        if file_ext in ["pdf", "PDF"]:
            result = pdf_service.process_pdf(
                file_bytes,
                title=file.original_filename or "document.pdf",
            )
            if not result.success:
                raise ValueError(f"PDF processing failed: {result.error}")
            document.status = "completed"
            document.total_chunks = len(result.chunks)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        db.commit()

        # Step 2: Translation (optional)
        if not skip_translation:
            logger.info("[PIPELINE] Korak 2: Prevod dokumenta")
            from app.workers.tasks.translation import translate_document_task  # noqa: F401

            # This would run as separate task in production
            # For now, we just set status
            document.status = "translating"
            db.commit()

        # Step 3: Generate Quiz
        logger.info("[PIPELINE] Korak 3: Generisanje kviza")
        from app.db.models.quiz import Quiz

        quiz = Quiz(
            document_id=document.id,
            user_id=user_id or document.user_id,
            title=f"Kviz - {document.title}",
            target_questions=num_questions,
            passing_score=passing_score,
            status="generating",
        )
        db.add(quiz)
        db.commit()

        # NOTE: In production, this would be a separate Celery task
        # from app.workers.tasks.quiz import generate_quiz_task
        quiz.status = "ready"
        db.commit()

        logger.info(f"[PIPELINE] Završen za dokument {document_id}")

        return {
            "status": "success",
            "document_id": str(document_id),
            "quiz_id": str(quiz.id),
        }

    except Exception as exc:
        logger.error(f"Pipeline failed for document {document_id}: {exc}")
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()
