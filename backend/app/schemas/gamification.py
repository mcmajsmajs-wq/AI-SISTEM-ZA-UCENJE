from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class BadgeResponse(BaseModel):
    slug: str
    name: str
    description: str
    icon_name: str
    xp_reward: int
    criteria_type: str
    criteria_threshold: int
    earned: bool
    earned_at: Optional[str] = None


class GamificationProfile(BaseModel):
    xp: int
    level: int
    total_xp_earned: int
    xp_current_in_level: int
    xp_needed_for_next: int
    progress_pct: float
    current_streak: int
    longest_streak: int
    badges: List[BadgeResponse]
    recent_badges: List[BadgeResponse]


class XpAwardResponse(BaseModel):
    xp_awarded: int
    total_xp: int
    level: int
    leveled_up: bool
    new_badges: Optional[List[BadgeResponse]] = None
