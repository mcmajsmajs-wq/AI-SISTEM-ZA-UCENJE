# -*- coding: utf-8 -*-
"""
================================================================================
DOCX Export Service
================================================================================
Kreira Word dokument od prevedenih chunk-ova.

Verzija: 1.0.0
================================================================================
"""

import io
import logging
from typing import List, Dict, Any

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

logger = logging.getLogger(__name__)


class DOCXExportService:
    """Service za export dokumenta u DOCX format."""

    def generate(
        self,
        title: str,
        chunks: List[Dict[str, Any]],
        include_original: bool = False,
    ) -> bytes:
        """
        Generiše DOCX dokument od chunk-ova.

        Args:
            title: Naslov dokumenta
            chunks: Lista chunk-ova (dictionaries)
            include_original: Da li uključuje originalni tekst

        Returns:
            DOCX bytes
        """
        doc = Document()

        # Title
        title_paragraph = doc.add_heading(title, level=0)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Uvodni tekst
        doc.add_paragraph(f"Broj sekcija: {len(chunks)}", style="Intense Quote")
        doc.add_paragraph()

        # Stilovi za heading
        heading_styles = [
            "Heading 1",
            "Heading 2",
            "Heading 3",
        ]

        # Dodaj chunks
        for idx, chunk in enumerate(chunks):
            # Odredi nivo headinga na osnovu heading_level
            heading_level = chunk.get("heading_level", 1)
            if heading_level > 3:
                heading_level = 3

            # Naslov sekcije (heading)
            heading_style = (
                heading_styles[heading_level - 1] if heading_level <= 3 else "Heading 1"
            )

            # Koristi parent_heading kao naslov ako postoji
            if chunk.get("parent_heading"):
                doc.add_heading(chunk.get("parent_heading"), level=2)

            # Tekst (translated ili original)
            if chunk.get("translated_content"):
                content = chunk["translated_content"]
            elif chunk.get("content"):
                content = chunk["content"]
            else:
                content = ""

            if content:
                # Dodaj kao paragraph sa styling
                para = doc.add_paragraph(content)

                # Font settings
                for run in para.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)

            # Ako treba original
            if include_original and chunk.get("content"):
                doc.add_paragraph(
                    f"Original: {chunk['content'][:200]}...", style="Quote"
                )

            # Page break nakon svakog chunk-a (opciono)
            # doc.add_page_break()

        # Dodaj footer sa metadata
        doc.add_paragraph()
        footer = doc.add_paragraph("---")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"Generisano: AI Learning System", style="Intense Quote")

        # Sačuvaj u bytes
        docx_bytes = io.BytesIO()
        doc.save(docx_bytes)
        docx_bytes.seek(0)

        return docx_bytes.getvalue()


docx_export_service = DOCXExportService()
