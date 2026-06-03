# -*- coding: utf-8 -*-
"""
============================================================================
TASKS - TRANSLATION MODULE
============================================================================
Background task za AI prevod dokumenata sa checkpoint/resume podrškom.

Tasks:
- translate_document_task
- translate_with_fallback()

Verzija: 2.2.0 (FAZA 14.1 - Fixed duplicate code)
============================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
import logging
import os
import time
import re
from typing import Any, Optional
from datetime import datetime

from app.core.config import settings
from app.db.session import engine
from app.db.models.document import Document, Chunk
from app.db.models.user import User
from app.services.translation import (
    translation_service,
)
from app.utils.cyrillic import cyrillic_to_latin

logger = logging.getLogger(__name__)


def get_db_session():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def translate_with_fallback(
    text: str,
    source_language: str = "en",
    target_language: str = "sr",
    user_api_keys: Optional[dict] = None,
    preferred_provider: Optional[str] = None,
) -> Any:
    providers_to_try = []

    if preferred_provider and preferred_provider not in ["auto", "libretranslate"]:
        providers_to_try.append(preferred_provider)

    if user_api_keys and isinstance(user_api_keys, dict):
        priority_order = ["mistral", "groq", "gemini", "deepseek", "openai"]
        for p in priority_order:
            if (user_api_keys or {}).get(p) and p not in providers_to_try:
                providers_to_try.append(p)
    else:
        user_api_keys = {}

    mistral_key = os.environ.get("MISTRAL_API_KEY") or getattr(
        settings, "MISTRAL_API_KEY", None
    )
    groq_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
    gemini_key = os.environ.get("GOOGLE_API_KEY") or getattr(
        settings, "GOOGLE_API_KEY", None
    )
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY") or getattr(
        settings, "DEEPSEEK_API_KEY", None
    )
    openai_key = os.environ.get("OPENAI_API_KEY") or getattr(
        settings, "OPENAI_API_KEY", None
    )

    system_keys = {
        "mistral": mistral_key,
        "groq": groq_key,
        "gemini": gemini_key,
        "deepseek": deepseek_key,
        "openai": openai_key,
    }

    has_user_keys = bool(user_api_keys and any(v for v in user_api_keys.values() if v))

    if not has_user_keys:
        priority_order = ["groq", "mistral", "deepseek", "openai", "gemini"]
        for p in priority_order:
            if system_keys.get(p) and p not in providers_to_try:
                providers_to_try.append(p)

    if not any(
        p in providers_to_try
        for p in ["groq", "mistral", "deepseek", "openai", "gemini"]
    ):
        providers_to_try.append("ollama")

    last_error = None
    logger.info(f"Translation providers to try: {providers_to_try}")

    for provider in providers_to_try:
        try:
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


def run_document_translation(
    db,
    document_id: str,
    provider: Optional[str] = None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Core translation logic — može se pozvati sinhrono iz pipeline-a ili API-ja.

    Args:
        db: SQLAlchemy session
        document_id: ID dokumenta za prevod
        provider: Preferovani AI provajder (None=auto)
        progress_callback: Opcioni callback za dodatne progress update-e

    Returns:
        dict: Rezultat prevoda

    Raises:
        Exception: Ako prevod potpuno ne uspe
    """
    logger.info(
        f"Starting translation for document: {document_id}, provider: {provider}"
    )

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document not found: {document_id}")

    if document.status not in ["completed", "translating", "partial"]:
        raise ValueError(
            f"Document must be processed first. Current status: {document.status}"
        )

    # Signal frontendu da pocne da polira progress
    if document.status == "completed":
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

    # === CHECKPOINT RESUME LOGIC ===
    start_from_chunk = 0
    checkpoint_data = (
        document.file_metadata.get("translation_checkpoint", {})
        if document.file_metadata
        else {}
    )

    if checkpoint_data:
        start_from_chunk = checkpoint_data.get("last_chunk_index", 0)
        logger.info(f"Resuming from checkpoint: chunk {start_from_chunk}")

    # Count already translated
    already_translated = sum(1 for c in chunks if c.is_translated)
    untranslated = [c for c in chunks if not c.is_translated]

    if already_translated > 0:
        logger.info(f"Skipping {already_translated} already translated chunks")
    # === END CHECKPOINT RESUME ===

    total_cost = 0.0
    total_tokens = 0
    errors = []

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

    _use_provider = provider or "auto"

    if _use_provider == "auto":
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
        else:
            _use_provider = "ollama"

    logger.info(
        f"Translating {len(untranslated)} chunks for document {document_id} "
        f"using provider: {_use_provider}"
    )

    BATCH_SIZE = 2
    CHECKPOINT_EVERY = 5
    MAX_RETRIES_PER_CHUNK = 2

    translated_count = already_translated
    batch_num = 0
    start_time = time.time()

    while batch_num * BATCH_SIZE < len(untranslated):
        batch_start = batch_num * BATCH_SIZE
        batch = untranslated[batch_start : batch_start + BATCH_SIZE]
        if not batch:
            break

        batch_text = ""
        for idx, chunk in enumerate(batch):
            batch_text += f"\n\n### {idx + 1}\n" + chunk.content

        batch_success = False
        result = None

        for attempt in range(MAX_RETRIES_PER_CHUNK):
            try:
                result = translate_with_fallback(
                    text=batch_text,
                    source_language=document.source_language,
                    target_language=document.target_language,
                    user_api_keys=user_api_keys,
                    preferred_provider=_use_provider,
                )
                if result.success:
                    batch_success = True
                    break
            except Exception as e:
                logger.warning(f"Batch attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES_PER_CHUNK - 1:
                    time.sleep(1)

        if batch_success and result:
            parts = re.split(r"\n\n?###\s+\d+", result.translated_text)
            parts = [p.strip() for p in parts if p.strip()]

            for idx, chunk in enumerate(batch):
                translated_part = (
                    parts[idx] if idx < len(parts) else result.translated_text
                )
                chunk.translated_content = cyrillic_to_latin(translated_part)
                chunk.is_translated = 1
                translated_count += 1

                document.file_metadata = document.file_metadata or {}
                document.file_metadata["translation_progress"] = {
                    "translated_chunks": translated_count,
                    "total_chunks": total_chunks,
                    "elapsed_seconds": int(time.time() - start_time),
                    "last_activity_at": datetime.utcnow().isoformat() + "Z",
                }
                if translated_count % CHECKPOINT_EVERY == 0:
                    document.file_metadata["translation_checkpoint"] = {
                        "last_chunk_index": translated_count,
                        "last_translated_count": translated_count,
                        "last_updated": datetime.utcnow().isoformat() + "Z",
                    }
                flag_modified(document, "file_metadata")
                db.commit()
                logger.info(f"Translated {translated_count}/{total_chunks} chunks")

            total_cost += result.cost
            total_tokens += result.tokens_used
        else:
            for chunk in batch:
                single_success = False
                for attempt in range(MAX_RETRIES_PER_CHUNK):
                    try:
                        single_result = translate_with_fallback(
                            text=chunk.content,
                            source_language=document.source_language,
                            target_language=document.target_language,
                            user_api_keys=user_api_keys,
                        )
                        if single_result.success:
                            chunk.translated_content = cyrillic_to_latin(
                                single_result.translated_text
                            )
                            chunk.is_translated = 1
                            translated_count += 1
                            total_cost += single_result.cost
                            total_tokens += single_result.tokens_used
                            single_success = True

                            document.file_metadata = document.file_metadata or {}
                            document.file_metadata["translation_progress"] = {
                                "translated_chunks": translated_count,
                                "total_chunks": total_chunks,
                                "elapsed_seconds": int(time.time() - start_time),
                                "last_activity_at": datetime.utcnow().isoformat() + "Z",
                            }
                            if translated_count % CHECKPOINT_EVERY == 0:
                                document.file_metadata["translation_checkpoint"] = {
                                    "last_chunk_index": translated_count,
                                    "last_translated_count": translated_count,
                                    "last_updated": datetime.utcnow().isoformat() + "Z",
                                }
                            flag_modified(document, "file_metadata")
                            db.commit()
                            logger.info(
                                f"Translated {translated_count}/{total_chunks} chunks"
                            )
                            break
                    except Exception as e:
                        if attempt < MAX_RETRIES_PER_CHUNK - 1:
                            time.sleep(0.5)

                if not single_success:
                    errors.append(f"Chunk {chunk.sequence_number}: Failed")
                    logger.error(f"Failed to translate chunk {chunk.sequence_number}")

                time.sleep(0.2)

        time.sleep(0.2)
        batch_num += 1

    db.commit()

    if document.file_metadata:
        document.file_metadata.pop("translation_checkpoint", None)

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
        logger.info(f"Translation completed: {translated_count}/{total_chunks} chunks")
    elif translated_count > 0:
        document.status = "partial"
        document.file_metadata["translation"]["partial"] = True
        logger.warning(f"Partial translation: {translated_count}/{total_chunks} chunks")
    else:
        document.file_metadata["translation"]["failed"] = True

    db.commit()

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
        except Exception as email_err:
            logger.warning(f"Email notification failed: {email_err}")

    return {
        "status": "success",
        "document_id": str(document_id),
        "total_chunks": total_chunks,
        "translated_chunks": translated_count,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "errors_count": len(errors),
    }


@shared_task(bind=True, max_retries=3)
def translate_document_task(self, document_id: str, provider: Optional[str] = None):
    """
    Celery task za AI prevod dokumenta — delegira run_document_translation().
    """
    db = get_db_session()
    try:
        return run_document_translation(db, document_id, provider)
    except Exception as exc:
        logger.error(f"translate_document_task failed for {document_id}: {exc}")
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
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
                if translated_before_failure > 0:
                    document.status = "partial"
                else:
                    document.status = "error"
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
