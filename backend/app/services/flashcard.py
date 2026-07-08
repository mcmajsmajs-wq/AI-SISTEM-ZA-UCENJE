import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.flashcard import Deck, Flashcard, ReviewLog
from app.db.models.document import Chunk
from app.db.models.user import User
from app.services.gamification import award_xp, xp_for_flashcard_review, update_streak

logger = logging.getLogger(__name__)


def sm2_calculate(
    quality: int, repetitions: int, ease_factor: float, interval: int
) -> dict:
    if quality < 3:
        return {
            "repetitions": 0,
            "interval": 1,
            "ease_factor": ease_factor,
            "next_review_at": datetime.now(timezone.utc) + timedelta(days=1),
        }

    new_ef = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = round(interval * new_ef)

    return {
        "repetitions": repetitions + 1,
        "interval": new_interval,
        "ease_factor": round(new_ef, 2),
        "next_review_at": datetime.now(timezone.utc) + timedelta(days=new_interval),
    }


def create_deck(
    db: Session,
    user_id,
    name: str,
    description: Optional[str] = None,
    source_document_id=None,
) -> Deck:
    deck = Deck(
        user_id=user_id,
        name=name,
        description=description,
        source_document_id=source_document_id,
    )
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return deck


def get_deck(db: Session, deck_id, user_id) -> Optional[Deck]:
    return (
        db.query(Deck)
        .filter(Deck.id == deck_id, Deck.user_id == user_id)
        .first()
    )


def list_decks(db: Session, user_id) -> List[dict]:
    now = datetime.now(timezone.utc)
    decks = db.query(Deck).filter(Deck.user_id == user_id).order_by(Deck.created_at.desc()).all()
    result = []
    for deck in decks:
        total_cards = db.query(Flashcard).filter(Flashcard.deck_id == deck.id).count()
        due_today = (
            db.query(ReviewLog)
            .join(Flashcard, ReviewLog.card_id == Flashcard.id)
            .filter(
                Flashcard.deck_id == deck.id,
                ReviewLog.user_id == user_id,
                ReviewLog.next_review_at <= now,
            )
            .count()
        )
        cards_without_review = (
            db.query(Flashcard)
            .filter(
                Flashcard.deck_id == deck.id,
                ~Flashcard.id.in_(
                    db.query(ReviewLog.card_id).filter(
                        ReviewLog.user_id == user_id,
                        ReviewLog.next_review_at <= now,
                    )
                ),
            )
            .count()
        )
        # If never reviewed, all cards are due
        has_any_review = (
            db.query(ReviewLog)
            .join(Flashcard)
            .filter(Flashcard.deck_id == deck.id, ReviewLog.user_id == user_id)
            .first()
        )
        if not has_any_review:
            due_today = total_cards
        else:
            due_today = due_today + cards_without_review

        result.append({
            "id": str(deck.id),
            "user_id": str(deck.user_id),
            "name": deck.name,
            "description": deck.description,
            "source_document_id": str(deck.source_document_id) if deck.source_document_id else None,
            "total_cards": total_cards,
            "due_today": due_today,
            "created_at": deck.created_at,
            "updated_at": deck.updated_at,
        })
    return result


def delete_deck(db: Session, deck_id, user_id) -> bool:
    deck = get_deck(db, deck_id, user_id)
    if not deck:
        return False
    db.delete(deck)
    db.commit()
    return True


def add_card(
    db: Session,
    deck_id,
    front: str,
    back: str,
    source_chunk_id=None,
    order_index: Optional[int] = None,
) -> Flashcard:
    if order_index is None:
        max_idx = (
            db.query(func.max(Flashcard.order_index))
            .filter(Flashcard.deck_id == deck_id)
            .scalar()
        )
        order_index = (max_idx or 0) + 1
    card = Flashcard(
        deck_id=deck_id,
        front=front,
        back=back,
        source_chunk_id=source_chunk_id,
        order_index=order_index,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def add_cards_batch(db: Session, deck_id, cards: list) -> List[Flashcard]:
    created = []
    for i, card_data in enumerate(cards):
        card = Flashcard(
            deck_id=deck_id,
            front=card_data["front"],
            back=card_data["back"],
            source_chunk_id=card_data.get("source_chunk_id"),
            order_index=i,
        )
        db.add(card)
        created.append(card)
    db.commit()
    for card in created:
        db.refresh(card)
    return created


def get_due_cards(
    db: Session, user_id, deck_id: Optional[str] = None, limit: int = 20
) -> List[dict]:
    now = datetime.now(timezone.utc)
    query = (
        db.query(Flashcard)
        .join(Deck, Flashcard.deck_id == Deck.id)
        .filter(Deck.user_id == user_id)
    )

    if deck_id:
        query = query.filter(Flashcard.deck_id == deck_id)

    # Cards that have never been reviewed
    never_reviewed = query.filter(
        ~Flashcard.id.in_(
            db.query(ReviewLog.card_id).filter(ReviewLog.user_id == user_id)
        )
    ).all()

    # Cards due for review
    due = (
        query.filter(
            Flashcard.id.in_(
                db.query(ReviewLog.card_id)
                .filter(
                    ReviewLog.user_id == user_id,
                    ReviewLog.next_review_at <= now,
                )
            )
        )
        .order_by(
            db.query(ReviewLog.next_review_at)
            .filter(ReviewLog.card_id == Flashcard.id, ReviewLog.user_id == user_id)
            .order_by(ReviewLog.next_review_at.desc())
            .limit(1)
            .correlate(Flashcard)
            .scalar_subquery()
            .asc()
        )
        .limit(limit)
        .all()
    )

    result = never_reviewed + due
    result = result[:limit]

    return [
        {
            "id": str(card.id),
            "deck_id": str(card.deck_id),
            "front": card.front,
            "back": card.back,
            "source_chunk_id": str(card.source_chunk_id) if card.source_chunk_id else None,
            "order_index": card.order_index,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
        }
        for card in result
    ]


def review_card(db: Session, card_id, user_id, quality: int) -> dict:
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        raise ValueError("Card not found")

    deck = db.query(Deck).filter(Deck.id == card.deck_id, Deck.user_id == user_id).first()
    if not deck:
        raise PermissionError("Card does not belong to user")

    last_review = (
        db.query(ReviewLog)
        .filter(ReviewLog.card_id == card_id, ReviewLog.user_id == user_id)
        .order_by(ReviewLog.reviewed_at.desc())
        .first()
    )

    prev_repetitions = last_review.repetitions if last_review else 0
    prev_ef = last_review.ease_factor if last_review else 2.5
    prev_interval = last_review.interval if last_review else 0

    sm2_result = sm2_calculate(quality, prev_repetitions, prev_ef, prev_interval)

    review_log = ReviewLog(
        card_id=card_id,
        user_id=user_id,
        quality=quality,
        ease_factor=sm2_result["ease_factor"],
        interval=sm2_result["interval"],
        repetitions=sm2_result["repetitions"],
        next_review_at=sm2_result["next_review_at"],
    )
    db.add(review_log)

    user = db.query(User).filter(User.id == user_id).first()
    xp_amount = xp_for_flashcard_review(quality)
    xp_result = award_xp(user, xp_amount, db)
    streak_result = update_streak(user, db)

    db.commit()

    return {
        "card_id": str(card_id),
        "quality": quality,
        "next_review_at": sm2_result["next_review_at"],
        "interval": sm2_result["interval"],
        "ease_factor": sm2_result["ease_factor"],
        "repetitions": sm2_result["repetitions"],
        "xp_awarded": xp_result["xp_awarded"],
        "total_xp": xp_result["total_xp"],
        "level": xp_result["level"],
        "leveled_up": xp_result["leveled_up"],
        "new_badges": xp_result["new_badges"] + streak_result.get("new_badges", []),
    }


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, handling Unicode punctuation."""
    parts = re.split(r"(?<=[.!?…])\s+", text)
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result


def _extract_keywords_auto(chunks: List[Chunk], max_cards: int = 20) -> List[dict]:
    """Auto mode: extract key terms and their context as definition cards."""
    cards = []
    seen_terms = set()

    for chunk in chunks:
        if not chunk.content:
            continue
        text = chunk.content
        chunk_id = str(chunk.id)

        bold_terms = re.findall(r"\*\*(.+?)\*\*", text)
        italic_terms = re.findall(r"\*(.+?)\*", text)
        quoted_terms = re.findall(r'"([^"]+)"', text)

        for term in bold_terms + italic_terms + quoted_terms:
            term_clean = term.strip().lower()
            if term_clean in seen_terms or len(term_clean) < 3:
                continue
            if len(cards) >= max_cards:
                break

            sentences = _split_sentences(text)
            context = ""
            for sent in sentences:
                if term.lower() in sent.lower():
                    context = sent.strip()
                    break
            if not context:
                context = text[:200]

            seen_terms.add(term_clean)
            trimmed = context[:600].rsplit(".", 1)[0] if len(context) > 600 else context
            cards.append({
                "front": term.strip(),
                "back": trimmed[:600],
                "source_chunk_id": chunk_id,
            })

        if len(cards) >= max_cards:
            break

    if not cards:
        sentences = []
        for chunk in chunks:
            if chunk.content:
                sentences.extend(_split_sentences(chunk.content))
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 50]
        for sent in meaningful[:max_cards]:
            comma_idx = sent.find(",")
            if 30 < comma_idx < 200:
                front = sent[:comma_idx].strip()
                back = sent[comma_idx + 1:].strip()
            else:
                words = sent.split()
                mid = max(4, min(len(words) // 2, 10))
                front = " ".join(words[:mid])
                back = " ".join(words[mid:])
            trimmed_back = back[:600].rsplit(". ", 1)[0] if len(back) > 600 and ". " in back[:600] else back[:600]
            cards.append({
                "front": front[:250],
                "back": trimmed_back[:600],
                "source_chunk_id": str(chunks[0].id) if chunks else None,
            })

    return cards


def generate_from_document(
    db: Session, user_id, document_id, mode: str = "auto", max_cards: int = 20, deck_name: Optional[str] = None, deck_id: Optional[str] = None
) -> dict:
    from app.db.models.document import Document

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError("Document not found")

    all_chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.sequence_number)
        .all()
    )
    if not all_chunks:
        raise ValueError("Document has no chunks")

    from app.services.quiz.helpers.selection import is_chunk_quality

    used_provider = None
    chunks = []
    for c in all_chunks:
        if is_chunk_quality(c.content or ""):
            chunks.append(c)
        if len(chunks) >= 50:
            break

    if not chunks:
        chunks = all_chunks

    logger.info(f"Collected {len(chunks)} content chunks from {len(all_chunks)} total")

    if mode == "ai":
        from app.services.quiz.clients import get_available_providers
        available = get_available_providers()
        ai_providers = [
            p["id"] for p in available
            if p.get("available") and p.get("id") in ("openai", "claude", "groq", "gemini", "mistral")
        ]

        if not ai_providers:
            mode = "auto"
            logger.info("No AI provider available, falling back to auto mode")

    if mode == "ai":
        last_error = None
        used_provider = None
        for provider in ai_providers:
            try:
                cards, used_provider = _generate_with_ai(chunks, provider, user_id, db, max_cards)
                last_error = None
                break
            except Exception as e:
                last_error = e
                logger.warning(f"AI provider {provider} failed: {e}, trying next...")
                continue

        if last_error:
            err_msg = str(last_error)
            if "quota" in err_msg.lower() or "insufficient_quota" in err_msg.lower():
                raise ValueError("AI API kvota je iscrpljena za sve dostupne provajdere. Proveri billing ili koristi auto mod.")
            if "api key" in err_msg.lower() or "unauthorized" in err_msg.lower() or "auth" in err_msg.lower():
                raise ValueError("API ključ nije ispravan ni za jedan dostupan provajder. Proveri podešavanja.")
            raise ValueError(f"AI greška: {err_msg[:200]}")
    else:
        cards = _extract_keywords_auto(chunks, max_cards)

    final_deck_name = deck_name or f"Kartice: {doc.title}"

    if deck_id:
        deck = get_deck(db=db, deck_id=deck_id, user_id=user_id)
        if not deck:
            raise ValueError("Špil nije pronađen")
    else:
        deck = create_deck(
            db=db, user_id=user_id, name=final_deck_name, source_document_id=document_id
        )

    created_cards = add_cards_batch(db, deck.id, cards)

    return {
        "deck": {
            "id": str(deck.id),
            "user_id": str(deck.user_id),
            "name": deck.name,
            "description": deck.description,
            "source_document_id": str(deck.source_document_id) if deck.source_document_id else None,
            "total_cards": len(created_cards),
            "due_today": len(created_cards),
            "created_at": deck.created_at,
            "updated_at": deck.updated_at,
        },
        "cards_created": len(created_cards),
        "mode": mode,
        "provider_used": used_provider,
    }


def _generate_with_ai(chunks, provider, user_id, db, max_cards=20) -> tuple:
    import json
    import logging as _logging
    _logger = _logging.getLogger(__name__)

    chunk_texts = []
    for c in chunks[:30]:
        if c.content:
            chunk_texts.append(c.content[:400])

    combined = "\n\n---\n\n".join(chunk_texts)

    lang_hint = ""
    if combined and sum(1 for c in combined if '\u0400' <= c <= '\u04FF') > len(combined) * 0.02:
        lang_hint = (
            "\n\nIMPORTANT: The input text is in Serbian. "
            "ALL flashcards must be in Serbian language - both front and back. "
            "Use LATIN script only, not Cyrillic. "
            "Do NOT mix Serbian and English."
        )

    prompt = f"""You are a flashcard generator. Based on the following text, create up to {max_cards} flashcards in the format {{"front": "term/question", "back": "definition/answer"}}.

Return ONLY a valid JSON array of objects with "front" and "back" fields. Each front should be a key concept or question, each back should be a clear definition or answer.

Text:
{combined}{lang_hint}
"""

    from app.core.config import settings
    from app.db.models.user import User

    PROVIDER_CONFIG = {
        "openai": {
            "base_url": None,
            "model": "gpt-4o-mini",
            "key_source": lambda u, s: (u.ai_api_key_openai if u else None) or s.OPENAI_API_KEY,
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.1-8b-instant",
            "key_source": lambda u, s: (u.ai_api_key_groq if u else None) or s.GROQ_API_KEY,
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "model": "gemini-2.0-flash",
            "key_source": lambda u, s: (u.ai_api_key_gemini if u else None) or s.GEMINI_API_KEY,
        },
        "mistral": {
            "base_url": "https://api.mistral.ai/v1",
            "model": "mistral-small-latest",
            "key_source": lambda u, s: (u.ai_api_key_mistral if u else None) or s.MISTRAL_API_KEY,
        },
    }

    if provider == "claude":
        from anthropic import Anthropic

        user = db.query(User).filter(User.id == user_id).first()
        api_key = (user.ai_api_key_claude if user else None) or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("Claude API ključ nije podešen.")
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
    elif provider in PROVIDER_CONFIG:
        from openai import OpenAI

        cfg = PROVIDER_CONFIG[provider]
        user = db.query(User).filter(User.id == user_id).first()
        api_key = cfg["key_source"](user, settings)
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API ključ nije podešen.")
        client = OpenAI(api_key=api_key, base_url=cfg["base_url"]) if cfg["base_url"] else OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000,
        )
        content = response.choices[0].message.content
    else:
        raise ValueError(f"Nepodržan AI provajder: {provider}")

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    cards = json.loads(content)
    if not isinstance(cards, list):
        raise ValueError("AI response is not a list")

    result = []
    for card in cards:
        result.append({
            "front": card.get("front", "")[:500],
            "back": card.get("back", "")[:1000],
            "source_chunk_id": None,
        })

    return result[:max_cards], provider
