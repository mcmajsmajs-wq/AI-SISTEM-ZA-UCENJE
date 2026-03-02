# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TASKS
================================================================================
Background task-ovi za asinhronu obradu.

Verzija: 1.2.0
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.db.session import engine
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.services.storage import storage_service
from app.services.pdf import pdf_service
from app.services.translation import translation_service, make_gemini_client, make_groq_client, make_mistral_client

logger = logging.getLogger(__name__)


def get_db_session():
    """Kreira novu database session za Celery task."""
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
        pdf_bytes = storage_service.download_file(file.storage_path)
        
        logger.info(f"Processing PDF: {file.original_filename}")

        import time as _time
        _started_at = _time.time()

        def _progress(pages_done: int, pages_total: int, chunks_so_far: int):
            """Write incremental progress using a separate DB session (avoids poisoning main session)."""
            _pdb = None
            try:
                elapsed = int(_time.time() - _started_at)
                patch = __import__('json').dumps({
                    "processing_progress": {
                        "pages_done": pages_done,
                        "pages_total": pages_total,
                        "chunks_so_far": chunks_so_far,
                        "elapsed_seconds": elapsed,
                    }
                })
                _pdb = get_db_session()
                _pdb.execute(
                    __import__('sqlalchemy').text(
                        "UPDATE documents SET metadata = (COALESCE(metadata, '{}')::jsonb || :patch::jsonb)::json WHERE id = :doc_id"
                    ),
                    {"patch": patch, "doc_id": str(document.id)}
                )
                _pdb.commit()
            except Exception as _e:
                logger.debug(f"Progress update skipped: {_e}")
                if _pdb:
                    try: _pdb.rollback()
                    except Exception: pass
            finally:
                if _pdb:
                    try: _pdb.close()
                    except Exception: pass

        result = pdf_service.process_pdf(pdf_bytes, title=document.title, progress_callback=_progress)
        
        if not result.success:
            raise Exception(f"PDF processing failed: {result.error}")
        
        document.total_pages = result.metadata.total_pages
        document.total_chunks = len(result.chunks)
        document.file_metadata = {
            "author": result.metadata.author,
            "subject": result.metadata.subject,
            "creator": result.metadata.creator,
            "producer": result.metadata.producer,
            "has_images": result.metadata.has_images,
            "is_scanned": result.metadata.is_scanned,
            "total_chars": result.metadata.total_chars
        }
        
        for chunk_data in result.chunks:
            chunk = Chunk(
                document_id=document.id,
                sequence_number=chunk_data.sequence_number,
                content=chunk_data.content,
                token_count=chunk_data.token_count,
                heading_level=chunk_data.heading_level,
                parent_heading=chunk_data.parent_heading
            )
            db.add(chunk)
        
        document.status = "completed"
        file.status = "completed"
        db.commit()
        
        logger.info(
            f"PDF processing completed for document {document_id}: "
            f"{result.metadata.total_pages} pages, {len(result.chunks)} chunks"
        )
        
        # Automatski pokreni RAG indeksiranje u pozadini
        try:
            index_document_task.delay(
                document_id=str(document_id),
                file_path=file.storage_path,
                source_name=document.title or file.original_filename
            )
            logger.info(f"RAG index task queued for document {document_id}")
        except Exception as rag_exc:
            logger.warning(f"RAG index task not queued (non-critical): {rag_exc}")
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_pages": result.metadata.total_pages,
            "total_chunks": len(result.chunks),
            "is_scanned": result.metadata.is_scanned
        }
        
    except Exception as exc:
        logger.error(f"PDF processing failed for document {document_id}: {exc}")
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = {"error": str(exc)}
                db.commit()
            
            if file_id:
                file = db.query(File).filter(File.id == file_id).first()
                if file:
                    file.status = "error"
                    file.file_metadata = {"error": str(exc)}
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def translate_document_task(self, document_id: str, provider: Optional[str] = None):
    """
    Task za AI prevod dokumenta.
    Prevod chunk-ova koristeći Ollama, DeepL, OpenAI, Google ili Claude.
    
    Args:
        document_id: ID dokumenta za prevod
        provider: Specifični provajder (ollama, deepl, openai, google, claude)
    """
    logger.info(f"Starting translation for document: {document_id}, provider: {provider}")
    
    db = get_db_session()
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        if document.status not in ["completed", "translating"]:
            raise ValueError(f"Document must be processed first. Current status: {document.status}")
        
        document.status = "translating"
        db.commit()
        
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document.id
        ).order_by(Chunk.sequence_number).all()
        
        if not chunks:
            raise ValueError("No chunks found for document")
        
        total_chunks = len(chunks)
        translated_count = 0
        total_cost = 0.0
        total_tokens = 0
        errors = []

        # Load user API key for cloud providers
        user = db.query(Document).filter(Document.id == document_id).first()
        from app.db.models.user import User
        user_obj = db.query(User).filter(User.id == document.user_id).first() if document.user_id else None

        # Build a per-request client if user has their own key for this provider
        _provider_client = None
        if provider and user_obj:
            if provider == "gemini" and getattr(user_obj, 'ai_api_key_gemini', None):
                _provider_client = make_gemini_client(user_obj.ai_api_key_gemini)
            elif provider == "groq" and getattr(user_obj, 'ai_api_key_groq', None):
                _provider_client = make_groq_client(user_obj.ai_api_key_groq)
            elif provider == "mistral" and getattr(user_obj, 'ai_api_key_mistral', None):
                _provider_client = make_mistral_client(user_obj.ai_api_key_mistral)

        logger.info(f"Translating {total_chunks} chunks for document {document_id}")

        for i, chunk in enumerate(chunks):
            if chunk.is_translated:
                translated_count += 1
                continue

            # Use per-user client if available, otherwise global service
            if _provider_client:
                result = _provider_client.translate(
                    text=chunk.content,
                    source_language=document.source_language,
                    target_language=document.target_language,
                )
            else:
                result = translation_service.translate(
                    text=chunk.content,
                    source_language=document.source_language,
                    target_language=document.target_language,
                    provider=provider
                )
            
            if result.success:
                chunk.translated_content = result.translated_text
                chunk.is_translated = 1
                total_cost += result.cost
                total_tokens += result.tokens_used
                translated_count += 1
                
                if (i + 1) % 10 == 0:
                    db.commit()
                    logger.info(f"Translated {i + 1}/{total_chunks} chunks")
            else:
                errors.append(f"Chunk {chunk.sequence_number}: {result.error}")
                logger.error(f"Failed to translate chunk {chunk.sequence_number}: {result.error}")
        
        db.commit()
        
        document.file_metadata = document.file_metadata or {}
        document.file_metadata["translation"] = {
            "provider": provider or "auto",
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "translated_chunks": translated_count,
            "errors": errors[:10] if errors else []
        }
        
        if translated_count == total_chunks:
            document.status = "completed"
            logger.info(f"Translation completed for document {document_id}: {translated_count}/{total_chunks} chunks")
        elif translated_count > 0:
            # Partial translation — still usable, mark as completed
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            logger.warning(f"Partial translation for document {document_id}: {translated_count}/{total_chunks} chunks")
        else:
            # All chunks failed — reset to completed so user can retry
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            document.file_metadata["translation"]["failed"] = True
            logger.warning(f"Translation fully failed for document {document_id}: 0/{total_chunks} chunks translated")
        
        db.commit()
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_chunks": total_chunks,
            "translated_chunks": translated_count,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "errors_count": len(errors)
        }
        
    except Exception as exc:
        logger.error(f"Translation failed for document {document_id}: {exc}")
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = document.file_metadata or {}
                document.file_metadata["translation_error"] = str(exc)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        
        raise self.retry(exc=exc, countdown=300)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_quiz_task(self, quiz_id: str, document_id: str, num_questions: int = 5, provider: Optional[str] = None, user_openai_key: Optional[str] = None, user_claude_key: Optional[str] = None, user_gemini_key: Optional[str] = None, user_groq_key: Optional[str] = None, user_mistral_key: Optional[str] = None):
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
    logger.info(f"Generisanje kviza {quiz_id} za dokument {document_id} "
                f"({num_questions} pitanja, provider={provider or 'auto'})")

    db = get_db_session()

    try:
        from app.services.quiz import quiz_service

        success, used_provider = quiz_service.populate_quiz_questions(
            db=db,
            quiz_id=quiz_id,
            document_id=document_id,
            num_questions=num_questions,
            provider=provider,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
        )

        if success:
            logger.info(f"Kviz {quiz_id} uspešno generisan [{used_provider}]")
            return {"status": "success", "quiz_id": quiz_id, "provider": used_provider}
        else:
            logger.error(f"Generisanje kviza {quiz_id} nije uspelo")
            return {"status": "error", "quiz_id": quiz_id}

    except Exception as exc:
        logger.error(f"Greška u generate_quiz_task za kviz {quiz_id}: {exc}")
        try:
            from app.db.models.quiz import Quiz
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "error"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


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
            raise ValueError(f"Dokument nije pronađen: {document_id}")

        owner_id = str(user_id or document.user_id)

        # ── KORAK 1: Procesiranje PDF-a ─────────────────────────────────────
        if document.status not in ("completed",):
            logger.info(f"[PIPELINE] Korak 1/3: PDF processing za {document_id}")
            document.status = "processing"
            db.commit()

            file = db.query(File).filter(File.id == document.file_id).first()
            if not file:
                raise ValueError(f"Fajl nije pronađen za dokument {document_id}")

            file.status = "processing"
            db.commit()

            pdf_bytes = storage_service.download_file(file.storage_path)
            result = pdf_service.process_pdf(pdf_bytes, title=document.title)

            if not result.success:
                raise Exception(f"PDF processing greška: {result.error}")

            document.total_pages = result.metadata.total_pages
            document.total_chunks = len(result.chunks)
            document.source_language = source_language
            document.target_language = target_language
            document.file_metadata = {
                "author": result.metadata.author,
                "total_chars": result.metadata.total_chars,
                "is_scanned": result.metadata.is_scanned,
            }

            for chunk_data in result.chunks:
                chunk = Chunk(
                    document_id=document.id,
                    sequence_number=chunk_data.sequence_number,
                    content=chunk_data.content,
                    token_count=chunk_data.token_count,
                    heading_level=chunk_data.heading_level,
                    parent_heading=chunk_data.parent_heading,
                )
                db.add(chunk)

            document.status = "completed"
            file.status = "completed"
            db.commit()
            logger.info(f"[PIPELINE] PDF procesuiran: {result.metadata.total_pages} str, {len(result.chunks)} chunk-ova")
        else:
            logger.info(f"[PIPELINE] Dokument već procesuiran, preskačem korak 1")

        # ── KORAK 2: Prevod ─────────────────────────────────────────────────
        if not skip_translation and source_language != target_language:
            logger.info(f"[PIPELINE] Korak 2/3: Prevod ({source_language}→{target_language}) [{translation_provider or 'auto'}]")
            document.status = "translating"
            db.commit()

            chunks = db.query(Chunk).filter(
                Chunk.document_id == document.id,
                Chunk.is_translated == 0
            ).order_by(Chunk.sequence_number).all()

            total_cost = 0.0
            translated_count = 0

            for i, chunk in enumerate(chunks):
                trans_result = translation_service.translate(
                    text=chunk.content,
                    source_language=source_language,
                    target_language=target_language,
                    provider=translation_provider,
                )
                if trans_result.success:
                    chunk.translated_content = trans_result.translated_text
                    chunk.is_translated = 1
                    total_cost += trans_result.cost
                    translated_count += 1
                    if (i + 1) % 10 == 0:
                        db.commit()
                else:
                    logger.warning(f"[PIPELINE] Chunk {chunk.sequence_number} prevod neuspešan: {trans_result.error}")

            db.commit()
            document.file_metadata = document.file_metadata or {}
            document.file_metadata["translation"] = {
                "provider": translation_provider or "auto",
                "translated_chunks": translated_count,
                "total_cost": total_cost,
            }
            document.status = "completed"
            db.commit()
            logger.info(f"[PIPELINE] Prevod završen: {translated_count} chunk-ova")
        else:
            logger.info(f"[PIPELINE] Prevod preskočen (skip={skip_translation}, lang={source_language}→{target_language})")

        # ── KORAK 3: Generisanje kviza ───────────────────────────────────────
        logger.info(f"[PIPELINE] Korak 3/3: Generisanje kviza [{quiz_provider or 'auto'}]")

        from app.services.quiz import quiz_service

        quiz = quiz_service.create_quiz_from_document(
            db=db,
            document_id=str(document.id),
            user_id=owner_id,
            num_questions=num_questions,
            passing_score=passing_score,
        )

        success, used_provider = quiz_service.populate_quiz_questions(
            db=db,
            quiz_id=str(quiz.id),
            document_id=str(document.id),
            num_questions=num_questions,
            provider=quiz_provider,
        )

        if not success:
            raise Exception("Generisanje kviza nije uspelo")

        logger.info(f"[PIPELINE] ✅ Kompletiran! Dokument={document_id}, Kviz={quiz.id} [{used_provider}]")

        return {
            "status": "success",
            "document_id": str(document_id),
            "quiz_id": str(quiz.id),
            "total_chunks": document.total_chunks,
            "quiz_questions": quiz.total_questions,
            "quiz_provider": used_provider,
        }

    except Exception as exc:
        logger.error(f"[PIPELINE] Greška za dokument {document_id}: {exc}")
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "error"
                doc.file_metadata = doc.file_metadata or {}
                doc.file_metadata["pipeline_error"] = str(exc)
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()


@shared_task
def cleanup_old_files():
    """
    Periodični task za čišćenje starih fajlova.
    Briše soft-deleted fajlove starije od 30 dana.
    """
    logger.info("Starting cleanup of old files")
    
    # TODO: Implementirati cleanup
    # 1. Pronađi fajlove sa deleted_at starijim od 30 dana
    # 2. Obriši iz storage-a
    # 3. Obriši iz baze
    
    logger.info("Cleanup completed")
    return {"status": "success", "files_deleted": 0}


@shared_task
def send_study_reminders():
    """
    Periodični task: šalje dnevne podsetnike svim korisnicima koji imaju
    reminder_enabled=True u StudyPlan-u i čiji je reminder_time = trenutni sat.
    Poziva se svakih sat vremena (Celery Beat).
    """
    from datetime import date, datetime
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import QuizAttempt
    from sqlalchemy import func
    from app.services.email_service import email_service

    logger.info("Pokretanje dnevnih podsetnika...")
    db = get_db_session()
    sent = 0
    try:
        current_hour = datetime.now().strftime("%H")
        today = date.today()

        plans = db.query(StudyPlan).filter(
            StudyPlan.is_active == True,
            StudyPlan.reminder_enabled == True,
        ).all()

        for plan in plans:
            if not plan.reminder_time:
                continue
            # reminder_time je "HH:MM" — poredimo samo sat
            plan_hour = plan.reminder_time.split(":")[0].zfill(2)
            if plan_hour != current_hour:
                continue

            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            # Zakazani kvizovi za danas
            today_items = db.query(StudyPlanItem).filter(
                StudyPlanItem.plan_id == plan.id,
                StudyPlanItem.scheduled_for == today,
                StudyPlanItem.is_completed == False,
            ).all()

            # Streak
            from app.api.endpoints.analytics import _calc_streak
            streak = _calc_streak(user.id, db)

            titles = []
            for item in today_items:
                from app.db.models.quiz import Quiz
                quiz = db.query(Quiz).filter(Quiz.id == item.quiz_id).first()
                if quiz:
                    titles.append(quiz.title)

            ok = email_service.send_daily_reminder(
                to=user.email,
                full_name=user.full_name or "",
                today_quiz_titles=titles,
                streak=streak,
            )
            if ok:
                sent += 1

    except Exception as e:
        logger.error(f"Greška u send_study_reminders: {e}")
    finally:
        db.close()

    logger.info(f"Podsetnici poslati: {sent}")
    return {"status": "success", "reminders_sent": sent}


@shared_task
def send_weekly_summaries():
    """
    Periodični task: šalje nedeljni sažetak svakom aktivnom korisniku.
    Poziva se jednom nedeljno (npr. nedeljom u 10:00).
    """
    from datetime import date, timedelta
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import Quiz, QuizAttempt
    from sqlalchemy import func
    from app.services.email_service import email_service
    from app.api.endpoints.analytics import _calc_streak

    logger.info("Pokretanje nedeljnih sažetaka...")
    db = get_db_session()
    sent = 0
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plans = db.query(StudyPlan).filter(StudyPlan.is_active == True).all()
        for plan in plans:
            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            # Urađeni kvizovi ove nedelje
            week_done = db.query(StudyPlanItem).filter(
                StudyPlanItem.plan_id == plan.id,
                StudyPlanItem.is_completed == True,
                StudyPlanItem.completed_at >= week_start,
            ).count()

            # Prosečan score ove nedelje
            avg_row = db.query(func.avg(QuizAttempt.percentage)).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.completed_at >= week_start,
            ).scalar()
            avg_score = round(float(avg_row or 0), 1)

            streak = _calc_streak(user.id, db)

            # Najbol kviz (najviši score ove nedelje)
            best_attempt = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.completed_at >= week_start,
            ).order_by(QuizAttempt.percentage.desc()).first()
            best_title = None
            if best_attempt:
                bq = db.query(Quiz).filter(Quiz.id == best_attempt.quiz_id).first()
                best_title = bq.title if bq else None

            ok = email_service.send_weekly_summary(
                to=user.email,
                full_name=user.full_name or "",
                week_completed=week_done,
                week_goal=plan.weekly_quiz_goal,
                avg_score=avg_score,
                streak=streak,
                best_quiz=best_title,
            )
            if ok:
                sent += 1

    except Exception as e:
        logger.error(f"Greška u send_weekly_summaries: {e}")
    finally:
        db.close()

    logger.info(f"Nedeljni sažeci poslati: {sent}")
    return {"status": "success", "summaries_sent": sent}


# ============================================================
# KNOWLEDGE BASE INGESTION TASKS
# ============================================================

@shared_task(bind=True, max_retries=2, name="index_document_task")
def index_document_task(self, document_id: str, file_path: str, source_name: str):
    """
    Indeksira PDF dokument u RAG knowledge base.
    Poziva se automatski posle obrade PDF-a.
    Čita već iztraktovane chunks iz baze umjesto direktnog čitanja PDF-a sa diska.
    """
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import ingest_source
    from sqlalchemy import text

    logger.info(f"Indeksiranje dokumenta: {source_name}")
    db = SessionLocal()
    try:
        # Pokupi chunks iz baze koji su već procesovani
        rows = db.execute(
            text("SELECT content FROM chunks WHERE document_id = :doc_id ORDER BY sequence_number"),
            {"doc_id": document_id}
        ).fetchall()

        if not rows:
            logger.warning(f"Nema chunk-ova za dokument {document_id}")
            return {"status": "empty", "chunks": 0}

        text_content = "\n\n".join(row.content for row in rows if row.content)

        # Provjeri/kreiraj knowledge_source
        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE file_path = :fp"),
            {"fp": file_path}
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(text("""
                INSERT INTO knowledge_sources (source_type, name, file_path, status)
                VALUES ('pdf', :name, :fp, 'pending')
                RETURNING id
            """), {"name": source_name, "fp": file_path})
            db.commit()
            source_id = str(result.fetchone().id)

        # Indeksiraj
        chunks = ingest_source(db, source_id, "pdf", text_content, source_name)
        return {"status": "ok", "chunks": chunks, "source_id": source_id}
    except Exception as exc:
        logger.error(f"Greška pri indeksiranju dokumenta {source_name}: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@shared_task(bind=True, name="crawl_project_docs_task")
def crawl_project_docs_task(self):
    """
    Periodični task: skenira /docs/ i .md fajlove u projektu i indeksira ih.
    Pokreće se svakih 24h putem Celery Beat.
    """
    from pathlib import Path
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_markdown, ingest_source
    from sqlalchemy import text

    project_dirs = [
        Path("/app"),  # root (unutar container-a)
    ]

    md_files = []
    for d in project_dirs:
        if d.exists():
            md_files.extend(d.glob("*.md"))
            if (d / "docs").exists():
                md_files.extend((d / "docs").glob("**/*.md"))

    db = SessionLocal()
    indexed = 0
    try:
        for md_file in md_files:
            try:
                name = md_file.stem
                fp = str(md_file)

                existing = db.execute(
                    text("SELECT id FROM knowledge_sources WHERE file_path = :fp"),
                    {"fp": fp}
                ).fetchone()

                if existing:
                    source_id = str(existing.id)
                else:
                    result = db.execute(text("""
                        INSERT INTO knowledge_sources (source_type, name, file_path, status)
                        VALUES ('markdown', :name, :fp, 'pending') RETURNING id
                    """), {"name": name, "fp": fp})
                    db.commit()
                    source_id = str(result.fetchone().id)

                content = extract_text_from_markdown(fp)
                if content:
                    ingest_source(db, source_id, "markdown", content, name)
                    indexed += 1
            except Exception as e:
                logger.warning(f"Greška pri indeksiranju {md_file}: {e}")
                continue
    finally:
        db.close()

    logger.info(f"crawl_project_docs_task: {indexed}/{len(md_files)} fajlova indeksirano")
    return {"indexed": indexed, "total": len(md_files)}


@shared_task(bind=True, max_retries=2, name="crawl_url_task")
def crawl_url_task(self, url: str, source_name: Optional[str] = None, created_by: Optional[str] = None):
    """
    Preuzima web stranicu i indeksira je u knowledge base.
    Pokreće se na zahtev.
    """
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_url, ingest_source
    from sqlalchemy import text

    db = SessionLocal()
    try:
        text_content, title = extract_text_from_url(url)
        name = source_name or title or url

        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE url = :url"),
            {"url": url}
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(text("""
                INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
            """), {"name": name, "url": url, "uid": created_by})
            db.commit()
            source_id = str(result.fetchone().id)

        chunks = ingest_source(db, source_id, "url", text_content, name)
        return {"status": "ok", "chunks": chunks, "source_id": source_id, "title": title}
    except Exception as exc:
        logger.error(f"Greška pri crawl-u {url}: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@shared_task(bind=True, name="crawl_site_task")
def crawl_site_task(
    self,
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 50,
    source_name: Optional[str] = None,
    created_by: Optional[str] = None,
):
    """
    Rekurzivni web crawler — prati linkove unutar istog domena.
    
    Parametri:
    - start_url: početna URL adresa
    - max_depth: maksimalna dubina praćenja linkova (default 2)
    - max_pages: maksimalan broj stranica (default 50, sigurnosni limit)
    - source_name: naziv grupe izvora
    - created_by: UUID korisnika koji je pokrenuo

    Indeksira svaku pronađenu stranicu kao poseban knowledge_source.
    """
    from urllib.parse import urljoin, urlparse
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_url, ingest_source
    from sqlalchemy import text
    import httpx
    from bs4 import BeautifulSoup

    parsed_start = urlparse(start_url)
    base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
    indexed_count = 0
    total_chunks = 0

    db = SessionLocal()
    try:
        while queue and indexed_count < max_pages:
            url, depth = queue.pop(0)

            # Normalizuj URL (ukloni fragment)
            url = url.split("#")[0].rstrip("/")
            if url in visited:
                continue
            visited.add(url)

            logger.info(f"crawl_site_task: [{depth}/{max_depth}] {url}")

            # Preuzmi stranicu
            try:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; AI-Learning-Bot/1.0)"}
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code != 200:
                        continue
                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        continue
                    html = resp.text
            except Exception as e:
                logger.warning(f"Nije moguće preuzeti {url}: {e}")
                continue

            # Parsiraj sadržaj
            soup = BeautifulSoup(html, "lxml")
            title = soup.title.string.strip() if soup.title else url

            # Ukloni nepotrebne tagove
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()
            main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.body
            page_text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

            import re
            page_text = re.sub(r"\n{3,}", "\n\n", page_text).strip()

            if len(page_text) < 100:
                # Previše kratka stranica, preskoči
                continue

            # Sačuvaj kao knowledge_source
            name = f"{source_name or parsed_start.netloc} — {title}"[:200]
            existing = db.execute(
                text("SELECT id FROM knowledge_sources WHERE url = :url"), {"url": url}
            ).fetchone()

            if existing:
                source_id = str(existing.id)
            else:
                result = db.execute(text("""
                    INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                    VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
                """), {"name": name, "url": url, "uid": created_by})
                db.commit()
                source_id = str(result.fetchone().id)

            chunks = ingest_source(db, source_id, "url", page_text, name)
            total_chunks += chunks
            indexed_count += 1

            # Prati linkove ako nismo na max dubini
            if depth < max_depth:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                        continue
                    full_url = urljoin(url, href).split("#")[0].rstrip("/")
                    # Samo isti domen
                    if full_url.startswith(base_domain) and full_url not in visited:
                        queue.append((full_url, depth + 1))

        logger.info(f"crawl_site_task završen: {indexed_count} stranica, {total_chunks} chunk-ova")
        return {
            "status": "ok",
            "pages_indexed": indexed_count,
            "total_chunks": total_chunks,
            "start_url": start_url,
            "max_depth": max_depth,
        }
    except Exception as exc:
        logger.error(f"crawl_site_task greška: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
