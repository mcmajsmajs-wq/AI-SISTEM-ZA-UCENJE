from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any


class FlashcardBase(BaseModel):
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    source_chunk_id: Optional[str] = None
    order_index: int = 0


class FlashcardCreate(FlashcardBase):
    pass


class FlashcardResponse(FlashcardBase):
    id: str
    deck_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeckBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_document_id: Optional[str] = None


class DeckCreate(DeckBase):
    pass


class DeckResponse(DeckBase):
    id: str
    user_id: str
    total_cards: int = 0
    due_today: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeckDetailResponse(DeckResponse):
    flashcards: List[FlashcardResponse] = []

    class Config:
        from_attributes = True


class DeckListResponse(BaseModel):
    items: List[DeckResponse]
    total: int


class ReviewRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5)


class ReviewResponse(BaseModel):
    card_id: str
    quality: int
    next_review_at: datetime
    interval: int
    ease_factor: float
    repetitions: int
    xp_awarded: int
    total_xp: int
    level: int
    leveled_up: bool
    new_badges: List[Any] = []


class DueCardsResponse(BaseModel):
    items: List[FlashcardResponse]
    total: int
    deck_id: Optional[str] = None
    deck_name: Optional[str] = None


class GenerateFlashcardsRequest(BaseModel):
    mode: str = Field("auto", pattern="^(auto|ai)$")
    deck_name: Optional[str] = None
    max_cards: int = Field(20, ge=1, le=100)
    deck_id: Optional[str] = None


class GenerateFlashcardsResponse(BaseModel):
    deck: DeckResponse
    cards_created: int
    mode: str
    provider_used: Optional[str] = None
