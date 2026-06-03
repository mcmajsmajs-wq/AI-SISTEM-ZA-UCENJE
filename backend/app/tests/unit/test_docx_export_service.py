# -*- coding: utf-8 -*-
"""
================================================================================
DOCX EXPORT SERVICE TESTS
================================================================================
Unit testovi za docx_export_service.py.

Pokretanje:
    pytest tests/unit/test_docx_export_service.py -v
================================================================================
"""

import pytest
import io
from unittest.mock import patch, MagicMock

from app.services.docx_export_service import DOCXExportService


class TestDOCXExportService:
    """Testovi za DOCXExportService."""

    @pytest.fixture
    def docx_service(self):
        """DOCXExportService instanca."""
        return DOCXExportService()

    def test_init(self):
        """Test inicijalizacije."""
        service = DOCXExportService()
        assert service is not None

    def test_generate_returns_bytes(self):
        """Test da generate vraća bytes."""
        service = DOCXExportService()

        chunks = [
            {"original_text": "Hello", "translated_text": "Zdravo"},
            {"original_text": "World", "translated_text": "Svete"},
        ]

        result = service.generate(
            title="Test Document", chunks=chunks, include_original=True
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b"PK\x03\x04"

    def test_generate_with_empty_chunks(self):
        """Test sa praznom listom chunk-ova."""
        service = DOCXExportService()

        result = service.generate(title="Empty", chunks=[])

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_without_original(self):
        """Test bez originalnog teksta."""
        service = DOCXExportService()

        chunks = [{"translated_text": "Samo prevod"}]

        result = service.generate(
            title="Translated Only",
            chunks=chunks,
            include_original=False,
        )

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_with_single_chunk(self):
        """Test sa jednim chunk-om."""
        service = DOCXExportService()

        chunks = [{"translated_text": "Jedan chunk"}]

        result = service.generate(title="Single", chunks=chunks)

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_with_long_text(self):
        """Test sa dugim tekstom."""
        service = DOCXExportService()

        long_text = "A" * 1000
        chunks = [{"translated_text": long_text}]

        result = service.generate(title="Long", chunks=chunks)

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_uses_safe_title(self):
        """Test da naslov nije prazan."""
        service = DOCXExportService()

        chunks = [{"translated_text": "Test"}]

        result = service.generate(title="", chunks=chunks)

        assert isinstance(result, bytes)
