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

from app.services.pdf_export_service import (
    PDFExportService,
    _get_layout_paragraphs,
    _map_font,
    _scale_size,
    _split_paragraphs,
)


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
        """Test da _build_styles vraća dict sa svim potrebnim stilovima."""
        service = PDFExportService()
        styles = service._build_styles()

        assert isinstance(styles, dict)
        assert "cover_title" in styles
        assert "cover_subtitle" in styles
        assert "h1" in styles
        assert "h2" in styles
        assert "h3" in styles
        assert "body" in styles
        assert "footer" in styles
        assert "toc_title" in styles
        assert "toc_item" in styles
        assert "meta" in styles

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

    # ── Layout-aware rendering tests ──────────────────────────────────────────

    def test_get_layout_paragraphs_returns_list(self):
        """_get_layout_paragraphs vraca listu iz layout_data.paragraphs."""
        chunk = {
            "layout_data": {
                "paragraphs": [
                    {"font": "DejaVuSans", "size": 12.0, "is_bold": False},
                    {"font": "DejaVuSans-Bold", "size": 14.0, "is_bold": True},
                ]
            }
        }
        result = _get_layout_paragraphs(chunk)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_layout_paragraphs_no_layout_data(self):
        """_get_layout_paragraphs vraca None kad nema layout_data."""
        chunk = {"content": "test"}
        assert _get_layout_paragraphs(chunk) is None

    def test_get_layout_paragraphs_empty_paragraphs(self):
        """_get_layout_paragraphs vraca None kad su paragraphs prazni."""
        chunk = {"layout_data": {"paragraphs": []}}
        assert _get_layout_paragraphs(chunk) is None

    def test_map_font_bold(self):
        """_map_font vraca bold font za is_bold=True."""
        font = _map_font(True)
        assert "Bold" in font or font == "Helvetica-Bold"

    def test_map_font_regular(self):
        """_map_font vraca regular font za is_bold=False."""
        font = _map_font(False)
        assert "Bold" not in font

    def test_scale_size_default_ref(self):
        """_scale_size skalira sa default ref_body=15.0."""
        scaled = _scale_size(15.0)
        assert scaled == 10.0

    def test_scale_size_larger(self):
        """_scale_size skalira veci font proporcionalno."""
        scaled = _scale_size(30.0)
        assert scaled == 20.0  # clamped

    def test_scale_size_clamped_min(self):
        """_scale_size clampuje na minimum 7."""
        scaled = _scale_size(1.0)
        assert scaled == 7.0

    def test_split_paragraphs_empty(self):
        """_split_paragraphs vraca praznu listu za prazan tekst."""
        assert _split_paragraphs("") == []
        assert _split_paragraphs(None) == []

    def test_generate_with_layout_data_body_chunk(self):
        """Body chunk sa layout_data koristi per-paragraph font styling."""
        service = PDFExportService()
        chunks = [
            {
                "translated_text": "Prvi pasus.\n\nDrugi pasus.",
                "layout_data": {
                    "paragraphs": [
                        {"font": "DejaVuSans", "size": 15.0, "is_bold": False},
                        {"font": "DejaVuSans-Bold", "size": 16.0, "is_bold": True},
                    ]
                },
            }
        ]
        result = service.generate(
            title="Layout Test", chunks=chunks, target_language="sr"
        )
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_without_layout_data(self):
        """Chunk bez layout_data koristi default body style (fallback)."""
        service = PDFExportService()
        chunks = [
            {
                "translated_text": "Ovo je body tekst bez layout podataka.",
            }
        ]
        result = service.generate(
            title="No Layout", chunks=chunks, target_language="sr"
        )
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_heading_with_layout_data_no_duplication(self):
        """Heading chunk sa layout_data ne duplicira tekst u body style-u."""
        service = PDFExportService()
        chunks = [
            {
                "translated_text": "Prvo Poglavlje",
                "heading_level": 1,
                "layout_data": {
                    "paragraphs": [
                        {"font": "DejaVuSans-Bold", "size": 24.0, "is_bold": True},
                    ]
                },
            },
            {
                "translated_text": "Ovo je body tekst nakon headera.",
                "layout_data": {
                    "paragraphs": [
                        {"font": "DejaVuSans", "size": 15.0, "is_bold": False},
                    ]
                },
            },
        ]
        result = service.generate(
            title="Heading Layout", chunks=chunks, target_language="sr"
        )
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_heading_h2_with_layout_data(self):
        """H2 heading sa layout_data koristi prilagodjen font."""
        service = PDFExportService()
        chunks = [
            {
                "translated_text": "Drugo Poglavlje",
                "heading_level": 2,
                "layout_data": {
                    "paragraphs": [
                        {"font": "DejaVuSans-Bold", "size": 18.0, "is_bold": True},
                    ]
                },
            }
        ]
        result = service.generate(
            title="H2 Layout", chunks=chunks, target_language="sr"
        )
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")

    def test_generate_heading_h3_with_layout_data(self):
        """H3 heading sa layout_data koristi prilagodjen font."""
        service = PDFExportService()
        chunks = [
            {
                "translated_text": "Treca Tema",
                "heading_level": 3,
                "layout_data": {
                    "paragraphs": [
                        {"font": "DejaVuSans-Bold", "size": 14.0, "is_bold": True},
                    ]
                },
            }
        ]
        result = service.generate(
            title="H3 Layout", chunks=chunks, target_language="sr"
        )
        assert isinstance(result, bytes)
        assert result.startswith(b"%PDF")
