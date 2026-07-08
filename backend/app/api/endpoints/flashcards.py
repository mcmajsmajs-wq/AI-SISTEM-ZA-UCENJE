import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth import get_current_user
from app.db.models.user import User
from app.db.models.flashcard import Deck, Flashcard
from app.schemas.flashcard import (
    DeckCreate,
    DeckResponse,
    DeckDetailResponse,
    DeckListResponse,
    FlashcardCreate,
    FlashcardResponse,
    ReviewRequest,
    ReviewResponse,
    DueCardsResponse,
    GenerateFlashcardsRequest,
    GenerateFlashcardsResponse,
)
from app.services import flashcard as flashcard_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/decks", response_model=DeckResponse, status_code=201)
async def create_deck(
    data: DeckCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.source_document_id:
        from app.db.models.document import Document
        doc = db.query(Document).filter(
            Document.id == data.source_document_id,
            Document.user_id == current_user.id,
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

    deck = flashcard_service.create_deck(
        db=db,
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        source_document_id=data.source_document_id,
    )
    return DeckResponse(
        id=str(deck.id),
        user_id=str(deck.user_id),
        name=deck.name,
        description=deck.description,
        source_document_id=str(deck.source_document_id) if deck.source_document_id else None,
        total_cards=0,
        due_today=0,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


@router.get("/decks", response_model=DeckListResponse)
async def list_decks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = flashcard_service.list_decks(db=db, user_id=current_user.id)
    return DeckListResponse(items=items, total=len(items))


@router.get("/decks/{deck_id}", response_model=DeckDetailResponse)
async def get_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = flashcard_service.get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    cards = db.query(Flashcard).filter(Flashcard.deck_id == deck.id).order_by(Flashcard.order_index).all()
    total_cards = len(cards)

    from app.services.flashcard import get_due_cards
    due = get_due_cards(db, current_user.id, deck_id=deck_id, limit=9999)

    return DeckDetailResponse(
        id=str(deck.id),
        user_id=str(deck.user_id),
        name=deck.name,
        description=deck.description,
        source_document_id=str(deck.source_document_id) if deck.source_document_id else None,
        total_cards=total_cards,
        due_today=len(due),
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        flashcards=[
            FlashcardResponse(
                id=str(c.id),
                deck_id=str(c.deck_id),
                front=c.front,
                back=c.back,
                source_chunk_id=str(c.source_chunk_id) if c.source_chunk_id else None,
                order_index=c.order_index,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in cards
        ],
    )


@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = flashcard_service.delete_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Deck not found")
    return {"message": "Deck deleted"}


@router.post("/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201)
async def add_card(
    deck_id: str,
    data: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = flashcard_service.get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    card = flashcard_service.add_card(
        db=db,
        deck_id=deck.id,
        front=data.front,
        back=data.back,
        source_chunk_id=data.source_chunk_id,
        order_index=data.order_index,
    )
    return FlashcardResponse(
        id=str(card.id),
        deck_id=str(card.deck_id),
        front=card.front,
        back=card.back,
        source_chunk_id=str(card.source_chunk_id) if card.source_chunk_id else None,
        order_index=card.order_index,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.post("/decks/{deck_id}/cards/batch", status_code=201)
async def add_cards_batch(
    deck_id: str,
    cards: List[FlashcardCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = flashcard_service.get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    created = flashcard_service.add_cards_batch(
        db=db,
        deck_id=deck.id,
        cards=[{"front": c.front, "back": c.back, "source_chunk_id": c.source_chunk_id} for c in cards],
    )
    return {
        "message": f"{len(created)} cards created",
        "cards": [
            FlashcardResponse(
                id=str(c.id),
                deck_id=str(c.deck_id),
                front=c.front,
                back=c.back,
                source_chunk_id=str(c.source_chunk_id) if c.source_chunk_id else None,
                order_index=c.order_index,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in created
        ],
    }


@router.delete("/decks/{deck_id}/cards/{card_id}")
async def delete_card(
    deck_id: str,
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = flashcard_service.get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    card = db.query(Flashcard).filter(Flashcard.id == card_id, Flashcard.deck_id == deck.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
    return {"message": "Card deleted"}


@router.get("/flashcards/review", response_model=DueCardsResponse)
async def get_due_cards(
    deck_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cards = flashcard_service.get_due_cards(
        db=db, user_id=current_user.id, deck_id=deck_id, limit=limit
    )

    deck_name = None
    if deck_id:
        deck = flashcard_service.get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
        if deck:
            deck_name = deck.name

    return DueCardsResponse(
        items=cards,
        total=len(cards),
        deck_id=deck_id,
        deck_name=deck_name,
    )


@router.post("/flashcards/{card_id}/review", response_model=ReviewResponse)
async def review_card(
    card_id: str,
    data: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = flashcard_service.review_card(
            db=db, card_id=card_id, user_id=current_user.id, quality=data.quality
        )
        return ReviewResponse(**result)
    except ValueError:
        raise HTTPException(status_code=404, detail="Card not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/documents/{document_id}/generate-flashcards", response_model=GenerateFlashcardsResponse)
async def generate_flashcards(
    document_id: str,
    data: GenerateFlashcardsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.db.models.document import Document
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    logger.info(f"generate_flashcards: deck_id={data.deck_id}, mode={data.mode}, max_cards={data.max_cards}, deck_name={data.deck_name}")

    try:
        result = flashcard_service.generate_from_document(
            db=db,
            user_id=current_user.id,
            document_id=document_id,
            mode=data.mode,
            max_cards=data.max_cards,
            deck_name=data.deck_name,
            deck_id=data.deck_id,
        )
        return GenerateFlashcardsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Greška pri generisanju kartica: {str(e)[:200]}")
