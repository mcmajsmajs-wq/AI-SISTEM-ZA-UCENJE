# -*- coding: utf-8 -*-
"""
================================================================================
XLSX EXPORT SERVICE TESTS
================================================================================
Unit testovi za xlsx_export_service.py.

Pokretanje:
    pytest tests/unit/test_xlsx_export_service.py -v
================================================================================
"""

import pytest
import io
from unittest.mock import patch, MagicMock

from app.services.xlsx_export_service import XLSXExportService


class TestXLSXExportService:
    """Testovi za XLSXExportService."""

    @pytest.fixture
    def xlsx_service(self):
        """XLSXExportService instanca."""
        return XLSXExportService()

    def test_init(self):
        """Test inicijalizacije."""
        service = XLSXExportService()
        assert service is not None

    def test_generate_returns_bytes(self):
        """Test da generate vraća bytes."""
        service = XLSXExportService()

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
        service = XLSXExportService()

        result = service.generate(title="Empty", chunks=[])

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_without_original(self):
        """Test bez originalnog teksta."""
        service = XLSXExportService()

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
        service = XLSXExportService()

        chunks = [{"translated_text": "Jedan chunk"}]

        result = service.generate(title="Single", chunks=chunks)

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_with_many_chunks(self):
        """Test sa puno chunk-ova."""
        service = XLSXExportService()

        chunks = [
            {"original_text": f"Text {i}", "translated_text": f"Prevod {i}"}
            for i in range(100)
        ]

        result = service.generate(title="Many", chunks=chunks)

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"

    def test_generate_with_long_text(self):
        """Test sa dugim tekstom."""
        service = XLSXExportService()

        long_text = "A" * 500
        chunks = [{"translated_text": long_text}]

        result = service.generate(title="Long", chunks=chunks)

        assert isinstance(result, bytes)
        assert result[:4] == b"PK\x03\x04"
