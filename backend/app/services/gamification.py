import logging
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.user import User
from app.db.models.gamification import Badge, UserBadge

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────────
# XP Matematika
# ────────────────────────────────────────────────────────────────────────────────

def xp_for_quiz(score_pct: float) -> int:
    return max(10, int(50 + score_pct * 0.5))

def xp_for_quiz_pass() -> int:
    return 25

def xp_for_flashcard_review(quality: int) -> int:
    return quality * 5

def xp_for_streak_bonus(streak_days: int) -> int:
    return streak_days * 2

def level_from_xp(total_xp: int) -> int:
    return int((total_xp / 100) ** 0.5) + 1

def _level_threshold(level: int) -> int:
    return ((level - 1) ** 2) * 100

def xp_progress(total_xp: int) -> dict:
    level = level_from_xp(total_xp)
    current_level_xp = _level_threshold(level)
    next_level_xp = _level_threshold(level + 1)
    xp_in_level = total_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    progress_pct = min(100, round((xp_in_level / xp_needed) * 100, 1)) if xp_needed > 0 else 100
    return {
        "level": level,
        "xp_current_in_level": xp_in_level,
        "xp_needed_for_next": xp_needed,
        "progress_pct": progress_pct,
    }


# ────────────────────────────────────────────────────────────────────────────────
# Streak
# ────────────────────────────────────────────────────────────────────────────────

def update_streak(user: User, db: Session) -> dict:
    today = date.today()
    if user.last_activity_date is None:
        user.current_streak = 1
        user.longest_streak = 1
        user.last_activity_date = today
        db.commit()
        return {"streak": 1, "new_badges": []}

    last_date = user.last_activity_date
    if isinstance(last_date, datetime):
        last_date = last_date.date()

    if last_date == today:
        return {"streak": user.current_streak, "new_badges": []}

    diff = (today - last_date).days
    if diff == 1:
        user.current_streak += 1
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
    elif diff > 1:
        user.current_streak = 1

    user.last_activity_date = today
    db.commit()
    return {"streak": user.current_streak, "new_badges": check_streak_badges(user, db)}


# ────────────────────────────────────────────────────────────────────────────────
# XP Award
# ────────────────────────────────────────────────────────────────────────────────

def award_xp(user: User, amount: int, db: Session) -> dict:
    user.xp += amount
    user.total_xp_earned += amount
    new_level = level_from_xp(user.total_xp_earned)
    leveled_up = new_level > user.level
    user.level = new_level
    db.commit()
    new_badges = check_milestone_badges(user, db)
    return {
        "xp_awarded": amount,
        "total_xp": user.xp,
        "level": user.level,
        "leveled_up": leveled_up,
        "new_badges": new_badges,
    }


# ────────────────────────────────────────────────────────────────────────────────
# Badge System
# ────────────────────────────────────────────────────────────────────────────────

BADGE_CATALOG = [
    {"slug": "first_quiz", "criteria_type": "quizzes_completed", "criteria_threshold": 1},
    {"slug": "quiz_master", "criteria_type": "quizzes_completed", "criteria_threshold": 10},
    {"slug": "perfect_score", "criteria_type": "perfect_score", "criteria_threshold": 1},
    {"slug": "streak_7", "criteria_type": "streak_days", "criteria_threshold": 7},
    {"slug": "streak_30", "criteria_type": "streak_days", "criteria_threshold": 30},
    {"slug": "document_processor", "criteria_type": "documents_processed", "criteria_threshold": 5},
    {"slug": "ten_quizzes_pass", "criteria_type": "consecutive_passes", "criteria_threshold": 10},
    {"slug": "knowledge_seeker", "criteria_type": "knowledge_queries", "criteria_threshold": 25},
]


def has_badge(user_id, badge_slug, db):
    badge = db.query(Badge).filter(Badge.slug == badge_slug).first()
    if not badge:
        return True
    existing = db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.badge_id == badge.id,
    ).first()
    return existing is not None


def _award_badge(user_id, badge_slug, db):
    badge = db.query(Badge).filter(Badge.slug == badge_slug).first()
    if not badge:
        logger.warning(f"Badge {badge_slug} not found in catalog")
        return None
    existing = db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.badge_id == badge.id,
    ).first()
    if existing:
        return None
    ub = UserBadge(user_id=user_id, badge_id=badge.id)
    db.add(ub)
    db.commit()
    return {
        "slug": badge.slug,
        "name": badge.name,
        "description": badge.description,
        "icon_name": badge.icon_name,
        "xp_reward": badge.xp_reward,
    }


def check_streak_badges(user: User, db: Session) -> list:
    new_badges = []
    streak = user.current_streak
    for badge_def in BADGE_CATALOG:
        if badge_def["criteria_type"] != "streak_days":
            continue
        if streak >= badge_def["criteria_threshold"]:
            awarded = _award_badge(user.id, badge_def["slug"], db)
            if awarded:
                if awarded["xp_reward"]:
                    award_xp(user, awarded["xp_reward"], db)
                new_badges.append(awarded)
    return new_badges


def check_milestone_badges(user: User, db: Session) -> list:
    new_badges = []
    from app.db.models.quiz import QuizAttempt, Quiz

    total_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user.id
    ).count()

    perfect_count = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == user.id,
        QuizAttempt.percentage == 100.0,
    ).count()

    doc_count = db.query(
        func.count(func.distinct(Quiz.document_id))
    ).select_from(QuizAttempt).join(
        Quiz, QuizAttempt.quiz_id == Quiz.id
    ).filter(
        QuizAttempt.user_id == user.id
    ).scalar() or 0

    for badge_def in BADGE_CATALOG:
        ct = badge_def["criteria_type"]
        threshold = badge_def["criteria_threshold"]
        if ct == "streak_days":
            continue
        qualifies = False
        if ct == "quizzes_completed" and total_attempts >= threshold:
            qualifies = True
        elif ct == "perfect_score" and perfect_count >= threshold:
            qualifies = True
        elif ct == "documents_processed" and doc_count >= threshold:
            qualifies = True
        if qualifies:
            awarded = _award_badge(user.id, badge_def["slug"], db)
            if awarded:
                if awarded["xp_reward"]:
                    award_xp(user, awarded["xp_reward"], db)
                new_badges.append(awarded)

    return new_badges


def get_user_badges(user_id, db):
    earned = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    earned_ids = {ub.badge_id for ub in earned}

    all_badges = db.query(Badge).all()
    result = []
    for badge in all_badges:
        result.append({
            "slug": badge.slug,
            "name": badge.name,
            "description": badge.description,
            "icon_name": badge.icon_name,
            "xp_reward": badge.xp_reward,
            "criteria_type": badge.criteria_type,
            "criteria_threshold": badge.criteria_threshold,
            "earned": badge.id in earned_ids,
            "earned_at": next(
                (ub.earned_at.isoformat() for ub in earned if ub.badge_id == badge.id),
                None,
            ),
        })
    return result
