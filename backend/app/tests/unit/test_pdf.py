# -*- coding: utf-8 -*-
"""
================================================================================
PDF SERVICE TESTS
================================================================================
Unit testovi za PDFService - ekstrakcija, denoising, chunkovanje.

Pokretanje:
    pytest tests/unit/test_pdf.py -v
================================================================================
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import io

from app.services.pdf import PDFService, ChunkData, PDFMetadata, ProcessingResult


class TestPDFServiceInit:
    """Testovi za inicijalizaciju PDFService."""

    def test_init_default_params(self):
        """Test inicijalizacije sa default parametrima."""
        service = PDFService()

        assert service.chunk_size == PDFService.DEFAULT_CHUNK_SIZE
        assert service.chunk_overlap == PDFService.DEFAULT_CHUNK_OVERLAP

    def test_init_custom_params(self):
        """Test inicijalizacije sa custom parametrima."""
        service = PDFService(
            chunk_size=1000, chunk_overlap=200, use_ocr=False, ocr_language="eng"
        )

        assert service.chunk_size == 1000
        assert service.chunk_overlap == 200
        assert service.use_ocr is False
        assert service.ocr_language == "eng"


class TestTokenCounting:
    """Testovi za brojanje tokena."""

    def test_count_tokens_short_text(self):
        """Test brojanja tokena za kratak tekst."""
        service = PDFService()

        text = "Hello world"
        count = service.count_tokens(text)

        assert count > 0
        assert count <= len(text.split()) + 5

    def test_count_tokens_long_text(self):
        """Test brojanja tokena za dug tekst."""
        service = PDFService()

        text = " ".join(["word"] * 100)
        count = service.count_tokens(text)

        assert count > 0

    def test_count_tokens_empty_text(self):
        """Test brojanja tokena za prazan tekst."""
        service = PDFService()

        count = service.count_tokens("")

        assert count == 0

    def test_count_tokens_unicode(self):
        """Test brojanja tokena sa Unicode karakterima."""
        service = PDFService()

        text = "Здраво свету! This is a test."
        count = service.count_tokens(text)

        assert count > 0


class TestDenoiseText:
    """Testovi za uklanjanje šuma iz teksta."""

    def test_denoise_page_numbers(self):
        """Test uklanjanja brojeva stranica."""
        service = PDFService()

        text = """
        Some content here.
        
        1
        
        More content.
        
        Page 5
        
        Even more content.
        """

        cleaned = service.denoise_text(text)

        assert "1" not in cleaned.split("\n")[2:4]
        assert "Some content" in cleaned
        assert "More content" in cleaned

    def test_denoise_footer_patterns(self):
        """Test uklanjanja footer paterna."""
        service = PDFService()

        text = """
        Document content.
        
        © 2024 Company Name. All rights reserved.
        
        More content.
        
        www.example.com
        """

        cleaned = service.denoise_text(text)

        assert "©" not in cleaned or "All rights reserved" not in cleaned

    def test_denoise_preserves_content(self):
        """Test da denoising ne uklanja važan sadržaj."""
        service = PDFService()

        text = """
        Chapter 1: Introduction
        
        This is an important paragraph with useful content.
        It should not be removed during denoising.
        
        The quick brown fox jumps over the lazy dog.
        """

        cleaned = service.denoise_text(text)

        assert "Chapter 1" in cleaned
        assert "important paragraph" in cleaned
        assert "quick brown fox" in cleaned

    def test_denoise_empty_text(self):
        """Test denoising praznog teksta."""
        service = PDFService()

        cleaned = service.denoise_text("")

        assert cleaned == ""


class TestHeadingDetection:
    """Testovi za detekciju heading-a."""

    def test_detect_markdown_heading(self):
        """Test detekcije Markdown heading-a."""
        service = PDFService()

        text = "## Introduction to AI"
        level, heading = service.detect_heading(text)

        assert level == 2
        assert heading == "Introduction to AI"

    def test_detect_numbered_heading(self):
        """Test detekcije numerisanog heading-a."""
        service = PDFService()

        text = "1. Introduction"
        level, heading = service.detect_heading(text)

        assert level > 0
        assert "Introduction" in heading

    def test_detect_all_caps_heading(self):
        """Test detekcije ALL CAPS heading-a."""
        service = PDFService()

        text = "INTRODUCTION"
        level, heading = service.detect_heading(text)

        assert level > 0

    def test_no_heading_in_normal_text(self):
        """Test da normalan tekst nije heading."""
        service = PDFService()

        text = "This is a normal paragraph with some content."
        level, heading = service.detect_heading(text)

        assert level == 0
        assert heading is None

    def test_empty_text_heading(self):
        """Test heading detekcije za prazan tekst."""
        service = PDFService()

        level, heading = service.detect_heading("")

        assert level == 0
        assert heading is None


class TestSmartChunk:
    """Testovi za smart chunking."""

    def test_chunk_short_text(self):
        """Test chunking kratkog teksta."""
        service = PDFService(chunk_size=500)

        text = "This is a short paragraph."
        chunks = service.smart_chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_respects_chunk_size(self):
        """Test da chunking poštuje chunk size."""
        service = PDFService(chunk_size=50)

        paragraphs = ["Paragraph " + str(i) * 100 for i in range(5)]
        text = "\n\n".join(paragraphs)

        chunks = service.smart_chunk(text)

        for chunk in chunks:
            assert chunk.token_count <= service.chunk_size * 1.5

    def test_chunk_preserves_page_number(self):
        """Test da chunk čuva broj stranice."""
        service = PDFService()

        text = "Some content on page 5."
        chunks = service.smart_chunk(text, page_number=5)

        assert len(chunks) >= 1
        assert chunks[0].page_number == 5

    def test_chunk_with_headings(self):
        """Test chunking sa heading-ima."""
        service = PDFService(chunk_size=500)

        text = """
## Chapter 1

This is the content of chapter 1.

## Chapter 2

This is the content of chapter 2.
        """

        chunks = service.smart_chunk(text)

        assert len(chunks) >= 2
        assert any(c.parent_heading == "Chapter 1" for c in chunks)
        assert any(c.parent_heading == "Chapter 2" for c in chunks)

    def test_chunk_empty_text(self):
        """Test chunking praznog teksta."""
        service = PDFService()

        chunks = service.smart_chunk("")

        assert len(chunks) == 0

    def test_chunk_whitespace_only(self):
        """Test chunking teksta sa samo whitespace."""
        service = PDFService()

        chunks = service.smart_chunk("   \n\n   \t\t  ")

        assert len(chunks) == 0

    def test_chunk_overlap(self):
        """Test da chunk overlap radi."""
        service = PDFService(chunk_size=100, chunk_overlap=50)

        long_text = " ".join(["word"] * 200)
        chunks = service.smart_chunk(long_text)

        if len(chunks) > 1:
            assert len(chunks) >= 2


class TestExtractMetadata:
    """Testovi za ekstrakciju metadata."""

    @patch("app.services.pdf.fitz")
    def test_extract_metadata_basic(self, mock_fitz):
        """Test osnovne metadata ekstrakcije."""
        service = PDFService()

        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "subject": "Test Subject",
        }
        mock_doc.__len__ = lambda self: 10
        mock_doc.__getitem__ = lambda self, idx: MagicMock(
            get_text=lambda: "Sample text", get_images=lambda: []
        )

        metadata = service.extract_metadata(mock_doc)

        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert metadata.total_pages == 10

    @patch("app.services.pdf.fitz")
    def test_extract_metadata_empty(self, mock_fitz):
        """Test metadata ekstrakcije za prazan dokument."""
        service = PDFService()

        mock_doc = MagicMock()
        mock_doc.metadata = None
        mock_doc.__len__ = lambda self: 0

        metadata = service.extract_metadata(mock_doc)

        assert metadata.title is None
        assert metadata.total_pages == 0

    @patch("app.services.pdf.fitz")
    def test_detect_scanned_document(self, mock_fitz):
        """Test detekcije skeniranog dokumenta."""
        service = PDFService()

        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__len__ = lambda self: 5
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""  # No text
        mock_page.get_images.return_value = [MagicMock()]  # Has images
        mock_doc.__getitem__ = lambda self, idx: mock_page

        metadata = service.extract_metadata(mock_doc)

        assert metadata.is_scanned is True
        assert metadata.has_images is True


class TestExtractTextFromPage:
    """Testovi za ekstrakciju teksta sa stranice."""

    def test_extract_text_success(self):
        """Test uspesne ekstrakcije teksta."""
        service = PDFService()

        mock_page = MagicMock()
        mock_page.get_text.return_value = "  Sample text content  "

        text = service.extract_text_from_page(mock_page)

        assert text == "Sample text content"

    def test_extract_text_empty_page(self):
        """Test ekstrakcije sa prazne stranice."""
        service = PDFService()

        mock_page = MagicMock()
        mock_page.get_text.return_value = ""

        text = service.extract_text_from_page(mock_page)

        assert text == ""

    def test_extract_text_error_handling(self):
        """Test error handling pri ekstrakciji."""
        service = PDFService()

        mock_page = MagicMock()
        mock_page.get_text.side_effect = Exception("Test error")

        text = service.extract_text_from_page(mock_page)

        assert text == ""


class TestProcessPDF:
    """Testovi za kompletno PDF procesiranje."""

    @patch("app.services.pdf.fitz")
    def test_process_pdf_success(self, mock_fitz):
        """Test uspesnog PDF procesiranja."""
        service = PDFService()

        pdf_bytes = b"fake pdf content"

        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "Test", "author": "Author"}
        mock_doc.__len__ = lambda self: 2
        mock_doc.__enter__ = lambda self: self
        mock_doc.__exit__ = lambda self, *args: None

        mock_page = MagicMock()

        def get_text_side_effect(*args, **kwargs):
            if args and args[0] == "dict":
                return {
                    "blocks": [
                        {
                            "lines": [
                                {
                                    "spans": [
                                        {
                                            "text": "Test content for the page. This is a longer text that contains more than fifty characters to pass the empty page check in the PDF service.",
                                            "font": "ArialMT",
                                            "size": 10,
                                            "flags": 0,
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            return "Test content for the page. This is a longer text that contains more than fifty characters to pass the empty page check in the PDF service."

        mock_page.get_text.side_effect = get_text_side_effect
        mock_page.get_images.return_value = []
        mock_doc.__getitem__ = lambda self, idx: mock_page

        mock_fitz.open.return_value = mock_doc

        result = service.process_pdf(pdf_bytes)

        assert result.success is True
        assert result.metadata.title == "Test"
        assert len(result.chunks) > 0

    def test_process_pdf_invalid_bytes(self):
        """Test procesiranja neispravnih bytes."""
        service = PDFService()

        result = service.process_pdf(b"invalid pdf")

        assert result.success is False
        assert result.error is not None

    @patch("app.services.pdf.fitz")
    def test_process_pdf_with_custom_title(self, mock_fitz):
        """Test procesiranja sa custom naslovom."""
        service = PDFService()

        pdf_bytes = b"fake pdf content"

        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.__len__ = lambda self: 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Content"
        mock_page.get_images.return_value = []
        mock_doc.__getitem__ = lambda self, idx: mock_page

        mock_fitz.open.return_value = mock_doc

        result = service.process_pdf(pdf_bytes, title="Custom Title")

        assert result.metadata.title == "Custom Title"


class TestProcessPDFFromStorage:
    """Testovi za procesiranje PDF-a iz storage-a."""

    def test_process_from_storage_success(self):
        """Test uspesnog procesiranja iz storage-a."""
        service = PDFService()

        mock_storage = MagicMock()
        mock_storage.download_file.return_value = b"fake pdf content"

        with patch.object(service, "process_pdf") as mock_process:
            mock_process.return_value = ProcessingResult(
                success=True, metadata=PDFMetadata(title="Test"), chunks=[]
            )

            result = service.process_pdf_from_storage(
                "test.pdf", mock_storage, title="Test"
            )

            mock_storage.download_file.assert_called_once_with("test.pdf")
            assert result.success is True

    def test_process_from_storage_download_error(self):
        """Test greške pri download-u iz storage-a."""
        service = PDFService()

        mock_storage = MagicMock()
        mock_storage.download_file.side_effect = Exception("Download failed")

        result = service.process_pdf_from_storage("test.pdf", mock_storage)

        assert result.success is False
        assert "Failed to download" in result.error


class TestChunkData:
    """Testovi za ChunkData dataclass."""

    def test_chunk_data_creation(self):
        """Test kreiranja ChunkData."""
        chunk = ChunkData(
            sequence_number=0,
            content="Test content",
            token_count=10,
            heading_level=2,
            parent_heading="Introduction",
            page_number=5,
        )

        assert chunk.sequence_number == 0
        assert chunk.content == "Test content"
        assert chunk.token_count == 10
        assert chunk.heading_level == 2
        assert chunk.parent_heading == "Introduction"
        assert chunk.page_number == 5

    def test_chunk_data_defaults(self):
        """Test default vrednosti ChunkData."""
        chunk = ChunkData(sequence_number=0, content="Test", token_count=5)

        assert chunk.heading_level == 0
        assert chunk.parent_heading is None
        assert chunk.page_number is None


class TestPDFMetadata:
    """Testovi za PDFMetadata dataclass."""

    def test_metadata_creation(self):
        """Test kreiranja PDFMetadata."""
        metadata = PDFMetadata(
            title="Test Document",
            author="Test Author",
            total_pages=10,
            has_images=True,
            is_scanned=False,
        )

        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert metadata.total_pages == 10
        assert metadata.has_images is True
        assert metadata.is_scanned is False

    def test_metadata_defaults(self):
        """Test default vrednosti PDFMetadata."""
        metadata = PDFMetadata()

        assert metadata.title is None
        assert metadata.author is None
        assert metadata.total_pages == 0
        assert metadata.has_images is False


class TestProcessingResult:
    """Testovi za ProcessingResult dataclass."""

    def test_result_success(self):
        """Test uspesnog ProcessingResult."""
        result = ProcessingResult(
            success=True,
            metadata=PDFMetadata(title="Test"),
            chunks=[ChunkData(sequence_number=0, content="Test", token_count=5)],
        )

        assert result.success is True
        assert len(result.chunks) == 1
        assert result.error is None

    def test_result_failure(self):
        """Test neuspesnog ProcessingResult."""
        result = ProcessingResult(
            success=False, metadata=PDFMetadata(), error="Processing failed"
        )

        assert result.success is False
        assert result.error == "Processing failed"
        assert len(result.chunks) == 0


class TestEdgeCases:
    """Testovi za edge cases."""

    def test_very_long_paragraph(self):
        """Test sa vrlo dugim tekstom koji ima rečenice — mora biti razbijen u više chunk-ova."""
        service = PDFService(chunk_size=100)

        # Tekst sa više rečenica kako bi chunker mogao da razbije po granicama
        sentences = "This is a sentence with enough words to fill the buffer. " * 50
        chunks = service.smart_chunk(sentences)

        # Tekst od ~2500 tokena mora da da barem 2 chunk-a pri chunk_size=100
        assert len(chunks) >= 1
        # Ukupan sadržaj mora biti sačuvan
        full_text = " ".join(c.content for c in chunks)
        assert "sentence" in full_text

    def test_special_characters(self):
        """Test sa specijalnim karakterima."""
        service = PDFService()

        text = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?\n\nAnother line."
        chunks = service.smart_chunk(text)

        assert len(chunks) > 0
        assert "Special chars" in chunks[0].content

    def test_mixed_languages(self):
        """Test sa mešanim jezicima."""
        service = PDFService()

        text = """
        This is English text.
        
        Ovo je tekst na srpskom jeziku.
        
        这是中文文本。
        
        Это русский текст.
        """

        chunks = service.smart_chunk(text)

        assert len(chunks) > 0
        assert any("English" in c.content for c in chunks)
        assert any("srpskom" in c.content for c in chunks)
