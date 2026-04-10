# -*- coding: utf-8 -*-
"""
================================================================================
PDF EXPORT SERVICE TESTS
================================================================================
Unit testovi za pdf_export_service.py.

Pokretanje:
    pytest tests/unit/test_pdf_export_service.py -v
================================================================================
"""

import pytest
import io
from unittest.mock import patch, MagicMock

from app.services.pdf_export_service import PDFExportService


class TestPDFExportService:
    """Testovi za PDFExportService."""

    @pytest.fixture
    def pdf_service(self):
        """PDFExportService instanca."""
        return PDFExportService()

    def test_init(self):
        """Test inicijalizacije."""
        service = PDFExportService()
        assert service is not None

    def test_build_styles(self):
        """Test da _build_styles vraća dict."""
        service = PDFExportService()
        styles = service._build_styles()

        assert isinstance(styles, dict)
        assert "title" in styles
        assert "subtitle" in styles
        assert "translated" in styles

    def test_build_styles_has_paragraph_styles(self):
        """Test da sadrži sve potrebne stilove."""
        service = PDFExportService()
        styles = service._build_styles()

        required = [
            "title",
            "subtitle",
            "meta",
            "section_label",
            "original",
            "translated",
            "footer",
        ]
        for key in required:
            assert key in styles, f"Missing style: {key}"

    def test_generate_returns_bytes(self):
        """Test da generate vraća bytes."""
        service = PDFExportService()

        chunks = [
            {"original": "Hello", "translated": "Zdravo"},
            {"original": "World", "translated": "Svet"},
        ]

        result = service.generate(
            title="Test Document", chunks=chunks, target_language="sr"
        )

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_with_empty_chunks(self):
        """Test sa praznom listom chunk-ova."""
        service = PDFExportService()

        result = service.generate(title="Empty", chunks=[], target_language="sr")

        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_without_original(self):
        """Test bez originalnog teksta."""
        service = PDFExportService()

        chunks = [{"translated": "Samo prevod"}]

        result = service.generate(
            title="Translated Only",
            chunks=chunks,
            target_language="sr",
            include_original=False,
        )

        assert isinstance(result, bytes)

    def test_generate_with_custom_author(self):
        """Test sa prilagođenim autorom."""
        service = PDFExportService()

        chunks = [{"original": "test", "translated": "test prevod"}]

        result = service.generate(
            title="Custom Author", chunks=chunks, author="Custom Author Name"
        )

        assert isinstance(result, bytes)
