# -*- coding: utf-8 -*-
"""
================================================================================
PDF PROCESSING SERVICE
================================================================================
Servis za ekstrakciju, obradu i chunkovanje PDF dokumenata.

Verzija: 1.0.0
================================================================================
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import fitz

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """Podaci o jednom chunk-u."""

    sequence_number: int
    content: str
    token_count: int
    heading_level: int = 0
    parent_heading: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class PDFMetadata:
    """Metadata ekstrahovan iz PDF-a."""

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    total_pages: int = 0
    total_chars: int = 0
    has_images: bool = False
    is_scanned: bool = False


@dataclass
class ProcessingResult:
    """Rezultat procesiranja PDF-a."""

    success: bool
    metadata: PDFMetadata
    chunks: List[ChunkData] = field(default_factory=list)
    error: Optional[str] = None
    pages_text: List[str] = field(default_factory=list)


class PDFService:
    """
    ================================================================================
    PDF PROCESSING SERVICE
    ================================================================================
    Servis za ekstrakciju teksta iz PDF dokumenata, denoising i chunkovanje.
    ================================================================================
    """

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 100
    MIN_CHUNK_SIZE = 50
    ENCODING_NAME = "cl100k_base"

    HEADING_PATTERNS = [
        re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE),
        re.compile(r"^[A-Z][A-Z\s]{2,50}$", re.MULTILINE),
        re.compile(r"^\d+\.\s+[A-Z].+$", re.MULTILINE),
        re.compile(r"^[IVX]+\.\s+[A-Z].+$", re.MULTILINE),
    ]

    NOISE_PATTERNS = [
        re.compile(r"^\s*\d+\s*$", re.MULTILINE),
        re.compile(r"^\s*Page\s+\d+\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"^\s*Strana\s+\d+\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"^\s*-\s*\d+\s*-\s*$", re.MULTILINE),
    ]

    FOOTER_PATTERNS = [
        re.compile(r"©\s*\d{4}.*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"All rights reserved.*$", re.MULTILINE | re.IGNORECASE),
        re.compile(
            r"www\.[a-zA-Z0-9.-]+\.(com|org|net|edu).*$", re.MULTILINE | re.IGNORECASE
        ),
    ]

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        use_ocr: bool = True,
        ocr_language: str = "eng+srp",
    ):
        """
        Inicijalizuje PDF servis.

        Args:
            chunk_size: Maksimalan broj tokena po chunk-u
            chunk_overlap: Broj tokena preklapanja između chunk-ova
            use_ocr: Da li koristiti OCR za skenirane PDF-ove
            ocr_language: Jezik za OCR (npr. "eng+srp" za engleski i srpski)
        """
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
        self.use_ocr = use_ocr and TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE
        self.ocr_language = ocr_language

        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.get_encoding(self.ENCODING_NAME)
            except Exception:
                self.encoder = None
                logger.warning(
                    "Tiktoken encoder not available, using word count approximation"
                )
        else:
            self.encoder = None
            logger.warning("Tiktoken not available, using word count approximation")

    def count_tokens(self, text: str) -> int:
        """
        Broji tokene u tekstu.

        Args:
            text: Tekst za analizu

        Returns:
            Broj tokena
        """
        if self.encoder:
            return len(self.encoder.encode(text))
        return len(text.split())

    def extract_metadata(self, pdf_document: fitz.Document) -> PDFMetadata:
        """
        Ekstrahuje metadata iz PDF dokumenta.

        Args:
            pdf_document: PyMuPDF dokument objekat

        Returns:
            PDFMetadata objekat
        """
        metadata = pdf_document.metadata or {}

        has_images = False
        total_chars = 0

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            total_chars += len(text)

            images = page.get_images()
            if images:
                has_images = True

        is_scanned = total_chars < 100 and has_images

        return PDFMetadata(
            title=metadata.get("title"),
            author=metadata.get("author"),
            subject=metadata.get("subject"),
            creator=metadata.get("creator"),
            producer=metadata.get("producer"),
            total_pages=len(pdf_document),
            total_chars=total_chars,
            has_images=has_images,
            is_scanned=is_scanned,
        )

    def extract_text_from_page(self, page: fitz.Page) -> str:
        """
        Ekstrahuje tekst sa jedne stranice.

        Args:
            page: PyMuPDF page objekat

        Returns:
            Ekstrahovan tekst
        """
        try:
            text = page.get_text("text", sort=True)
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from page: {e}")
            return ""

    def perform_ocr(
        self, pdf_bytes: bytes, page_numbers: List[int] = None, progress_callback=None
    ) -> Dict[int, str]:
        """
        Izvršava OCR na PDF stranicama.

        Args:
            pdf_bytes: PDF sadržaj kao bytes
            page_numbers: Lista brojeva stranica (None = sve)
            progress_callback: Funkcija za ažuriranje progresa (ocr_pages_done, total_pages)

        Returns:
            Dict mapping page_number -> OCR text
        """
        if not self.use_ocr:
            logger.warning("OCR not available or disabled")
            return {}

        ocr_results = {}
        total_pages = len(page_numbers) if page_numbers else 0

        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=200,
                first_page=page_numbers[0] + 1 if page_numbers else None,
                last_page=page_numbers[-1] + 1 if page_numbers else None,
            )

            # Ako page_numbers nije dato, koristimo broj konvertovanih slika
            if not page_numbers:
                total_pages = len(images)

            for idx, image in enumerate(images):
                page_num = page_numbers[idx] if page_numbers else idx
                try:
                    text = pytesseract.image_to_string(image, lang=self.ocr_language)
                    ocr_results[page_num] = text.strip()
                except Exception as e:
                    logger.error(f"OCR failed for page {page_num}: {e}")
                    ocr_results[page_num] = ""

                if progress_callback:
                    progress_callback(idx + 1, total_pages)

            logger.info(f"OCR completed for {len(ocr_results)} pages")

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")

        return ocr_results

    def denoise_text(self, text: str) -> str:
        """
        Uklanja šum iz teksta (header-i, footer-i, brojevi stranica).

        Args:
            text: Tekst za čišćenje

        Returns:
            Očišćen tekst
        """
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                cleaned_lines.append(line)
                continue

            skip = False
            for pattern in self.NOISE_PATTERNS:
                if pattern.match(stripped):
                    skip = True
                    break

            if skip:
                continue

            for pattern in self.FOOTER_PATTERNS:
                if pattern.search(stripped):
                    stripped = pattern.sub("", stripped).strip()
                    if not stripped:
                        skip = True
                        break

            if not skip:
                cleaned_lines.append(stripped if stripped != line.strip() else line)

        return "\n".join(cleaned_lines)

    def detect_heading(self, text: str) -> Tuple[int, Optional[str]]:
        """
        Detektuje da li je tekst heading i vraća nivo.

        Args:
            text: Tekst za analizu

        Returns:
            Tuple (level, heading_text)
        """
        stripped = text.strip()

        if not stripped:
            return 0, None

        for pattern in self.HEADING_PATTERNS:
            match = pattern.match(stripped)
            if match:
                if stripped.startswith("#"):
                    level = len(stripped) - len(stripped.lstrip("#"))
                    return level, stripped.lstrip("#").strip()
                return 1, stripped

        return 0, None

    def smart_chunk(
        self, text: str, page_number: Optional[int] = None
    ) -> List[ChunkData]:
        """
        Vrši pametno chunkovanje teksta.

        Args:
            text: Tekst za chunkovanje
            page_number: Broj stranice (opcionalno)

        Returns:
            Lista ChunkData objekata
        """
        if not text.strip():
            return []

        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current_chunk_text = ""
        current_tokens = 0
        sequence = 0
        current_heading_level = 0
        current_parent_heading = None

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            heading_level, heading_text = self.detect_heading(para)

            if heading_level > 0:
                if current_chunk_text:
                    chunks.append(
                        ChunkData(
                            sequence_number=sequence,
                            content=current_chunk_text.strip(),
                            token_count=current_tokens,
                            heading_level=current_heading_level,
                            parent_heading=current_parent_heading,
                            page_number=page_number,
                        )
                    )
                    sequence += 1
                    current_chunk_text = ""
                    current_tokens = 0

                current_heading_level = heading_level
                current_parent_heading = heading_text
                continue

            para_tokens = self.count_tokens(para)

            if current_tokens + para_tokens > self.chunk_size and current_chunk_text:
                chunks.append(
                    ChunkData(
                        sequence_number=sequence,
                        content=current_chunk_text.strip(),
                        token_count=current_tokens,
                        heading_level=current_heading_level,
                        parent_heading=current_parent_heading,
                        page_number=page_number,
                    )
                )
                sequence += 1

                if self.chunk_overlap > 0 and current_tokens > self.chunk_overlap:
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_text = overlap_text + "\n\n" + para
                    current_tokens = self.count_tokens(current_chunk_text)
                else:
                    current_chunk_text = para
                    current_tokens = para_tokens
            else:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
                current_tokens += para_tokens

        if current_chunk_text.strip():
            chunks.append(
                ChunkData(
                    sequence_number=sequence,
                    content=current_chunk_text.strip(),
                    token_count=current_tokens,
                    heading_level=current_heading_level,
                    parent_heading=current_parent_heading,
                    page_number=page_number,
                )
            )

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """
        Dobija tekst za preklapanje iz kraja chunk-a.

        Args:
            text: Ceo tekst chunk-a

        Returns:
            Tekst za preklapanje
        """
        if self.encoder:
            tokens = self.encoder.encode(text)
            if len(tokens) > self.chunk_overlap:
                overlap_tokens = tokens[-self.chunk_overlap :]
                return self.encoder.decode(overlap_tokens)

        words = text.split()
        if len(words) > self.chunk_overlap // 2:
            return " ".join(words[-(self.chunk_overlap // 2) :])
        return text

    def process_pdf(
        self, pdf_bytes: bytes, title: Optional[str] = None, progress_callback=None
    ) -> ProcessingResult:
        """
        Procesira PDF dokument - ekstrahuje tekst, denoise-uje i chunk-uje.

        Args:
            pdf_bytes: PDF sadržaj kao bytes
            title: Naslov dokumenta (opcionalno)
            progress_callback: Callback za praćenje progresa (pages_done, pages_total, chunks_so_far)

        Returns:
            ProcessingResult sa chunk-ovima i metadata
        """
        logger.info("Starting PDF processing")

        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            return ProcessingResult(
                success=False,
                metadata=PDFMetadata(),
                error=f"Failed to open PDF: {str(e)}",
            )

        try:
            metadata = self.extract_metadata(pdf_document)
            if title:
                metadata.title = title

            pages_text = []
            all_chunks = []
            global_sequence = 0

            ocr_needed = metadata.is_scanned
            ocr_results = {}

            if ocr_needed and self.use_ocr:
                logger.info("Document appears to be scanned, performing OCR")

                # Wrapper za progress tokom OCR - koristi 0 chunks dok se OCR zavrsi
                def ocr_progress_wrapper(ocr_done, ocr_total):
                    if progress_callback:
                        progress_callback(ocr_done, ocr_total, 0)

                ocr_results = self.perform_ocr(
                    pdf_bytes, progress_callback=ocr_progress_wrapper
                )

            for page_num in range(metadata.total_pages):
                page = pdf_document[page_num]

                if page_num in ocr_results and ocr_results[page_num]:
                    text = ocr_results[page_num]
                else:
                    text = self.extract_text_from_page(page)

                if not text and self.use_ocr and page_num not in ocr_results:
                    logger.info(f"No text on page {page_num}, trying OCR")
                    ocr_page = self.perform_ocr(pdf_bytes, [page_num])
                    text = ocr_page.get(page_num, "")

                text = self.denoise_text(text)
                pages_text.append(text)

                page_chunks = self.smart_chunk(text, page_number=page_num + 1)

                for chunk in page_chunks:
                    chunk.sequence_number = global_sequence
                    global_sequence += 1
                    all_chunks.append(chunk)

                if progress_callback:
                    progress_callback(
                        page_num + 1, metadata.total_pages, len(all_chunks)
                    )

            logger.info(
                f"PDF processing completed: {metadata.total_pages} pages, "
                f"{len(all_chunks)} chunks, {metadata.total_chars} chars"
            )

            return ProcessingResult(
                success=True,
                metadata=metadata,
                chunks=all_chunks,
                pages_text=pages_text,
            )

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return ProcessingResult(
                success=False,
                metadata=PDFMetadata(),
                error=f"Processing failed: {str(e)}",
            )
        finally:
            pdf_document.close()

    def process_pdf_from_storage(
        self, storage_path: str, storage_service, title: Optional[str] = None
    ) -> ProcessingResult:
        """
        Procesira PDF iz storage-a.

        Args:
            storage_path: Path do fajla u storage-u
            storage_service: StorageService instanca
            title: Naslov dokumenta (opcionalno)

        Returns:
            ProcessingResult sa chunk-ovima i metadata
        """
        try:
            pdf_bytes = storage_service.download_file(storage_path)
            return self.process_pdf(pdf_bytes, title=title)
        except Exception as e:
            logger.error(f"Failed to process PDF from storage: {e}")
            return ProcessingResult(
                success=False,
                metadata=PDFMetadata(),
                error=f"Failed to download from storage: {str(e)}",
            )


pdf_service = PDFService()
