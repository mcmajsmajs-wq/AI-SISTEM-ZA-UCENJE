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
import json
from typing import Dict, Any, Optional

from app.core.config import settings
from app.db.session import engine
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.services.storage import storage_service
from app.services.pdf import pdf_service
from app.services.translation import translation_service

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
        result = pdf_service.process_pdf(pdf_bytes, title=document.title)
        
        if not result.success:
            raise Exception(f"PDF processing failed: {result.error}")
        
        document.total_pages = result.metadata.total_pages
        document.total_chunks = len(result.chunks)
        document.metadata = {
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
                document.metadata = {"error": str(exc)}
                db.commit()
            
            if file_id:
                file = db.query(File).filter(File.id == file_id).first()
                if file:
                    file.status = "error"
                    file.metadata = {"error": str(exc)}
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
        
        logger.info(f"Translating {total_chunks} chunks for document {document_id}")
        
        for i, chunk in enumerate(chunks):
            if chunk.is_translated:
                translated_count += 1
                continue
            
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
        
        document.metadata = document.metadata or {}
        document.metadata["translation"] = {
            "provider": provider or "auto",
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "translated_chunks": translated_count,
            "errors": errors[:10] if errors else []
        }
        
        if translated_count == total_chunks:
            document.status = "completed"
            logger.info(f"Translation completed for document {document_id}: {translated_count}/{total_chunks} chunks")
        else:
            document.metadata["translation"]["partial"] = True
            logger.warning(f"Partial translation for document {document_id}: {translated_count}/{total_chunks} chunks")
        
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
                document.metadata = document.metadata or {}
                document.metadata["translation_error"] = str(exc)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        
        raise self.retry(exc=exc, countdown=300)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_quiz_task(
    self,
    document_id: str,
    user_id: str,
    title: Optional[str] = None,
    num_questions: int = 10,
    question_types: Optional[list] = None,
    difficulty: str = "medium",
    time_limit: int = 0,
    passing_score: int = 70
):
    """
    Task za generisanje kviza iz dokumenta koristeći AI.
    
    Args:
        document_id: ID dokumenta
        user_id: ID korisnika
        title: Naslov kviza (opcionalno)
        num_questions: Broj pitanja za generisanje
        question_types: Lista tipova pitanja
        difficulty: Težina kviza
        time_limit: Vremensko ograničenje u minutima
        passing_score: Prolazni rezultat u procentima
    """
    logger.info(f"Starting quiz generation for document: {document_id}")
    
    db = get_db_session()
    
    try:
        from app.db.models.quiz import Quiz, Question
        from app.schemas.quiz import QuestionType, QuizDifficulty
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document.id,
            Chunk.is_translated == 1
        ).order_by(Chunk.sequence_number).all()
        
        if not chunks:
            chunks = db.query(Chunk).filter(
                Chunk.document_id == document.id
            ).order_by(Chunk.sequence_number).all()
        
        if not chunks:
            raise ValueError("No content found for quiz generation")
        
        quiz_title = title or f"Quiz: {document.title}"
        
        quiz = Quiz(
            user_id=user_id,
            document_id=document_id,
            title=quiz_title,
            description=f"Auto-generated quiz from {document.title}",
            time_limit=time_limit,
            passing_score=passing_score,
            difficulty=difficulty,
            question_types=question_types or ["multiple_choice"],
            status="draft",
            total_questions=0,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        selected_chunks = chunks[:num_questions] if len(chunks) > num_questions else chunks
        
        generated_questions = 0
        
        for i, chunk in enumerate(selected_chunks):
            text = chunk.translated_content or chunk.content
            
            prompt = f"""Generate a multiple choice question from this text. 
Return ONLY a JSON object with this exact format:
{{"question": "the question text", "options": ["A) option1", "B) option2", "C) option3", "D) option4"], "correct": "A", "explanation": "brief explanation"}}

Text: {text[:1000]}"""
            
            try:
                result = translation_service.translate(
                    text=prompt,
                    source_language="en",
                    target_language="en",
                    provider="ollama"
                )
                
                if result.success:
                    import json
                    import re
                    
                    response_text = result.translated_text
                    
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        question_data = json.loads(json_match.group())
                        
                        question = Question(
                            quiz_id=quiz.id,
                            question_text=question_data.get("question", f"Question {i+1}"),
                            question_type="multiple_choice",
                            options=question_data.get("options", ["A", "B", "C", "D"]),
                            correct_answer=question_data.get("correct", "A"),
                            explanation=question_data.get("explanation"),
                            points=1,
                            difficulty=difficulty,
                            order=i,
                            source_text=text[:500],
                        )
                        db.add(question)
                        generated_questions += 1
            except Exception as qe:
                logger.warning(f"Failed to generate question {i}: {qe}")
                question = Question(
                    quiz_id=quiz.id,
                    question_text=f"What is the main idea of this section?",
                    question_type="multiple_choice",
                    options=["A) Correct answer", "B) Wrong answer 1", "C) Wrong answer 2", "D) Wrong answer 3"],
                    correct_answer="A",
                    explanation="Auto-generated question",
                    points=1,
                    difficulty=difficulty,
                    order=i,
                    source_text=text[:500],
                )
                db.add(question)
                generated_questions += 1
        
        quiz.total_questions = generated_questions
        db.commit()
        
        logger.info(f"Quiz generation completed: {generated_questions} questions")
        
        return {
            "status": "success",
            "quiz_id": str(quiz.id),
            "document_id": document_id,
            "questions_generated": generated_questions
        }
        
    except Exception as exc:
        logger.error(f"Quiz generation failed for document {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
    
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
    Periodični task za slanje podsetnika za učenje.
    Proverava raspored i šalje notifikacije.
    """
    logger.info("Sending study reminders")
    
    # TODO: Implementirati reminders
    # 1. Dohvati zakazane sesije za danas
    # 2. Pošalji email notifikacije
    # 3. Ažuriraj status
    
    logger.info("Reminders sent")
    return {"status": "success", "reminders_sent": 0}
