# -*- coding: utf-8 -*-
"""
===============================================================================
PDF GENERATOR ENDPOINTS
===============================================================================
Endpoint-i za generisanje PDF dokumenata.

Verzija: 1.0.0
===============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz, Question
from app.schemas.document import DocumentResponse
from app.core.config import settings
from app.services.auth import get_current_user
from app.services.pdf_generator import pdf_generator_service, QuizQuestionPDF

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/documents/{document_id}/export-pdf")
async def export_document_pdf(
    document_id: int,
    include_original: bool = Query(True, description="Ukljuci originalni tekst"),
    include_translated: bool = Query(True, description="Ukljuci prevedeni tekst"),
    include_metadata: bool = Query(True, description="Ukljuci metadata"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    EXPORT DOCUMENT TO PDF
    ================================================================================
    Eksportuje dokument u PDF format.
    ================================================================================
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != 'translated':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be translated before export"
        )
    
    chunks = db.query(Document).filter(
        Document.parent_document_id == document_id
    ).all()
    
    chunks_data = []
    for chunk in chunks:
        chunk_data = {}
        if include_original:
            chunk_data['original_text'] = chunk.original_text
        if include_translated:
            chunk_data['translated_text'] = chunk.translated_text
        chunk_data['heading'] = chunk.heading
        chunk_data['page_number'] = chunk.page_number
        chunks_data.append(chunk_data)
    
    if not chunks_data:
        chunks_data = [{
            'original_text': document.original_text,
            'translated_text': document.translated_text,
            'heading': document.title,
        }]
    
    try:
        pdf_bytes = pdf_generator_service.generate_document_pdf(
            title=document.title,
            chunks=chunks_data,
            show_original=include_original,
            show_translated=include_translated,
            include_metadata=include_metadata,
        )
        
        filename = f"{document.title.replace(' ', '_')}_{document_id}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation not available. Install reportlab."
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )


@router.get("/quizzes/{quiz_id}/export-pdf")
async def export_quiz_pdf(
    quiz_id: int,
    include_answers: bool = Query(False, description="Ukljuci odgovore"),
    include_explanations: bool = Query(True, description="Ukljuci objašnjenja"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    EXPORT QUIZ TO PDF
    ================================================================================
    Eksportuje kviz u PDF format.
    ================================================================================
    """
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    questions = db.query(Question).filter(
        Question.quiz_id == quiz_id
    ).order_by(Question.question_index).all()
    
    questions_pdf = []
    for q in questions:
        options = q.options if q.options else None
        questions_pdf.append(QuizQuestionPDF(
            question_number=q.question_index + 1,
            question_text=q.question_text,
            question_type=q.question_type,
            options=options,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            points=q.points,
        ))
    
    try:
        pdf_bytes = pdf_generator_service.generate_quiz_pdf(
            title=quiz.title,
            questions=questions_pdf,
            include_answers=include_answers,
            include_explanations=include_explanations,
            time_limit=quiz.time_limit,
            passing_score=quiz.passing_score,
        )
        
        filename = f"{quiz.title.replace(' ', '_')}_kviz_{quiz_id}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation not available. Install reportlab."
        )
    except Exception as e:
        logger.error(f"Failed to generate quiz PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )


@router.get("/documents/{document_id}/study-guide-pdf")
async def export_study_guide_pdf(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    EXPORT STUDY GUIDE TO PDF
    ================================================================================
    Eksportuje studijski vodič u PDF format.
    ================================================================================
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    chunks = db.query(Document).filter(
        Document.parent_document_id == document_id
    ).all()
    
    chunks_data = []
    for chunk in chunks:
        chunks_data.append({
            'original_text': chunk.original_text,
            'translated_text': chunk.translated_text,
            'heading': chunk.heading,
            'page_number': chunk.page_number,
        })
    
    if not chunks_data:
        chunks_data = [{
            'translated_text': document.translated_text,
            'heading': document.title,
        }]
    
    try:
        pdf_bytes = pdf_generator_service.generate_study_guide_pdf(
            title=f"Studijski vodič - {document.title}",
            document_title=document.title,
            chunks=chunks_data,
        )
        
        filename = f"Studijski_vodic_{document.title.replace(' ', '_')}_{document_id}.pdf"
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation not available. Install reportlab."
        )
    except Exception as e:
        logger.error(f"Failed to generate study guide PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF"
        )
