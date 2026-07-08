import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.db.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    ChunkResponse,
    DocumentFromTextCreate,
    DocumentFromTextResponse,
)
from app.services.auth import get_current_user
from app.core.config import settings
from app.workers.tasks import auto_pipeline_task
from . import router

@router.post("/{document_id}/export")
async def export_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    EXPORT DOCUMENT
    ================================================================================
    Eksportuje dokument kao PDF.

    Args:
        document_id: ID dokumenta
        current_user: Trenutni korisnik
        db: Database session

    Returns:
        URL za download generisanog PDF-a
    ================================================================================
    """
    logger.info(f"Export requested for document: {document_id}")

    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        )

    document = (
        db.query(Document)
        .filter(and_(Document.id == doc_uuid, Document.user_id == current_user.id))
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully processed before export",
        )

    return {
        "document_id": document_id,
        "status": "queued",
        "download_url": None,
        "message": "Export feature coming soon",
    }


# ============================================================
# PIPELINE ENDPOINTS
# ============================================================


@router.post("/{document_id}/pipeline")
async def start_pipeline(
    document_id: str,
    pipeline_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pokretanje automatskog pipeline-a za postojeći dokument.
    PDF mora biti uploadovan, dokument mora postojati.

    Pipeline: process_pdf → translate → generate_quiz

    Body (JSON):
    {
      "source_language": "en",
      "target_language": "sr",
      "translation_provider": "ollama|deepl|openai|google|claude|null",
      "quiz_provider": "ollama|openai|claude|null",
      "num_questions": 5,
      "skip_translation": false,
      "passing_score": 60
    }
    """
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Dokument nije pronađen")

    # Auto-detekcija jezika - proveri prvi chunk
    detected_lang = None
    first_chunk = db.query(Chunk).filter(Chunk.document_id == document.id).first()
    if first_chunk and first_chunk.content:
        text = first_chunk.content[:1000]  # Proveri prvih 1000 karaktera
        text_lower = text.lower()

        # Proveri da li sadrži ćirilične karaktere
        cyrillic_chars = sum(1 for c in text if "\u0400" <= c <= "\u04ff")
        latin_chars = sum(1 for c in text if "a" <= c.lower() <= "z")

        # Proveri srpske latinične karaktere
        serbian_latin_chars = sum(1 for c in text if c in "čćžšđČĆŽŠĐ")

        # Srpske reči bez specijalnih karaktera (detektuju srpski tekst koji je sacuvan kao ASCII)
        SERBIAN_WORDS = [
            "i",
            "u",
            "na",
            "za",
            "od",
            "sa",
            "su",
            "se",
            "da",
            "je",
            "ili",
            "to",
            "je",
            "samo",
            "ali",
            "tak",
            "jer",
            "pa",
            "te",
            "kao",
            "biti",
            "bitno",
            "moze",
            "sadrzi",
            "sadrzi",
            "ima",
            "jesu",
            "bila",
            "bili",
            "bilo",
            "smo",
            "ste",
            "hemijski",
            "hemija",
            "element",
            "molekul",
            "atom",
            "reakcija",
            "jedinjenje",
            "kiselina",
            "baza",
            "oksidacija",
            "redukcija",
            "supstanca",
            "rastvor",
            "matematika",
            "matematicki",
            "matematike",
            "jednacina",
            "formula",
            "resenje",
            "fizika",
            "fizicki",
            "energije",
            "sila",
            "brzina",
            "masa",
            "temperatura",
            "biologija",
            "bilogija",
            "organizam",
            "celija",
            "tkivo",
            "organ",
            "sistem",
            "istorija",
            "istorijski",
            "godina",
            "veka",
            "doba",
            "događaj",
            "dogadaj",
            "srbija",
            "beograd",
            "narod",
            "drzava",
            "drzavni",
            "vojvodina",
            "kosovo",
            "geografija",
            "drzava",
            "grad",
            "reka",
            "planina",
            "more",
            "jezero",
            "knjizevnost",
            "autor",
            "del",
            "glavni",
            "lik",
            "radnja",
            "pesnik",
            "informati",
            "racunar",
            "program",
            "algoritam",
            "podatak",
            "sistem",
            "lekcija",
            "nastav",
            "ucenik",
            "skola",
            "udzbenik",
            "gradivo",
            "poglavlje",
            "strana",
            " stran",
            "zadatak",
            "pitanje",
            "odgovor",
            "primer",
            "objasnjenje",
        ]

        # Prepoznaje srpski tekst bez specijalnih karaktera
        serbian_word_matches = sum(1 for word in SERBIAN_WORDS if word in text_lower)

        # Engleske reči koje mogu da se pojave u srpskim dokumentima
        ENGLISH_WORDS = [
            "the",
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "been",
            "being",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "their",
            "them",
            "and",
            "or",
            "but",
            "not",
            "no",
            "if",
            "then",
            "so",
            "because",
            "when",
            "which",
            "what",
            "who",
            "whom",
            "how",
            "where",
            "why",
            "chapter",
            "page",
            "figure",
            "table",
            "section",
            "introduction",
            "conclusion",
            "abstract",
            "references",
            "bibliography",
            "appendix",
        ]
        english_word_matches = sum(
            1 for word in ENGLISH_WORDS if f" {word} " in f" {text_lower} "
        )

        # Detekcija - POPRAVLJENA LOGIKA:
        # Srpski se detektuje ako:
        # 1. Ima bilo koju ćirilicu (> 0)
        # 2. Ima srpske latinične karaktere (č, ć, ž, š, đ)
        # 3. Ima dosta ćirilice (>10%) - za mešovite tekstove
        # 4. Ima dosta srpskih reči bez specijalnih karaktera (> 3)
        if cyrillic_chars > 0:
            detected_lang = "sr"
        elif serbian_latin_chars > 0:
            detected_lang = "sr"
        elif cyrillic_chars > latin_chars * 0.1:
            detected_lang = "sr"
        elif serbian_word_matches >= 3 and english_word_matches < 3:
            # Ako ima dosta srpskih reči a malo engleskih → srpski
            detected_lang = "sr"
        elif serbian_word_matches >= english_word_matches + 2:
            # Ako ima značajno više srpskih reči → srpski
            detected_lang = "sr"
        elif (
            latin_chars > 10
            and cyrillic_chars < 5
            and serbian_latin_chars < 3
            and serbian_word_matches < 3
        ):
            detected_lang = "en"

    # Koristi auto-detektovani jezik ili default
    source_language = pipeline_data.get("source_language") or detected_lang or "en"
    # Target language je uvek suprotan od source
    if not pipeline_data.get("target_language"):
        target_language = "sr" if source_language == "en" else "en"
    else:
        target_language = pipeline_data.get("target_language")
    translation_provider = pipeline_data.get("translation_provider")
    quiz_provider = pipeline_data.get("quiz_provider")
    num_questions = int(pipeline_data.get("num_questions", 5))
    skip_translation = bool(pipeline_data.get("skip_translation", False))
    passing_score = int(pipeline_data.get("passing_score", 60))

    # Reset status ako je potrebno
    if document.status == "error":
        document.status = "pending"
        db.commit()

    task = auto_pipeline_task.delay(
        document_id=str(document.id),
        source_language=source_language,
        target_language=target_language,
        translation_provider=translation_provider,
        quiz_provider=quiz_provider,
        num_questions=num_questions,
        skip_translation=skip_translation,
        passing_score=passing_score,
        user_id=str(current_user.id),
    )

    logger.info(f"Pipeline pokrenut za dokument {document_id} — Celery task {task.id}")

    return {
        "task_id": task.id,
        "document_id": document_id,
        "status": "started",
        "message": f"Pipeline pokrenut: PDF → {'→ Prevod ' if not skip_translation else ''}→ Kviz",
        "stages": [
            {"name": "PDF Processing", "skipped": document.status == "completed"},
            {
                "name": f"Prevod ({source_language}→{target_language})",
                "skipped": skip_translation or source_language == target_language,
            },
            {"name": f"Generisanje kviza ({num_questions} pitanja)", "skipped": False},
        ],
        "providers": {
            "translation": translation_provider or "auto",
            "quiz": quiz_provider or "auto",
        },
    }


@router.get("/pipeline/providers")
async def get_pipeline_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Vraća listu dostupnih AI provajdera za pipeline.
    """
    from app.services.translation import translation_service
    from app.services.quiz import quiz_service

    translation_providers = translation_service.get_available_providers()
    quiz_providers = quiz_service.get_available_providers()

    return {
        "translation_providers": translation_providers,
        "quiz_providers": quiz_providers,
    }


