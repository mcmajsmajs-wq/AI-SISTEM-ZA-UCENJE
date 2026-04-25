# -*- coding: utf-8 -*-
"""
================================================================================
ANALYTICS TESTS
================================================================================
Testovi za analitiku: streak, aktivnost, performanse kvizova.

Pokretanje:
    pytest tests/integration/test_analytics.py -v
================================================================================
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz, QuizAttempt


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def _make_attempt(
    db: Session,
    quiz_id,
    user_id,
    score: int = 3,
    total_points: int = 5,
    passed: bool = True,
    days_ago: int = 0,
) -> QuizAttempt:
    """Helper: kreira QuizAttempt unazad N dana."""
    completed = datetime.utcnow() - timedelta(days=days_ago)
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        score=score,
        total_points=total_points,
        percentage=round(score / total_points * 100, 1),
        passed=passed,
        started_at=completed - timedelta(minutes=5),
        completed_at=completed,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@pytest.fixture
def test_quiz_ready(db: Session, test_document: Document) -> Quiz:
    quiz = Quiz(
        document_id=test_document.id,
        user_id=test_document.user_id,
        title="Analitika test kviz",
        total_questions=5,
        passing_score=60,
        status="ready",
        created_at=datetime.utcnow(),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


# ────────────────────────────────────────────────────────────────────────────────
# Tests: Streak calculation
# ────────────────────────────────────────────────────────────────────────────────

class TestStreakCalculation:
    def _calc_streak(self, attempts):
        """Replika _calc_streak logike iz analytics.py za testiranje."""
        from datetime import date, timedelta
        if not attempts:
            return 0
        # Grupiši po datumima
        completed_dates = {a.completed_at.date() for a in attempts if a.completed_at}
        if not completed_dates:
            return 0
        today = date.today()
        # Ako danas nema pokušaja, počni od juče
        check = today if today in completed_dates else today - timedelta(days=1)
        streak = 0
        for _ in range(365):
            if check in completed_dates:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
        return streak

    def test_empty_attempts_returns_zero(self):
        assert self._calc_streak([]) == 0

    def test_single_today_attempt_returns_one(self):
        class FakeAttempt:
            completed_at = datetime.utcnow()
        assert self._calc_streak([FakeAttempt()]) == 1

    def test_consecutive_days_streak(self):
        class FakeAttempt:
            def __init__(self, days_ago):
                self.completed_at = datetime.utcnow() - timedelta(days=days_ago)
        attempts = [FakeAttempt(0), FakeAttempt(1), FakeAttempt(2)]
        assert self._calc_streak(attempts) == 3

    def test_gap_breaks_streak(self):
        class FakeAttempt:
            def __init__(self, days_ago):
                self.completed_at = datetime.utcnow() - timedelta(days=days_ago)
        # Dan 0, 1, ali ne i 2 — streak=2
        attempts = [FakeAttempt(0), FakeAttempt(1), FakeAttempt(3)]
        assert self._calc_streak(attempts) == 2

    def test_only_old_attempts_zero_streak(self):
        class FakeAttempt:
            def __init__(self, days_ago):
                self.completed_at = datetime.utcnow() - timedelta(days=days_ago)
        # Nema danas ni juče → streak=0
        attempts = [FakeAttempt(5), FakeAttempt(6), FakeAttempt(7)]
        assert self._calc_streak(attempts) == 0


# ────────────────────────────────────────────────────────────────────────────────
# Tests: QuizAttempt aggregations
# ────────────────────────────────────────────────────────────────────────────────

class TestAttemptAggregations:
    def test_no_attempts_returns_zero(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        count = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id
        ).count()
        assert count == 0

    def test_multiple_attempts_counted(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        for i in range(5):
            _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=i)
        count = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id
        ).count()
        assert count == 5

    def test_average_score_calculation(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        """Prosečan skor: 60% + 80% + 100% = 80%."""
        scores = [
            (3, 5),  # 60%
            (4, 5),  # 80%
            (5, 5),  # 100%
        ]
        for score, total in scores:
            _make_attempt(
                db,
                test_quiz_ready.id,
                test_user.id,
                score=score,
                total_points=total,
                passed=(score / total >= 0.6),
            )

        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id
        ).all()
        avg = sum(a.percentage for a in attempts) / len(attempts)
        assert abs(avg - 80.0) < 0.5

    def test_passed_attempts_filter(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        """Filtriranje položenih pokušaja."""
        _make_attempt(db, test_quiz_ready.id, test_user.id, passed=True)
        _make_attempt(db, test_quiz_ready.id, test_user.id, score=1, total_points=5, passed=False)

        passed = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id,
            QuizAttempt.passed == True,
        ).count()
        failed = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id,
            QuizAttempt.passed == False,
        ).count()

        assert passed == 1
        assert failed == 1

    def test_activity_window_30_days(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        """Aktivnost u poslednjih 30 dana."""
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=5)
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=15)
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=40)  # Van 30d

        cutoff = datetime.utcnow() - timedelta(days=30)
        recent = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id,
            QuizAttempt.completed_at >= cutoff,
        ).count()
        assert recent == 2

    def test_daily_activity_grouping(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        """Grupiranje pokušaja po danima."""
        # 2 pokušaja danas, 1 juče
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=0)
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=0)
        _make_attempt(db, test_quiz_ready.id, test_user.id, days_ago=1)

        all_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id,
        ).all()

        by_date = {}
        for a in all_attempts:
            if a.completed_at:
                d = a.completed_at.date()
                by_date[d] = by_date.get(d, 0) + 1

        assert by_date[date.today()] == 2
        assert by_date[date.today() - timedelta(days=1)] == 1


# ────────────────────────────────────────────────────────────────────────────────
# Tests: Overview stats
# ────────────────────────────────────────────────────────────────────────────────

class TestOverviewStats:
    def test_total_documents(self, db: Session, test_user: User, test_document: Document):
        """Ukupan broj dokumenata za korisnika."""
        from app.db.models.document import Document as DocModel
        count = db.query(DocModel).filter(DocModel.user_id == test_user.id).count()
        assert count >= 1

    def test_quiz_pass_rate(self, db: Session, test_user: User, test_quiz_ready: Quiz):
        """Procenat položenih kvizova."""
        _make_attempt(db, test_quiz_ready.id, test_user.id, passed=True)
        _make_attempt(db, test_quiz_ready.id, test_user.id, passed=True)
        _make_attempt(db, test_quiz_ready.id, test_user.id, score=1, total_points=5, passed=False)

        total = db.query(QuizAttempt).filter(QuizAttempt.user_id == test_user.id).count()
        passed = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == test_user.id,
            QuizAttempt.passed == True,
        ).count()

        pass_rate = (passed / total * 100) if total > 0 else 0
        assert abs(pass_rate - 66.67) < 1.0
