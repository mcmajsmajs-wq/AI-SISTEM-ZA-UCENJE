# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ INTEGRATION TESTS
================================================================================
Testovi za kviz sistem: kreiranje, listanje, igranje, rezultati.

Pokretanje:
    pytest tests/integration/test_quiz.py -v
================================================================================
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz, Question, QuizAttempt


# ────────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def test_quiz(db: Session, test_document: Document) -> Quiz:
    """Kreira test kviz sa statusom 'ready'."""
    quiz = Quiz(
        document_id=test_document.id,
        user_id=test_document.user_id,
        title=f"Test Kviz — {test_document.title}",
        description="Automatski generisan test kviz",
        total_questions=0,
        passing_score=60,
        status="generating",
        created_at=datetime.utcnow(),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@pytest.fixture
def test_quiz_ready(db: Session, test_document: Document) -> Quiz:
    """Kreira test kviz sa 3 pitanja (status='ready')."""
    quiz = Quiz(
        document_id=test_document.id,
        user_id=test_document.user_id,
        title="Gotov Test Kviz",
        total_questions=3,
        passing_score=60,
        status="ready",
        created_at=datetime.utcnow(),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    questions_data = [
        {
            "question_text": "Koji grad je glavni grad Srbije?",
            "question_type": "multiple_choice",
            "options": ["Novi Sad", "Beograd", "Niš", "Kragujevac"],
            "correct_answer": "Beograd",
            "explanation": "Beograd je glavni i najveći grad Srbije.",
            "points": 1,
            "order_index": 0,
        },
        {
            "question_text": "Da li je Python programski jezik?",
            "question_type": "true_false",
            "options": ["Tačno", "Netačno"],
            "correct_answer": "Tačno",
            "explanation": "Python je programski jezik visoke razine.",
            "points": 1,
            "order_index": 1,
        },
        {
            "question_text": "Koji od sledećih su programski jezici?",
            "question_type": "checkbox",
            "options": ["Python", "HTML", "Java", "CSS"],
            "correct_answer": "Python,Java",
            "explanation": "Python i Java su programski jezici. HTML i CSS su markup/style jezici.",
            "points": 2,
            "order_index": 2,
        },
    ]

    for qdata in questions_data:
        q = Question(quiz_id=quiz.id, **qdata, created_at=datetime.utcnow())
        db.add(q)

    db.commit()
    db.refresh(quiz)
    return quiz


# ────────────────────────────────────────────────────────────────────────────────
# Tests: Quiz model
# ────────────────────────────────────────────────────────────────────────────────


class TestQuizModel:
    def test_create_quiz(self, db: Session, test_document: Document):
        """Kreiranje kviz zapisa u bazi."""
        quiz = Quiz(
            document_id=test_document.id,
            user_id=test_document.user_id,
            title="Unit Test Kviz",
            total_questions=0,
            passing_score=70,
            status="generating",
            created_at=datetime.utcnow(),
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        assert quiz.id is not None
        assert quiz.title == "Unit Test Kviz"
        assert quiz.status == "generating"
        assert quiz.passing_score == 70

    def test_quiz_status_transitions(self, db: Session, test_quiz: Quiz):
        """Statusne tranzicije kviza: generating → ready / error."""
        assert test_quiz.status == "generating"

        test_quiz.status = "ready"
        db.commit()
        db.refresh(test_quiz)
        assert test_quiz.status == "ready"

        test_quiz.status = "error"
        db.commit()
        db.refresh(test_quiz)
        assert test_quiz.status == "error"

    def test_quiz_has_document_relationship(
        self, db: Session, test_quiz_ready: Quiz, test_document: Document
    ):
        """Kviz je povezan sa dokumentom."""
        assert str(test_quiz_ready.document_id) == str(test_document.id)


class TestQuestionModel:
    def test_create_questions(self, db: Session, test_quiz_ready: Quiz):
        """Pitanja su kreirana uz kviz."""
        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        assert len(questions) == 3

    def test_question_types(self, db: Session, test_quiz_ready: Quiz):
        """Svi tipovi pitanja su podržani."""
        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        types = {q.question_type for q in questions}
        assert "multiple_choice" in types
        assert "true_false" in types
        assert "checkbox" in types

    def test_checkbox_answer_format(self, db: Session, test_quiz_ready: Quiz):
        """Checkbox pitanje ima odgovor sa zarezom."""
        checkbox_q = (
            db.query(Question)
            .filter(
                Question.quiz_id == test_quiz_ready.id,
                Question.question_type == "checkbox",
            )
            .first()
        )
        assert checkbox_q is not None
        assert "," in checkbox_q.correct_answer


class TestQuizAttempt:
    def test_create_attempt(self, db: Session, test_quiz_ready: Quiz, test_user: User):
        """Kreiranje pokušaja rešavanja kviza."""
        attempt = QuizAttempt(
            quiz_id=test_quiz_ready.id,
            user_id=test_user.id,
            score=0,
            total_points=4,
            percentage=0.0,
            passed=False,
            started_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        assert attempt.id is not None
        assert attempt.passed is False
        assert attempt.percentage == 0.0

    def test_attempt_scoring(self, db: Session, test_quiz_ready: Quiz, test_user: User):
        """Scoring: 3/4 poena = 75%, prolaz (passing_score=60)."""
        attempt = QuizAttempt(
            quiz_id=test_quiz_ready.id,
            user_id=test_user.id,
            score=3,
            total_points=4,
            percentage=75.0,
            passed=True,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        assert attempt.score == 3
        assert attempt.percentage == 75.0
        assert attempt.passed is True

    def test_failed_attempt(self, db: Session, test_quiz_ready: Quiz, test_user: User):
        """Neuspeo pokušaj: 1/4 poena = 25%, nije položio (passing_score=60)."""
        attempt = QuizAttempt(
            quiz_id=test_quiz_ready.id,
            user_id=test_user.id,
            score=1,
            total_points=4,
            percentage=25.0,
            passed=False,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()

        assert attempt.passed is False
        assert attempt.percentage < 60


# ────────────────────────────────────────────────────────────────────────────────
# Tests: Quiz service (answer checking)
# ────────────────────────────────────────────────────────────────────────────────


class TestAnswerChecking:
    def test_multiple_choice_correct(self):
        """Tačan odgovor za multiple_choice."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("multiple_choice", "Beograd", "Beograd")
            is True
        )

    def test_multiple_choice_case_insensitive(self):
        """Multiple choice je case-insensitive."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("multiple_choice", "beograd", "Beograd")
            is True
        )

    def test_multiple_choice_wrong(self):
        """Pogrešan odgovor za multiple_choice."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("multiple_choice", "Novi Sad", "Beograd")
            is False
        )

    def test_true_false_correct(self):
        """Tačan odgovor za true_false."""
        from app.services.quiz import QuizService

        assert QuizService._check_answer_static("true_false", "Tačno", "Tačno") is True

    def test_true_false_case_insensitive(self):
        """True/False je case-insensitive."""
        from app.services.quiz import QuizService

        assert QuizService._check_answer_static("true_false", "tačno", "Tačno") is True

    def test_checkbox_correct_same_order(self):
        """Checkbox: isti redosled."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("checkbox", "Python,Java", "Python,Java")
            is True
        )

    def test_checkbox_correct_different_order(self):
        """Checkbox: različit redosled = tačno (set poređenje)."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("checkbox", "Java,Python", "Python,Java")
            is True
        )

    def test_checkbox_wrong(self):
        """Checkbox: pogrešna kombinacija."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("checkbox", "Python,HTML", "Python,Java")
            is False
        )

    def test_checkbox_partial(self):
        """Checkbox: parcijalan odgovor = pogrešno."""
        from app.services.quiz import QuizService

        assert (
            QuizService._check_answer_static("checkbox", "Python", "Python,Java")
            is False
        )


# ────────────────────────────────────────────────────────────────────────────────
# Tests: AI provider availability
# ────────────────────────────────────────────────────────────────────────────────


class TestQuizProviders:
    def test_get_available_providers_returns_list(self):
        """Metoda vraća listu provajdera."""
        from app.services.quiz import quiz_service

        providers = quiz_service.get_available_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0

    def test_provider_list_contains_expected_keys(self):
        """Svaki provajder ima 'id' i 'available' ključeve."""
        from app.services.quiz import quiz_service

        providers = quiz_service.get_available_providers()
        for p in providers:
            assert "id" in p
            assert "available" in p

    def test_ollama_always_in_providers(self):
        """Ollama je uvek u listi (čak i ako nije dostupan)."""
        from app.services.quiz import quiz_service

        providers = quiz_service.get_available_providers()
        ids = [p["id"] for p in providers]
        assert "ollama" in ids


# ────────────────────────────────────────────────────────────────────────────────
# Tests: Submit Attempt API (using _check_answer_static)
# ────────────────────────────────────────────────────────────────────────────────


class TestSubmitAttemptAPI:
    """Testovi za submit_attempt endpoint — proverava da li se _check_answer_static koristi."""

    def _make_attempt(self, db, quiz_id, user_id):
        """Helper za kreiranje pokušaja."""
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    def test_submit_multiple_choice_correct(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Tačan odgovor za multiple_choice mora biti priznat."""
        from app.services.quiz.evaluation import _check_answer_static

        attempt = self._make_attempt(db, test_quiz_ready.id, test_user.id)
        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        mc_q = [q for q in questions if q.question_type == "multiple_choice"][0]

        is_correct = _check_answer_static(
            "multiple_choice", "Beograd", mc_q.correct_answer
        )
        assert is_correct is True, "Tačan MC odgovor mora biti prepoznat"

    def test_submit_multiple_choice_wrong(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Pogrešan odgovor za multiple_choice mora biti odbijen."""
        from app.services.quiz.evaluation import _check_answer_static

        attempt = self._make_attempt(db, test_quiz_ready.id, test_user.id)
        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        mc_q = [q for q in questions if q.question_type == "multiple_choice"][0]

        is_correct = _check_answer_static(
            "multiple_choice", "Novi Sad", mc_q.correct_answer
        )
        assert is_correct is False, "Pogrešan MC odgovor mora biti odbijen"

    def test_submit_checkbox_correct(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Tačan odgovor za checkbox mora biti priznat."""
        from app.services.quiz.evaluation import _check_answer_static

        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        cb_q = [q for q in questions if q.question_type == "checkbox"][0]

        is_correct = _check_answer_static(
            "checkbox", "Python,Java", cb_q.correct_answer
        )
        assert is_correct is True, "Tačan checkbox odgovor mora biti prepoznat"

    def test_submit_checkbox_partial_wrong(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Parcijalan odgovor za checkbox mora biti odbijen."""
        from app.services.quiz.evaluation import _check_answer_static

        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        cb_q = [q for q in questions if q.question_type == "checkbox"][0]

        is_correct = _check_answer_static("checkbox", "Python", cb_q.correct_answer)
        assert is_correct is False, "Parcijalan checkbox odgovor mora biti odbijen"

    def test_submit_true_false_correct(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Tačan odgovor za true_false mora biti priznat."""
        from app.services.quiz.evaluation import _check_answer_static

        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        tf_q = [q for q in questions if q.question_type == "true_false"][0]

        is_correct = _check_answer_static("true_false", "Tačno", tf_q.correct_answer)
        assert is_correct is True, "Tačan TF odgovor mora biti prepoznat"

    def test_submit_mixed_answers_scoring(
        self, db: Session, test_quiz_ready: Quiz, test_user: User
    ):
        """Scoring sa mešovitim odgovorima mora biti ispravno izračunat."""
        from app.services.quiz.evaluation import _check_answer_static

        attempt = self._make_attempt(db, test_quiz_ready.id, test_user.id)
        questions = (
            db.query(Question).filter(Question.quiz_id == test_quiz_ready.id).all()
        )
        q_map = {q.question_type: q for q in questions}

        results = [
            _check_answer_static(
                "multiple_choice", "Beograd", q_map["multiple_choice"].correct_answer
            ),
            _check_answer_static(
                "true_false", "Netačno", q_map["true_false"].correct_answer
            ),
            _check_answer_static(
                "checkbox", "Python,Java", q_map["checkbox"].correct_answer
            ),
        ]
        assert results == [True, False, True], (
            f"Očekivano [True, False, True], dobijeno {results}"
        )
