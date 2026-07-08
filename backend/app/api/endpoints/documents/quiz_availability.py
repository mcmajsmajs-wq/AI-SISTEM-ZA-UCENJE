import logging
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
from . import router

@router.get("/{document_id}/quiz-availability")
async def get_quiz_availability(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vraća dostupnost pitanja za kviz za dati dokument.

    Returns:
        - total: Ukupno generisanih pitanja za dokument
        - used: Broj pitanja koja su vec koriscena u kvizovima
        - available: Broj dostupnih pitanja za nove kvizove
    """
    from app.db.models.quiz import Quiz, Question

    doc_uuid = uuid.UUID(document_id)
    document = (
        db.query(Document)
        .filter(
            Document.id == doc_uuid,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    quizzes = db.query(Quiz).filter(Quiz.document_id == doc_uuid).all()

    total = 0
    used = 0

    for quiz in quizzes:
        questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
        total += len(questions)
        used += sum(1 for q in questions if q.used)

    available = total - used

    return {
        "total": total,
        "used": used,
        "available": available,
    }


