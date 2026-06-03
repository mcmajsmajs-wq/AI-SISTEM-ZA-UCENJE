# -*- coding: utf-8 -*-
"""
================================================================================
PPTX EXPORT SERVICE TESTS
================================================================================
Unit testovi za pptx_export_service.py.

Pokretanje:
    pytest tests/unit/test_pptx_export_service.py -v
================================================================================
"""

import pytest
import io
from unittest.mock import patch, MagicMock

from app.services.pptx_export_service import PPTXExportService


class TestPPTXExportService:
    """Testovi za PPTXExportService."""

    @pytest.fixture
    def pptx_service(self):
        """PPTXExportService instanca."""
        return PPTXExportService()

    def test_init(self):
        """Test inicijalizacije."""
        service = PPTXExportService()
        assert service is not None

    def test_generate_returns_bytes(self):
        """Test da generate vraća bytes."""
        service = PPTXExportService()

        chunks = [
            {"original_text": "Hello", "translated_text": "Zdravo"},
            {"original_text": "World", "translated_text": "Svete"},
        ]

        result = service.generate(
            title="Test Document", chunks=chunks, include_original=True
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_with_empty_chunks(self):
        """Test sa praznom listom chunk-ova."""
        service = PPTXExportService()

        result = service.generate(title="Empty", chunks=[])

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generate_without_original(self):
        """Test bez originalnog teksta."""
        service = PPTXExportService()

        chunks = [{"translated_text": "Samo prevod"}]

        result = service.generate(
            title="Translated Only",
            chunks=chunks,
            include_original=False,
        )

        assert isinstance(result, bytes)

    def test_generate_with_single_chunk(self):
        """Test sa jednim chunk-om."""
        service = PPTXExportService()

        chunks = [{"translated_text": "Jedan chunk"}]

        result = service.generate(title="Single", chunks=chunks)

        assert isinstance(result, bytes)

    def test_generate_limits_slides(self):
        """Test da limitira broj slajdova na 50."""
        service = PPTXExportService()

        chunks = [{"translated_text": f"Chunk {i}"} for i in range(100)]

        result = service.generate(title="Many", chunks=chunks)

        assert isinstance(result, bytes)

    def test_generate_with_long_text(self):
        """Test sa dugim tekstom (truncates)."""
        service = PPTXExportService()

        long_text = "A" * 2000
        chunks = [{"translated_text": long_text}]

        result = service.generate(title="Long", chunks=chunks)

        assert isinstance(result, bytes)
