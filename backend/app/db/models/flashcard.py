from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Deck(Base):
    __tablename__ = "decks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    flashcards = relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
        order_by="Flashcard.order_index",
    )

    def __repr__(self):
        return f"<Deck(id={self.id}, name={self.name})>"


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deck_id = Column(
        UUID(as_uuid=True), ForeignKey("decks.id"), nullable=False, index=True
    )
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    source_chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=True
    )
    order_index = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    deck = relationship("Deck", back_populates="flashcards")
    review_logs = relationship(
        "ReviewLog", back_populates="flashcard", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Flashcard(id={self.id}, front={self.front[:50]})>"


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(
        UUID(as_uuid=True),
        ForeignKey("flashcards.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    quality = Column(Integer, nullable=False)  # 0-5 SM-2 quality rating
    ease_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=0)  # days
    repetitions = Column(Integer, default=0)
    next_review_at = Column(DateTime(timezone=True), nullable=False)

    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())

    flashcard = relationship("Flashcard", back_populates="review_logs")

    def __repr__(self):
        return f"<ReviewLog(card={self.card_id}, quality={self.quality})>"
