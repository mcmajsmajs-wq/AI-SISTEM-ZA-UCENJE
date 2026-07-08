# -*- coding: utf-8 -*-
"""
============================================================================
QUIZ GENERATION - AI Question Generation Logic
============================================================================

Extracted from service.py for modularity (Phase 4).

Sadrzi:
- _auto_num_questions
- _get_image_for_vision
- generate_questions_with_ai
- generate_quiz_questions
- detect_subject_area
- _detect_subject_fallback

Verzija: 1.0.0
============================================================================
"""

import json
import logging
from typing import List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.db.models.quiz import Quiz, Question
from app.db.models.document import Document, Chunk

from app.services.quiz.helpers import (
    _parse_questions,
    _fallback_questions,
    select_chunks_for_quiz,
    mark_chunks_as_used,
)
from app.services.quiz.clients import _build_clients, _PROVIDER_ORDER
from app.utils.cyrillic import cyrillic_to_latin

logger = logging.getLogger(__name__)


def _auto_num_questions(total_chunks: int, requested: int) -> int:
    """
    If requested > 0, use it (capped to a sane max).
    If requested == 0, calculate based on document size.
    """
    try:
        requested = int(requested) if requested else 0
    except (ValueError, TypeError):
        requested = 0

    if requested > 0:
        return min(requested, 50)
    return min(50, max(5, total_chunks // 10))


def _get_image_for_vision(storage_service, img, timeout: int = 5) -> Tuple[str, str]:
    """
    Hibridni pristup: prvo probaj MinIO URL, pa fallback na base64.
    """
    import base64

    try:
        public_url = storage_service.get_public_url(img.storage_path)
        logger.info(f"Trying MinIO URL: {public_url[:80]}...")

        response = httpx.get(public_url, timeout=timeout)
        if response.status_code == 200:
            logger.info("MinIO URL accessible - using URL mode")
            return public_url, "url"
        else:
            logger.warning(
                f"MinIO URL returned {response.status_code} - falling back to base64"
            )

    except Exception as e:
        logger.warning(f"MinIO URL failed: {e} - falling back to base64")

    try:
        from app.services.storage_cloud import CloudStorageService

        storage = CloudStorageService()

        from botocore.exceptions import ClientError

        try:
            response = storage.client.get_object(
                Bucket=storage.bucket_name, Key=img.storage_path
            )
            image_data = response["Body"].read()

            b64_image = base64.b64encode(image_data).decode("utf-8")

            path_lower = img.storage_path.lower()
            if path_lower.endswith(".png"):
                mime_type = "image/png"
            elif path_lower.endswith(".gif"):
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"

            logger.info(f"Using base64 mode (image size: {len(image_data)} bytes)")
            return f"data:{mime_type};base64,{b64_image}", "base64"

        except ClientError as e:
            logger.error(f"Failed to download image from MinIO: {e}")
            raise

    except Exception as e:
        logger.error(f"Base64 fallback also failed: {e}")
        raise


def generate_questions_with_ai(
    text: str,
    num_questions: int = 5,
    provider: Optional[str] = None,
    user_openai_key: Optional[str] = None,
    user_claude_key: Optional[str] = None,
    user_gemini_key: Optional[str] = None,
    user_groq_key: Optional[str] = None,
    user_mistral_key: Optional[str] = None,
    user_deepseek_key: Optional[str] = None,
    quiz_images: list = None,
    chunk_image_map: dict = None,
    subject_area: str = None,
    use_crewai: bool = False,
) -> Tuple[bool, List[dict], str]:
    """
    Generiše pitanja koristeći AI.
    Ako je use_crewai=True, koristi CrewAI multi-agent Flow umesto standardnog klijenta.
    """
    if use_crewai:
        return _generate_with_crewai_questions(
            text=text,
            num_questions=num_questions,
            provider=provider,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
        )

    if not subject_area:
        logger.info("Detecting subject area...")
        subject_area = detect_subject_area(text)
        logger.info(f"Detected subject area: {subject_area}")

    from app.services.quiz.prompts.subjects import get_specialized_prompt

    prompt = get_specialized_prompt(subject_area, num_questions, text)

    clients = _build_clients(
        user_openai_key=user_openai_key,
        user_claude_key=user_claude_key,
        user_gemini_key=user_gemini_key,
        user_groq_key=user_groq_key,
        user_mistral_key=user_mistral_key,
        user_deepseek_key=user_deepseek_key,
    )

    def get_client(p: str):
        return clients.get(p)

    def generate_with_prompt(client, text_to_use: str, num: int):
        return client.generate(prompt, num)

    if provider and provider in clients:
        client = get_client(provider)
        if not client or not client.is_available():
            logger.warning(
                f"Provajder '{provider}' nije dostupan, koristim fallback lanac"
            )
        else:
            ok, raw, err = generate_with_prompt(client, text, num_questions)
            if ok:
                questions = _parse_questions(raw)
                if questions:
                    logger.info(
                        f"[{provider}] Generisano {len(questions)} pitanja za oblast: {subject_area}"
                    )
                    return True, questions, provider
                logger.warning(
                    f"[{provider}] AI vratio prazan odgovor, prelazim na fallback"
                )
            logger.warning(f"[{provider}] Greška: {err}, prelazim na fallback")

    order = [p for p in _PROVIDER_ORDER if p != provider]
    if provider:
        order = [provider] + order

    for p in order:
        client = get_client(p)
        if not client or not client.is_available():
            continue
        ok, raw, err = generate_with_prompt(client, text, num_questions)
        if ok:
            logger.info(f"[{p}] AI odgovor: {raw[:200]}...")
            questions = _parse_questions(raw)
            if questions:
                logger.info(
                    f"[{p}] Generisano {len(questions)} pitanja za oblast: {subject_area}"
                )
                return True, questions, p
            logger.warning(f"[{p}] AI vratio prazan odgovor, probam sledeci")
        logger.warning(f"[{p}] Nije uspelo: {err}")

    logger.warning("Svi AI provajderi zakazali, koristim fallback pitanja")
    fallback = _fallback_questions(text, num_questions)
    return True, fallback, "fallback"


def _generate_with_crewai_questions(
    text: str,
    num_questions: int = 5,
    provider: Optional[str] = None,
    user_openai_key: Optional[str] = None,
    user_claude_key: Optional[str] = None,
    user_gemini_key: Optional[str] = None,
    user_groq_key: Optional[str] = None,
    user_mistral_key: Optional[str] = None,
    user_deepseek_key: Optional[str] = None,
) -> Tuple[bool, List[dict], str]:
    """Generiše pitanja koristeći CrewAI multi-agent Flow."""
    if not provider:
        logger.warning("CrewAI zahteva specifičan provider, ne 'auto'")
        fallback = _fallback_questions(text, num_questions)
        return True, fallback, "fallback"

    key_map = {
        "openai": user_openai_key,
        "claude": user_claude_key,
        "gemini": user_gemini_key,
        "groq": user_groq_key,
        "mistral": user_mistral_key,
        "deepseek": user_deepseek_key,
    }

    api_key = key_map.get(provider)
    if not api_key:
        logger.warning(
            f"CrewAI: API ključ za '{provider}' nije dostupan, koristim fallback"
        )
        fallback = _fallback_questions(text, num_questions)
        return True, fallback, "fallback"

    try:
        from app.services.crewai_flashcard import generate_quiz_questions_with_crewai

        questions = generate_quiz_questions_with_crewai(
            text=text,
            provider=provider,
            api_key=api_key,
            num_questions=num_questions,
        )

        if questions:
            logger.info(
                f"[CrewAI-{provider}] Generisano {len(questions)} pitanja"
            )
            return True, questions, f"crewai-{provider}"

        logger.warning(
            "CrewAI vratio 0 pitanja, koristim fallback"
        )
    except Exception as e:
        logger.warning(f"CrewAI quiz generation failed: {e}, koristim fallback")

    fallback = _fallback_questions(text, num_questions)
    return True, fallback, "fallback"


def generate_quiz_questions(
    db: Session,
    quiz_id: str,
    num_questions: int = 5,
    user_openai_key: Optional[str] = None,
    user_claude_key: Optional[str] = None,
    user_gemini_key: Optional[str] = None,
    user_groq_key: Optional[str] = None,
    user_mistral_key: Optional[str] = None,
    user_deepseek_key: Optional[str] = None,
    source_content: Optional[str] = None,
) -> Tuple[bool, str]:
    """Generiše pitanja za kviz.

    Args:
        source_content: 'translated' za srpski, 'original' za engleski, None za auto
    """
    from app.services.quiz import update_quiz_progress

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return False, "Kviz nije pronađen"

    document = db.query(Document).filter(Document.id == quiz.document_id).first()
    if not document:
        return False, "Dokument nije pronađen"

    chunks = db.query(Chunk).filter(Chunk.document_id == document.id).all()
    if not chunks:
        return False, "Nema chunk-ova za dokument"

    selected_chunks = select_chunks_for_quiz(chunks)
    if not selected_chunks:
        return False, "Nema validnih chunk-ova"

    total_chars = 0
    text_parts = []
    for c in selected_chunks:
        if source_content == "original":
            content = getattr(c, "content", "") or ""
        elif source_content == "translated" or (
            source_content is None and getattr(c, "translated_content", "")
        ):
            content = (
                getattr(c, "translated_content", "")
                or getattr(c, "content", "")
                or ""
            )
        else:
            content = getattr(c, "content", "") or ""

        if content:
            text_parts.append(content)
            total_chars += len(content)

    text = "\n\n".join(text_parts)

    num_to_generate = _auto_num_questions(len(selected_chunks), num_questions)

    update_quiz_progress(
        quiz_id, "started", 5, f"0 / {num_to_generate} - Priprema..."
    )
    update_quiz_progress(
        quiz_id, "processing", 10, f"Generisanje pitanja: 0 / {num_to_generate}"
    )

    ok, questions, provider = generate_questions_with_ai(
        text=text,
        num_questions=num_to_generate,
        user_openai_key=user_openai_key,
        user_claude_key=user_claude_key,
        user_gemini_key=user_gemini_key,
        user_groq_key=user_groq_key,
        user_mistral_key=user_mistral_key,
        user_deepseek_key=user_deepseek_key,
        subject_area=getattr(document, "subject_area", None),
    )

    if not ok or not questions:
        quiz.status = "failed"
        quiz.error_message = provider
        db.commit()
        update_quiz_progress(
            quiz_id, "failed", -1, f"Greška: {provider}", error=provider
        )
        return False, f"Greška pri generisanju: {provider}"

    update_quiz_progress(
        quiz_id, "completed", 100, f"{len(questions)} / {num_to_generate}"
    )

    for i, q_data in enumerate(questions):
        question_text = cyrillic_to_latin(str(q_data.get("question_text", "")))
        options = q_data.get("options", [])
        if isinstance(options, list):
            options = [cyrillic_to_latin(str(opt)) for opt in options]
        else:
            options = []

        correct_answer_raw = q_data.get("correct_answer", "")
        if isinstance(correct_answer_raw, list):
            correct_answer = ", ".join(str(x) for x in correct_answer_raw)
        elif isinstance(correct_answer_raw, str):
            try:
                parsed = json.loads(correct_answer_raw)
                if isinstance(parsed, list):
                    correct_answer = ", ".join(str(x) for x in parsed)
                else:
                    correct_answer = str(parsed)
            except Exception:
                correct_answer = str(correct_answer_raw).strip("[]")
        else:
            correct_answer = str(correct_answer_raw) if correct_answer_raw else ""
        correct_answer = cyrillic_to_latin(correct_answer)

        explanation = cyrillic_to_latin(str(q_data.get("explanation", "")))

        question = Question(
            quiz_id=quiz.id,
            question_text=question_text,
            question_type=q_data.get("question_type", "multiple_choice"),
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            points=q_data.get("points", 1),
            order_index=i,
        )
        db.add(question)

    chunk_ids = [c.id for c in selected_chunks if hasattr(c, "id")]
    mark_chunks_as_used(chunk_ids, db)

    quiz.status = "ready"
    quiz.total_questions = len(questions)
    if quiz.target_questions == 0:
        quiz.target_questions = num_questions
    db.commit()

    return True, f"Generisano {len(questions)} pitanja (provider: {provider})"


def detect_subject_area(text: str, num_samples: int = 20) -> str:
    """
    Detektuje oblast dokumenta na osnovu teksta.

    Koristi pdf_detector koji ima 68 oblasti (srpski + engleski).
    """
    try:
        from app.services.skills.pdf_detector import detect_subject_from_text

        return detect_subject_from_text(text, num_samples)
    except Exception as e:
        logger.warning(f"pdf_detector failed: {e}, falling back to basic keywords")
        return _detect_subject_fallback(text)


def _detect_subject_fallback(text: str) -> str:
    """Fallback detekcija ako pdf_detector nije dostupan.

    Delegira na helpers.subject_detection (keyword-based).
    """
    from app.services.quiz.helpers.subject_detection import detect_subject_area

    return detect_subject_area(text)



