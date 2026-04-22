# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ ENDPOINTS
================================================================================
REST API za kviz sistem: generisanje, igranje, rezultati.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.db.models.quiz import Quiz, Question, QuizAttempt
from app.db.models.user import User
from app.schemas.quiz import (
    QuizCreate,
    QuizResponse,
    QuizWithQuestions,
    QuizListResponse,
    QuestionResponse,
    QuestionWithAnswer,
    AttemptSubmit,
    AttemptResponse,
    AttemptResult,
    AttemptListResponse,
    AnswerResult,
)
from app.services.auth import get_current_user
from app.workers.tasks import generate_quiz_task
from app.core.posthog import posthog_client

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================


def get_quiz_progress(quiz_id: str) -> tuple:
    """Get quiz progress from Redis. Returns (current, total).

    Koristi JSON format kompatibilan sa update_quiz_progress.
    """
    try:
        import json
        import redis as redis_client
        from app.core.config import settings

        r = redis_client.from_url(settings.REDIS_CONNECTION_URL, decode_responses=True)
        data = r.get(f"quiz_progress:{quiz_id}")
        if data:
            progress_data = json.loads(data)
            # progress je 0-100 procenat, konvertujemo u pitanja
            progress = progress_data.get("progress", 0)
            message = progress_data.get("message", "")

            # Ako poruka sadrzi "X / Y" format, parsiraj to
            import re

            match = re.search(r"(\d+)\s*/\s*(\d+)", message)
            if match:
                return int(match.group(1)), int(match.group(2))

            # Inače vrati progress procenat kao placeholder
            return progress, 100
    except Exception:
        pass
    return 0, 0


def quiz_to_response(quiz: Quiz) -> QuizResponse:
    # If quiz is still generating, get real-time progress from Redis
    current_progress, total_progress = 0, 0
    if quiz.status == "generating":
        current_progress, total_progress = get_quiz_progress(str(quiz.id))
        if current_progress > 0:
            actual_question_count = current_progress
        elif quiz.questions:
            actual_question_count = len(quiz.questions)
        else:
            actual_question_count = quiz.total_questions
    else:
        actual_question_count = quiz.total_questions
        current_progress = actual_question_count
        total_progress = actual_question_count

    return QuizResponse(
        id=str(quiz.id),
        document_id=str(quiz.document_id),
        user_id=str(quiz.user_id),
        title=quiz.title,
        description=quiz.description,
        total_questions=current_progress or actual_question_count,
        target_questions=total_progress
        or quiz.target_questions
        or actual_question_count,
        time_limit=quiz.time_limit,
        passing_score=quiz.passing_score,
        status=quiz.status,
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
    )


def question_to_response(q: Question, include_answer: bool = False):
    # Handle image URL - use permanent public URL
    image_url = q.image_url
    if image_url:
        # If URL starts with /minio/ or contains presigned params, get permanent URL
        if image_url.startswith("/minio/") or "X-Amz-" in image_url:
            try:
                from app.services.storage_cloud import CloudStorageService

                storage = CloudStorageService()
                # Extract the path from /minio/ai-learning-uploads/...
                # First remove query string if present
                url_without_query = image_url.split("?")[0]
                # Remove /minio/ prefix
                path = url_without_query.replace("/minio/", "")
                # path is now: ai-learning-uploads/3edf0f17-.../file.jpg
                # Remove bucket name prefix to get: 3edf0f17-.../file.jpg
                if "/" in path:
                    path = path.split("/", 1)[1]
                # Generate permanent public URL (no expiration)
                image_url = storage.get_public_url(path)
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(
                    f"Could not get public image URL: {e}"
                )

    if include_answer:
        return QuestionWithAnswer(
            id=str(q.id),
            quiz_id=str(q.quiz_id),
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options or [],
            points=q.points,
            order_index=q.order_index,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            image_url=image_url,
            image_caption=q.image_caption,
        )
    return QuestionResponse(
        id=str(q.id),
        quiz_id=str(q.quiz_id),
        question_text=q.question_text,
        question_type=q.question_type,
        options=q.options or [],
        points=q.points,
        order_index=q.order_index,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        image_url=image_url,
        image_caption=q.image_caption,
    )


def attempt_to_response(a: QuizAttempt) -> AttemptResponse:
    return AttemptResponse(
        id=str(a.id),
        quiz_id=str(a.quiz_id),
        user_id=str(a.user_id),
        score=a.score,
        total_points=a.total_points,
        percentage=a.percentage,
        passed=a.passed,
        started_at=a.started_at,
        completed_at=a.completed_at,
    )


# ============================================================
# QUIZ PROVIDERS (MORA BITI PRE quiz_id!)
# ============================================================


@router.get("/providers/list")
async def get_quiz_providers(
    current_user: User = Depends(get_current_user),
):
    """Lista dostupnih AI provajdera za generisanje kvizova."""
    from app.services.quiz import quiz_service

    return {"providers": quiz_service.get_available_providers()}


# ============================================================
# QUIZ CRUD
# ============================================================


@router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    data: QuizCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pokretanje generisanja kviza iz dokumenta.
    Vraća odmah (status=generating), generisanje teče u background-u.
    """
    from app.services.quiz import quiz_service
    from app.db.models.document import Document

    document = (
        db.query(Document)
        .filter(Document.id == data.document_id, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    # Allow quiz creation for completed documents, error documents with images,
    # or documents that have chunks (even if status is error)
    from app.db.models.quiz import QuizImage

    has_images = (
        db.query(QuizImage).filter(QuizImage.document_id == document.id).count() > 0
    )

    # Check if document has chunks with content (can be used for quiz)
    has_chunks = document.total_chunks and document.total_chunks > 0

    if document.status != "completed" and not has_images and not has_chunks:
        raise HTTPException(
            status_code=400,
            detail="Dokument mora biti kompletno obrađen pre generisanja kviza",
        )

    quiz = quiz_service.create_quiz_from_document(
        db=db,
        document_id=str(document.id),
        user_id=str(current_user.id),
        num_questions=data.num_questions,
        time_limit=data.time_limit,
        passing_score=data.passing_score,
    )
    quiz.shuffle_questions = data.shuffle_questions
    db.commit()
    db.refresh(quiz)

    # Pokrenuti Celery task — koristi user-ov AI provider i API ključ ako postoje
    user_provider = data.provider or current_user.ai_provider or "auto"
    user_provider = None if user_provider == "auto" else user_provider
    user_openai_key = current_user.ai_api_key_openai
    user_claude_key = current_user.ai_api_key_claude
    user_gemini_key = getattr(current_user, "ai_api_key_gemini", None)
    user_groq_key = getattr(current_user, "ai_api_key_groq", None)
    user_mistral_key = getattr(current_user, "ai_api_key_mistral", None)
    user_deepseek_key = getattr(current_user, "ai_api_key_deepseek", None)
    generate_quiz_task.delay(
        str(quiz.id),
        str(document.id),
        data.num_questions,
        user_provider,
        user_openai_key,
        user_claude_key,
        user_gemini_key,
        user_groq_key,
        user_mistral_key,
        user_deepseek_key,
    )

    logger.info(f"Kviz {quiz.id} kreiran, generisanje pokrenuto")

    posthog_client.capture(
        "quiz created",
        distinct_id=str(current_user.id),
        properties={
            "num_questions": data.num_questions,
            "ai_provider": user_provider or "auto",
            "shuffle_questions": data.shuffle_questions,
        },
    )

    return quiz_to_response(quiz)


@router.get("", response_model=QuizListResponse)
async def list_quizzes(
    skip: int = 0,
    limit: int = 20,
    document_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista svih kvizova korisnika, opcionalno filtrirano po dokumentu."""
    from sqlalchemy.orm import joinedload

    query = (
        db.query(Quiz)
        .options(joinedload(Quiz.questions))
        .filter(Quiz.user_id == current_user.id)
    )
    if document_id:
        query = query.filter(Quiz.document_id == document_id)

    total = query.count()
    quizzes = query.order_by(Quiz.created_at.desc()).offset(skip).limit(limit).all()

    return QuizListResponse(
        items=[quiz_to_response(q) for q in quizzes],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{quiz_id}", response_model=QuizWithQuestions)
async def get_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dohvata kviz sa svim pitanjima (bez tačnih odgovora).
    Ako je shuffle_questions=True, pitanja se vraćaju u nasumičnom redosledu.
    """
    import random

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    questions = list(quiz.questions)
    if quiz.shuffle_questions:
        random.shuffle(questions)

    return QuizWithQuestions(
        **quiz_to_response(quiz).model_dump(),
        questions=[question_to_response(q) for q in questions],
    )


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Briše kviz i vraća pitanja u pool za ponovnu upotrebu."""
    from app.db.models.quiz import Question

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    db.query(Question).filter(Question.quiz_id == quiz.id).update({"used": False})

    db.delete(quiz)
    db.commit()


@router.get("/{quiz_id}/status")
async def get_quiz_status(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Proverava status generisanja kviza."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")
    return {
        "quiz_id": str(quiz.id),
        "status": quiz.status,
        "total_questions": quiz.total_questions,
    }


# ============================================================
# ATTEMPTS — igranje kviza
# ============================================================


@router.post(
    "/{quiz_id}/attempts",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_attempt(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pokreće novi pokušaj rešavanja kviza."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")
    if quiz.status != "ready":
        raise HTTPException(status_code=400, detail="Kviz još nije spreman")

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    posthog_client.capture(
        "quiz attempt started",
        distinct_id=str(current_user.id),
        properties={"quiz_id": quiz_id},
    )

    return attempt_to_response(attempt)


@router.post("/{quiz_id}/attempts/{attempt_id}/submit", response_model=AttemptResult)
async def submit_attempt(
    quiz_id: str,
    attempt_id: str,
    data: AttemptSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submituje odgovore i vraća detaljan rezultat sa tačnim odgovorima.
    """
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Pokušaj nije pronađen")
    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="Pokušaj je već završen")

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    questions_map = {str(q.id): q for q in questions}

    total_score = 0
    total_points = 0
    answer_results = []

    for submitted_answer in data.answers:
        q = questions_map.get(submitted_answer.question_id)
        if not q:
            continue

        user_answer = submitted_answer.user_answer.strip()
        correct_answer = q.correct_answer.strip() if q.correct_answer else ""

        is_correct = False
        if q.question_type in ("multiple_choice", "calculation", "true_false"):
            is_correct = user_answer.lower() == correct_answer.lower()
        elif q.question_type == "checkbox":
            correct_parts = set(
                p.strip().lower() for p in correct_answer.split(",") if p.strip()
            )
            selected_parts = set(
                p.strip().lower() for p in user_answer.split(",") if p.strip()
            )
            is_correct = correct_parts == selected_parts

        points = q.points if is_correct else 0
        total_score += points
        total_points += q.points

        answer_results.append(
            AnswerResult(
                question_id=str(q.id),
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                points_earned=points,
                explanation=q.explanation or "",
            )
        )

    attempt.score = total_score
    attempt.total_points = total_points
    attempt.percentage = round(
        (total_score / total_points * 100) if total_points > 0 else 0, 1
    )
    attempt.passed = attempt.percentage >= (quiz.passing_score or 60)
    from datetime import datetime

    attempt.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)

    posthog_client.capture(
        "quiz attempt completed",
        distinct_id=str(current_user.id),
        properties={
            "quiz_id": quiz_id,
            "score": attempt.score,
            "total_points": attempt.total_points,
            "percentage": attempt.percentage,
            "passed": attempt.passed,
            "num_answers": len(answer_results),
        },
    )

    return AttemptResult(
        id=str(attempt.id),
        quiz_id=str(attempt.quiz_id),
        user_id=str(attempt.user_id),
        score=attempt.score,
        total_points=attempt.total_points,
        percentage=attempt.percentage,
        passed=attempt.passed,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        answers=answer_results,
    )


@router.get("/{quiz_id}/attempts", response_model=AttemptListResponse)
async def list_attempts(
    quiz_id: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista svih pokušaja korisnika za ovaj kviz."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    total = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == current_user.id)
        .count()
    )

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AttemptListResponse(
        items=[attempt_to_response(a) for a in attempts],
        total=total,
    )


@router.get("/{quiz_id}/attempts/latest/result", response_model=AttemptResult)
async def get_latest_attempt_result(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dohvata rezultat najskorrijeg završenog pokušaja za kviz."""
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at.isnot(None),
        )
        .order_by(QuizAttempt.completed_at.desc())
        .first()
    )
    if not attempt:
        raise HTTPException(
            status_code=404, detail="Nema završenih pokušaja za ovaj kviz"
        )
    # Reuse existing logic via redirect to the specific attempt
    questions_map = {
        str(q.id): q
        for q in db.query(Question).filter(Question.quiz_id == quiz_id).all()
    }
    answer_results = []
    for ans in attempt.answers:
        q = questions_map.get(str(ans.question_id))
        if q:
            answer_results.append(
                AnswerResult(
                    question_id=str(ans.question_id),
                    user_answer=ans.user_answer,
                    correct_answer=q.correct_answer,
                    is_correct=ans.is_correct,
                    points_earned=ans.points_earned,
                    explanation=q.explanation,
                )
            )
    return AttemptResult(
        **attempt_to_response(attempt).model_dump(),
        answers=answer_results,
    )


@router.get("/{quiz_id}/attempts/{attempt_id}/result", response_model=AttemptResult)
async def get_attempt_result(
    quiz_id: str,
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dohvata detaljan rezultat završenog pokušaja."""
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
        )
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Pokušaj nije pronađen")
    if not attempt.completed_at:
        raise HTTPException(status_code=400, detail="Pokušaj nije završen")

    questions_map = {
        str(q.id): q
        for q in db.query(Question).filter(Question.quiz_id == quiz_id).all()
    }
    answer_results = []
    for ans in attempt.answers:
        q = questions_map.get(str(ans.question_id))
        if q:
            answer_results.append(
                AnswerResult(
                    question_id=str(ans.question_id),
                    user_answer=ans.user_answer,
                    correct_answer=q.correct_answer,
                    is_correct=ans.is_correct,
                    points_earned=ans.points_earned,
                    explanation=q.explanation,
                )
            )

    return AttemptResult(
        **attempt_to_response(attempt).model_dump(),
        answers=answer_results,
    )


# ============================================================
# QUIZ QUESTION CHAT
# ============================================================


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class QuestionChatRequest(BaseModel):
    message: str
    question_id: str
    user_answer: str  # what the user selected
    history: List[ChatMessage] = []
    provider: Optional[str] = None  # provider override for this chat session


class QuestionChatResponse(BaseModel):
    reply: str
    question_id: str


@router.post("/{quiz_id}/chat", response_model=QuestionChatResponse)
async def quiz_question_chat(
    quiz_id: str,
    body: QuestionChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI chat za pojašnjenje posle potvrde odgovora.
    Korisnik može da pita AI za dodatna objašnjenja vezana za pitanje.
    Podržava i opšte chat poruke sa question_id="help" ili slično.
    """
    import uuid as uuid_module

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=404, detail="Kviz nije pronađen")

    is_general_help = False
    try:
        uuid_module.UUID(body.question_id)
    except (ValueError, AttributeError):
        is_general_help = True

    if is_general_help:
        system_prompt = f"""Ti si pedagoški AI tutor koji pomaže studentu da razume gradivo iz kviza.

Kviz: {quiz.title}
Broj pitanja: {quiz.total_questions}

Korisnik traži pomoć ili objašnjenje. Odgovori jasno, pedagoški i motivišuće.
Fokusiraj se na temu kviza i pomozi korisniku da razume gradivo.
Budi koncizan ali potpun. Odgovaraj na srpskom jeziku."""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in body.history[-8:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": body.message})

    reply = await _call_chat_ai(messages, current_user, provider_override=body.provider)

    try:
        _save_chat_to_knowledge(db, current_user, question, body, reply)
    except Exception as kb_err:
        logger.warning(f"Failed to save chat to knowledge base: {kb_err}")

    return QuestionChatResponse(reply=reply, question_id=body.question_id)


async def _call_chat_ai(
    messages: list, user: User, provider_override: str = None
) -> str:
    """Poziva AI za chat, po user.ai_provider podešavanju."""
    from app.core.config import settings
    import httpx

    provider = provider_override or getattr(user, "ai_provider", "auto") or "auto"
    user_openai_key = getattr(user, "ai_api_key_openai", None)
    user_gemini_key = getattr(user, "ai_api_key_gemini", None)
    user_groq_key = getattr(user, "ai_api_key_groq", None)
    user_mistral_key = getattr(user, "ai_api_key_mistral", None)
    user_claude_key = getattr(user, "ai_api_key_claude", None)

    providers_to_try: list
    if provider == "auto":
        # Try providers in order of availability — prefer configured ones
        auto_order = ["gemini", "groq", "mistral", "openai", "claude", "ollama"]
        providers_to_try = []
        key_map = {
            "gemini": user_gemini_key or getattr(settings, "GEMINI_API_KEY", ""),
            "groq": user_groq_key or getattr(settings, "GROQ_API_KEY", ""),
            "mistral": user_mistral_key or getattr(settings, "MISTRAL_API_KEY", ""),
            "openai": user_openai_key or getattr(settings, "OPENAI_API_KEY", ""),
            "claude": user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", ""),
            "ollama": True,  # always try ollama
        }
        for p in auto_order:
            if key_map.get(p):
                providers_to_try.append(p)
        if not providers_to_try:
            providers_to_try = ["ollama"]
    else:
        providers_to_try = [provider]

    async def _openai_compat(base_url: str, api_key: str, model: str) -> str | None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 600,
                    "temperature": 0.7,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            logger.warning(
                f"[chat] {base_url} model={model} → {resp.status_code}: {resp.text[:300]}"
            )
        return None

    for p in providers_to_try:
        try:
            if p == "ollama":
                ollama_host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
                ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{ollama_host}/api/chat",
                        json={
                            "model": ollama_model,
                            "messages": messages,
                            "stream": False,
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json().get("message", {}).get("content", "").strip()
            elif p == "openai":
                api_key = user_openai_key or getattr(settings, "OPENAI_API_KEY", "")
                if not api_key:
                    continue
                result = await _openai_compat(
                    "https://api.openai.com/v1",
                    api_key,
                    getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                )
                if result:
                    return result
            elif p == "gemini":
                api_key = user_gemini_key or getattr(settings, "GEMINI_API_KEY", "")
                if not api_key:
                    continue
                # Try current Gemini model names for OpenAI-compat endpoint
                for model in [
                    "gemini-2.0-flash",
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-flash",
                ]:
                    result = await _openai_compat(
                        "https://generativelanguage.googleapis.com/v1beta/openai",
                        api_key,
                        model,
                    )
                    if result:
                        return result
            elif p == "groq":
                api_key = user_groq_key or getattr(settings, "GROQ_API_KEY", "")
                if not api_key:
                    continue
                for model in [
                    "llama-3.1-8b-instant",
                    "llama3-8b-8192",
                    "mixtral-8x7b-32768",
                ]:
                    result = await _openai_compat(
                        "https://api.groq.com/openai/v1", api_key, model
                    )
                    if result:
                        return result
            elif p == "mistral":
                api_key = user_mistral_key or getattr(settings, "MISTRAL_API_KEY", "")
                if not api_key:
                    continue
                result = await _openai_compat(
                    "https://api.mistral.ai/v1", api_key, "mistral-small-latest"
                )
                if result:
                    return result
            elif p == "claude":
                api_key = user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", "")
                if not api_key:
                    continue
                async with httpx.AsyncClient(timeout=60.0) as client:
                    sys_msg = next(
                        (m["content"] for m in messages if m["role"] == "system"), ""
                    )
                    user_msgs = [m for m in messages if m["role"] != "system"]
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 600,
                            "system": sys_msg,
                            "messages": user_msgs,
                        },
                    )
                    if resp.status_code == 200:
                        return resp.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Chat AI provider {p} failed: {e}")
            continue

    return "Izvini, trenutno ne mogu da odgovorim. Proveri AI podešavanja ili pokušaj ponovo."


def _save_chat_to_knowledge(db, user, question, body, reply: str):
    """Čuva kviz chat razmenu u bazu znanja za budući RAG retrieval."""

    content = f"""Kviz pitanje: {question.question_text}
Tačan odgovor: {question.correct_answer}
Korisnikovo pitanje: {body.message}
AI odgovor: {reply}"""

    # Find or create "Quiz Chat" knowledge source for this user
    source_name = f"Quiz Chat — {user.email}"
    source_row = db.execute(
        text(
            "SELECT id, total_chunks FROM knowledge_sources WHERE created_by = :uid AND name = :name LIMIT 1"
        ),
        {"uid": str(user.id), "name": source_name},
    ).fetchone()

    if not source_row:
        source_row = db.execute(
            text("""INSERT INTO knowledge_sources (source_type, name, status, created_by)
                    VALUES ('log', :name, 'indexed', :uid) RETURNING id, total_chunks"""),
            {"name": source_name, "uid": str(user.id)},
        ).fetchone()
        db.commit()

    source_id = source_row[0]
    chunk_index = source_row[1] or 0

    # Generate embedding for the content
    try:
        from app.services.rag import embed_text

        embedding = embed_text(content)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    except Exception:
        embedding_str = None

    db.execute(
        text("""INSERT INTO knowledge_chunks (source_id, content, embedding, chunk_index, metadata)
                VALUES (:sid, :content, :emb::vector, :idx, :meta::jsonb)"""),
        {
            "sid": str(source_id),
            "content": content,
            "emb": embedding_str,
            "idx": chunk_index,
            "meta": '{"source": "quiz_chat"}',
        },
    )
    db.execute(
        text(
            "UPDATE knowledge_sources SET total_chunks = total_chunks + 1, updated_at = now() WHERE id = :sid"
        ),
        {"sid": str(source_id)},
    )
    db.commit()
    logger.info(f"Saved quiz chat to knowledge base for user {user.email}")
