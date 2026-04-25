# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ API ENDPOINTS
================================================================================
API endpointi za kviz sistem.

Verzija: 1.0.0
================================================================================
"""

from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user
from app.services.quiz import QuizService
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizResponse,
    QuizWithQuestions,
    QuizListResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    AnswerCreate,
    AnswerResponse,
    QuizAttemptResponse,
    QuizAttemptWithAnswers,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    CompleteAttemptResponse,
    QuizStats,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuestionForAttempt,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kreira novi kviz."""
    quiz = QuizService.create_quiz(db, current_user.id, quiz_data)
    return quiz


@router.get("", response_model=QuizListResponse)
def list_quizzes(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista kvizove korisnika."""
    quizzes, total = QuizService.list_quizzes(
        db, current_user.id, page, size, status, difficulty
    )
    
    pages = ceil(total / size) if total > 0 else 1
    
    return QuizListResponse(
        quizzes=quizzes,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/stats", response_model=QuizStats)
def get_quiz_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dohvata statistiku kvizova."""
    return QuizService.get_quiz_stats(db, current_user.id)


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dohvata kviz po ID-u."""
    quiz = QuizService.get_quiz(db, quiz_id, current_user.id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.get("/{quiz_id}/questions", response_model=list[QuestionResponse])
def get_quiz_questions(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dohvata pitanja za kviz."""
    quiz = QuizService.get_quiz(db, quiz_id, current_user.id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return QuizService.get_questions_for_quiz(db, quiz_id)


@router.put("/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: UUID,
    quiz_data: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ažurira kviz."""
    quiz = QuizService.get_quiz(db, quiz_id, current_user.id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    updated_quiz = QuizService.update_quiz(db, quiz_id, quiz_data)
    return updated_quiz


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Briše kviz."""
    quiz = QuizService.get_quiz(db, quiz_id, current_user.id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    QuizService.delete_quiz(db, quiz_id)
    return None


@router.post("/{quiz_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    quiz_id: UUID,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dodaje pitanje u kviz."""
    quiz = QuizService.get_quiz(db, quiz_id, current_user.id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    question = QuizService.add_question(db, quiz_id, question_data)
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: UUID,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ažurira pitanje."""
    question = QuizService.update_question(db, question_id, question_data)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Briše pitanje."""
    success = QuizService.delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return None


@router.post("/{quiz_id}/attempts", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
def start_attempt(
    quiz_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Započinje novi pokušaj rešavanja kviza."""
    try:
        attempt = QuizService.start_attempt(db, quiz_id, current_user.id)
        return attempt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptWithAnswers)
def get_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dohvata pokušaj sa odgovorima."""
    attempt = QuizService.get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    from app.schemas.quiz import AnswerWithQuestion
    answers = []
    for answer in attempt.answers:
        answers.append(AnswerWithQuestion(
            id=answer.id,
            attempt_id=answer.attempt_id,
            question_id=answer.question_id,
            selected_answer=answer.selected_answer,
            selected_answers=answer.selected_answers,
            text_answer=answer.text_answer,
            is_correct=answer.is_correct,
            points_earned=answer.points_earned,
            time_spent=answer.time_spent,
            question=answer.question
        ))
    
    return QuizAttemptWithAnswers(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        score=attempt.score,
        total_points=attempt.total_points,
        percentage=attempt.percentage,
        passed=attempt.passed,
        correct_answers=attempt.correct_answers,
        wrong_answers=attempt.wrong_answers,
        skipped_answers=attempt.skipped_answers,
        time_spent=attempt.time_spent,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        answers=answers
    )


@router.post("/attempts/{attempt_id}/answers", response_model=SubmitAnswerResponse)
def submit_answer(
    attempt_id: UUID,
    answer_data: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Podnosi odgovor na pitanje."""
    attempt = QuizService.get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    try:
        answer = QuizService.submit_answer(
            db,
            attempt_id,
            answer_data.question_id,
            answer_data.selected_answer,
            answer_data.selected_answers,
            answer_data.text_answer,
            answer_data.time_spent
        )
        
        question = answer.question
        
        return SubmitAnswerResponse(
            is_correct=answer.is_correct,
            points_earned=answer.points_earned,
            correct_answer=question.correct_answer if not answer.is_correct else None,
            explanation=question.explanation
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/attempts/{attempt_id}/complete", response_model=CompleteAttemptResponse)
def complete_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Završava pokušaj."""
    attempt = QuizService.get_attempt(db, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    try:
        completed = QuizService.complete_attempt(db, attempt_id)
        
        return CompleteAttemptResponse(
            attempt=completed,
            correct_answers=completed.correct_answers,
            wrong_answers=completed.wrong_answers,
            time_spent=completed.time_spent,
            passed=completed.passed
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/attempts", response_model=list[QuizAttemptResponse])
def list_user_attempts(
    quiz_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista pokušaje korisnika."""
    return QuizService.get_user_attempts(db, current_user.id, quiz_id)


@router.post("/generate", response_model=QuizGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generiše kviz iz dokumenta koristeći AI."""
    from app.workers.tasks import generate_quiz_task
    
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    task = generate_quiz_task.delay(
        str(request.document_id),
        str(current_user.id),
        request.title,
        request.num_questions,
        [qt.value for qt in request.question_types] if request.question_types else None,
        request.difficulty.value,
        request.time_limit,
        request.passing_score
    )
    
    return QuizGenerateResponse(
        quiz_id=UUID("00000000-0000-0000-0000-000000000000"),
        status="processing",
        message=f"Quiz generation started. Task ID: {task.id}"
    )


from app.db.models.document import Document
