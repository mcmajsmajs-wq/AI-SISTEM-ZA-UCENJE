# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
PDF Export Service
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026
================================================================================
"""
import io
import logging
from datetime import datetime
from typing import Optional, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

# Pokušaj registracije UTF-8 fonta (DejaVu); fallback na Helvetica
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

class PDFExportService:
    """PDF Export Service - Generisanje PDF fajla od prevedenih chunkova."""
    
    def _build_styles(self):
        styles = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "DocTitle",
                fontName=_FONT_BOLD,
                fontSize=22,
                leading=28,
                spaceAfter=6,
                textColor=colors.HexColor("#1e1b4b"),
                alignment=TA_CENTER,
            ),
            "subtitle": ParagraphStyle(
                "DocSubtitle",
                fontName=_FONT_NAME,
                fontSize=11,
                leading=14,
                spaceAfter=4,
                textColor=colors.HexColor("#6366f1"),
                alignment=TA_CENTER,
            ),
            "meta": ParagraphStyle(
                "DocMeta",
                fontName=_FONT_NAME,
                fontSize=9,
                textColor=colors.HexColor("#9ca3af"),
                alignment=TA_CENTER,
                spaceAfter=20,
            ),
            "section_label": ParagraphStyle(
                "SectionLabel",
                fontName=_FONT_BOLD,
                fontSize=7,
                textColor=colors.HexColor("#6366f1"),
                spaceAfter=2,
                spaceBefore=12,
                leading=10,
            ),
            "original": ParagraphStyle(
                "Original",
                fontName=_FONT_NAME,
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#6b7280"),
                spaceAfter=3,
                leftIndent=0,
            ),
            "translated": ParagraphStyle(
                "Translated",
                fontName=_FONT_NAME,
                fontSize=11,
                leading=16,
                textColor=colors.HexColor("#111827"),
                spaceAfter=6,
                alignment=TA_JUSTIFY,
            ),
            "footer": ParagraphStyle(
                "Footer",
                fontName=_FONT_NAME,
                fontSize=8,
                textColor=colors.HexColor("#d1d5db"),
                alignment=TA_CENTER,
            ),
        }

    def generate(
        self,
        title: str,
        chunks: List[dict],
        target_language: str = "sr",
        include_original: bool = True,
        author: str = "AI Sistem za učenje",
    ) -> bytes:
        """
        Generiše PDF i vraća bytes.

        Args:
            title: Naziv dokumenta
            chunks: Lista dict-ova sa 'original_text' i 'translated_text'
            target_language: Jezik prevoda (za metadata)
            include_original: Da li uključiti originalni tekst iznad prevoda
            author: Autor (korisničko ime)

        Returns:
            PDF kao bytes
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=2.5 * cm,
            rightMargin=2.5 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
            title=title,
            author=author,
        )

        styles = self._build_styles()
        story = []

        # ── Naslovnica ───────────────────────────────────────────────────────
        story.append(Spacer(1, 1.5 * cm))
        story.append(Paragraph(_esc(title), styles["title"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"Prevod: {target_language.upper()}", styles["subtitle"]))
        story.append(Paragraph(
            f"Generisano: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  {author}",
            styles["meta"]
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
        story.append(Spacer(1, 0.5 * cm))

        # ── Sadržaj (chunkovi) ───────────────────────────────────────────────
        translated_chunks = [c for c in chunks if c.get("translated_text")]
        if not translated_chunks:
            story.append(Paragraph("Nema prevedenog sadržaja.", styles["translated"]))
        else:
            for i, chunk in enumerate(translated_chunks, 1):
                orig = chunk.get("original_text", "")
                trans = chunk.get("translated_text", "")

                if include_original and orig:
                    story.append(Paragraph(f"ORIGINAL [{i}]", styles["section_label"]))
                    story.append(Paragraph(_esc(orig[:600] + ("..." if len(orig) > 600 else "")), styles["original"]))
                    story.append(Paragraph(f"PREVOD", styles["section_label"]))

                story.append(Paragraph(_esc(trans), styles["translated"]))
                story.append(Spacer(1, 0.2 * cm))

                # Razmak na svakih 20 chunkova radi preglednosti
                if i % 20 == 0:
                    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#f3f4f6")))
                    story.append(Spacer(1, 0.3 * cm))

        # ── Footer ───────────────────────────────────────────────────────────
        story.append(Spacer(1, 1 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"AI Sistem za učenje  •  {len(translated_chunks)} segmenata  •  {datetime.now().strftime('%Y')}",
            styles["footer"]
        ))

        doc.build(story)
        return buf.getvalue()

def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )

# Singleton
pdf_export_service = PDFExportService()
