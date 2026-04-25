# -*- coding: utf-8 -*-
"""
===============================================================================
PDF GENERATOR SERVICE
===============================================================================
Servis za generisanje PDF dokumenata iz prevedenih tekstova i materijala.

Verzija: 1.0.0
===============================================================================
"""

import io
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, HRFlowable, Image as RLImage
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available. PDF generation disabled.")


@dataclass
class DocumentMetadata:
    """Metadata za PDF dokument."""
    title: str
    author: str = "AI Learning System"
    subject: str = ""
    creator: str = "AI Learning System PDF Generator"
    keywords: str = ""


@dataclass
class QuizQuestionPDF:
    """Pitanje za PDF export."""
    question_number: int
    question_text: str
    question_type: str
    options: List[str] = None
    correct_answer: str = None
    explanation: str = None
    points: int = 1


class PDFGeneratorService:
    """
    ================================================================================
    PDF GENERATOR SERVICE
    ================================================================================
    Servis za generisanje PDF dokumenata u različitim formatima.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Postavlja prilagođene stilove za PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            spaceBefore=20,
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            spaceBefore=15,
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyTextJustified',
            parent=self.styles['BodyText'],
            alignment=TA_JUSTIFY,
            spaceAfter=12,
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuizQuestion',
            parent=self.styles['BodyText'],
            fontSize=12,
            spaceAfter=8,
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuizOption',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=4,
            leftIndent=20,
        ))
    
    def _create_header(self, title: str) -> List:
        """Kreira header za PDF."""
        elements = []
        
        elements.append(Paragraph("AI Learning System", self.styles['CustomHeading2']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", color=colors.HexColor('#1e40af'), thickness=2))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_footer(self, canvas, doc):
        """Kreira footer za PDF."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        
        page_num = canvas.getPageNumber()
        text = f"Strana {page_num} | Generisano: {datetime.now().strftime('%d.%m.%Y.')}"
        canvas.drawRightString(doc.pagesize[0] - 20, 20, text)
        
        canvas.restoreState()
    
    def generate_document_pdf(
        self,
        title: str,
        chunks: List[Dict[str, Any]],
        show_original: bool = True,
        show_translated: bool = True,
        include_metadata: bool = True,
    ) -> bytes:
        """
        Generiše PDF od dokumenta sa chunk-ovima.
        
        Args:
            title: Naslov dokumenta
            chunks: Lista chunk-ova (original + translated)
            show_original: Prikazi originalni tekst
            show_translated: Prikazi prevedeni tekst
            include_metadata: Ukljuci metadata
        
        Returns:
            PDF kao bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not installed. Run: pip install reportlab")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        if include_metadata:
            story.extend(self._create_header(title))
        
        for i, chunk in enumerate(chunks):
            if chunk.get('heading'):
                story.append(Paragraph(chunk['heading'], self.styles['CustomHeading1']))
            
            if chunk.get('page_number'):
                story.append(Paragraph(
                    f"<i>Strana {chunk['page_number']}</i>",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 10))
            
            if show_original and chunk.get('original_text'):
                story.append(Paragraph("<b>Original:</b>", self.styles['CustomHeading2']))
                story.append(Paragraph(chunk['original_text'], self.styles['BodyTextJustified']))
                story.append(Spacer(1, 10))
            
            if show_translated and chunk.get('translated_text'):
                story.append(Paragraph("<b>Prevod:</b>", self.styles['CustomHeading2']))
                story.append(Paragraph(chunk['translated_text'], self.styles['BodyTextJustified']))
                story.append(Spacer(1, 20))
            
            if i < len(chunks) - 1:
                story.append(HRFlowable(width="30%", color=colors.lightgrey, thickness=1))
                story.append(Spacer(1, 15))
        
        if include_metadata:
            story.append(PageBreak())
            story.append(Paragraph("Informacije o dokumentu", self.styles['CustomHeading1']))
            story.append(Spacer(1, 15))
            
            info_data = [
                ["Naslov:", title],
                ["Broj segmenata:", str(len(chunks))],
                ["Datum generisanja:", datetime.now().strftime('%d.%m.%Y. %H:%M')],
                ["AI Learning System", "https://ai-learning.com"],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(info_table)
        
        doc.build(story, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return buffer.getvalue()
    
    def generate_quiz_pdf(
        self,
        title: str,
        questions: List[QuizQuestionPDF],
        include_answers: bool = False,
        include_explanations: bool = True,
        time_limit: int = None,
        passing_score: int = None,
    ) -> bytes:
        """
        Generiše PDF od kviza sa pitanjima.
        
        Args:
            title: Naslov kviza
            questions: Lista pitanja
            include_answers: Ukljuci odgovore
            include_explanations: Ukljuci objasnjenja
            time_limit: Vremensko ogranicenje (minuti)
            passing_score: Prolazni rezultat (%)
        
        Returns:
            PDF kao bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not installed. Run: pip install reportlab")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        story.extend(self._create_header(title))
        
        if time_limit or passing_score:
            info_parts = []
            if time_limit:
                info_parts.append(f"Vreme: {time_limit} min")
            if passing_score:
                info_parts.append(f"Prolaz: {passing_score}%")
            
            story.append(Paragraph(" | ".join(info_parts), self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        story.append(Paragraph(
            f"<b>Ukupno pitanja: {len(questions)}</b>",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 30))
        
        for q in questions:
            story.append(Paragraph(
                f"<b>{q.question_number}.</b> {q.question_text}",
                self.styles['QuizQuestion']
            ))
            
            if q.options:
                for j, option in enumerate(q.options):
                    option_label = chr(65 + j)
                    story.append(Paragraph(
                        f"{option_label}) {option}",
                        self.styles['QuizOption']
                    ))
            
            story.append(Spacer(1, 15))
            
            if include_answers and q.correct_answer:
                story.append(Paragraph(
                    f"<b>Odgovor:</b> {q.correct_answer}",
                    self.styles['Normal']
                ))
            
            if include_explanations and q.explanation:
                story.append(Paragraph(
                    f"<i>Objašnjenje: {q.explanation}</i>",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 10))
            
            story.append(HRFlowable(width="30%", color=colors.lightgrey, thickness=1))
            story.append(Spacer(1, 15))
        
        if include_answers:
            story.append(PageBreak())
            story.append(Paragraph("Odgovori", self.styles['CustomHeading1']))
            story.append(Spacer(1, 20))
            
            answers_data = []
            for q in questions:
                answers_data.append([
                    str(q.question_number),
                    q.correct_answer or "N/A",
                    f"{q.points} poen"
                ])
            
            answers_table = Table(
                answers_data,
                colWidths=[1*inch, 3*inch, 1*inch]
            )
            answers_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(answers_table)
        
        doc.build(story, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return buffer.getvalue()
    
    def generate_study_guide_pdf(
        self,
        title: str,
        document_title: str,
        chunks: List[Dict[str, Any]],
        include_quiz_questions: bool = True,
    ) -> bytes:
        """
        Generiše PDF studijskog vodiča.
        
        Args:
            title: Naslov vodiča
            document_title: Naslov dokumenta
            chunks: Lista chunk-ova
            include_quiz_questions: Ukljuci pitanja za proveru znanja
        
        Returns:
            PDF kao bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not installed. Run: pip install reportlab")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        story.extend(self._create_header(f"Studijski vodič: {title}"))
        
        story.append(Paragraph(
            f"<i>Na osnovu dokumenta: {document_title}</i>",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 30))
        
        story.append(Paragraph("Ključni koncepti", self.styles['CustomHeading1']))
        story.append(Spacer(1, 15))
        
        for chunk in chunks:
            if chunk.get('heading'):
                story.append(Paragraph(chunk['heading'], self.styles['CustomHeading2']))
            
            if chunk.get('translated_text'):
                story.append(Paragraph(chunk['translated_text'], self.styles['BodyTextJustified']))
                story.append(Spacer(1, 15))
        
        story.append(PageBreak())
        story.append(Paragraph("Pitanja za proveru znanja", self.styles['CustomHeading1']))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph(
            "Odgovorite na sledeća pitanja da biste proverili razumevanje materijala:",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        study_questions = [
            "Koji su glavni koncepti opisani u ovom materijalu?",
            "Objasnite ključne ideje svojim rečima.",
            "Kako se ovi koncepti mogu primeniti u praksi?",
            "Koje veze postoje između različitih delova materijala?",
        ]
        
        for i, q in enumerate(study_questions, 1):
            story.append(Paragraph(f"{i}. {q}", self.styles['QuizQuestion']))
            story.append(Spacer(1, 10))
        
        story.append(PageBreak())
        story.append(Paragraph("Notes", self.styles['CustomHeading1']))
        story.append(Spacer(1, 15))
        
        for _ in range(10):
            story.append(Spacer(1, 30))
            story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=1))
        
        doc.build(story, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return buffer.getvalue()


pdf_generator_service = PDFGeneratorService()
