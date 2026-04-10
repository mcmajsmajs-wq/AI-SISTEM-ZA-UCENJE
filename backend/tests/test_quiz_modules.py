# -*- coding: utf-8 -*-
"""
================================================================================
TEST QUIZ MODULES - Phase 2 & 3 Full Verification
================================================================================

Testovi za verifikaciju svih novih modula:
- prompts/subjects.py
- helpers/subject_detection.py
- helpers/document_structure.py
- helpers/progress.py

Verzija: 1.0.0
================================================================================
"""

import pytest
from unittest.mock import Mock, patch


class TestSubjectsModule:
    """Testovi za prompts/subjects.py"""

    def test_get_specialized_prompt_returns_string(self):
        """Test da get_specialized_prompt vraća string."""
        from app.services.quiz.prompts import get_specialized_prompt

        result = get_specialized_prompt("matematika", 5, "Test text")

        assert isinstance(result, str)
        assert len(result) > 1000

    def test_get_specialized_prompt_includes_subject_instruction(self):
        """Test da specijalizovani prompt sadrži instrukcije za oblast."""
        from app.services.quiz.prompts import get_specialized_prompt

        result = get_specialized_prompt("matematika", 5, "Test text")

        assert "MATEMATIKA" in result or "matematika" in result.lower()

    def test_get_subject_instruction(self):
        """Test get_subject_instruction funkcije."""
        from app.services.quiz.prompts import get_subject_instruction

        result = get_subject_instruction("fizika")

        assert isinstance(result, str)
        assert len(result) > 10

    def test_get_all_subjects(self):
        """Test da get_all_subjects vraća sve oblasti."""
        from app.services.quiz.prompts import get_all_subjects

        subjects = get_all_subjects()

        assert isinstance(subjects, list)
        assert "matematika" in subjects
        assert "fizika" in subjects
        assert "hemija" in subjects
        assert len(subjects) >= 10


class TestSubjectDetectionModule:
    """Testovi za helpers/subject_detection.py"""

    def test_detect_subject_area_math(self):
        """Test detekcije matematike."""
        from app.services.quiz.helpers.subject_detection import detect_subject_area

        text = "Jednačina x + y = 5 predstavlja linearnu jednačinu. Izračunati površinu trougla."
        result = detect_subject_area(text)

        assert result == "matematika"

    def test_detect_subject_area_physics(self):
        """Test detekcije fizike."""
        from app.services.quiz.helpers.subject_detection import detect_subject_area

        text = "Sila F = m * a. Brzina v = s / t. Energija je kinetička."
        result = detect_subject_area(text)

        assert result == "fizika"

    def test_detect_subject_area_chemistry(self):
        """Test detekcije hemije."""
        from app.services.quiz.helpers.subject_detection import detect_subject_area

        text = (
            "Atom je najmanja jedinica hemijskog elementa. Molekul se sastoji od atoma."
        )
        result = detect_subject_area(text)

        assert result == "hemija"

    def test_detect_subject_area_empty_text(self):
        """Test za prazan tekst."""
        from app.services.quiz.helpers.subject_detection import detect_subject_area

        result = detect_subject_area("")

        assert result == "ostalo"

    def test_get_subject_keywords(self):
        """Test get_subject_keywords."""
        from app.services.quiz.helpers.subject_detection import get_subject_keywords

        keywords = get_subject_keywords("matematika")

        assert isinstance(keywords, list)
        assert "jednačina" in keywords
        assert "površina" in keywords

    def test_get_all_subjects(self):
        """Test get_all_subjects."""
        from app.services.quiz.helpers.subject_detection import get_all_subjects

        subjects = get_all_subjects()

        assert isinstance(subjects, list)
        assert "matematika" in subjects
        assert "fizika" in subjects


class TestDocumentStructureModule:
    """Testovi za helpers/document_structure.py"""

    def test_detect_document_structure_test(self):
        """Test detekcije strukture test."""
        from app.services.quiz.helpers.document_structure import (
            detect_document_structure,
        )

        text = "Pitanje 1: Koji je glavni grad? Odgovor: Beograd. Test iz matematike."
        result = detect_document_structure(text)

        assert result == "test"

    def test_detect_document_structure_zadaci(self):
        """Test detekcije strukture zadaci."""
        from app.services.quiz.helpers.document_structure import (
            detect_document_structure,
        )

        text = "Zadatak: Izračunati površinu kvadrata. Rešenje: P = a * a"
        result = detect_document_structure(text)

        assert result == "zadaci"

    def test_detect_document_structure_formula(self):
        """Test detekcije strukture formula."""
        from app.services.quiz.helpers.document_structure import (
            detect_document_structure,
        )

        text = "Formula: E = mc^2. Jednačina: a^2 + b^2 = c^2"
        result = detect_document_structure(text)

        assert result == "formula"

    def test_get_structure_based_prompt(self):
        """Test get_structure_based_prompt."""
        from app.services.quiz.helpers.document_structure import get_structure_based_prompt
        
        result = get_structure_based_prompt("zadaci")
        
        assert isinstance(result, str)
        assert "zadatak" in result.lower() or "zadatke" in result.lower() or "postupak" in result.lower()

    def test_get_all_structures(self):
        """Test get_all_structures."""
        from app.services.quiz.helpers.document_structure import get_all_structures

        structures = get_all_structures()

        assert isinstance(structures, list)
        assert "test" in structures
        assert "zadaci" in structures


class TestProgressModule:
    """Testovi za helpers/progress.py"""

    @patch("app.services.quiz.helpers.progress._get_redis")
    def test_update_quiz_progress_success(self, mock_redis):
        """Test uspešnog update-a progressa."""
        from app.services.quiz.helpers.progress import update_quiz_progress

        mock_client = Mock()
        mock_redis.return_value = mock_client

        result = update_quiz_progress("task-123", "started", 0, "Starting")

        assert result is True
        mock_client.setex.assert_called_once()

    @patch("app.services.quiz.helpers.progress._get_redis")
    def test_get_quiz_progress(self, mock_redis):
        """Test dohvatanja progressa."""
        from app.services.quiz.helpers.progress import get_quiz_progress

        mock_client = Mock()
        mock_client.get.return_value = '{"task_id": "task-123", "status": "started"}'
        mock_redis.return_value = mock_client

        result = get_quiz_progress("task-123")

        assert result is not None
        assert result["task_id"] == "task-123"

    @patch("app.services.quiz.helpers.progress._get_redis")
    def test_set_quiz_cache(self, mock_redis):
        """Test postavljanja cache-a."""
        from app.services.quiz.helpers.progress import set_quiz_cache

        mock_client = Mock()
        mock_redis.return_value = mock_client

        result = set_quiz_cache(1, "test-key", {"data": "value"})

        assert result is True

    @patch("app.services.quiz.helpers.progress._get_redis")
    def test_get_quiz_cache(self, mock_redis):
        """Test dohvatanja cache-a."""
        from app.services.quiz.helpers.progress import get_quiz_cache

        mock_client = Mock()
        mock_client.get.return_value = '{"data": "value"}'
        mock_redis.return_value = mock_client

        result = get_quiz_cache(1, "test-key")

        assert result is not None


class TestIntegrationFullModule:
    """Integration testovi za kompletan quiz modul."""

    def test_all_exports_available(self):
        """Test da svi export-i postoje."""
        from app.services import quiz

        # Prompts
        assert hasattr(quiz, "QUIZ_PROMPT")
        assert hasattr(quiz, "get_specialized_prompt")

        # Helpers - parsing
        assert callable(quiz._parse_questions)
        assert callable(quiz._validate_questions)
        assert callable(quiz._fallback_questions)

        # Helpers - subject detection
        assert callable(quiz.detect_subject_area)
        assert hasattr(quiz, "SUBJECT_KEYWORDS")

        # Helpers - document structure
        assert callable(quiz.detect_document_structure)
        assert hasattr(quiz, "STRUCTURE_PATTERNS")

        # Helpers - progress
        assert callable(quiz.update_quiz_progress)
        assert callable(quiz.get_quiz_progress)

        # Clients
        assert hasattr(quiz, "get_clients")
        assert hasattr(quiz, "get_available_providers")

        # Service
        assert hasattr(quiz, "QuizService")
        assert hasattr(quiz, "quiz_service")

    def test_detect_subject_and_structure_together(self):
        """Test korišćenja obe funkcije zajedno."""
        from app.services import quiz

        text = """
        Zadatak: Izračunati površinu pravougaonika.
        Stranice a = 5cm i b = 3cm.
        Formula: P = a * b = 5 * 3 = 15cm²
        """

        subject = quiz.detect_subject_area(text)
        structure = quiz.detect_document_structure(text)

        assert subject == "matematika"
        assert structure == "zadaci"

    def test_specialized_prompt_with_subject(self):
        """Test specijalizovanog prompta sa detektovanim subjectom."""
        from app.services import quiz

        text = "Jednačina x² + y² = r² predstavlja krug."

        subject = quiz.detect_subject_area(text)
        prompt = quiz.get_specialized_prompt(subject, 5, text)

        assert isinstance(prompt, str)
        assert len(prompt) > 1000


class TestBackwardCompatibility:
    """Testovi za backward compatibility."""

    def test_old_imports_still_work(self):
        """Test da stari import-i i dalje rade."""
        from app.services.quiz import (
            quiz_service,
            QuizService,
            QUIZ_PROMPT,
            _parse_questions,
            get_available_providers,
        )

        assert quiz_service is not None
        assert QuizService is not None
        assert QUIZ_PROMPT is not None
        assert callable(_parse_questions)
        assert callable(get_available_providers)

    def test_quiz_service_method_compatibility(self):
        """Test da QuizService metode rade."""
        from app.services.quiz import QuizService

        service = QuizService()

        # Test get_available_providers
        providers = service.get_available_providers()
        assert isinstance(providers, list)

        # Test _check_answer_static
        result = QuizService._check_answer_static(
            "multiple_choice", "beograd", "beograd"
        )
        assert result is True
