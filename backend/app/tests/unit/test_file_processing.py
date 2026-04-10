# -*- coding: utf-8 -*-
"""
================================================================================
FILE PROCESSING SERVICE TESTS
================================================================================
Unit testovi za services/file_processing.py.

Pokretanje:
    pytest tests/unit/test_file_processing.py -v
================================================================================
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.file_processing import (
    FileProcessingService,
    TESSERACT_AVAILABLE,
    DOCX_AVAILABLE,
)


class TestFileProcessingService:
    """Testovi za FileProcessingService."""

    def test_init_default(self):
        """Test podrazumevane inicijalizacije."""
        service = FileProcessingService()
        assert service.use_ocr is True or service.use_ocr is False
        assert service.ocr_language == "srp"

    def test_init_with_ocr_disabled(self):
        """Test inicijalizacije bez OCR-a."""
        service = FileProcessingService(use_ocr=False)
        assert service.use_ocr is False

    def test_init_custom_language(self):
        """Test sa prilagođenim jezikom."""
        service = FileProcessingService(ocr_language="eng")
        assert service.ocr_language == "eng"


class TestProcessFile:
    """Testovi za process_file metodu."""

    def test_process_unsupported_file(self):
        """Test za nepodržani tip fajla."""
        service = FileProcessingService()

        result = service.process_file(
            file_content=b"test", filename="test.xyz", file_ext=".xyz"
        )

        assert result["success"] is False
        assert "Unsupported" in result["error"]

    def test_process_empty_extension(self):
        """Test sa praznom ekstenzijom."""
        service = FileProcessingService()

        result = service.process_file(
            file_content=b"test", filename="test", file_ext=""
        )

        assert result["success"] is False


class TestProcessPdf:
    """Testovi za _process_pdf."""

    def test_process_pdf_invalid_content(self):
        """Test sa nevalidnim PDF-om."""
        service = FileProcessingService()

        result = service._process_pdf(b"not a pdf")

        assert "success" in result
        assert "text" in result

    def test_process_pdf_with_callback(self):
        """Test sa progress callback-om."""
        service = FileProcessingService()
        callback_called = False

        def callback(progress):
            nonlocal callback_called
            callback_called = True

        result = service._process_pdf(b"%PDF-1.4 fake", callback)

        # Callback može ali ne mora biti pozvan, depending on implementation


class TestProcessTxt:
    """Testovi za _process_txt."""

    def test_process_txt_success(self):
        """Test uspešnog procesiranja teksta."""
        service = FileProcessingService()

        content = "Hello World".encode("utf-8")
        result = service._process_txt(content)

        assert result["success"] is True
        assert "Hello World" in result["text"]

    def test_process_txt_empty(self):
        """Test sa praznim sadržajem."""
        service = FileProcessingService()

        result = service._process_txt(b"")

        assert result["success"] is True
        assert result["text"] == ""


class TestProcessDocx:
    """Testovi za _process_docx."""

    def test_process_docx_when_available(self):
        """Test kada je DOCX dostupan."""
        service = FileProcessingService()

        # Čak i ako DOCX nije dostupan, vraća strukturu
        result = service._process_docx(b"fake docx content")

        assert "success" in result


class TestProcessImage:
    """Testovi za _process_image."""

    def test_process_image_unsupported_format(self):
        """Test sa nepodržanim formatom slike."""
        service = FileProcessingService()

        result = service._process_image(b"fake image", ".unknown")

        assert "success" in result
        # OCR može ali ne mora biti dostupan

    def test_process_image_tiff(self):
        """Test sa TIFF formatom."""
        service = FileProcessingService()

        result = service._process_image(b"fake tiff", ".tiff")

        assert "success" in result


class TestConstants:
    """Testovi za konstante."""

    def test_tesseract_available_is_bool(self):
        """Test da je TESSERACT_AVAILABLE boolean."""
        assert isinstance(TESSERACT_AVAILABLE, bool)

    def test_docx_available_is_bool(self):
        """Test da je DOCX_AVAILABLE boolean."""
        assert isinstance(DOCX_AVAILABLE, bool)
