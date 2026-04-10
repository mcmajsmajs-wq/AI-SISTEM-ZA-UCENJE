# -*- coding: utf-8 -*-
"""
================================================================================
TEST QUIZ PROMPTS & HELPERS - Phase 2
================================================================================

Testovi za verifikaciju Phase 2 implementacije:
- prompts/quiz_prompt.py - QUIZ_PROMPT template
- prompts/subjects.py - Subject-specific prompts (ako postoji)
- helpers/parsing.py - Question parsing
- helpers/chunks.py - Chunk selection
- helpers/subject_detection.py - Subject detection (ako postoji)

Verzija: 1.0.0
================================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List


class TestQuizPrompt:
    """Testovi za QUIZ_PROMPT template."""

    def test_quiz_prompt_exists(self):
        """Test da QUIZ_PROMPT postoji."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        assert QUIZ_PROMPT is not None
        assert isinstance(QUIZ_PROMPT, str)

    def test_quiz_prompt_has_placeholders(self):
        """Test da QUIZ_PROMPT ima potrebne placeholder-e."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        assert "{num_questions}" in QUIZ_PROMPT
        assert "{text}" in QUIZ_PROMPT or "text" in QUIZ_PROMPT.lower()

    def test_quiz_prompt_minimum_length(self):
        """Test da je QUIZ_PROMPT dovoljno dugačak."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        assert len(QUIZ_PROMPT) > 1000, "QUIZ_PROMPT should be substantial"

    def test_quiz_prompt_contains_filter_rules(self):
        """Test da QUIZ_PROMPT sadrži filter pravila."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        prompt_lower = QUIZ_PROMPT.lower()
        assert "filter" in prompt_lower or "ignore" in prompt_lower

    def test_quiz_prompt_contains_question_types(self):
        """Test da QUIZ_PROMPT definiše tipove pitanja."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        prompt_lower = QUIZ_PROMPT.lower()
        assert "multiple_choice" in prompt_lower or "multiple" in prompt_lower
        assert "true_false" in prompt_lower or "true" in prompt_lower

    def test_quiz_prompt_contains_explanation_rules(self):
        """Test da QUIZ_PROMPT ima pravila za objašnjenja."""
        from app.services.quiz.prompts import QUIZ_PROMPT

        prompt_lower = QUIZ_PROMPT.lower()
        assert "explanation" in prompt_lower or "explain" in prompt_lower


class TestParsing:
    """Testovi za parsing funkcije."""

    def test_parse_questions_valid_json(self):
        """Test parsiranja validnog JSON-a."""
        from app.services.quiz.helpers import _parse_questions

        raw = '[{"question_text": "Koji je glavni grad Srbije?", "question_type": "multiple_choice", "options": ["Beograd", "Novi Sad", "Nis", "Kragujevac"], "correct_answer": "Beograd"}]'
        result = _parse_questions(raw)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_questions_json_with_wrapper(self):
        """Test parsiranja JSON-a sa wrapper objektom."""
        from app.services.quiz.helpers import _parse_questions

        raw = '{"questions": [{"question_text": "Test?", "question_type": "multiple_choice", "options": ["A", "B"], "correct_answer": "A"}]}'
        result = _parse_questions(raw)

        assert isinstance(result, list)

    def test_parse_questions_with_regex(self):
        """Test parsiranja JSON-a pomoću regex-a."""
        from app.services.quiz.helpers import _parse_questions

        raw = 'Some text before [{"question_text": "Test?", "question_type": "multiple_choice", "options": ["A", "B"], "correct_answer": "A"}] some text after'
        result = _parse_questions(raw)

        assert isinstance(result, list)

    def test_parse_questions_invalid_returns_empty(self):
        """Test da nevalidan JSON vraća praznu listu."""
        from app.services.quiz.helpers import _parse_questions

        raw = "This is not JSON at all"
        result = _parse_questions(raw)

        assert isinstance(result, list)
        assert len(result) == 0


class TestValidateQuestions:
    """Testovi za validaciju pitanja."""

    def test_validate_questions_valid(self):
        """Test validacije validnih pitanja."""
        from app.services.quiz.helpers import _validate_questions

        data = [
            {
                "question_text": "Koji je glavni grad Srbije?",
                "question_type": "multiple_choice",
                "options": ["Beograd", "Novi Sad", "Niš", "Kragujevac"],
                "correct_answer": "Beograd",
            }
        ]
        result = _validate_questions(data)

        assert len(result) > 0

    def test_validate_questions_missing_fields(self):
        """Test da nedostajuća polja rezultiraju preskakanjem."""
        from app.services.quiz.helpers import _validate_questions

        data = [
            {
                "question_text": "Test?",
                "question_type": "multiple_choice",
                # Missing: options, correct_answer
            }
        ]
        result = _validate_questions(data)

        assert len(result) == 0

    def test_validate_questions_adds_defaults(self):
        """Test da se dodaju default vrednosti."""
        from app.services.quiz.helpers import _validate_questions

        data = [
            {
                "question_text": "Koji je glavni grad Srbije?",
                "question_type": "multiple_choice",
                "options": ["Beograd", "Novi Sad", "Niš", "Kragujevac"],
                "correct_answer": "Beograd",
            }
        ]
        result = _validate_questions(data)

        assert "explanation" in result[0]
        assert "points" in result[0]
        assert "order_index" in result[0]

    def test_validate_questions_checkbox_conversion(self):
        """Test da se checkbox sa 1 odgovor konvertuje u multiple_choice."""
        from app.services.quiz.helpers import _validate_questions

        data = [
            {
                "question_text": "Koji su glavni gradovi u Srbiji?",
                "question_type": "checkbox",
                "options": ["Beograd", "Novi Sad", "Niš", "Kragujevac"],
                "correct_answer": "Beograd",
            }
        ]
        result = _validate_questions(data)

        assert result[0]["question_type"] == "multiple_choice"

    def test_validate_questions_checkbox_multiple_answers(self):
        """Test da checkbox sa više odgovora zadržava tip."""
        from app.services.quiz.helpers import _validate_questions

        data = [
            {
                "question_text": "Koji su glavni gradovi u Srbiji?",
                "question_type": "checkbox",
                "options": ["Beograd", "Novi Sad", "Niš", "Kragujevac"],
                "correct_answer": "Beograd, Novi Sad",
            }
        ]
        result = _validate_questions(data)

        assert result[0]["question_type"] == "checkbox"
        assert result[0]["points"] >= 2


class TestFallbackQuestions:
    """Testovi za fallback pitanja."""

    def test_fallback_questions_returns_list(self):
        """Test da fallback vraća listu."""
        from app.services.quiz.helpers import _fallback_questions

        text = "Ovo je test tekst. Ovo je drugi tekst. Ovo je treci tekst."
        result = _fallback_questions(text, 3)

        assert isinstance(result, list)
        assert len(result) == 3

    def test_fallback_questions_structure(self):
        """Test da fallback pitanja imaju ispravnu strukturu."""
        from app.services.quiz.helpers import _fallback_questions

        text = "Ovo je test tekst. Ovo je drugi tekst. Ovo je treci tekst."
        result = _fallback_questions(text, 1)

        assert "question_text" in result[0]
        assert "question_type" in result[0]
        assert "options" in result[0]
        assert "correct_answer" in result[0]

    def test_fallback_questions_type(self):
        """Test da su fallback pitanja tipa true_false."""
        from app.services.quiz.helpers import _fallback_questions

        text = "Ovo je test tekst. Ovo je drugi tekst. Ovo je treci tekst."
        result = _fallback_questions(text, 1)

        assert result[0]["question_type"] == "true_false"

    def test_fallback_questions_has_explanation(self):
        """Test da fallback pitanja imaju objašnjenje."""
        from app.services.quiz.helpers import _fallback_questions

        text = "Ovo je test tekst. Ovo je drugi tekst. Ovo je treci tekst."
        result = _fallback_questions(text, 1)

        assert "explanation" in result[0]
        assert len(result[0]["explanation"]) > 0


class TestChunkQuality:
    """Testovi za proveru kvaliteta chunk-a."""

    def test_is_chunk_quality_valid(self):
        """Test da validan chunk prolazi."""
        from app.services.quiz.helpers import is_chunk_quality

        text = "Ovo je validan tekst chunka koji ima dovoljno sadrzaja za quiz."
        result = is_chunk_quality(text)

        assert result is True

    def test_is_chunk_quality_too_short(self):
        """Test da prekratak chunk ne prolazi."""
        from app.services.quiz.helpers import is_chunk_quality

        text = "Kratak tekst"
        result = is_chunk_quality(text)

        assert result is False

    def test_is_chunk_quality_copyright(self):
        """Test da copyright notice ne prolazi."""
        from app.services.quiz.helpers import is_chunk_quality

        text = "Copyright 2024 all rights reserved. Neki sadrzaj."
        result = is_chunk_quality(text)

        assert result is False

    def test_is_chunk_quality_blank_page(self):
        """Test da blank page ne prolazi."""
        from app.services.quiz.helpers import is_chunk_quality

        text = "This page intentionally left blank"
        result = is_chunk_quality(text)

        assert result is False


class TestSelectChunksForQuiz:
    """Testovi za selekciju chunk-ova."""

    def test_select_chunks_empty(self):
        """Test za praznu listu."""
        from app.services.quiz.helpers import select_chunks_for_quiz

        result = select_chunks_for_quiz([])

        assert result == []

    def test_select_chunks_under_limit(self):
        """Test da svi chunk-ovi prolaze ako su ispod limita."""
        from app.services.quiz.helpers import select_chunks_for_quiz

        chunks = [
            {"text": "Text 1 " * 50},
            {"text": "Text 2 " * 50},
        ]
        result = select_chunks_for_quiz(chunks, max_chars=10000)

        assert len(result) == 2

    def test_select_chunks_filters_quality(self):
        """Test da se filtriraju low-quality chunk-ovi."""
        from app.services.quiz.helpers import select_chunks_for_quiz, is_chunk_quality

        chunks = [
            {"text": "Valid content here with enough text to pass the quality check"},
            {"text": "Copyright 2024 all rights reserved"},
            {"text": "Another valid content chunk with sufficient text"},
        ]
        result = select_chunks_for_quiz(chunks)

        # Should filter out copyright notice
        assert all(is_chunk_quality(c["text"]) for c in result)


class TestGetImagesForChunks:
    """Testovi za mapiranje slika na chunk-ove."""

    def test_get_images_for_chunks_empty(self):
        """Test za prazne inpute."""
        from app.services.quiz.helpers import get_images_for_chunks

        result = get_images_for_chunks([], [])

        assert result == {}

    def test_get_images_for_chunks_mapping(self):
        """Test mapiranja slika na chunk-ove."""
        from app.services.quiz.helpers import get_images_for_chunks

        chunks = [{"id": 1}, {"id": 2}]
        images = [
            {"chunk_id": 1, "url": "img1.jpg"},
            {"chunk_id": 2, "url": "img2.jpg"},
        ]

        result = get_images_for_chunks(chunks, images)

        assert 1 in result
        assert 2 in result
        assert len(result[1]) == 1


class TestGetQuizUsageStats:
    """Testovi za statistiku korišćenja."""

    def test_get_quiz_usage_stats_all_unused(self):
        """Test kada nijedan chunk nije korišćen."""
        from app.services.quiz.helpers import get_quiz_usage_stats

        chunks = [{"used_in_quiz": False}, {"used_in_quiz": False}]
        result = get_quiz_usage_stats(chunks)

        assert result["total"] == 2
        assert result["used_in_quiz"] == 0
        assert result["unused"] == 2

    def test_get_quiz_usage_stats_all_used(self):
        """Test kada su svi chunk-ovi korišćeni."""
        from app.services.quiz.helpers import get_quiz_usage_stats

        chunks = [{"used_in_quiz": True}, {"used_in_quiz": True}]
        result = get_quiz_usage_stats(chunks)

        assert result["total"] == 2
        assert result["used_in_quiz"] == 2
        assert result["unused"] == 0

    def test_get_quiz_usage_stats_percentage(self):
        """Test izračunavanja procenta."""
        from app.services.quiz.helpers import get_quiz_usage_stats

        chunks = [{"used_in_quiz": True}, {"used_in_quiz": False}]
        result = get_quiz_usage_stats(chunks)

        assert result["usage_percentage"] == 50.0


class TestMarkChunksAsUsed:
    """Testovi za označavanje chunk-ova."""

    def test_mark_chunks_as_used_empty(self):
        """Test za praznu listu."""
        from app.services.quiz.helpers import mark_chunks_as_used

        # Should not raise an error
        result = mark_chunks_as_used([], Mock())

        assert result is None


class TestModuleImports:
    """Testovi za module import-e."""

    def test_prompts_import(self):
        """Test import-a prompts modula."""
        from app.services.quiz import prompts

        assert hasattr(prompts, "QUIZ_PROMPT")

    def test_helpers_import(self):
        """Test import-a helpers modula."""
        from app.services.quiz import helpers

        # Check all expected functions are exported
        expected = [
            "_parse_questions",
            "_validate_questions",
            "_fallback_questions",
            "is_chunk_quality",
            "select_chunks_for_quiz",
            "get_images_for_chunks",
            "get_quiz_usage_stats",
            "mark_chunks_as_used",
        ]

        for func in expected:
            assert hasattr(helpers, func), f"Missing: {func}"

    def test_full_import_from_service(self):
        """Test potpunog import-a iz app.services.quiz."""
        from app.services import quiz

        # Check all exports exist
        assert hasattr(quiz, "QUIZ_PROMPT")
        assert hasattr(quiz, "_parse_questions")
        assert hasattr(quiz, "_validate_questions")
        assert hasattr(quiz, "_fallback_questions")
        assert hasattr(quiz, "is_chunk_quality")
        assert hasattr(quiz, "select_chunks_for_quiz")

    def test_quiz_prompt_in_service_import(self):
        """Test da je QUIZ_PROMPT dostupan u app.services.quiz."""
        from app.services.quiz import QUIZ_PROMPT

        assert QUIZ_PROMPT is not None
        assert len(QUIZ_PROMPT) > 1000


class TestBackwardCompatibility:
    """Testovi za backward compatibility."""

    def test_helpers_exports_in_quiz_module(self):
        """Test da su helpers funkcije eksportovane u quiz modulu."""
        from app.services import quiz

        # All helper functions should be accessible
        assert callable(quiz._parse_questions)
        assert callable(quiz._validate_questions)
        assert callable(quiz._fallback_questions)
        assert callable(quiz.is_chunk_quality)
        assert callable(quiz.select_chunks_for_quiz)
        assert callable(quiz.get_images_for_chunks)
        assert callable(quiz.get_quiz_usage_stats)
        assert callable(quiz.mark_chunks_as_used)

    def test_prompt_exported_in_quiz_module(self):
        """Test da je QUIZ_PROMPT eksportovan u quiz modulu."""
        from app.services import quiz

        assert quiz.QUIZ_PROMPT is not None
        assert isinstance(quiz.QUIZ_PROMPT, str)
