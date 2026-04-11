# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - TRANSLATION MODULE
================================================================================
Background task za AI prevod dokumenata.

Tasks:
- translate_document_task
- translate_with_fallback()

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
import logging
import time
from typing import Any, Optional

from app.core.config import settings  # noqa: F401
from app.db.session import engine
from app.db.models.document import Document, Chunk
from app.db.models.user import User
from app.services.translation import (
    translation_service,
    make_gemini_client,
    make_groq_client,
    make_mistral_client,
)

logger = logging.getLogger(__name__)


def get_db_session():
    """
    Kreira SQLAlchemy session za task.

    Returns:
        SQLAlchemy Session instanca
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def translate_with_fallback(
    text: str, source_language: str, target_language: str, user_api_keys: dict = None
) -> Any:
    """
    Prevodi tekst sa automatskim prebacivanjem između provajdera.

    Pokušava više provajdera redom dok neki ne uspe:
    1. Korisnikovi API ključevi (Mistral, Groq, Gemini, DeepSeek, OpenAI)
    2. Sistemski provajderi (LibreTranslate - besplatan)

    Args:
        text: Tekst za prevođenje
        source_language: Izvorni jezik (npr. 'en', 'sr')
        target_language: Ciljni jezik (npr. 'sr', 'en')
        user_api_keys: Rečnik korisnikovih API ključeva

    Returns:
        Prevedeni tekst ili None ako prevod ne uspe

    Raises:
        Exception: Poslednja greška ako nijedan provajder ne uspe
    """
    # Get all available user API keys
    providers_to_try = []

    if user_api_keys:
        priority_order = ["mistral", "groq", "gemini", "deepseek", "openai"]
        for p in priority_order:
            if user_api_keys.get(p):
                providers_to_try.append(p)

    system_order = ["libretranslate"]
    for p in system_order:
        if p not in providers_to_try:
            providers_to_try.append(p)

    last_error = None

    for provider in providers_to_try:
        client = None
        if provider == "mistral" and user_api_keys.get("mistral"):
            client = make_mistral_client(user_api_keys["mistral"])
        elif provider == "groq" and user_api_keys.get("groq"):
            client = make_groq_client(user_api_keys["groq"])
        elif provider == "gemini" and user_api_keys.get("gemini"):
            client = make_gemini_client(user_api_keys["gemini"])

        if client:
            for attempt in range(3):
                try:
                    result = client.translate(text, source_language, target_language)
                    if result.success:
                        return result
                    last_error = result.error
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Translation attempt {attempt + 1} failed: {e}")

                if attempt < 2:
                    time.sleep(1)

        # Fallback: use system translation service
        if provider not in ["mistral", "groq", "gemini", "deepseek", "openai"]:
            try:
                result = translation_service.translate(
                    text,
                    source_language=source_language,
                    target_language=target_language,
                    provider=provider,
                )
                if result.success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)

    # All providers failed
    logger.error(f"All translation providers failed. Last error: {last_error}")
    raise Exception(f"Translation failed: {last_error}")


@shared_task(bind=True, max_retries=3)
def translate_document_task(self, document_id: str, provider: Optional[str] = None):
    """
    Task za AI prevod dokumenta.
    Prevod chunk-ova koristeći Ollama, DeepL, OpenAI, Google ili Claude.

    Args:
        document_id: ID dokumenta za prevod
        provider: Specifični provajder (ollama, deepl, openai, google, claude)
    """
    logger.info(
        f"Starting translation for document: {document_id}, provider: {provider}"
    )

    db = get_db_session()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        if document.status not in ["completed", "translating"]:
            raise ValueError(
                f"Document must be processed first. Current status: {document.status}"
            )

        document.status = "translating"
        db.commit()

        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document.id)
            .order_by(Chunk.sequence_number)
            .all()
        )

        if not chunks:
            raise ValueError("No chunks found for document")

        total_chunks = len(chunks)
        translated_count = 0
        total_cost = 0.0
        total_tokens = 0
        errors = []

        # Load user API key for cloud providers
        user_obj = (
            db.query(User).filter(User.id == document.user_id).first()
            if document.user_id
            else None
        )

        user_api_keys = {}
        if user_obj:
            user_api_keys = {
                "mistral": getattr(user_obj, "ai_api_key_mistral", None),
                "groq": getattr(user_obj, "ai_api_key_groq", None),
                "gemini": getattr(user_obj, "ai_api_key_gemini", None),
                "deepseek": getattr(user_obj, "ai_api_key_deepseek", None),
                "openai": getattr(user_obj, "ai_api_key_openai", None),
            }
            user_api_keys = {k: v for k, v in user_api_keys.items() if v}

        _use_provider = provider

        # Auto-detect provider based on user's available API keys
        if not _use_provider or _use_provider == "auto":
            if user_obj:
                if getattr(user_obj, "ai_api_key_mistral", None):
                    _use_provider = "mistral"
                elif getattr(user_obj, "ai_api_key_groq", None):
                    _use_provider = "groq"
                elif getattr(user_obj, "ai_api_key_gemini", None):
                    _use_provider = "gemini"
                elif getattr(user_obj, "ai_api_key_deepseek", None):
                    _use_provider = "deepseek"

        logger.info(
            f"Translating {total_chunks} chunks for document {document_id} using provider: {_use_provider or 'auto'}"
        )

        BATCH_SIZE = 8
        untranslated = [c for c in chunks if not c.is_translated]
        translated_count += total_chunks - len(untranslated)

        import re as _re

        for batch_start in range(0, len(untranslated), BATCH_SIZE):
            batch = untranslated[batch_start : batch_start + BATCH_SIZE]

            separator = "\n\n### {}\n"
            batch_text = ""
            for idx, chunk in enumerate(batch):
                batch_text += separator.format(idx + 1) + chunk.content

            result = translate_with_fallback(
                text=batch_text,
                source_language=document.source_language,
                target_language=document.target_language,
                user_api_keys=user_api_keys,
            )

            if result.success:
                parts = _re.split(r"\n\n?###\s+\d+\n", result.translated_text)
                parts = [p.strip() for p in parts if p.strip()]

                for idx, chunk in enumerate(batch):
                    translated_part = (
                        parts[idx] if idx < len(parts) else result.translated_text
                    )
                    chunk.translated_content = translated_part
                    chunk.is_translated = 1
                    translated_count += 1

                total_cost += result.cost
                total_tokens += result.tokens_used
            else:
                logger.warning(
                    f"Batch translation failed, trying individually: {result.error}"
                )
                for chunk in batch:
                    single_result = translate_with_fallback(
                        text=chunk.content,
                        source_language=document.source_language,
                        target_language=document.target_language,
                        user_api_keys=user_api_keys,
                    )
                    if single_result.success:
                        chunk.translated_content = single_result.translated_text
                        chunk.is_translated = 1
                        translated_count += 1
                        total_cost += single_result.cost
                        total_tokens += single_result.tokens_used
                    else:
                        errors.append(
                            f"Chunk {chunk.sequence_number}: {single_result.error}"
                        )
                        logger.error(
                            f"Failed to translate chunk {chunk.sequence_number}: {single_result.error}"
                        )
                    time.sleep(0.5)

            db.commit()

            import datetime as _dt

            _meta = dict(document.file_metadata or {})
            _meta["translation_progress"] = {
                "translated_chunks": translated_count,
                "total_chunks": total_chunks,
                "last_activity_at": _dt.datetime.utcnow().isoformat() + "Z",
            }
            document.file_metadata = _meta
            flag_modified(document, "file_metadata")
            db.commit()
            logger.info(f"Translated {translated_count}/{total_chunks} chunks")

            time.sleep(0.3)

        db.commit()

        document.file_metadata = document.file_metadata or {}
        document.file_metadata["translation"] = {
            "provider": provider or "auto",
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "translated_chunks": translated_count,
            "errors": errors[:10] if errors else [],
        }

        if translated_count == total_chunks:
            document.status = "completed"
            logger.info(
                f"Translation completed for document {document_id}: {translated_count}/{total_chunks} chunks"
            )
        elif translated_count > 0:
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            logger.warning(
                f"Partial translation for document {document_id}: {translated_count}/{total_chunks} chunks"
            )
        else:
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            document.file_metadata["translation"]["failed"] = True
            logger.warning(
                f"Translation fully failed for document {document_id}: 0/{total_chunks} chunks translated"
            )

        db.commit()

        return {
            "status": "success",
            "document_id": str(document_id),
            "total_chunks": total_chunks,
            "translated_chunks": translated_count,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "errors_count": len(errors),
        }

    except Exception as exc:
        logger.error(f"Translation failed for document {document_id}: {exc}")

        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = document.file_metadata or {}
                document.file_metadata["translation_error"] = str(exc)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

        raise self.retry(exc=exc, countdown=300)

    finally:
        db.close()
