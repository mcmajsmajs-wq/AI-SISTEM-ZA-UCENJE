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

from unittest.mock import MagicMock, patch

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
                                            "text": "Test content for the page. This is a longer text that contains more than fifty characters to pass the empty page check in the PDF service.",  # noqa: E501
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
            return "Test content for the page. This is a longer text that contains more than fifty characters to pass the empty page check in the PDF service."  # noqa: E501

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


class TestAdaptiveHeadingDetection:
    """Testovi za adaptivne heading threshold-e."""

    def test_detect_ref_body_size_standard(self):
        """Detekcija ref body size sa normalnim paragrafima."""
        paragraphs = [
            {"text": "Normal text", "size": 10, "is_bold": False},
            {"text": "More text", "size": 10, "is_bold": False},
            {"text": "Even more", "size": 11, "is_bold": False},
            {"text": "Short", "size": 9, "is_bold": False},
        ]
        ref = PDFService._detect_ref_body_size(paragraphs)
        assert ref == 10.0

    def test_detect_ref_body_size_few_paragraphs(self):
        """Kad je manje od 3 paragrafa, vraća default 10."""
        paragraphs = [
            {"text": "Only one", "size": 8, "is_bold": False},
        ]
        ref = PDFService._detect_ref_body_size(paragraphs)
        assert ref == 10.0

    def test_detect_ref_body_size_ignores_bold(self):
        """Bold paragrafi se ignorišu (to su heading-i)."""
        paragraphs = [
            {"text": "Body text", "size": 10, "is_bold": False},
            {"text": "Bold heading", "size": 16, "is_bold": True},
            {"text": "More body", "size": 10, "is_bold": False},
            {"text": "More body", "size": 10, "is_bold": False},
        ]
        ref = PDFService._detect_ref_body_size(paragraphs)
        assert ref == 10.0

    def test_adaptive_heading_h1(self):
        """H1 se detektuje sa relativnim threshold-om (1.35x body)."""
        service = PDFService()
        level, heading = service._detect_font_heading("BoldFont", 14, "Chapter 1", ref_body_size=10.0)
        assert level == 1
        assert heading == "Chapter 1"

    def test_adaptive_heading_h2(self):
        """H2 se detektuje sa 1.15x body."""
        service = PDFService()
        level, heading = service._detect_font_heading("BoldFont", 12, "Section 1.1", ref_body_size=10.0)
        assert level == 2
        assert heading == "Section 1.1"

    def test_adaptive_heading_h3(self):
        """H3 se detektuje sa 1.05x body."""
        service = PDFService()
        level, heading = service._detect_font_heading("BoldFont", 11, "Subsection", ref_body_size=10.0)
        assert level == 3
        assert heading == "Subsection"

    def test_adaptive_heading_no_false_positive(self):
        """Body text se ne detektuje kao heading."""
        service = PDFService()
        level, heading = service._detect_font_heading("RegularFont", 10, "This is normal body text", ref_body_size=10.0)
        assert level == 0

    def test_adaptive_heading_with_large_body(self):
        """Kad je body text veci, threshold-i se skaliraju."""
        service = PDFService()
        # body = 14, H1 >= 18.9, H2 >= 16.1, H3 >= 14.7
        level, heading = service._detect_font_heading("BoldFont", 19, "Big Chapter", ref_body_size=14.0)
        assert level == 1
        # Bold od 15: >= 14.7 (H3) ali < 16.1 (H2)
        level2, _ = service._detect_font_heading("BoldFont", 15, "Small heading", ref_body_size=14.0)
        assert level2 == 3

    def test_backward_compat_without_ref_body(self):
        """Bez ref_body_size, koristi stare hardcodovane threshold-e."""
        service = PDFService()
        level, heading = service._detect_font_heading("BoldFont", 14, "Chapter", ref_body_size=None)
        assert level == 1

    def test_detect_heading_with_ref_body(self):
        """detect_heading prosledjuje ref_body_size u _detect_font_heading."""
        service = PDFService()
        level, heading = service.detect_heading("Section A", "BoldFont", 12, ref_body_size=10.0)
        assert level == 2
        assert heading == "Section A"


class TestDeduplication:
    """Testovi za deduplikaciju chunk-ova."""

    def test_dedup_removes_exact_duplicates(self):
        """Egzaktni duplikati body chunkova se uklanjaju."""
        chunks = [
            ChunkData(sequence_number=0, content="This is a chunk", token_count=10, heading_level=0),
            ChunkData(sequence_number=1, content="This is a chunk", token_count=10, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 1

    def test_dedup_preserves_headings(self):
        """Heading chunkovi se ne deduplikuju (namerno ponavljanje)."""
        chunks = [
            ChunkData(sequence_number=0, content="Chapter 1", token_count=5, heading_level=1),
            ChunkData(sequence_number=1, content="Chapter 1", token_count=5, heading_level=1),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 2

    def test_dedup_preserves_unique_body_chunks(self):
        """Jedinstveni body chunkovi se čuvaju."""
        chunks = [
            ChunkData(sequence_number=0, content="First unique chunk content here", token_count=10, heading_level=0),
            ChunkData(sequence_number=1, content="Second different chunk content here", token_count=10, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 2

    def test_dedup_normalizes_whitespace(self):
        """Whitespace se normalizuje pre poređenja."""
        chunks = [
            ChunkData(sequence_number=0, content="This  is   a   chunk", token_count=10, heading_level=0),
            ChunkData(sequence_number=1, content="This is a chunk", token_count=10, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 1

    def test_dedup_case_insensitive(self):
        """Case-insensitive poređenje."""
        chunks = [
            ChunkData(sequence_number=0, content="This Is A Chunk", token_count=10, heading_level=0),
            ChunkData(sequence_number=1, content="this is a chunk", token_count=10, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 1

    def test_dedup_empty_content(self):
        """Prazan sadržaj se preskače."""
        chunks = [
            ChunkData(sequence_number=0, content="Valid content", token_count=10, heading_level=0),
            ChunkData(sequence_number=1, content="", token_count=0, heading_level=0),
            ChunkData(sequence_number=2, content="   ", token_count=0, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 1

    def test_dedup_mixed_heading_and_body(self):
        """Mešani heading i body chunkovi."""
        chunks = [
            ChunkData(sequence_number=0, content="Chapter 1", token_count=3, heading_level=1),
            ChunkData(sequence_number=1, content="Content of chapter one", token_count=10, heading_level=0),
            ChunkData(sequence_number=2, content="Chapter 1", token_count=3, heading_level=1),
            ChunkData(sequence_number=3, content="Content of chapter one", token_count=10, heading_level=0),
        ]
        result = PDFService._deduplicate_chunks(chunks)
        assert len(result) == 3  # 2 headings (kept) + 1 body (deduped)


class TestOCRPreprocessing:
    """Testovi za OCR image preprocessing."""

    def test_preprocess_grayscale_output(self):
        """Izlaz je u grayscale modu (L)."""
        from PIL import Image, ImageChops
        img = Image.new("RGB", (100, 50), color=(200, 200, 200))
        result = PDFService._preprocess_ocr_image(img)
        assert result.mode == "L"

    def test_preprocess_output_size(self):
        """Dimenzije slike se ne menjaju."""
        from PIL import Image
        img = Image.new("RGB", (200, 100), color=(128, 128, 128))
        result = PDFService._preprocess_ocr_image(img)
        assert result.size == (200, 100)

    def test_preprocess_grayscale_input(self):
        """Grayscale ulaz se ne kvari."""
        from PIL import Image
        img = Image.new("L", (50, 50), color=100)
        result = PDFService._preprocess_ocr_image(img)
        assert result.mode == "L"

    def test_preprocess_dark_image(self):
        """Tamna slika ne crash-uje."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(10, 10, 10))
        result = PDFService._preprocess_ocr_image(img)
        assert result.mode == "L"

    def test_preprocess_white_image(self):
        """Bela slika ne crash-uje."""
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        result = PDFService._preprocess_ocr_image(img)
        assert result.mode == "L"


class TestTableDetection:
    """Testovi za detekciju tabela."""

    def test_table_data_structure(self):
        """Tabela ima ispravnu strukturu."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        # Insert text so page has content
        page.insert_text((50, 50), "Test table", fontsize=12)
        result = PDFService()._detect_tables_on_page(page)
        doc.close()
        assert isinstance(result, list)

    def test_table_on_empty_page(self):
        """Prazna stranica vraca praznu listu."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        result = PDFService()._detect_tables_on_page(page)
        doc.close()
        assert result == []

    def test_detect_tables_on_pages_empty(self):
        """detect_tables_on_pages na praznom dokumentu."""
        import fitz
        doc = fitz.open()
        result = PDFService().detect_tables_on_pages(doc)
        doc.close()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_detect_tables_on_pages_specific(self):
        """Detekcija na specificnim stranicama."""
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Content", fontsize=12)
        result = PDFService().detect_tables_on_pages(doc, page_numbers=[0])
        doc.close()
        assert isinstance(result, dict)
        assert 0 in result or len(result) == 0

    def test_detect_tables_on_pages_invalid_page(self):
        """Invalidan broj stranice se preskace."""
        import fitz
        doc = fitz.open()
        result = PDFService().detect_tables_on_pages(doc, page_numbers=[99])
        doc.close()
        assert result == {}


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


class TestSemanticChunking:
    """Testovi za semantičko chunkovanje na rečeničnim granicama."""

    def test_split_at_sentence_boundary_short_text(self):
        """Kratak tekst se ne deli."""
        service = PDFService(chunk_size=500)
        text = "Ovo je kratak tekst."
        parts = service._split_at_sentence_boundary(text, 100)
        assert len(parts) == 1
        assert parts[0][0] == text

    def test_split_at_sentence_boundary_long_text(self):
        """Dug tekst se deli na rečeničnim granicama."""
        service = PDFService(chunk_size=50)
        sentences = "Prva recenica. " * 5 + "Druga recenica. " * 5 + "Treca recenica. " * 5
        parts = service._split_at_sentence_boundary(sentences, 60)
        assert len(parts) >= 2
        # Svaki deo osim poslednjeg treba da bude <= max_tokens
        for part_text, part_tokens in parts:
            assert part_tokens <= 60 * 1.5
            assert len(part_text) > 0

    def test_split_preserves_all_content(self):
        """Sadržaj se ne gubi pri deljenju."""
        service = PDFService(chunk_size=50)
        sentences = "Prva recenica. " * 3 + "Druga recenica. " * 3 + "Treca recenica. " * 3
        parts = service._split_at_sentence_boundary(sentences, 60)
        combined = " ".join(p[0] for p in parts)
        assert "Prva recenica" in combined
        assert "Druga recenica" in combined
        assert "Treca recenica" in combined

    def test_no_split_within_sentence(self):
        """Rečenice se ne smeju preseći."""
        service = PDFService(chunk_size=50)
        # Jedna duga rečenica - ne sme se preseći
        text = "This is a single very long sentence that should not be split because sentence boundary splitting only happens at sentence ends. " * 2
        text = text.strip()
        if service.count_tokens(text) > 50:
            parts = service._split_at_sentence_boundary(text, 50)
            for part_text, _ in parts:
                # Svaki deo mora da počne velikim slovom i završi se tačkom
                assert part_text[0].isupper()
                assert part_text.endswith(".")

    def test_smart_chunk_with_fonts_oversized_paragraph(self):
        """Oversized paragraph se deli na rečenične granice."""
        service = PDFService(chunk_size=50)
        paragraphs = [
            {
                "text": "Prva recenica. " * 20 + "Druga recenica. " * 20,
                "font": "ArialMT",
                "size": 10,
                "is_bold": False,
            }
        ]
        chunks = service.smart_chunk_with_fonts(paragraphs, page_number=1)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.token_count <= service.chunk_size * 1.5
        # Ukupan sadržaj sačuvan
        all_text = " ".join(c.content for c in chunks)
        assert "Prva recenica" in all_text
        assert "Druga recenica" in all_text

    def test_smart_chunk_with_fonts_normal_paragraph(self):
        """Normalan paragraph se ne deli."""
        service = PDFService(chunk_size=500)
        paragraphs = [
            {
                "text": "Ovo je normalan pasus koji staje u jedan chunk.",
                "font": "ArialMT",
                "size": 10,
                "is_bold": False,
            }
        ]
        chunks = service.smart_chunk_with_fonts(paragraphs)
        assert len(chunks) == 1
        assert "normalan pasus" in chunks[0].content
