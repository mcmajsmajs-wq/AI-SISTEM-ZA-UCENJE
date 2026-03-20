# -*- coding: utf-8 -*-
"""
================================================================================
PDF PROCESSING SERVICE
================================================================================
Servis za ekstrakciju, obradu i chunkovanje PDF dokumenata.

Verzija: 1.0.0
================================================================================
"""

import io
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import fitz
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Surya OCR - modern ML-based OCR (fallback option)
try:
    import surya
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    SURYA_AVAILABLE = True
except ImportError:
    SURYA_AVAILABLE = False

# EasyOCR - koristi ruski kao fallback za ćirilicu
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

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

from app.core.config import settings

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
    """Metadata ekstrahovana iz PDF-a."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    total_pages: int = 0
    total_chars: int = 0
    has_images: bool = False
    is_scanned: bool = False
    skipped_pages: int = 0  # Number of empty/TOC pages skipped


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
        re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE),
        re.compile(r'^[A-Z][A-Z\s]{2,50}$', re.MULTILINE),
        re.compile(r'^\d+\.\s+[A-Z].+$', re.MULTILINE),
        re.compile(r'^[IVX]+\.\s+[A-Z].+$', re.MULTILINE),
    ]
    
    NOISE_PATTERNS = [
        re.compile(r'^\s*\d+\s*$', re.MULTILINE),
        re.compile(r'^\s*Page\s+\d+\s*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'^\s*Strana\s+\d+\s*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'^\s*-\s*\d+\s*-\s*$', re.MULTILINE),
        # TOC entries: "Chapter Name ......... 12" or "1.2 Section ... 45"
        re.compile(r'^.{3,80}\.{3,}\s*\d+\s*$', re.MULTILINE),
        re.compile(r'^.{3,80}\s{2,}\d+\s*$', re.MULTILINE),
        # Figure captions: "Figure 1.", "Figure 2.3", "FIG. 1", "Slika 1"
        re.compile(r'^figure\s+\d+[\d.:\s]', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^fig\.\s*\d+', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^slika\s+\d+', re.IGNORECASE | re.MULTILINE),
        # Serbian metadata - author, publisher, copyright pages
        re.compile(r'^др\s+војислав', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^аутор', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^рецензент', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^уредник', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^илустраци', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^лектура', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^коректура', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^дизајн', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^прелом', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^издавач', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^тираж', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^штампа', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^isbn', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^министарство просвете', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^одобрило\s+је', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^решење\s+број', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^фондаци', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^математички\s+клуб', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^реч\s+аутора', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^реч\s+издавача', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^сadrжај', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^казало', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^литература', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^регистар', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^индекс', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^увод', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^предговор', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^закључак', re.IGNORECASE | re.MULTILINE),
    ]

    # Pattern for detecting figure captions (just the caption, no content)
    FIGURE_CAPTION_PATTERN = re.compile(
        r'^(figure|fig\.|slika)\s+\d+[\d.:\s]?.{0,100}$',
        re.IGNORECASE | re.MULTILINE
    )

    # Detect if a page is mostly a Table of Contents (dotted lines OR numbered sections)
    TOC_PAGE_PATTERN = re.compile(r'(\.{3,}\s*\d+|\b\d+\.\d+\s+[A-Z])', re.MULTILINE)
    # Count numbered section references in text (e.g. "7.6 How to ...")
    NUMBERED_SECTION_PATTERN = re.compile(r'\b\d+\.\d+[\d.]*\s+[A-Z]')
    # Detect a TOC header page ("Contents", "Table of Contents", "Sadržaj", etc.)
    TOC_HEADER_PATTERN = re.compile(
        r'^\s*(table\s+of\s+contents|contents|sadržaj|inhalt|inhaltsverzeichnis|'
        r'índice|sommaire|содержание|kazalo|sadrzaj|pregled\s+sadržaja)\s*$',
        re.IGNORECASE | re.MULTILINE
    )
    
    FOOTER_PATTERNS = [
        re.compile(r'©\s*\d{4}.*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'All rights reserved.*$', re.MULTILINE | re.IGNORECASE),
        re.compile(r'www\.[a-zA-Z0-9.-]+\.(com|org|net|edu).*$', re.MULTILINE | re.IGNORECASE),
    ]
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        use_ocr: bool = True,
        ocr_language: str = "srp"  # Serbian - podržava i ćirilicu i latinicu
    ):
        """
        Inicijalizuje PDF servis.
        
        Args:
            chunk_size: Maksimalan broj tokena po chunk-u
            chunk_overlap: Broj tokena preklapanja između chunk-ova
            use_ocr: Da li koristiti OCR za skenirane PDF-ove
            ocr_language: Jezik za OCR ("srp" za srpski cirilicu, "srp+eng" za oba)
        """
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
        self.use_ocr = use_ocr and (TESSERACT_AVAILABLE or SURYA_AVAILABLE or EASYOCR_AVAILABLE) and PDF2IMAGE_AVAILABLE
        self.ocr_language = ocr_language
        # Tiktoken se učitava lazily pri prvom count_tokens pozivu
        self.encoder = None
        self._tiktoken_loaded = False
        # Surya OCR - inicijalizira se lazily
        self._surya_ocr = None
        self._surya_detector = None
        self._surya_initialized = False
        # EasyOCR - inicijalizira se lazily (koristi ru kao fallback za cirilicu)
        self._easyocr_reader = None
        self._easyocr_initialized = False
        # Provera kvaliteta OCR - smanjeno za stranice sa slikama
        self._min_ocr_char_ratio = 0.00005  # Minimum 0.005% karaktera po slici (smanjeno za skenirane dokumente sa slikama)
    
    
    def _verify_ocr_quality(self, text: str, image_size: tuple, is_easyocr: bool = False) -> bool:
        """
        Proverava da li OCR rezultat ima smisla.
        Returns True ako je kvalitet dovoljan.
        """
        if not text or len(text.strip()) == 0:
            return False
        
        # EasyOCR je dizajniran za dokumente, verujemo mu
        if is_easyocr and len(text.strip()) > 10:
            return True
        
        # Provera minimalnog broja karaktera
        image_pixels = image_size[0] * image_size[1]
        char_density = len(text.strip()) / max(image_pixels, 1)
        
        if char_density < self._min_ocr_char_ratio:
            logger.warning(f"OCR low char density: {char_density:.4f} < {self._min_ocr_char_ratio}")
            return False
        
        return True
    
    
    def _init_easyocr(self):
        """Inicijalizira EasyOCR lazily sa srpskim jezicima."""
        if self._easyocr_initialized:
            return
        
        if EASYOCR_AVAILABLE:
            try:
                logger.info("Inicijaliziram EasyOCR sa srpskim jezicima...")
                # rs_cyrillic requires ru as base for Cyrillic support
                # Works: ru + rs_cyrillic + en
                # Optimizacija memorije: gpu=False, manji batch size
                self._easyocr_reader = easyocr.Reader(
                    ['ru', 'rs_cyrillic', 'en'], 
                    gpu=False, 
                    verbose=False,
                    batch_size=5,  # Smanjen batch za manje memorije
                    reporter=None
                )
                self._easyocr_initialized = True
                logger.info("EasyOCR uspešno inicijalizovan sa ru, rs_cyrillic, en (optimizovano za memoriju)")
            except Exception as e:
                logger.warning(f"EasyOCR init failed: {e}")
                self._easyocr_initialized = False
        else:
            logger.warning("EasyOCR nije dostupna")
            self._easyocr_initialized = False
    
    
    def _init_surya(self):
        """Inicijalizira Surya OCR lazily."""
        if self._surya_initialized:
            return
        
        if SURYA_AVAILABLE:
            try:
                logger.info("Inicijaliziram Surya OCR...")
                import os
                os.environ['TORCH_DEVICE'] = 'cpu'
                self._surya_detector = DetectionPredictor()
                self._surya_ocr = RecognitionPredictor(self._surya_detector)
                self._surya_initialized = True
                logger.info("Surya OCR uspešno inicijalizovan")
            except Exception as e:
                logger.warning(f"Surya OCR init failed: {e}")
                self._surya_initialized = False
        else:
            logger.warning("Surya OCR nije dostupna")
            self._surya_initialized = False
    
    
    def count_tokens(self, text: str) -> int:
        """Broji tokene u tekstu."""
        if not self._tiktoken_loaded:
            self._tiktoken_loaded = True
            if TIKTOKEN_AVAILABLE:
                import concurrent.futures
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                future = executor.submit(tiktoken.get_encoding, self.ENCODING_NAME)
                executor.shutdown(wait=False)
                try:
                    self.encoder = future.result(timeout=5)
                except Exception:
                    self.encoder = None
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
            is_scanned=is_scanned
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
    
    def is_empty_page(self, page: fitz.Page, text: str = None) -> bool:
        """
        Proverava da li je stranica prazna ili skoro prazna.
        
        Args:
            page: PyMuPDF page objekat
            text: Prethodno ekstrahovan tekst (opciono)
            
        Returns:
            True ako je stranica prazna
        """
        # If text is provided, check its content
        if text is not None:
            # Count non-whitespace characters
            char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
            
            # Extended list of phrases that indicate low-quality/empty content
            empty_phrases = [
                # English
                'this page intentionally left blank',
                'this page intentionally blank',
                'page left blank',
                'blank page',
                'reserved',
                'notes',
                'copyright',
                'all rights reserved',
                'this material is copyright',
                'no part of this publication',
                'first edition',
                'second edition',
                'third edition',
                'fourth edition',
                'updated edition',
                'revised edition',
                'edition notice',
                'notice to reader',
                'notice to readers',
                'preface',
                'acknowledgments',
                'acknowledgements',
                'table of contents',
                'about the author',
                'author biography',
                'back cover',
                'front cover',
                'cover page',
                'title page',
                'dedication',
                'epigraph',
                # Serbian
                'stranica namerno ostavljena prazna',
                'prazna stranica',
                'sva prava zadržana',
                'copyright ©',
                'sva prava zadržana ©',
                'napomene',
                'bilješke',
                'sadržaj',
                'kazalo',
                'predgovor',
                'zahvalnice',
                'izdanje',
                'prvo izdanje',
                'drugo izdanje',
                'treće izdanje',
            ]
            
            text_lower = text.lower().strip()
            
            # Check for "intentionally left blank" patterns - filter these regardless of length
            for phrase in empty_phrases:
                if phrase in text_lower:
                    # But allow if the page has substantial content beyond this phrase
                    if char_count > 500:
                        continue
                    return True
            
            # If text is very short, consider it empty
            if char_count < 100:
                return True
            
            return False
        
        # Otherwise extract text and check
        text = self.extract_text_from_page(page)
        return self.is_empty_page(page, text)
    
    def extract_images_from_page(self, page: fitz.Page) -> List[bytes]:
        """
        Ekstrahuje sve slike sa stranice.
        
        Args:
            page: PyMuPDF page objekat
            
        Returns:
            Lista slika kao bytes
        """
        images = []
        for img in page.get_images():
            xref = img[0]
            try:
                base_image = page.parent.extract_image(xref)
                images.append(base_image["image"])
            except Exception as e:
                logger.debug(f"Failed to extract image: {e}")
        return images
    
    def perform_ocr(self, pdf_bytes: bytes, page_numbers: List[int] = None) -> Dict[int, str]:
        """
        Izvršava OCR na PDF stranicama sa fallback sistemom.
        Prvo pokušava Tesseract, zatim Surya ako je kvalitet loš.
        
        Args:
            pdf_bytes: PDF sadržaj kao bytes
            page_numbers: Lista brojeva stranica (None = sve)
            
        Returns:
            Dict mapping page_number -> OCR text
        """
        if not self.use_ocr:
            logger.warning("OCR not available or disabled")
            return {}
        
        ocr_results = {}
        
        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=200,
                first_page=page_numbers[0] + 1 if page_numbers else None,
                last_page=page_numbers[-1] + 1 if page_numbers else None
            )
            
            logger.info(f"Starting OCR on {len(images)} pages with fallback system")
            
            for idx, image in enumerate(images):
                page_num = page_numbers[idx] if page_numbers else idx
                text = ""
                ocr_method = "none"
                
                # 1. Pokušaj Tesseract prvo
                if TESSERACT_AVAILABLE:
                    try:
                        text = pytesseract.image_to_string(
                            image, 
                            lang=self.ocr_language,
                            config='--psm 3'
                        )
                        text = text.strip()
                        ocr_method = "tesseract"
                        
                        # Proveri kvalitet
                        if not self._verify_ocr_quality(text, image.size):
                            logger.warning(f"Tesseract low quality for page {page_num}, trying Surya...")
                            text = ""  # Reset for Surya
                        else:
                            logger.debug(f"Tesseract OK for page {page_num}")
                    except Exception as e:
                        logger.warning(f"Tesseract failed for page {page_num}: {e}")
                        text = ""
                
                # 2. Ako Tesseract nije dao dobar rezultat, probaj EasyOCR (sa srpskim jezicima)
                if not text and EASYOCR_AVAILABLE:
                    try:
                        self._init_easyocr()
                        if self._easyocr_reader:
                            import numpy as np
                            img_array = np.array(image)
                            results = self._easyocr_reader.readtext(
                                img_array,
                                detail=0,
                                paragraph=True
                            )
                            if results:
                                text = '\n'.join(results)
                                text = text.strip()
                                ocr_method = "easyocr_sr"
                                
                                if not self._verify_ocr_quality(text, image.size, is_easyocr=True):
                                    logger.warning(f"EasyOCR also low quality for page {page_num}")
                                else:
                                    logger.debug(f"EasyOCR OK for page {page_num}")
                    except Exception as e:
                        logger.warning(f"EasyOCR failed for page {page_num}: {e}")
                
                # 3. Ako ništa nije radilo, pokušaj Surya
                if not text and SURYA_AVAILABLE:
                    try:
                        self._init_surya()
                        if self._surya_ocr:
                            predictions = self._surya_ocr.predict([image])
                            if predictions and len(predictions) > 0:
                                # Surya vraća listu text_lines objekata
                                text = ""
                                for pred in predictions:
                                    if hasattr(pred, 'text_lines'):
                                        for line in pred.text_lines:
                                            text += line.text + "\n"
                                    elif hasattr(pred, 'text'):
                                        text += pred.text + "\n"
                                text = text.strip()
                                ocr_method = "surya"
                                
                                if not self._verify_ocr_quality(text, image.size):
                                    logger.warning(f"Surya also low quality for page {page_num}")
                                else:
                                    logger.debug(f"Surya OK for page {page_num}")
                    except Exception as e:
                        logger.warning(f"Surya failed for page {page_num}: {e}")
                
                # 3. Ako ništa nije radilo, pokušaj Tesseract sa srpskim jezikom
                if not text and TESSERACT_AVAILABLE:
                    try:
                        text = pytesseract.image_to_string(image, lang=self.ocr_language, config='--psm 3')
                        text = text.strip()
                        ocr_method = "tesseract_fallback"
                        logger.warning(f"Using Tesseract fallback for page {page_num}")
                    except Exception as e:
                        logger.error(f"All OCR methods failed for page {page_num}: {e}")
                
                # Preskoči metadata stranice (korice, copyright, sadržaj, itd)
                if self.is_metadata_page(text):
                    logger.info(f"Skipping metadata page {page_num}")
                    text = ""
                
                ocr_results[page_num] = text
                logger.debug(f"Page {page_num}: {ocr_method}, chars={len(text)}")
                
                # Oslobodi memoriju nakon obrade stranice
                del image
                if idx % 10 == 0:
                    import gc
                    gc.collect()
            
            # Oslobodi sve slike nakon OCR-a
            del images
            import gc
            gc.collect()
            
            total_chars = sum(len(t) for t in ocr_results.values())
            logger.info(f"OCR completed for {len(ocr_results)} pages, total chars: {total_chars}")
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
        
        return ocr_results
    
    def is_metadata_page(self, text: str) -> bool:
        """
        Proverava da li je stranica uglavnom metadata (korice, copyright, sadržaj).
        Takve stranice treba preskočiti.
        
        Args:
            text: Tekst stranice
            
        Returns:
            True ako stranica treba da se preskoči
        """
        if not text or len(text.strip()) < 50:
            return True
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return True
        
        # Pokazatelji metadata stranica
        metadata_indicators = [
            # Serbian
            'аутор', 'аутора', 'аутору', 'аутором',
            'рецензент', 'рецензенти', 'рецензената',
            'уредник', 'уредника', 'уредници',
            'издавач', 'издавача', 'издаваштво',
            'тираж', 'штампа', 'штампане',
            'copyright', 'сва права', 'сва права задржана',
            'isbn', 'issn',
            'министарство просвете',
            'одобрило је', 'решење број',
            'фондаци', 'кавчић', 'алек',
            'математички клуб', 'диофант',
            'реч аутора', 'реч издавача',
            'садржина', 'казало', 'садржај',
            'литература', 'библиографиј',
            'регистар', 'индекс', 'појмовник',
            'увод', 'предговор', 'закључак',
            # English
            'author', 'authors', 'publisher',
            'copyright', 'all rights reserved',
            'table of contents', 'contents',
            'index', 'bibliography', 'references',
            'preface', 'introduction', 'foreword',
            'edition', 'first edition', 'second edition',
            'printed by', 'print', 'impression',
        ]
        
        text_lower = text.lower()
        metadata_count = sum(1 for ind in metadata_indicators if ind in text_lower)
        
        # Ako ima više od 3 metadata indikatora, verovatno je metadata stranica
        if metadata_count >= 3:
            return True
        
        # Provera za kratke stranice sa imenima (autori, recenzenti)
        if len(lines) < 20:
            short_metadata = ['аутор', 'рецензент', 'уредник', 'издавач', 'author', 'publisher']
            if any(m in text_lower for m in short_metadata):
                return True
        
        return False
    
    def denoise_text(self, text: str) -> str:
        """
        Uklanja šum iz teksta (header-i, footer-i, brojevi stranica).
        
        Args:
            text: Tekst za čišćenje
            
        Returns:
            Očišćen tekst
        """
        lines = text.split('\n')
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
                    stripped = pattern.sub('', stripped).strip()
                    if not stripped:
                        skip = True
                        break
            
            if not skip:
                cleaned_lines.append(stripped if stripped != line.strip() else line)
        
        return '\n'.join(cleaned_lines)
    
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
                if stripped.startswith('#'):
                    level = len(stripped) - len(stripped.lstrip('#'))
                    return level, stripped.lstrip('#').strip()
                return 1, stripped
        
        return 0, None
    
    def smart_chunk(
        self,
        text: str,
        page_number: Optional[int] = None
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
        
        paragraphs = re.split(r'\n\s*\n', text)
        
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
                    chunks.append(ChunkData(
                        sequence_number=sequence,
                        content=current_chunk_text.strip(),
                        token_count=current_tokens,
                        heading_level=current_heading_level,
                        parent_heading=current_parent_heading,
                        page_number=page_number
                    ))
                    sequence += 1
                    current_chunk_text = ""
                    current_tokens = 0
                
                current_heading_level = heading_level
                current_parent_heading = heading_text
                continue
            
            para_tokens = self.count_tokens(para)
            
            if current_tokens + para_tokens > self.chunk_size and current_chunk_text:
                chunks.append(ChunkData(
                    sequence_number=sequence,
                    content=current_chunk_text.strip(),
                    token_count=current_tokens,
                    heading_level=current_heading_level,
                    parent_heading=current_parent_heading,
                    page_number=page_number
                ))
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
            chunks.append(ChunkData(
                sequence_number=sequence,
                content=current_chunk_text.strip(),
                token_count=current_tokens,
                heading_level=current_heading_level,
                parent_heading=current_parent_heading,
                page_number=page_number
            ))
        
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
                overlap_tokens = tokens[-self.chunk_overlap:]
                return self.encoder.decode(overlap_tokens)
        
        words = text.split()
        if len(words) > self.chunk_overlap // 2:
            return ' '.join(words[-(self.chunk_overlap // 2):])
        return text
    
    def process_pdf(
        self,
        pdf_bytes: bytes,
        title: Optional[str] = None,
        progress_callback=None,
    ) -> ProcessingResult:
        """
        Procesira PDF dokument - ekstrahuje tekst, denoise-uje i chunk-uje.
        
        Args:
            pdf_bytes: PDF sadržaj kao bytes
            title: Naslov dokumenta (opcionalno)
            
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
                error=f"Failed to open PDF: {str(e)}"
            )
        
        try:
            metadata = self.extract_metadata(pdf_document)
            if title:
                metadata.title = title
            
            pages_text = []
            all_chunks = []
            global_sequence = 0
            in_toc = False  # Track if we're inside a TOC section
            skipped_pages = 0  # Track skipped empty/TOC pages
            
            ocr_needed = metadata.is_scanned
            ocr_results = {}
            
            if ocr_needed and self.use_ocr:
                logger.info("Document appears to be scanned, performing OCR")
                ocr_results = self.perform_ocr(pdf_bytes)
            
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

                # Skip Table of Contents pages
                lines = [l for l in text.splitlines() if l.strip()]
                numbered_section_count = len(self.NUMBERED_SECTION_PATTERN.findall(text))
                word_count = len(text.split())

                # Check for explicit TOC header on the first line ("Contents", "Sadržaj", etc.)
                first_line = lines[0] if lines else ''
                is_toc_header = bool(self.TOC_HEADER_PATTERN.match(first_line.strip()))

                if lines:
                    toc_lines = sum(1 for l in lines if self.TOC_PAGE_PATTERN.search(l))
                    toc_ratio = toc_lines / len(lines)

                    # Enter TOC mode: explicit header, dense TOC lines, or many section refs
                    if is_toc_header or toc_ratio >= 0.3 or numbered_section_count >= 8:
                        in_toc = True

                    # Exit TOC mode: page has substantial real content with few TOC markers
                    elif in_toc and toc_ratio < 0.15 and numbered_section_count < 3 and word_count > 120:
                        in_toc = False

                if in_toc:
                    logger.debug(f"Skipping TOC page {page_num + 1} (header={is_toc_header}, sections={numbered_section_count})")
                    skipped_pages += 1
                    pages_text.append("")
                    continue

                # Skip empty or nearly empty pages
                if self.is_empty_page(page, text):
                    logger.debug(f"Skipping empty page {page_num + 1}")
                    skipped_pages += 1
                    continue

                pages_text.append(text)
                
                page_chunks = self.smart_chunk(text, page_number=page_num + 1)
                
                for chunk in page_chunks:
                    # Skip TOC-like chunks (≥5 numbered section references in chunk content)
                    if len(self.NUMBERED_SECTION_PATTERN.findall(chunk.content)) >= 5:
                        logger.debug(f"Skipping TOC chunk on page {page_num + 1}")
                        continue
                    
                    # Skip figure captions (very short chunks starting with Figure/Fig/Slika)
                    chunk_text = chunk.content.strip()
                    if self.FIGURE_CAPTION_PATTERN.match(chunk_text[:50]):
                        logger.debug(f"Skipping figure caption chunk on page {page_num + 1}")
                        continue
                    
                    # Skip very short chunks (< 100 chars) - likely noise
                    if len(chunk_text) < 100:
                        logger.debug(f"Skipping short chunk on page {page_num + 1}: {chunk_text[:30]}...")
                        continue
                    
                    chunk.sequence_number = global_sequence
                    global_sequence += 1
                    all_chunks.append(chunk)

                # Report progress every 5 pages
                if progress_callback and (page_num % 5 == 0 or page_num == metadata.total_pages - 1):
                    try:
                        progress_callback(page_num + 1, metadata.total_pages, len(all_chunks))
                    except Exception:
                        pass
            
            logger.info(
                f"PDF processing completed: {metadata.total_pages} pages, "
                f"{len(all_chunks)} chunks, {metadata.total_chars} chars, "
                f"{skipped_pages} pages skipped (empty/TOC)"
            )
            
            # Update metadata with skipped pages count
            metadata.skipped_pages = skipped_pages
            
            return ProcessingResult(
                success=True,
                metadata=metadata,
                chunks=all_chunks,
                pages_text=pages_text
            )
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return ProcessingResult(
                success=False,
                metadata=PDFMetadata(),
                error=f"Processing failed: {str(e)}"
            )
        finally:
            pdf_document.close()
    
    def process_pdf_from_storage(
        self,
        storage_path: str,
        storage_service,
        title: Optional[str] = None
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
                error=f"Failed to download from storage: {str(e)}"
            )


pdf_service = PDFService()
