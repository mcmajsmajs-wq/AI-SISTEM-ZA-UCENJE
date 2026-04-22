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
import os
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
    text: str,
    source_language: str = "en",
    target_language: str = "sr",
    user_api_keys: Optional[dict] = None,
    preferred_provider: Optional[str] = None,
) -> Any:
    """
    Prevodi tekst sa automatskim prebacivanjem između provajdera.

    Pokušava više provajdera redom dok neki ne uspe:
    1. Preferirani provajder (ako je naveden)
    2. Korisnikovi API ključevi (Mistral, Groq, Gemini, DeepSeek, OpenAI)
    3. Sistemski provajderi (Ollama - lokalni)

    Args:
        text: Tekst za prevođenje
        source_language: Izvorni jezik (npr. 'en', 'sr')
        target_language: Ciljni jezik (npr. 'sr', 'en')
        user_api_keys: Rečnik korisnikovih API ključeva
        preferred_provider: Preferirani provajder (npr. 'deepseek', 'openai')

    Returns:
        Prevedeni tekst ili None ako prevod ne uspe

    Raises:
        Exception: Poslednja greška ako nijedan provajder ne uspe
    """
    providers_to_try = []

    if preferred_provider and preferred_provider not in ["auto", "libretranslate"]:
        providers_to_try.append(preferred_provider)

    # Add user API keys first - mistral/groq first as they have free tiers
    if user_api_keys and isinstance(user_api_keys, dict):
        priority_order = ["mistral", "groq", "gemini", "deepseek", "openai"]
        for p in priority_order:
            if (user_api_keys or {}).get(p) and p not in providers_to_try:
                providers_to_try.append(p)
    else:
        user_api_keys = {}

    # Add system-level API keys as fallback - mistral/groq first
    # Read API keys - try environment first, then settings
    mistral_key = (
        os.environ.get("MISTRAL_API_KEY")
        or os.environ.get("SYSTEM_MISTRAL_API_KEY")
        or getattr(settings, "MISTRAL_API_KEY", None)
        or getattr(settings, "SYSTEM_MISTRAL_API_KEY", None)
    )
    groq_key = (
        os.environ.get("GROQ_API_KEY")
        or os.environ.get("SYSTEM_GROQ_API_KEY")
        or getattr(settings, "GROQ_API_KEY", None)
        or getattr(settings, "SYSTEM_GROQ_API_KEY", None)
    )
    gemini_key = os.environ.get("GOOGLE_API_KEY") or getattr(
        settings, "GOOGLE_API_KEY", None
    )
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY") or getattr(
        settings, "DEEPSEEK_API_KEY", None
    )
    openai_key = os.environ.get("OPENAI_API_KEY") or getattr(
        settings, "OPENAI_API_KEY", None
    )

    # Build system keys dictionary
    system_keys = {
        "mistral": mistral_key,
        "groq": groq_key,
        "gemini": gemini_key,
        "deepseek": deepseek_key,
        "openai": openai_key,
    }

    # CRITICAL: Only add system keys if user has NO user-level keys
    # User keys ALWAYS take priority over system keys
    has_user_keys = bool(user_api_keys and any(v for v in user_api_keys.values() if v))

    if not has_user_keys:
        # Add system keys as fallback only when user has no keys
        priority_order = ["groq", "mistral", "deepseek", "openai", "gemini"]
        for p in priority_order:
            if system_keys.get(p) and p not in providers_to_try:
                providers_to_try.append(p)

    # ONLY add Ollama as absolute LAST resort - only if no cloud providers available
    # This ensures cloud providers are tried first
    if not any(
        p in providers_to_try
        for p in ["groq", "mistral", "deepseek", "openai", "gemini"]
    ):
        providers_to_try.append("ollama")

    last_error = None
    logger.info(f"Translation providers to try: {providers_to_try}")

    for provider in providers_to_try:
        try:
            from app.services.translation import translation_service

            result = translation_service.translate(
                text, source_language, target_language, provider=provider
            )
            if result.success:
                logger.info(f"Translation successful with provider: {provider}")
                return result
            last_error = result.error
            logger.warning(f"Provider {provider} failed: {result.error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Provider {provider} exception: {e}")

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

        if document.status not in ["completed", "translating", "partial"]:
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

        # Auto-detect provider - USER keys take priority over system keys
        if not _use_provider or _use_provider == "auto":
            # FIRST check only user keys - never use system keys if user has their own
            if getattr(user_obj, "ai_api_key_mistral", None):
                _use_provider = "mistral"
            elif getattr(user_obj, "ai_api_key_groq", None):
                _use_provider = "groq"
            elif getattr(user_obj, "ai_api_key_gemini", None):
                _use_provider = "gemini"
            elif getattr(user_obj, "ai_api_key_deepseek", None):
                _use_provider = "deepseek"
            elif getattr(user_obj, "ai_api_key_openai", None):
                _use_provider = "openai"
            # Only fallback to system keys if user has NO keys at all
            elif getattr(settings, "MISTRAL_API_KEY", None):
                _use_provider = "mistral"
            elif getattr(settings, "GROQ_API_KEY", None):
                _use_provider = "groq"
            elif getattr(settings, "GOOGLE_API_KEY", None):
                _use_provider = "gemini"
            elif getattr(settings, "DEEPSEEK_API_KEY", None):
                _use_provider = "deepseek"
            elif getattr(settings, "OPENAI_API_KEY", None):
                _use_provider = "openai"

        logger.info(
            f"Translating {total_chunks} chunks for document {document_id} using provider: {_use_provider or 'auto'}"
        )

        # Smaller batch size to avoid Groq 413 errors (was 8, now 4)
        BATCH_SIZE = 4
        MAX_RETRIES_PER_CHUNK = 3
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
                preferred_provider=_use_provider,
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
        flag_modified(document, "file_metadata")

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

        # Send email notification about translation being ready
        if document.user_id:
            try:
                user = db.query(User).filter(User.id == document.user_id).first()
                if user and user.email:
                    from app.services.email_service import email_service

                    email_service.send_translation_ready(
                        to=user.email,
                        full_name=user.full_name or "",
                        document_title=document.title or "Dokument",
                        source_language=document.source_language or "en",
                        target_language=document.target_language or "sr",
                        total_chunks=translated_count,
                    )
                    logger.info(
                        f"Translation email notification sent for document {document_id}"
                    )
            except Exception as email_err:
                logger.warning(f"Email notification failed (non-critical): {email_err}")

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
                # Check if some chunks were translated before failure
                translated_before_failure = (
                    db.query(Chunk)
                    .filter(Chunk.document_id == document_id, Chunk.is_translated == 1)
                    .count()
                )

                document.file_metadata = document.file_metadata or {}
                document.file_metadata["translation_error"] = str(exc)
                document.file_metadata["partial_translation"] = (
                    translated_before_failure > 0
                )

                # If some chunks were translated, mark as "partial" instead of "error"
                # This allows users to resume translation instead of deleting the document
                if translated_before_failure > 0:
                    document.status = "partial"
                    logger.info(
                        f"Document {document_id} marked as partial - "
                        f"{translated_before_failure} chunks translated before failure"
                    )
                else:
                    document.status = "error"

                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

        raise self.retry(exc=exc, countdown=300)

    finally:
        db.close()
