# -*- coding: utf-8 -*-
"""
================================================================================
STUDY PLAN INTEGRATION TESTS
================================================================================
Testovi za lični plan učenja: kreiranje, ciljevi, stavke, napredak.

Pokretanje:
    pytest tests/integration/test_study_plan.py -v
================================================================================
"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.quiz import Quiz
from app.db.models.study_plan import StudyPlan, StudyPlanItem


# ────────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def test_quiz_ready(db: Session, test_document: Document) -> Quiz:
    """Kviz spreman za zakazivanje."""
    quiz = Quiz(
        document_id=test_document.id,
        user_id=test_document.user_id,
        title="Kviz za plan učenja",
        total_questions=5,
        passing_score=60,
        status="ready",
        created_at=datetime.utcnow(),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


@pytest.fixture
def test_plan(db: Session, test_user: User) -> StudyPlan:
    """Kreira test plan učenja."""
    plan = StudyPlan(
        user_id=test_user.id,
        daily_quiz_goal=2,
        weekly_quiz_goal=10,
        session_duration_min=30,
        study_days=[1, 2, 3, 4, 5],
        reminder_enabled=False,
        reminder_time=None,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture
def test_plan_item(
    db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
) -> StudyPlanItem:
    """Kreira test stavku plana (kviz zakazan za danas)."""
    item = StudyPlanItem(
        plan_id=test_plan.id,
        quiz_id=test_quiz_ready.id,
        scheduled_for=date.today(),
        is_completed=False,
        priority=1,
        created_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ────────────────────────────────────────────────────────────────────────────────
# Tests: StudyPlan model
# ────────────────────────────────────────────────────────────────────────────────


class TestStudyPlanModel:
    def test_create_plan(self, db: Session, test_user: User):
        """Kreiranje plana učenja."""
        plan = StudyPlan(
            user_id=test_user.id,
            daily_quiz_goal=3,
            weekly_quiz_goal=15,
            session_duration_min=45,
            study_days=[1, 2, 3, 4, 5],
            reminder_enabled=True,
            reminder_time="08:00",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        assert plan.id is not None
        assert plan.daily_quiz_goal == 3
        assert plan.weekly_quiz_goal == 15
        assert plan.reminder_enabled is True
        assert plan.reminder_time == "08:00"

    def test_plan_defaults(self, db: Session, test_user: User):
        """Podrazumevane vrednosti plana."""
        plan = StudyPlan(
            user_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        assert plan.daily_quiz_goal >= 1
        assert plan.weekly_quiz_goal >= 1
        assert plan.is_active is True

    def test_study_days_stored_as_list(self, test_plan: StudyPlan):
        """Study days se čuvaju kao lista celih brojeva."""
        assert isinstance(test_plan.study_days, list)
        assert all(isinstance(d, int) for d in test_plan.study_days)

    def test_one_plan_per_user(
        self, db: Session, test_plan: StudyPlan, test_user: User
    ):
        """Jedan korisnik može imati samo jedan plan (unique constraint)."""
        existing = db.query(StudyPlan).filter(StudyPlan.user_id == test_user.id).count()
        assert existing == 1


class TestStudyPlanItem:
    def test_create_item(
        self, db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
    ):
        """Kreiranje stavke plana."""
        today = date.today()
        item = StudyPlanItem(
            plan_id=test_plan.id,
            quiz_id=test_quiz_ready.id,
            scheduled_for=today,
            is_completed=False,
            priority=2,
            created_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        assert item.id is not None
        assert item.scheduled_for == today
        assert item.is_completed is False
        assert item.priority == 2

    def test_complete_item(self, db: Session, test_plan_item: StudyPlanItem):
        """Označavanje stavke kao završene."""
        assert test_plan_item.is_completed is False

        test_plan_item.is_completed = True
        test_plan_item.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(test_plan_item)

        assert test_plan_item.is_completed is True
        assert test_plan_item.completed_at is not None

    def test_future_item(
        self, db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
    ):
        """Zakazivanje kviza u budućnosti."""
        future = date.today() + timedelta(days=7)
        item = StudyPlanItem(
            plan_id=test_plan.id,
            quiz_id=test_quiz_ready.id,
            scheduled_for=future,
            is_completed=False,
            priority=1,
            created_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        assert item.scheduled_for > date.today()

    def test_item_priorities(
        self, db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
    ):
        """Prioriteti stavki: 1=normalan, 2=visok, 3=kritičan."""
        for priority in [1, 2, 3]:
            item = StudyPlanItem(
                plan_id=test_plan.id,
                quiz_id=test_quiz_ready.id,
                scheduled_for=date.today() + timedelta(days=priority),
                priority=priority,
                is_completed=False,
                created_at=datetime.utcnow(),
            )
            db.add(item)
        db.commit()

        items = (
            db.query(StudyPlanItem).filter(StudyPlanItem.plan_id == test_plan.id).all()
        )
        priorities = {i.priority for i in items}
        assert {1, 2, 3}.issubset(priorities)

    def test_quiz_relationship(
        self, test_plan_item: StudyPlanItem, test_quiz_ready: Quiz
    ):
        """Stavka je povezana sa kvizom (lazy joined)."""
        assert str(test_plan_item.quiz_id) == str(test_quiz_ready.id)

    def test_multiple_items_same_plan(
        self, db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
    ):
        """Plan može imati više stavki."""
        for i in range(5):
            item = StudyPlanItem(
                plan_id=test_plan.id,
                quiz_id=test_quiz_ready.id,
                scheduled_for=date.today() + timedelta(days=i),
                priority=1,
                is_completed=False,
                created_at=datetime.utcnow(),
            )
            db.add(item)
        db.commit()

        count = (
            db.query(StudyPlanItem)
            .filter(StudyPlanItem.plan_id == test_plan.id)
            .count()
        )
        assert count == 5


class TestStudyPlanProgress:
    def test_today_items_count(
        self, db: Session, test_plan: StudyPlan, test_quiz_ready: Quiz
    ):
        """Pravilno broji stavke za danas."""
        today = date.today()
        # Dodamo 2 stavke za danas
        for _ in range(2):
            item = StudyPlanItem(
                plan_id=test_plan.id,
                quiz_id=test_quiz_ready.id,
                scheduled_for=today,
                is_completed=False,
                priority=1,
                created_at=datetime.utcnow(),
            )
            db.add(item)
        db.commit()

        today_items = (
            db.query(StudyPlanItem)
            .filter(
                StudyPlanItem.plan_id == test_plan.id,
                StudyPlanItem.scheduled_for == today,
            )
            .count()
        )
        assert today_items == 2

    def test_completed_items_tracked(self, db: Session, test_plan_item: StudyPlanItem):
        """Završene stavke se pravilno prate."""
        test_plan_item.is_completed = True
        test_plan_item.completed_at = datetime.utcnow()
        db.commit()

        completed = (
            db.query(StudyPlanItem)
            .filter(
                StudyPlanItem.plan_id == test_plan_item.plan_id,
                StudyPlanItem.is_completed.is_(True),
            )
            .count()
        )
        assert completed >= 1

    def test_delete_item(self, db: Session, test_plan_item: StudyPlanItem):
        """Brisanje stavke iz plana."""
        item_id = test_plan_item.id
        db.delete(test_plan_item)
        db.commit()

        deleted = db.query(StudyPlanItem).filter(StudyPlanItem.id == item_id).first()
        assert deleted is None
