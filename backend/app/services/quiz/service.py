# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE - Main Service Class
================================================================================

Verzija: 1.0.0
================================================================================
"""

import json
import logging
import random
import re
import time
from typing import List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.db.models.quiz import Quiz, Question
from app.db.models.document import Document, Chunk

from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.services.quiz.helpers import (
    _parse_questions,
    _fallback_questions,
    select_chunks_for_quiz,
    mark_chunks_as_used,
)
from app.services.quiz.clients import _build_clients, _PROVIDER_ORDER

logger = logging.getLogger(__name__)


CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "ѓ": "đ",
    "е": "e",
    "ж": "ž",
    "з": "z",
    "и": "i",
    "ј": "j",
    "к": "k",
    "л": "l",
    "љ": "lj",
    "м": "m",
    "н": "n",
    "њ": "nj",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "ћ": "ć",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "č",
    "Ѓ": "Đ",
    "Ѐ": "È",
    "Ё": "Ë",
    "Љ": "LJ",
    "Њ": "NJ",
    "Ћ": "Ć",
    "Џ": "DŽ",
    "ш": "š",
    "щ": "št",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "ju",
    "я": "ja",
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Ѓ": "Đ",
    "Е": "E",
    "Ё": "Ë",
    "Ж": "Ž",
    "З": "Z",
    "И": "I",
    "Й": "J",
    "К": "K",
    "Л": "L",
    "Љ": "LJ",
    "М": "M",
    "Н": "N",
    "Њ": "NJ",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "Ћ": "Ć",
    "У": "U",
    "Ф": "F",
    "Х": "H",
    "Ц": "C",
    "Ч": "Č",
    "Џ": "DŽ",
    "Ш": "Š",
    "Щ": "ŠT",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "JU",
    "Я": "JA",
}


def cyrillic_to_latin(text: str) -> str:
    """Convert Cyrillic text to Latin script."""
    if not text:
        return text
    result = []
    for char in text:
        if "\u0400" <= char <= "\u04ff" or char in "ёЁ":
            result.append(CYRILLIC_TO_LATIN.get(char, char))
        else:
            result.append(char)
    return "".join(result)


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


def _transliterate_text(text: str) -> str:
    """
    Konvertuje tekst latinica <-> ćirilica.

    Args:
        text: Ulazni tekst

    Returns:
        str: Konvertovani tekst
    """
    if not text:
        return text

    # Ćirilica -> Latinica
    cyrillic_to_latin = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "đ",
        "ђ": "đ",
        "е": "e",
        "ж": "ž",
        "з": "z",
        "и": "i",
        "ј": "j",
        "к": "k",
        "л": "l",
        "љ": "lj",
        "м": "m",
        "н": "n",
        "њ": "nj",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "ћ": "ć",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "č",
        "Ѓ": "Đ",
        # lowercase dž = дж (commented to avoid duplicate key),
        "ш": "š",
        "А": "A",
        "Б": "B",
        "В": "V",
        "Г": "G",
        "Д": "D",
        "Ђ": "Đ",
        "Е": "E",
        "Ж": "Ž",
        "З": "Z",
        "И": "I",
        "Ј": "J",
        "К": "K",
        "Л": "L",
        "Љ": "LJ",
        "М": "M",
        "Н": "N",
        "Њ": "NJ",
        "О": "O",
        "П": "P",
        "Р": "R",
        "С": "S",
        "Т": "T",
        "Ћ": "Ć",
        "У": "U",
        "Ф": "F",
        "Х": "H",
        "Ц": "C",
        "Ч": "Č",
        "Џ": "DŽ",  # uppercase
        "Ш": "Š",
    }

    # Latinica -> Ćirilica
    latin_to_cyrillic = {v: k for k, v in cyrillic_to_latin.items()}

    # Detektuj i konvertuj
    # Ako tekst sadrži ćirilična slova, konvertuj u latinicnu
    has_cyrillic = any(
        ord(c) >= 0x0430 and ord(c) <= 0x044F for c in text if c.isalpha()
    )

    if has_cyrillic:
        result = []
        for char in text:
            result.append(cyrillic_to_latin.get(char, char))
        return "".join(result)

    # Inače, konvertuj u ćirilicu (za fallback)
    result = []
    for char in text:
        result.append(latin_to_cyrillic.get(char, char))
    return "".join(result)


class QuizService:
    """
    Servis za generisanje i upravljanje kvizovima.
    Podržava Ollama, OpenAI, Claude sa fallback lancem.
    """

    @staticmethod
    def _check_answer_static(
        q_type: str, user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        """
        Static method for checking quiz answers.

        Podržava sve tipove pitanja (ažurirano 2026-04-06):
        - multiple_choice, true_false, calculation: direktno poređenje stringova
        - checkbox: skupovno poređenje (redosled nebitan)
        - sequencing: poređenje niza indeksa
        - categorization: poređenje mapping-a
        - matching: poređenje parova
        - odd_one_out: direktno poređenje
        - estimation: tolerance-based poređenje
        - matrix: poređenje niza odgovora
        - hotspot: direktno poređenje

        Args:
            q_type: Tip pitanja
            user_answer: Odgovor korisnika
            correct_answer: Tačan odgovor
            extra_data: Dodatni podaci (za kompleksne tipove)

        Returns:
            bool: True ako je odgovor tačan
        """
        user_answer = (user_answer or "").strip().lower()
        correct_answer = (correct_answer or "").strip().lower()

        if q_type in ("multiple_choice", "true_false", "calculation"):
            return user_answer == correct_answer

        elif q_type == "checkbox":
            correct_parts = set(
                p.strip().lower() for p in correct_answer.split(",") if p.strip()
            )
            user_parts = set(
                p.strip().lower() for p in user_answer.split(",") if p.strip()
            )
            return correct_parts == user_parts

        elif q_type == "sequencing":
            correct_indices = [i.strip() for i in correct_answer.split(",")]
            user_indices = [i.strip() for i in user_answer.split(",")]
            return correct_indices == user_indices

        elif q_type == "categorization":
            try:
                correct_map = json.loads(correct_answer)
                user_map = json.loads(user_answer)
                return correct_map == user_map
            except Exception:
                return False

        elif q_type == "matching":
            try:
                correct_pairs = json.loads(correct_answer)
                user_pairs = json.loads(user_answer)
                return set(correct_pairs) == set(user_pairs)
            except Exception:
                return False

        elif q_type == "estimation":
            try:
                user_num = float(user_answer)
                correct_num = float(correct_answer)
                tolerance = float(extra_data.get("tolerance", 10)) if extra_data else 10
                return abs(user_num - correct_num) <= tolerance
            except Exception:
                return False

        elif q_type == "matrix":
            try:
                correct_answers = json.loads(correct_answer)
                user_answers = json.loads(user_answer)
                return correct_answers == user_answers
            except Exception:
                return False

        elif q_type == "matching":
            try:
                correct_pairs = json.loads(correct_answer)
                user_pairs = json.loads(user_answer)
                return set(correct_pairs) == set(user_pairs)
            except Exception:
                return False

        elif q_type == "odd_one_out":
            correct_items = [i.strip().lower() for i in correct_answer.split(",")]
            return user_answer.strip().lower() in correct_items

        elif q_type == "estimation":
            try:
                user_num = float(user_answer)
                correct_num = float(correct_answer)
                tolerance = float(extra_data.get("tolerance", 10)) if extra_data else 10
                return abs(user_num - correct_num) <= tolerance
            except Exception:
                return False

        elif q_type == "matrix":
            try:
                correct_answers = json.loads(correct_answer)
                user_answers = json.loads(user_answer)
                return correct_answers == user_answers
            except Exception:
                return False

        elif q_type == "hotspot":
            return user_answer == correct_answer

        elif q_type in ("text_input", "fill_blank"):
            return QuizService._check_text_input_answer_static(
                user_answer, correct_answer, extra_data
            )

        return False

    @staticmethod
    def _check_text_input_answer_static(
        user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        """Proverava tekstualni odgovor za text_input tip."""
        if not user_answer or not correct_answer:
            return False

        user_answer = user_answer.strip()
        correct_answer = correct_answer.strip()

        case_insensitive = True
        exact_word = False
        fuzzy = False
        transliterate = True

        if extra_data:
            case_insensitive = extra_data.get("case_insensitive", True)
            exact_word = extra_data.get("exact_word", False)
            fuzzy = extra_data.get("fuzzy", False)
            transliterate = extra_data.get("transliterate", True)

        if transliterate:
            user_answer = _transliterate_text(user_answer)
            correct_answer = _transliterate_text(correct_answer)

        if case_insensitive:
            user_answer = user_answer.lower()
            correct_answer = correct_answer.lower()

        if exact_word:
            return user_answer == correct_answer

        if fuzzy:
            user_words = set(user_answer.split())
            correct_words = set(correct_answer.split())
            matching = len(user_words & correct_words) / max(len(correct_words), 1)
            return matching >= 0.8

        return user_answer == correct_answer

    @staticmethod
    def _check_fill_blank_answer_static(
        user_answer: str, correct_answer: str, extra_data: dict = None
    ) -> bool:
        """Proverava fill_blank odgovor sa alternativnim rečima."""
        if not user_answer or not correct_answer:
            return False

        user_answer = user_answer.strip()
        correct_answers = [
            a.strip() for a in re.split(r"[,|]", correct_answer) if a.strip()
        ]

        if not correct_answers:
            return False

        case_insensitive = True
        if extra_data:
            case_insensitive = extra_data.get("case_insensitive", True)

        user_answer = _transliterate_text(user_answer)
        if case_insensitive:
            user_answer = user_answer.lower()

        for correct in correct_answers:
            correct_processed = _transliterate_text(correct)
            if case_insensitive:
                correct_processed = correct_processed.lower()
            if user_answer == correct_processed:
                return True

        return False

    def _check_text_input_answer(
        self,
        user_answer: str,
        correct_answer: str,
        exact_word: bool,
        case_insensitive: bool,
    ) -> bool:
        """Wrapper for calling static method as instance method."""
        return QuizService._check_text_input_answer_static(
            user_answer,
            correct_answer,
            {"exact_word": exact_word, "case_insensitive": case_insensitive},
        )

    def _check_fill_blank_answer(
        self,
        user_answer: str,
        correct_answer: str,
        exact_word: bool,
        case_insensitive: bool,
    ) -> bool:
        """Wrapper for calling static method as instance method."""
        return QuizService._check_fill_blank_answer_static(
            user_answer,
            correct_answer,
            {"exact_word": exact_word, "case_insensitive": case_insensitive},
        )

    @staticmethod
    def get_available_providers() -> dict:
        """Vraća listu svih dostupnih provajdera."""
        from app.services.quiz.clients import get_available_providers as gap

        return gap()

    def _get_image_for_vision(self, img, storage, timeout: int = 5) -> Tuple[str, str]:
        """
        Hibridni pristup: prvo probaj MinIO URL, pa fallback na base64.
        """
        import base64

        try:
            public_url = storage.get_public_url(img.storage_path)
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

            import io
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
        self,
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
    ) -> Tuple[bool, List[dict], str]:
        """
        Generiše pitanja koristeći AI.
        """
        if not subject_area:
            logger.info("Detecting subject area...")
            from app.services.quiz.service import detect_subject_area

            subject_area = detect_subject_area(text)
            logger.info(f"Detected subject area: {subject_area}")

        from app.services.quiz.service import get_specialized_prompt

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

    def create_quiz_from_document(
        self,
        db: Session,
        document_id: str,
        user_id: str,
        num_questions: int = 5,
        time_limit: Optional[int] = None,
        passing_score: int = 60,
    ) -> Quiz:
        """Kreira Quiz zapis (status=generating), task generiše pitanja asinhrono."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Dokument nije pronađen: {document_id}")

        expected = num_questions if num_questions > 0 else 10

        quiz = Quiz(
            document_id=document_id,
            user_id=user_id,
            title=f"Kviz: {document.title}",
            description=f"Automatski generisan kviz iz dokumenta '{document.title}'",
            time_limit=time_limit,
            passing_score=passing_score,
            status="generating",
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return quiz

    def generate_quiz_questions(
        self,
        db: Session,
        quiz_id: str,
        num_questions: int = 5,
        user_openai_key: Optional[str] = None,
        user_claude_key: Optional[str] = None,
        user_gemini_key: Optional[str] = None,
        user_groq_key: Optional[str] = None,
        user_mistral_key: Optional[str] = None,
        user_deepseek_key: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Generiše pitanja za kviz."""
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

        total_chars = sum(len(c.content or "") for c in selected_chunks)
        text = "\n\n".join(
            c.content or c.translated_content or "" for c in selected_chunks
        )

        num_to_generate = _auto_num_questions(len(selected_chunks), num_questions)

        from app.services.quiz import update_quiz_progress

        update_quiz_progress(
            quiz_id, "started", 5, f"0 / {num_to_generate} - Priprema..."
        )
        update_quiz_progress(
            quiz_id, "processing", 10, f"Generisanje pitanja: 0 / {num_to_generate}"
        )

        ok, questions, provider = self.generate_questions_with_ai(
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
            question_text = cyrillic_to_latin(q_data.get("question_text", ""))
            options = [cyrillic_to_latin(opt) for opt in q_data.get("options", [])]
            correct_answer = cyrillic_to_latin(q_data.get("correct_answer", ""))
            explanation = cyrillic_to_latin(q_data.get("explanation", ""))

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

    def submit_quiz_answer(
        self,
        db: Session,
        quiz_id: str,
        question_id: str,
        selected_answer: str,
    ) -> Tuple[bool, int, str]:
        """Proverava odgovor i vraća poene."""
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False, 0, "Pitanje nije pronađeno"

        is_correct = False
        correct = question.correct_answer

        if question.question_type in ("multiple_choice", "calculation"):
            is_correct = selected_answer.strip().lower() == correct.strip().lower()
        elif question.question_type == "true_false":
            is_correct = selected_answer.strip().lower() == correct.strip().lower()
        elif question.question_type == "checkbox":
            correct_parts = set(p.strip().lower() for p in correct.split(","))
            selected_parts = set(p.strip().lower() for p in selected_answer.split(","))
            is_correct = correct_parts == selected_parts
        elif question.question_type == "text_input":
            is_correct = self._check_text_input_answer(
                selected_answer, correct, question.exact_word, question.case_insensitive
            )
        elif question.question_type == "fill_blank":
            is_correct = self._check_fill_blank_answer(
                selected_answer, correct, question.exact_word, question.case_insensitive
            )

        points = question.points if is_correct else 0

        return True, points, "Tačno" if is_correct else "Netačno"

    def get_quiz(self, db: Session, quiz_id: str) -> Optional[Quiz]:
        """Dohvata kviz sa pitanjima."""
        return db.query(Quiz).filter(Quiz.id == quiz_id).first()

    def get_quiz_questions(self, db: Session, quiz_id: str) -> List[Question]:
        """Dohvata sva pitanja za kviz."""
        return (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.order_index)
            .all()
        )


quiz_service = QuizService()


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
    """Fallback detekcija ako pdf_detector nije dostupan."""
    keywords = {
        "matematika": [
            "jednačina",
            "rešenje",
            "zadatak",
            "površina",
            "zapremina",
            "trougao",
            "krug",
            "vektor",
            "matrica",
            "funkcija",
            "izvod",
            "integral",
            "formula",
            "računati",
        ],
        "fizika": [
            "sila",
            "energija",
            "brzina",
            "ubrzanj",
            "masa",
            "temperatur",
            "pritisak",
            "električn",
            "magnet",
            "talas",
            "optika",
            "mehanika",
            "termodinamika",
        ],
        "hemija": [
            "atom",
            "molekul",
            "reakcija",
            "element",
            "jedinjenje",
            "kiselina",
            "baza",
            "oksidacija",
            "redukcija",
            "hemijski",
        ],
        "biologija": [
            "ćelija",
            "organ",
            "sistem",
            "tkivo",
            "organizam",
            "Dnk",
            "RNK",
            "gen",
            "evolucija",
            "ekologija",
        ],
        "istorija": [
            "godina",
            "vek",
            "rat",
            "država",
            "vladar",
            "car",
            "kralj",
            "istorijski",
            "događaj",
            "period",
            "civilizacija",
        ],
        "geografija": [
            "država",
            "grad",
            "reka",
            "planina",
            "more",
            "kontinent",
            "klimat",
            "populacija",
            "reljef",
            "region",
        ],
        "informatika": [
            "program",
            "algoritam",
            "kod",
            "funkcija",
            "varijabla",
            "klasa",
            "objekat",
            "baza",
            "podatak",
            "mreža",
        ],
    }

    text_lower = text.lower()
    scores = {}

    for area, words in keywords.items():
        score = sum(1 for w in words if w in text_lower)
        scores[area] = score

    if not scores or max(scores.values()) == 0:
        return "opšte"

    return max(scores, key=scores.get)


def get_specialized_prompt(subject_area: str, num_questions: int, text: str) -> str:
    """Vraća specijalizovani prompt za oblast."""
    return QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])


def _check_answer_static(
    q_type: str, user_answer: str, correct_answer: str, extra_data: dict = None
) -> bool:
    """
    Standalone function for checking quiz answers.

    Podržava sve tipove pitanja (ažurirano 2026-04-06):
    - multiple_choice, true_false, calculation: direktno poređenje
    - checkbox: skupovno poređenje
    - sequencing: poređenje niza indeksa
    - categorization: poređenje mapping-a
    - matching: poređenje parova
    - odd_one_out: direktno poređenje
    - estimation: tolerance-based
    - matrix: poređenje niza
    - hotspot: direktno poređenje

    Args:
        q_type: Tip pitanja
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        extra_data: Dodatni podaci

    Returns:
        bool: True ako je odgovor tačan
    """
    # Prosleđuje QuizService._check_answer_static za logiku
    return QuizService._check_answer_static(
        q_type, user_answer, correct_answer, extra_data
    )


def _check_text_input_answer(
    user_answer: str, correct_answer: str, exact_word: bool, case_insensitive: bool
) -> bool:
    """
    Proverava tekstualni odgovor za text_input tip pitanja.

    Args:
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        exact_word: Zahtevaj potpuno poklapanje reči
        case_insensitive: Ignoriši velika/mala slova

    Returns:
        bool: True ako je odgovor tačan
    """
    from app.services.quiz.service import QuizService

    return QuizService._check_text_input_answer_static(
        user_answer,
        correct_answer,
        {"exact_word": exact_word, "case_insensitive": case_insensitive},
    )


def _check_fill_blank_answer(
    user_answer: str, correct_answer: str, exact_word: bool, case_insensitive: bool
) -> bool:
    """
    Proverava odgovor za fill_blank tip pitanja sa alternativnim rečima.

    Args:
        user_answer: Odgovor korisnika
        correct_answer: Tačan odgovor
        exact_word: Zahtevaj potpuno poklapanje
        case_insensitive: Ignoriši velika/mala slova

    Returns:
        bool: True ako je odgovor tačan
    """
    from app.services.quiz.service import QuizService

    return QuizService._check_fill_blank_answer_static(
        user_answer,
        correct_answer,
        {"exact_word": exact_word, "case_insensitive": case_insensitive},
    )
