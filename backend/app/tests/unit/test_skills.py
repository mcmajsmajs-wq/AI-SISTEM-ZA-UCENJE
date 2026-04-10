# -*- coding: utf-8 -*-
"""
===============================================================================
SKILLS TESTS
===============================================================================
Unit testovi za Skill sistem - FAZA 6.

Pokretanje:
    pytest app/tests/unit/test_skills.py -v
===============================================================================
"""

import pytest
from app.services.skills import (
    SkillDetector,
    SkillService,
    detect_document_type,
    detect_from_file,
    get_all_templates,
    get_template,
    get_template_by_category,
    get_template_names,
    get_categories,
    SYSTEM_SKILL_TEMPLATES,
    DOCUMENT_TYPE_KEYWORDS,
)


class TestSkillDetector:
    """Testovi za SkillDetector."""

    def test_detector_init(self):
        """Test inicijalizacije detectora."""
        detector = SkillDetector()
        assert detector is not None
        assert detector.confidence_threshold == 50

    def test_detector_init_custom_threshold(self):
        """Test inicijalizacije sa custom threshold."""
        detector = SkillDetector(confidence_threshold=30)
        assert detector.confidence_threshold == 30

    def test_detect_legal_document(self):
        """Test detekcije pravnog dokumenta."""
        detector = SkillDetector()
        text = """This agreement establishes the terms and conditions between the parties.
        Section 1 defines the obligations of each party. Section 2 establishes the liability and damages.
        The termination clause specifies the deadline for notice. All clauses are subject to governing law."""

        result = detector.analyze_text(text)
        assert result["category"] == "legal"
        assert result["confidence"] > 0

    def test_detect_technical_document(self):
        """Test detekcije tehničkog dokumenta."""
        detector = SkillDetector()
        text = """This API documentation describes the installation and configuration parameters.
        The error codes are listed below. Follow the setup guide for troubleshooting.
        Configuration requires specific parameters."""

        result = detector.analyze_text(text)
        assert result["category"] == "technical"
        assert result["confidence"] > 0

    def test_detect_medical_document(self):
        """Test detekcije medicinskog dokumenta."""
        detector = SkillDetector()
        text = """The patient presents with symptoms of fever and cough. Treatment includes
        medication and therapy. Clinical diagnosis indicates the condition. The medication
        has contraindications and side effects."""

        result = detector.analyze_text(text)
        assert result["category"] == "medical"
        assert result["confidence"] > 0

    def test_detect_academic_document(self):
        """Test detekcije akademskog rada."""
        detector = SkillDetector()
        text = """This research paper presents methodology and findings. Statistical analysis
        shows significant results. The sample size was 100 participants. The hypothesis
        is supported by the data."""

        result = detector.analyze_text(text)
        assert result["category"] == "academic"
        assert result["confidence"] > 0

    def test_detect_textbook(self):
        """Test detekcije udžbenika."""
        detector = SkillDetector()
        text = """Chapter 1 introduces key concepts and definitions. This chapter summary
        covers important formulas. The exercise at the end tests understanding.
        Learning objectives are listed in each section."""

        result = detector.analyze_text(text)
        assert result["category"] == "textbook"
        assert result["confidence"] > 0

    def test_detect_general_document(self):
        """Test detekcije opšteg dokumenta."""
        detector = SkillDetector()
        text = """This document provides an overview of the topic. In conclusion,
        the background information is summarized. This is an introduction to the subject."""

        result = detector.analyze_text(text)
        assert result["category"] in ["general", "textbook"]
        assert result["confidence"] >= 0

    def test_detect_empty_text(self):
        """Test detekcije praznog teksta."""
        detector = SkillDetector()
        result = detector.analyze_text("")
        assert result["category"] == "general"
        assert result["confidence"] == 0

    def test_detect_from_chunks(self):
        """Test detekcije iz više chunks-a."""
        detector = SkillDetector()
        chunks = [
            "This contract agreement specifies the terms.",
            "Section 1 defines obligations. Section 2 covers liability.",
            "The termination clause mentions deadlines.",
        ]

        result = detector.detect_from_chunks(chunks)
        assert "chunks_analyzed" in result
        assert result["chunks_analyzed"] == 3

    def test_detect_from_title(self):
        """Test detekcije iz naslova."""
        detector = SkillDetector()
        result = detector.detect_from_title("Contract Agreement Terms and Conditions")
        assert result["source"] == "title"

    def test_get_available_categories(self):
        """Test dostupnih kategorija."""
        detector = SkillDetector()
        categories = detector.get_available_categories()
        assert len(categories) == 6
        assert "legal" in categories
        assert "technical" in categories
        assert "medical" in categories

    def test_keyword_matching(self):
        """Test keyword matching."""
        detector = SkillDetector()
        text = "This is a contract between two parties with obligations"
        result = detector.analyze_text(text)
        assert "legal" in result["matched_keywords"]
        assert len(result["matched_keywords"]["legal"]) > 0


class TestSkillService:
    """Testovi za SkillService."""

    def test_service_init(self):
        """Test inicijalizacije servisa."""
        service = SkillService()
        assert service is not None

    def test_detect_and_get_template(self):
        """Test detekcije i dobijanja template-a."""
        service = SkillService()
        result = service.detect_and_get_template(
            "This agreement establishes the terms and conditions."
        )

        assert "template" in result
        assert "category" in result
        assert "confidence" in result

    def test_get_system_template(self):
        """Test dobijanja sistemskog template-a."""
        service = SkillService()
        template = service.get_system_template("legal_document")
        assert template is not None
        assert template["category"] == "legal"

    def test_get_all_templates(self):
        """Test dobijanja svih template-a."""
        service = SkillService()
        templates = service.get_all_templates()
        assert len(templates) == 6

    def test_get_template_names(self):
        """Test imena template-a."""
        service = SkillService()
        names = service.get_template_names()
        assert "legal_document" in names
        assert "technical_manual" in names

    def test_get_categories(self):
        """Test kategorija."""
        service = SkillService()
        categories = service.get_categories()
        assert len(categories) == 6
        assert "legal" in categories

    def test_detect_category(self):
        """Test detekcije kategorije."""
        service = SkillService()
        category = service.detect_category(
            "This contract agreement specifies the terms."
        )
        assert category == "legal"

    def test_get_detection_details(self):
        """Test detalja detekcije."""
        service = SkillService()
        details = service.get_detection_details(
            "Medical symptoms and treatment protocols."
        )
        assert "scores" in details
        assert "matched_keywords" in details

    def test_get_prompt_for_document(self):
        """Test dobijanja prompt-a za dokument."""
        service = SkillService()
        prompt = service.get_prompt_for_document(
            "Technical API documentation and setup."
        )
        assert prompt is not None
        assert len(prompt) > 0

    def test_get_rules_for_document(self):
        """Test dobijanja pravila za dokument."""
        service = SkillService()
        rules = service.get_rules_for_document(
            "Legal contract with clauses and obligations."
        )
        assert "difficulty" in rules
        assert "question_types" in rules


class TestHelperFunctions:
    """Testovi za helper funkcije."""

    def test_detect_document_type(self):
        """Test helper funkcije za detekciju."""
        category = detect_document_type("Medical diagnosis and patient treatment.")
        assert category in ["medical", "general"]

    def test_detect_from_file(self):
        """Test detekcije iz fajla."""
        result = detect_from_file(
            "contract.pdf", "This agreement establishes the terms."
        )
        assert "category" in result
        assert "confidence" in result


class TestTemplates:
    """Testovi za template sisteme."""

    def test_system_skill_templates_exist(self):
        """Test da sistemski template-i postoje."""
        assert len(SYSTEM_SKILL_TEMPLATES) == 6
        assert "legal_document" in SYSTEM_SKILL_TEMPLATES
        assert "technical_manual" in SYSTEM_SKILL_TEMPLATES

    def test_document_type_keywords_exist(self):
        """Test da keywords za tipove dokumenata postoje."""
        assert len(DOCUMENT_TYPE_KEYWORDS) == 6
        assert "legal" in DOCUMENT_TYPE_KEYWORDS
        assert "technical" in DOCUMENT_TYPE_KEYWORDS

    def test_get_template_function(self):
        """Test get_template funkcije."""
        template = get_template("legal_document")
        assert template is not None
        assert template["name"] == "Legal Document Processor"

    def test_get_template_by_category_function(self):
        """Test get_template_by_category funkcije."""
        template = get_template_by_category("legal")
        assert template is not None

    def test_get_all_templates_function(self):
        """Test get_all_templates funkcije."""
        templates = get_all_templates()
        assert len(templates) == 6

    def test_get_template_names_function(self):
        """Test get_template_names funkcije."""
        names = get_template_names()
        assert "legal_document" in names
        assert len(names) == 6

    def test_get_categories_function(self):
        """Test get_categories funkcije."""
        categories = get_categories()
        assert len(categories) == 6
        assert "legal" in categories
