# -*- coding: utf-8 -*-
"""
================================================================================
AI Learning System
PDF Export Service - Verzija sa PDF Bookmarks i konzistentnim stilom
Verzija: 3.0.0
Koristi PyMuPDF za dodavanje bookmarks u generisani PDF.
================================================================================
"""

import io
import logging
import re
from datetime import datetime
from typing import List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.services.base_export_service import BaseExportService

logger = logging.getLogger(__name__)

# Font setup
_FONT_NAME = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
try:
    import os

    _dejavu_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    _dejavu_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(_dejavu_path):
        pdfmetrics.registerFont(TTFont("DejaVuSans", _dejavu_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _dejavu_bold))
        _FONT_NAME = "DejaVuSans"
        _FONT_BOLD = "DejaVuSans-Bold"
except Exception:
    pass


def _esc(text: str) -> str:
    """Escape special characters za PDF."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "<br/>")
    )


def _esc_simple(text: str) -> str:
    """Escape special characters - jednostavnija verzija bez <br/>."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _split_paragraphs(text: str, expected_count: int = 0) -> list:
    """Razbija tekst na pasuse.

    Ako je zadat expected_count, pokušava da podeli tekst na toliko delova
    (prvo heuristikom, pa ako ne uspe, grubom podelom).

    Args:
        text: Tekst za splitovanje
        expected_count: Očekivani broj pasusa (iz layout_data)

    Returns:
        Lista stringova, svaki jedan pasus
    """
    if not text:
        return []

    parts = re.split(r"\n\s*\n", text)
    if len(parts) > 1:
        result = [p.strip() for p in parts if p.strip()]
        if expected_count and len(result) != expected_count:
            pass  # nastavi dalje, probaj drugu metodu
        else:
            return result

    matches = list(
        re.finditer(r"\d+\.\s+(?:\*\*)?[A-Z\u0100-\u024F\u0400-\u04FF]", text)
    )
    if len(matches) > 1:
        result = []
        prev_end = 0
        for m in matches:
            if m.start() == prev_end and m.start() < 3:
                continue
            if m.start() > prev_end:
                result.append(text[prev_end : m.start()].strip())
            prev_end = m.start()
        if prev_end < len(text):
            result.append(text[prev_end:].strip())
        result = [p for p in result if p]
        if expected_count and len(result) != expected_count:
            pass
        else:
            return result

    if expected_count > 1:
        rough = _split_evenly(text, expected_count)
        return rough

    return [text.strip()]


def _split_evenly(text: str, n: int) -> list:
    """Grubo deli tekst na n približno jednakih delova po rečenicama."""
    if n <= 1 or not text:
        return [text.strip()] if text.strip() else []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return [text.strip()]

    if len(sentences) <= n:
        return sentences

    target = max(1, len(sentences) // n)
    result = []
    for i in range(n):
        start = i * target
        end = start + target if i < n - 1 else len(sentences)
        chunk = " ".join(sentences[start:end])
        if chunk.strip():
            result.append(chunk.strip())
    return result


def _map_font(is_bold: bool) -> str:
    """Mapira bold/regular na dostupne fontove."""
    return _FONT_BOLD if is_bold else _FONT_NAME


def _get_layout_paragraphs(chunk: dict) -> Optional[list]:
    """Vraća layout_data.paragraphs iz chunk-a ako postoje.

    Returns:
        list of dict (paragraph info) ili None ako nema
    """
    layout_data = chunk.get("layout_data")
    if layout_data and isinstance(layout_data, dict):
        paras = layout_data.get("paragraphs")
        if paras and isinstance(paras, list) and len(paras) > 0:
            return paras
    return None


def _scale_size(orig_size: float, ref_body: float = 15.0) -> float:
    """Skalira originalnu veličinu fonta na našu bazu (10pt).

    Ako je original body bio 15pt, a naš body je 10pt,
    faktor skaliranja = 10/15. Onda heading od 21pt postaje 21*10/15 = 14pt.

    Args:
        orig_size: Originalna veličina fonta
        ref_body: Referentna veličina body fonta u originalu (default 15pt)

    Returns:
        Skalirana veličina, clampovana na [7, 20]
    """
    if not orig_size or orig_size <= 0:
        return 10.0
    scale = 10.0 / max(ref_body, 1)
    scaled = orig_size * scale
    return max(7.0, min(20.0, scaled))


def _strip_marker(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"^###\s*\d+\s*", "", text)
    return text.strip()


class PDFExportService(BaseExportService):
    """PDF Export Service - Generisanje PDF sa bookmarks."""

    def _build_styles(self):
        """Kreira stilove sa konzistentnim bojama."""
        base_color = colors.HexColor("#1f2937")

        return {
            "cover_title": ParagraphStyle(
                "CoverTitle",
                fontName=_FONT_BOLD,
                fontSize=28,
                leading=34,
                spaceAfter=12,
                textColor=colors.HexColor("#111827"),
                alignment=TA_CENTER,
            ),
            "cover_subtitle": ParagraphStyle(
                "CoverSubtitle",
                fontName=_FONT_NAME,
                fontSize=14,
                leading=20,
                spaceAfter=8,
                textColor=colors.HexColor("#4b5563"),
                alignment=TA_CENTER,
            ),
            "meta": ParagraphStyle(
                "Meta",
                fontName=_FONT_NAME,
                fontSize=10,
                textColor=colors.HexColor("#6b7280"),
                alignment=TA_CENTER,
                spaceAfter=24,
            ),
            "h1": ParagraphStyle(
                "H1",
                fontName=_FONT_BOLD,
                fontSize=14,
                leading=18,
                spaceBefore=8,
                spaceAfter=4,
                textColor=base_color,
                alignment=TA_LEFT,
            ),
            "h2": ParagraphStyle(
                "H2",
                fontName=_FONT_BOLD,
                fontSize=12,
                leading=16,
                spaceBefore=6,
                spaceAfter=3,
                textColor=base_color,
                alignment=TA_LEFT,
            ),
            "h3": ParagraphStyle(
                "H3",
                fontName=_FONT_BOLD,
                fontSize=11,
                leading=14,
                spaceBefore=4,
                spaceAfter=2,
                textColor=base_color,
                alignment=TA_LEFT,
            ),
            "body": ParagraphStyle(
                "Body",
                fontName=_FONT_NAME,
                fontSize=10,
                leading=13,
                spaceBefore=2,
                spaceAfter=4,
                textColor=base_color,
                alignment=TA_LEFT,
            ),
            "footer": ParagraphStyle(
                "Footer",
                fontName=_FONT_NAME,
                fontSize=8,
                textColor=colors.HexColor("#9ca3af"),
                alignment=TA_CENTER,
            ),
            "toc_title": ParagraphStyle(
                "TocTitle",
                fontName=_FONT_BOLD,
                fontSize=16,
                leading=22,
                spaceAfter=10,
                textColor=colors.HexColor("#111827"),
                alignment=TA_CENTER,
            ),
            "toc_item": ParagraphStyle(
                "TocItem",
                fontName=_FONT_NAME,
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#4b5563"),
                spaceAfter=2,
            ),
        }

    def _build_layout_style(
        self, para_info: dict, base_style: ParagraphStyle, ref_body: float = 15.0
    ) -> ParagraphStyle:
        """Kreira ParagraphStyle iz layout_data informacija.

        Args:
            para_info: Dict sa 'font', 'size', 'is_bold' kljucevima
            base_style: Osnovni stil (za boju, alignment, spacing)
            ref_body: Referentna velicina body fonta u originalu

        Returns:
            ParagraphStyle sa prilagodjenim fontom i velicinom
        """
        is_bold = para_info.get("is_bold", False) or "Bold" in para_info.get("font", "")
        font_name = _map_font(is_bold)
        orig_size = para_info.get("size", 10.0)
        scaled = _scale_size(orig_size, ref_body)

        return ParagraphStyle(
            base_style.name + "Layout",
            fontName=font_name,
            fontSize=round(scaled, 1),
            leading=round(scaled * 1.4, 1),
            textColor=base_style.textColor,
            alignment=base_style.alignment,
            spaceBefore=base_style.spaceBefore,
            spaceAfter=base_style.spaceAfter,
        )

    def _parse_skill_prompt(self, prompt: str) -> dict:
        """Parsira skill prompt i ekstrahuje opcije za PDF formatiranje."""
        options = {
            "table_of_contents": False,
            "bold_headings": True,
            "justified": True,
            "font": "DejaVuSans",
            "font_size": 11,
        }

        if not prompt:
            return options

        prompt_lower = prompt.lower()

        if (
            "table of contents" in prompt_lower
            or "sadržaj" in prompt_lower
            or "toc" in prompt_lower
        ):
            options["table_of_contents"] = True

        if "bold" in prompt_lower:
            options["bold_headings"] = True

        if "justified" in prompt_lower:
            options["justified"] = True

        if "arial" in prompt_lower:
            options["font"] = "Arial"
        elif "times" in prompt_lower or "roman" in prompt_lower:
            options["font"] = "Times New Roman"
        elif "helvetica" in prompt_lower:
            options["font"] = "Helvetica"

        return options

    def _render_toc(
        self,
        story: list,
        styles: dict,
        translated_chunks: list,
        bookmarks: list,
        page_number_map: Optional[dict] = None,
    ):
        """Dodaje TOC stavke u story, sa originalnim brojevima strana.

        Priority for page numbers:
        1. page_number_map (from chunk.layout_data or page_number field)
        2. No page number shown

        Args:
            story: ReportLab story list
            styles: Style dict from _build_styles()
            translated_chunks: List of chunk dicts (deduplicated)
            bookmarks: List to append bookmark entries to
            page_number_map: Optional dict of bookmark_title -> page_number (original doc page)
        """
        for idx, chunk in enumerate(translated_chunks):
            trans = chunk.get("translated_text", "")
            heading_level = chunk.get("heading_level", 0)
            if heading_level > 0 and trans:
                clean = _strip_marker(trans)
                if not clean:
                    continue
                toc_text = clean[:90].replace("\n", " ").strip()
                if len(clean) > 90:
                    toc_text += "..."
                indent = (heading_level - 1) * 15
                bm_title = clean[:80]

                display_text = toc_text
                page_str = ""
                if page_number_map and bm_title in page_number_map:
                    page_num = page_number_map[bm_title]
                    page_str = str(page_num)
                    visible = len(toc_text)
                    dots = max(3, 76 - visible - len(page_str))
                    display_text = f"{toc_text} {'·' * dots} {page_str}"

                toc_style = ParagraphStyle(
                    "TocItem",
                    fontName=_FONT_NAME,
                    fontSize=9,
                    leading=13,
                    textColor=colors.HexColor("#4b5563"),
                    leftIndent=indent,
                    spaceAfter=2,
                )
                story.append(Paragraph(_esc_simple(display_text), toc_style))
                bookmarks.append(
                    {
                        "title": bm_title,
                        "level": heading_level - 1,
                        "page": page_number_map.get(bm_title)
                        if page_number_map
                        else None,
                    }
                )

            if idx % 500 == 0:
                self._report_progress(
                    10, 100, f"TOC: {idx}/{len(translated_chunks)}..."
                )

    def _extract_heading_pages(self, chunks: list) -> dict:
        """Extracts heading page numbers from chunk data.

        Builds a map of bookmark_title -> page_number using the chunk's
        page_number or layout_data.page_number. These are the page numbers
        from the ORIGINAL document, used for TOC display.

        Falls back to empty dict if no page numbers available.
        """
        result = {}
        seen_content = set()
        for chunk in chunks:
            if not chunk.get("translated_text"):
                continue
            content = chunk["translated_text"].strip()
            if content in seen_content:
                continue
            seen_content.add(content)

            heading_level = chunk.get("heading_level", 0)
            if heading_level > 0:
                clean = _strip_marker(content)
                if not clean:
                    continue
                bm_title = clean[:80]

                # Try page_number from chunk, then from layout_data
                page_num = chunk.get("page_number")
                if not page_num:
                    layout_data = chunk.get("layout_data")
                    if layout_data and isinstance(layout_data, dict):
                        page_num = layout_data.get("page_number")

                if page_num and page_num > 0:
                    result[bm_title] = page_num

        return result

    def _find_heading_pages(self, pdf_bytes: bytes, bookmarks: list) -> dict:
        """Pronalazi broj strane za svaki bookmark title koristeći PyMuPDF.

        Vraća dict: bookmark_title -> page_number (1-based).
        """
        import fitz

        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        heading_locations = {}

        bookmark_titles = [
            bm.get("title") if isinstance(bm, dict) else bm[0] for bm in bookmarks
        ]

        toc_end_page = 0
        for page_num in range(len(pdf_doc)):
            page_text = pdf_doc[page_num].get_text("text")
            if "SADRŽAJ" in page_text or "SADRZAJ" in page_text:
                toc_end_page = page_num

        content_start = toc_end_page + 1

        for page_num in reversed(range(content_start, len(pdf_doc))):
            page = pdf_doc[page_num]
            page_text = page.get_text("text")
            page_normalized = re.sub(r"\s", "", page_text).lower()

            for bm_title in bookmark_titles:
                if bm_title in heading_locations:
                    continue
                bm_normalized = re.sub(r"\s", "", bm_title).lower()
                if len(bm_normalized) < 3:
                    continue
                if bm_normalized in page_normalized:
                    heading_locations[bm_title] = page_num + 1

        pdf_doc.close()
        return heading_locations

    def generate(
        self,
        title: str,
        chunks: List[dict],
        target_language: str = "sr",
        include_original: bool = False,
        author: str = "AI Sistem za učenje",
        use_skill: bool = True,
    ) -> bytes:
        """
        Generiše PDF sa bookmarks i konzistentnim stilom.

        Koristi two-pass pristup:
        1. Prvi prolaz: generiše PDF, pronalazi brojeve strana za heading-e
        2. Drugi prolaz: regeneriše PDF sa brojevima strana u TOC-u
        """
        self._report_progress(0, 100, "Priprema PDF generisanja...")

        skill_options = {}
        if use_skill:
            try:
                from app.services.skills.file_skills import get_file_skill

                prompt = get_file_skill().get_pdf_prompt()
                skill_options = self._parse_skill_prompt(prompt)
            except Exception as e:
                logger.warning(f"Could not load PDF skill: {e}")

        self._report_progress(5, 100, f"Priprema {len(chunks)} segmenata...")

        base_margin = 2.0 * cm
        top_margin = base_margin + 0.6 * cm
        bottom_margin = base_margin + 0.6 * cm

        styles = self._build_styles()

        # Apply skill options to styles
        if skill_options:
            justified = skill_options.get("justified", False)
            fs = skill_options.get("font_size", 11)

            if justified:
                for st in styles.values():
                    st.alignment = TA_JUSTIFY

            styles["body"].fontSize = fs
            styles["body"].leading = fs * 1.4
        pdf_bytes = None
        heading_pages = {}
        final_bookmarks = []

        def _make_doc(buf):
            return SimpleDocTemplate(
                buf,
                pagesize=A4,
                leftMargin=base_margin,
                rightMargin=base_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin,
                title=title,
                author=author,
            )

        def _detect_ref_body_size(chunks_list: list) -> float:
            """Detektuje referentnu veličinu body fonta iz layout_data.

            Uzima median veličine iz body chunkova koji imaju layout_data.
            Ako nema podataka, vraća 15.0 (default).
            """
            sizes = []
            for c in chunks_list:
                if c.get("heading_level", 0) != 0:
                    continue
                layout_paras = _get_layout_paragraphs(c)
                if layout_paras:
                    for p in layout_paras:
                        s = p.get("size")
                        if s and s > 0:
                            sizes.append(float(s))
            if not sizes:
                return 15.0
            sizes.sort()
            return sizes[len(sizes) // 2]

        def _build_pdf(toc_page_map, bookmarks_out, ref_body_size=15.0):
            """Gradi PDF - cover, TOC (sa opcionim page numbers), sadrzaj."""
            buf = io.BytesIO()
            doc = _make_doc(buf)
            story = []
            local_bookmarks = []

            # ── Naslovnica ────────────────────────────────────────────────────
            story.append(Spacer(1, 2 * cm))
            story.append(Paragraph(_esc_simple(title), styles["cover_title"]))
            story.append(Spacer(1, 0.5 * cm))
            story.append(
                Paragraph(f"Izvor: {target_language.upper()}", styles["cover_subtitle"])
            )
            story.append(
                Paragraph(
                    f"Generisano: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    styles["meta"],
                )
            )
            story.append(Paragraph(f"Autor: {author}", styles["meta"]))
            story.append(Spacer(1, 0.3 * cm))
            story.append(
                HRFlowable(
                    width="100%", thickness=1.5, color=colors.HexColor("#d1d5db")
                )
            )
            story.append(Spacer(1, 0.5 * cm))

            # ── Sadržaj (TOC) ─────────────────────────────────────────────────
            self._report_progress(10, 100, "Kreiranje sadržaja (TOC)...")
            story.append(Paragraph("SADRŽAJ", styles["toc_title"]))
            story.append(Spacer(1, 0.3 * cm))
            story.append(
                HRFlowable(
                    width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")
                )
            )
            story.append(Spacer(1, 0.3 * cm))

            # Deduplikacija chunkova
            translated_chunks = []
            seen_content = set()
            for c in chunks:
                if not c.get("translated_text"):
                    continue
                content = c["translated_text"].strip()
                if content not in seen_content:
                    seen_content.add(content)
                    translated_chunks.append(c)

            self._render_toc(
                story, styles, translated_chunks, local_bookmarks, toc_page_map
            )

            story.append(Spacer(1, 0.3 * cm))
            story.append(
                HRFlowable(
                    width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")
                )
            )
            story.append(PageBreak())

            # ── Glavni sadržaj ────────────────────────────────────────────────
            self._report_progress(30, 100, "Generisanje sadržaja...")

            current_h1 = None

            def emit_body(chunk_dict: dict):
                """Renderuje body tekst sa layout-aware formatiranjem.

                Ako chunk ima layout_data.paragraphs, koristi per-paragraph
                font/size/bold info. Inače, koristi default body style.
                """
                text = chunk_dict.get("translated_text", "")
                clean = _strip_marker(text)
                if not clean:
                    return

                layout_paras = _get_layout_paragraphs(chunk_dict)
                if layout_paras:
                    expected_count = len(layout_paras)
                    splits = _split_paragraphs(clean, expected_count)
                    for i, para_text in enumerate(splits):
                        info = layout_paras[min(i, len(layout_paras) - 1)]
                        para_style = self._build_layout_style(
                            info, styles["body"], ref_body_size
                        )
                        story.append(Paragraph(_esc(para_text.strip()), para_style))
                else:
                    for para in _split_paragraphs(clean):
                        story.append(Paragraph(_esc(para.strip()), styles["body"]))

            for idx, chunk in enumerate(translated_chunks):
                trans = chunk.get("translated_text", "")
                heading_level = chunk.get("heading_level", 0)
                parent_heading = chunk.get("parent_heading") or ""

                if heading_level and heading_level > 0:
                    trans_clean = _strip_marker(trans)
                    layout_paras = _get_layout_paragraphs(chunk)
                    heading_layout = layout_paras[0] if layout_paras else None

                    if heading_level == 1:
                        current_h1 = trans_clean
                        story.append(Spacer(1, 0.3 * cm))
                        h1_style = (
                            self._build_layout_style(
                                heading_layout, styles["h1"], ref_body_size
                            )
                            if heading_layout
                            else styles["h1"]
                        )
                        heading_para = Paragraph(_esc_simple(trans_clean), h1_style)
                        story.append(KeepTogether([heading_para]))
                        story.append(
                            HRFlowable(
                                width="100%",
                                thickness=0.5,
                                color=colors.HexColor("#d1d5db"),
                            )
                        )
                        story.append(Spacer(1, 0.15 * cm))

                    elif heading_level == 2:
                        if current_h1 != parent_heading and parent_heading:
                            story.append(Spacer(1, 0.2 * cm))
                            parent_style = ParagraphStyle(
                                "ParentContext",
                                fontName=_FONT_NAME,
                                fontSize=7,
                                textColor=colors.HexColor("#9ca3af"),
                                spaceBefore=0,
                                spaceAfter=1,
                            )
                            if len(parent_heading) > 60:
                                story.append(
                                    Paragraph(
                                        _esc_simple(parent_heading[:57] + "..."),
                                        parent_style,
                                    )
                                )
                            else:
                                story.append(
                                    Paragraph(_esc_simple(parent_heading), parent_style)
                                )

                        story.append(Spacer(1, 0.15 * cm))
                        h2_style = (
                            self._build_layout_style(
                                heading_layout, styles["h2"], ref_body_size
                            )
                            if heading_layout
                            else styles["h2"]
                        )
                        heading_para = Paragraph(_esc_simple(trans_clean), h2_style)
                        story.append(KeepTogether([heading_para]))
                        story.append(Spacer(1, 0.1 * cm))

                    else:
                        story.append(Spacer(1, 0.15 * cm))
                        h3_style = (
                            self._build_layout_style(
                                heading_layout, styles["h3"], ref_body_size
                            )
                            if heading_layout
                            else styles["h3"]
                        )
                        heading_para = Paragraph(_esc_simple(trans_clean), h3_style)
                        story.append(KeepTogether([heading_para]))
                        story.append(Spacer(1, 0.1 * cm))
                else:
                    emit_body(chunk)

                if idx % 500 == 0:
                    progress = 30 + int((idx / len(translated_chunks)) * 30)
                    self._report_progress(
                        progress, 100, f"Sadržaj: {idx}/{len(translated_chunks)}..."
                    )

            # ── Footer ───────────────────────────────────────────────────────
            story.append(Spacer(1, 0.8 * cm))
            story.append(
                HRFlowable(
                    width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")
                )
            )
            story.append(Spacer(1, 0.2 * cm))
            story.append(
                Paragraph(
                    f"AI Sistem za učenje  •  {len(translated_chunks)} segmenata  •  {datetime.now().strftime('%Y')}",
                    styles["footer"],
                )
            )

            # Build PDF
            doc.build(
                story,
                onFirstPage=self._page_num_canvas,
                onLaterPages=self._page_num_canvas,
            )

            bookmarks_out[:] = local_bookmarks
            return buf.getvalue()

        # Build heading page numbers from chunk data (original document pages)
        heading_pages = self._extract_heading_pages(chunks)
        if heading_pages:
            self._report_progress(
                10,
                100,
                f"Pronađeno {len(heading_pages)} heading page numbers iz chunkova",
            )

        # Detect reference body size from layout_data for font scaling
        ref_body_size = _detect_ref_body_size(chunks)
        if ref_body_size != 15.0:
            self._report_progress(
                10, 100, f"Detektovana referentna veličina fonta: {ref_body_size:.1f}pt"
            )

        # Generiši PDF sa originalnim brojevima strana u TOC-u
        pdf_bytes = _build_pdf(
            toc_page_map=heading_pages,
            bookmarks_out=final_bookmarks,
            ref_body_size=ref_body_size,
        )

        # Pronađi stvarne brojeve strana u generisanom PDF-u za bookmarks
        # (obavezno je da bookmark-ovi pokazuju na tačne strane u izvezenom PDF-u)
        export_heading_pages = {}
        if final_bookmarks:
            self._report_progress(55, 100, "Lociranje headinga u generisanom PDF-u...")
            export_heading_pages = self._find_heading_pages(pdf_bytes, final_bookmarks)

        # Dodaj bookmarks koristeći PyMuPDF
        if final_bookmarks:
            try:
                import fitz

                pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

                toc = []
                for bm in final_bookmarks:
                    if isinstance(bm, dict):
                        title = bm.get("title", "")
                        level = bm.get("level", 0)
                    else:
                        title, level = bm

                    if title:
                        # Priority: export page number > original page number > 1
                        page_num = export_heading_pages.get(title)
                        if not page_num:
                            page_num = heading_pages.get(title, 1)
                        toc.append((level + 1, title[:80], page_num))

                if toc:
                    toc.sort(key=lambda x: (x[2], x[0]))

                    valid_toc = []
                    prev_page = 0
                    prev_level = 0
                    for item in toc:
                        level, title, page = item
                        if page < prev_page:
                            page = prev_page
                        if level > prev_level + 1:
                            level = prev_level + 1
                        if level < 1:
                            level = 1
                        valid_toc.append((level, title, page))
                        prev_page = page
                        prev_level = level

                    pdf_doc.set_toc(valid_toc)
                    self._report_progress(
                        90, 100, f"Dodato {len(valid_toc)} bookmarks..."
                    )
                    logger.info(f"Dodato {len(valid_toc)} bookmarks u PDF")
                else:
                    logger.warning("Nije moguce pronaci lokacije bookmarks")

                pdf_bytes = pdf_doc.tobytes()
                pdf_doc.close()
                self._report_progress(95, 100, "Finalizacija PDF-a...")

            except Exception as e:
                logger.warning(f"Could not add bookmarks: {e}")
                import traceback

                logger.warning(traceback.format_exc())

        self._report_progress(100, 100, "PDF generisanje završeno!")
        return pdf_bytes

    def _add_bookmarks_with_pymupdf(self, doc, bookmarks: list):
        """Dodaje bookmarks u PDF koristeći PyMuPDF."""
        try:
            logger.info(f"Starting bookmarks: {len(bookmarks)} entries")

            # bookmarks je lista dict-ova sa 'title' i 'level' kljucevima
            toc = []
            for bm in bookmarks:
                if isinstance(bm, dict):
                    title = str(bm.get("title", ""))
                    level = bm.get("level", 0)
                else:
                    title = str(bm[0]) if bm else ""
                    level = int(bm[1]) if bm and len(bm) > 1 else 0

                if title:
                    toc.append((level + 1, title[:80], 0))  # PyMuPDF level starts at 1

            if toc:
                doc.set_toc(toc)
                logger.info(f"Dodato {len(toc)} bookmarks u PDF")

        except Exception as e:
            logger.error(f"Error adding bookmarks with PyMuPDF: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _page_num_canvas(self, canvas, doc):
        """Canvas callback za header i page numbers."""
        page_num = canvas.getPageNumber()

        # Header
        canvas.setFont(_FONT_NAME, 8)
        canvas.setFillColor(colors.HexColor("#374151"))
        header_text = doc.title[:60] + ("..." if len(doc.title) > 60 else "")
        canvas.drawRightString(
            doc.width + doc.leftMargin - 20,
            doc.height + doc.topMargin - 15,
            header_text,
        )

        # Line under header
        canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
        canvas.line(
            doc.leftMargin,
            doc.height + doc.topMargin - 20,
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin - 20,
        )

        # Page number
        canvas.setFont(_FONT_NAME, 9)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        text = f"Strana {page_num}"
        canvas.drawCentredString(doc.width / 2, 20, text)


# Singleton
pdf_export_service = PDFExportService()
