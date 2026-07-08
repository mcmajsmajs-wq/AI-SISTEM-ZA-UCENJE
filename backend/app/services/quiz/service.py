# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE - Main Service Class
================================================================================

Verzija: 1.0.0
================================================================================
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models.quiz import Quiz, Question
from app.db.models.document import Document, Chunk

from app.services.quiz.evaluation import (
    _check_answer_static as _eval_check_answer,
    _check_text_input_answer_static as _eval_check_text_input,
    _check_fill_blank_answer_static as _eval_check_fill_blank,
)

logger = logging.getLogger(__name__)


class QuizService:
    """
    Servis za generisanje i upravljanje kvizovima.
    Podržava Ollama, OpenAI, Claude sa fallback lancem.
    """

    @staticmethod
    def _check_answer_static(
        q_type: str, user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        return _eval_check_answer(q_type, user_answer, correct_answer, extra_data)

    @staticmethod
    def _check_text_input_answer_static(
        user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        return _eval_check_text_input(user_answer, correct_answer, extra_data)

    @staticmethod
    def _check_fill_blank_answer_static(
        user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        return _eval_check_fill_blank(user_answer, correct_answer, extra_data)

    def _check_text_input_answer(
        self,
        user_answer: str,
        correct_answer: str,
        exact_word: bool,
        case_insensitive: bool,
    ) -> bool:
        """Wrapper for calling static method as instance method."""
        return _eval_check_text_input(
            user_answer,
            correct_answer,
            {"exact_word": exact_word, "case_insensitive": case_insensitive},
        )

    def _check_fill_blank_answer(
        self,
        user_answer: str,
        correct_answer: str,
        exact_word: bool,
        case_insensitive: bool,
    ) -> bool:
        """Wrapper for calling static method as instance method."""
        return _eval_check_fill_blank(
            user_answer,
            correct_answer,
            {"exact_word": exact_word, "case_insensitive": case_insensitive},
        )

    @staticmethod
    def get_available_providers() -> dict:
        """Vraća listu svih dostupnih provajdera."""
        from app.services.quiz.clients import get_available_providers as gap

        return gap()

    def create_quiz_from_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
        num_questions: int = 5,
        time_limit: Optional[int] = None,
        passing_score: int = 60,
    ) -> Quiz:
        """Kreira Quiz zapis (status=generating), task generiše pitanja asinhrono."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Dokument nije pronađen: {document_id}")

        num_questions = max(1, num_questions)

        quiz = Quiz(
            document_id=document_id,
            user_id=user_id,
            title=f"Kviz: {document.title}",
            description=f"Automatski generisan kviz iz dokumenta '{document.title}'",
            time_limit=time_limit,
            passing_score=passing_score,
            status="generating",
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return quiz

    def generate_quiz_questions(
        self,
        db: Session,
        quiz_id: str,
        num_questions: int = 5,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
        source_content: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Thin wrapper - delegates to generation module."""
        from app.services.quiz.generation import generate_quiz_questions as _generate

        return _generate(
            db=db,
            quiz_id=quiz_id,
            num_questions=num_questions,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
            source_content=source_content,
        )

    def submit_quiz_answer(
        self,
        db: Session,
        quiz_id: str,
        question_id: str,
        selected_answer: str,
    ) -> Tuple[bool, int, str]:
        """Proverava odgovor i vraća poene."""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False, 0, "Pitanje nije pronađeno"

        is_correct = False
        correct = question.correct_answer

        if question.question_type in ("multiple_choice", "calculation"):
            is_correct = selected_answer.strip().lower() == correct.strip().lower()
        elif question.question_type == "true_false":
            is_correct = selected_answer.strip().lower() == correct.strip().lower()
        elif question.question_type == "checkbox":
            correct_parts = set(p.strip().lower() for p in correct.split(","))
            selected_parts = set(p.strip().lower() for p in selected_answer.split(","))
            is_correct = correct_parts == selected_parts
        elif question.question_type == "text_input":
            is_correct = self._check_text_input_answer(
                selected_answer, correct, question.exact_word, question.case_insensitive
            )
        elif question.question_type == "fill_blank":
            is_correct = self._check_fill_blank_answer(
                selected_answer, correct, question.exact_word, question.case_insensitive
            )

        points = question.points if is_correct else 0

        return True, points, "Tačno" if is_correct else "Netačno"

    def get_quiz(self, db: Session, quiz_id: str) -> Optional[Quiz]:
        """Dohvata kviz sa pitanjima."""
        return db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def get_quiz_questions(self, db: Session, quiz_id: str) -> List[Question]:
        """Dohvata sva pitanja za kviz."""
        return (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.order_index)
            .all()
        )


quiz_service = QuizService()


def _check_answer_static(
    q_type: str, user_answer: str, correct_answer: str, extra_data: dict = None
) -> bool:
    """
    Standalone function for checking quiz answers.

    Podržava sve tipove pitanja (ažurirano 2026-04-06):
    - multiple_choice, true_false, calculation: direktno poređenje
    - checkbox: skupovno poređenje
    - sequencing: poređenje niza indeksa
    - categorization: poređenje mapping-a
    - matching: poređenje parova
    - odd_one_out: direktno poređenje
    - estimation: tolerance-based
    - matrix: poređenje niza
    - hotspot: direktno poređenje

    Args:
        q_type: Tip pitanja
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        extra_data: Dodatni podaci

    Returns:
        bool: True ako je odgovor tačan
    """
    return _eval_check_answer(q_type, user_answer, correct_answer, extra_data)


def _check_text_input_answer(
    user_answer: str, correct_answer: str, exact_word: bool, case_insensitive: bool
) -> bool:
    """
    Proverava tekstualni odgovor za text_input tip pitanja.

    Args:
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        exact_word: Zahtevaj potpuno poklapanje reči
        case_insensitive: Ignoriši velika/mala slova

    Returns:
        bool: True ako je odgovor tačan
    """
    return _eval_check_text_input(
        user_answer,
        correct_answer,
        {"exact_word": exact_word, "case_insensitive": case_insensitive},
    )


def _check_fill_blank_answer(
    user_answer: str, correct_answer: str, exact_word: bool, case_insensitive: bool
) -> bool:
    """
    Proverava odgovor za fill_blank tip pitanja sa alternativnim rečima.

    Args:
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        exact_word: Zahtevaj potpuno poklapanje
        case_insensitive: Ignoriši velika/mala slova

    Returns:
        bool: True ako je odgovor tačan
    """
    return _eval_check_fill_blank(
        user_answer,
        correct_answer,
        {"exact_word": exact_word, "case_insensitive": case_insensitive},
    )
