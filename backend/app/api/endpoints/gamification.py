from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user
from app.services.gamification import (
    xp_progress,
    get_user_badges,
    update_streak,
    award_xp,
)
from app.schemas.gamification import GamificationProfile

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/profile", response_model=GamificationProfile)
async def get_gamification_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Profil korisnika sa XP, levelom, badge-ovima i streak-om."""
    progress = xp_progress(current_user.total_xp_earned)
    badges = get_user_badges(current_user.id, db)
    earned_badges = [b for b in badges if b["earned"]]
    earned_badges.sort(key=lambda b: b["earned_at"] or "", reverse=True)
    recent = earned_badges[:3]

    return GamificationProfile(
        xp=current_user.xp,
        level=current_user.level,
        total_xp_earned=current_user.total_xp_earned,
        xp_current_in_level=progress["xp_current_in_level"],
        xp_needed_for_next=progress["xp_needed_for_next"],
        progress_pct=progress["progress_pct"],
        current_streak=current_user.current_streak,
        longest_streak=current_user.longest_streak,
        badges=badges,
        recent_badges=recent,
    )


@router.get("/badges")
async def list_badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Svi badge-evi (otključani + zaključani)."""
    return {"badges": get_user_badges(current_user.id, db)}
