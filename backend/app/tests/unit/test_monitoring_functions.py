# -*- coding: utf-8 -*-
"""
================================================================================
MONITORING FUNCTIONS TESTS
================================================================================
Unit testovi za utils/monitoring.py funkcije.

Pokretanje:
    pytest tests/unit/test_monitoring_functions.py -v
================================================================================
"""

from unittest.mock import patch

from app.utils.monitoring import (
    log_action,
    log_quiz_generation,
    log_quiz_progress,
    log_quiz_complete,
    log_pdf_processing,
    log_ocr_progress,
    get_system_status,
)


class TestLogAction:
    """Testovi za log_action dekorator."""

    def test_log_action_decorator(self):
        """Test da dekorator radi."""

        @log_action("test_action")
        def test_function():
            return "result"

        result = test_function()
        assert result == "result"

    def test_log_action_with_args(self):
        """Test sa argumentima."""

        @log_action("add")
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5


class TestLogQuizGeneration:
    """Testovi za log_quiz_generation."""

    def test_log_quiz_generation(self):
        """Test beleženja generisanja kviza."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_quiz_generation("openai", "doc-123", 10)

            mock_logger.info.assert_called_once()


class TestLogQuizProgress:
    """Testovi za log_quiz_progress."""

    def test_log_quiz_progress_in_progress(self):
        """Test logovanja progressa."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_quiz_progress("quiz-1", 5, 10, "in_progress")

            mock_logger.info.assert_called()

    def test_log_quiz_progress_completed(self):
        """Test logovanja završetka."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_quiz_progress("quiz-1", 10, 10, "completed")

            mock_logger.info.assert_called()


class TestLogQuizComplete:
    """Testovi za log_quiz_complete."""

    def test_log_quiz_complete(self):
        """Test logovanja završetka kviza."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_quiz_complete("quiz-1", 10, "openai", 5.5)

            mock_logger.info.assert_called()


class TestLogPdfProcessing:
    """Testovi za log_pdf_processing."""

    def test_log_pdf_processing_start(self):
        """Test logovanja početka obrade."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_pdf_processing("doc-1", 10, "started")

            mock_logger.info.assert_called()

    def test_log_pdf_processing_error(self):
        """Test logovanja greške."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_pdf_processing("doc-1", 10, "error")

            mock_logger.error.assert_called()


class TestLogOcrProgress:
    """Testovi za log_ocr_progress."""

    def test_log_ocr_progress(self):
        """Test logovanja OCR progresa."""
        with patch("app.utils.monitoring.logger") as mock_logger:
            log_ocr_progress("doc-1", 5, 10, "tesseract")

            mock_logger.info.assert_called()


class TestGetSystemStatus:
    """Testovi za get_system_status."""

    def test_get_system_status(self):
        """Test dobijanja statusa sistema."""
        with patch("app.utils.monitoring.logger"):
            status = get_system_status()

            assert isinstance(status, dict)
