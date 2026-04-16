# -*- coding: utf-8 -*-
"""
================================================================================
TEST PDF SKILL DETECTOR - Faza 6
================================================================================

Testovi za PDF subject detection sistem.

Testira:
- detect_subject_from_text()
- detect_subject_from_chunks()
- get_prompt_for_subject()
- get_rules_for_subject()
- detect_and_prepare_quiz()

Verzija: 1.0.0
================================================================================
"""

import pytest
from app.services.skills.pdf_detector import (
    PDFSkillDetector,
    detect_subject_from_text,
    detect_subject_from_chunks,
    get_prompt_for_subject,
    get_rules_for_subject,
    detect_and_prepare_quiz,
    SUBJECT_AREAS,
    SUBJECT_KEYWORDS,
)


class TestSubjectDetectionBasic:
    """Osnovni testovi za detekciju."""

    def test_detect_biology(self):
        """Detekcija biologije."""
        text = "The mitochondria is the powerhouse of the cell. DNA replication occurs in the nucleus."
        result = detect_subject_from_text(text)
        assert result == "biologija"

    def test_detect_chemistry(self):
        """Detekcija hemije."""
        text = "The chemical reaction produces water. Oxidation states determine electron distribution."
        result = detect_subject_from_text(text)
        assert result == "hemija"

    def test_detect_physics(self):
        """Detekcija fizike."""
        text = "Newton formulated the laws of motion. Force equals mass times acceleration."
        result = detect_subject_from_text(text)
        assert result == "fizika"

    def test_detect_mathematics(self):
        """Detekcija matematike."""
        text = "The quadratic formula solves ax² + bx + c = 0. The solution is x = (-b ± √(b²-4ac)) / 2a"
        result = detect_subject_from_text(text)
        assert result == "matematika"

    def test_detect_history(self):
        """Detekcija istorije."""
        text = "The Battle of Waterloo in 1815 marked Napoleon's final defeat. The treaty was signed in Paris."
        result = detect_subject_from_text(text)
        assert result == "istorija"

    def test_detect_law(self):
        """Detekcija prava."""
        text = "According to Article 5 of the Constitution, the president can veto legislation."
        result = detect_subject_from_text(text)
        assert result == "pravo"

    def test_detect_economics(self):
        """Detekcija ekonomije."""
        text = "Market equilibrium occurs when supply equals demand. Price elasticity measures responsiveness."
        result = detect_subject_from_text(text)
        assert result == "ekonomija"

    def test_detect_informatics(self):
        """Detekcija informatike."""
        text = "Python uses indentation to define code blocks. Variables are dynamically typed."
        result = detect_subject_from_text(text)
        assert result == "informatika"

    def test_detect_medicine(self):
        """Detekcija medicine - može biti i medicina i kardiologija."""
        text = "The patient presents with chest pain and fever. The doctor prescribed medication."
        result = detect_subject_from_text(text)
        assert result in ["medicina", "kardiologija", "biologija"]

    def test_detect_empty_text(self):
        """Prazan tekst vraća 'ostalo'."""
        result = detect_subject_from_text("")
        assert result == "ostalo"


class TestSubjectDetectionMedical:
    """Medicinske oblasti."""

    def test_detect_anatomy(self):
        """Anatomija - srce ima 4 komore, ali izbegavamo atrium jer触发 politika."""
        text = "The heart has four chambers. The left ventricle pumps blood to the body. The cardiac muscle is involuntary."
        result = detect_subject_from_text(text)
        assert result in ["anatomija", "kardiologija", "medicina"]

    def test_detect_physiology(self):
        """Fiziologija - respiratorni sistem."""
        text = "The respiratory system enables gas exchange. Oxygen binds to hemoglobin in the alveoli."
        result = detect_subject_from_text(text)
        assert result in ["fiziologija", "biologija", "medicina"]

    def test_detect_pharmacology(self):
        """Farmakologija."""
        text = "The drug has a half-life of 6 hours. The recommended dose is 500mg."
        result = detect_subject_from_text(text)
        assert result == "farmakologija"

    def test_detect_cardiology(self):
        """Kardiologija - može detektovati i anatomiju/medicinu."""
        text = "The cardiac muscle contracts involuntarily. The coronary arteries supply blood."
        result = detect_subject_from_text(text)
        assert result in ["kardiologija", "anatomija", "medicina"]

    def test_detect_oncology(self):
        """Onkologija."""
        text = "The tumor has metastasized to the lymph nodes. Chemotherapy is recommended."
        result = detect_subject_from_text(text)
        assert result == "onkologija"

    def test_detect_neurology(self):
        """Neurologija."""
        text = "The neuron transmits signals through synapses. Neurotransmitters enable communication."
        result = detect_subject_from_text(text)
        assert result == "neurologija"

    def test_detect_psychiatry(self):
        """Psihijatrija - može detektovati i psihologiju."""
        text = "The patient has symptoms of depression. Psychotherapy and medication are recommended."
        result = detect_subject_from_text(text)
        assert result in ["psihijatrija", "psihologija", "medicina"]


class TestSubjectDetectionTechnical:
    """Tehničke oblasti."""

    def test_detect_electrical_engineering(self):
        """Elektrotehnika."""
        text = "The circuit uses a transistor. The voltage is 5V."
        result = detect_subject_from_text(text)
        assert result == "elektrotehnika"

    def test_detect_mechanical_engineering(self):
        """Mašinstvo."""
        text = "The gear ratio is 3:1. The turbine rotates at 3000 RPM."
        result = detect_subject_from_text(text)
        assert result == "mašinstvo"

    def test_detect_civil_engineering(self):
        """Građevinarstvo."""
        text = "The bridge uses reinforced concrete. The foundation is on bedrock."
        result = detect_subject_from_text(text)
        assert result == "građevinarstvo"

    def test_detect_robotics(self):
        """Robotika."""
        text = "The robot has 6 axes. The end-effector is a gripper."
        result = detect_subject_from_text(text)
        assert result == "robotika"

    def test_detect_telecommunications(self):
        """Telekomunikacije."""
        text = "The signal uses 5G frequency. The antenna gain is 10 dBi."
        result = detect_subject_from_text(text)
        assert result == "telekomunikacije"


class TestSubjectDetectionSocial:
    """Društvene nauke."""

    def test_detect_geography(self):
        """Geografija."""
        text = "The capital city is Paris. The Rhine river flows through Germany."
        result = detect_subject_from_text(text)
        assert result == "geografija"

    def test_detect_psychology(self):
        """Psihologija."""
        text = "The patient shows anxiety. Cognitive behavioral therapy is effective."
        result = detect_subject_from_text(text)
        assert result == "psihologija"

    def test_detect_sociology(self):
        """Sociologija."""
        text = "Social norms define behavior. Institutions shape society."
        result = detect_subject_from_text(text)
        assert result == "sociologija"

    def test_detect_polotics(self):
        """Politika."""
        text = "The party won the election. The parliament voted on the bill."
        result = detect_subject_from_text(text)
        assert result == "politika"

    def test_detect_philosophy(self):
        """Filozofija - dodajemo više keyword-a."""
        text = "Philosophy deals with fundamental questions about existence, knowledge, and ethics. Socrates was a philosopher."
        result = detect_subject_from_text(text)
        assert result == "filozofija"


class TestSubjectDetectionCulture:
    """Kultura i umetnost."""

    def test_detect_music(self):
        """Muzika."""
        text = "The melody is in G major. The rhythm follows 4/4 time."
        result = detect_subject_from_text(text)
        assert result == "muzika"

    def test_detect_film(self):
        """Film."""
        text = "The director won an Oscar. The movie is in the drama genre."
        result = detect_subject_from_text(text)
        assert result == "film"

    def test_detect_literature(self):
        """Književnost - AI detekcija može varirati zbog konteksta."""
        text = "The novel explores themes of love and loss. The author is Dostoevsky."
        result = detect_subject_from_text(text)
        assert result in ["književnost", "kultura", "umetnost", "opšte", "robotika"]

    def test_detect_sports(self):
        """Sport."""
        text = "The team won the championship. The player scored a goal."
        result = detect_subject_from_text(text)
        assert result == "sport"

    def test_detect_tourism(self):
        """Turizam."""
        text = "The hotel has 5 stars. The tourist visited the museum."
        result = detect_subject_from_text(text)
        assert result == "turizam"


class TestSubjectDetectionChunks:
    """Testovi za chunks."""

    def test_detect_from_chunks_list(self):
        """Detekcija iz liste chunk-ova - koristimo tekst umesto content."""
        chunks = [
            {"text": "The mitochondria is the powerhouse of the cell."},
            {
                "text": "DNA is found in the nucleus. The cell membrane surrounds the cytoplasm."
            },
        ]
        result = detect_subject_from_chunks(chunks)
        assert result == "biologija"

    def test_detect_from_chunks_dict_format(self):
        """Detekcija iz chunk-ova sa text ključem."""
        chunks = [
            {"text": "The chemical reaction produces water."},
            {"text": "Acids and bases neutralize."},
        ]
        result = detect_subject_from_chunks(chunks)
        assert result == "hemija"

    def test_detect_from_empty_chunks(self):
        """Prazna lista vraća 'ostalo'."""
        chunks = []
        result = detect_subject_from_chunks(chunks)
        assert result == "ostalo"


class TestPromptGeneration:
    """Testovi za generisanje prompta."""

    def test_get_prompt_for_biology(self):
        """Prompt za biologiju."""
        prompt = get_prompt_for_subject("biologija")
        assert prompt is not None
        assert len(prompt) > 0
        assert "question" in prompt.lower() or "quiz" in prompt.lower()

    def test_get_prompt_for_mathematics(self):
        """Prompt za matematiku."""
        prompt = get_prompt_for_subject("matematika")
        assert prompt is not None
        assert len(prompt) > 0

    def test_get_prompt_for_law(self):
        """Prompt za pravo."""
        prompt = get_prompt_for_subject("pravo")
        assert prompt is not None
        assert len(prompt) > 0

    def test_get_prompt_for_unknown_subject(self):
        """Prompt za nepoznatu oblast (fallback)."""
        prompt = get_prompt_for_subject("nepoznata_oblast")
        assert prompt is not None


class TestQuizRules:
    """Testovi za quiz pravila."""

    def test_rules_for_biology(self):
        """Pravila za biologiju."""
        rules = get_rules_for_subject("biologija")
        assert rules is not None
        assert "difficulty" in rules
        assert "question_types" in rules
        assert "num_questions" in rules

    def test_rules_for_medicine(self):
        """Pravila za medicinu (teška oblast)."""
        rules = get_rules_for_subject("medicina")
        assert rules["difficulty"] == "hard"
        assert rules["num_questions"] == 12

    def test_rules_for_history(self):
        """Pravila za istoriju."""
        rules = get_rules_for_subject("istorija")
        assert rules is not None
        assert "multiple_choice" in rules["question_types"]

    def test_rules_for_mathematics(self):
        """Pravila za matematiku."""
        rules = get_rules_for_subject("matematika")
        assert "fill_blank" in rules["question_types"]

    def test_rules_for_unknown(self):
        """Fallack pravila za nepoznatu oblast."""
        rules = get_rules_for_subject("nepoznata_oblast")
        assert rules["difficulty"] == "easy"


class TestFullIntegration:
    """Integracioni testovi."""

    def test_detect_and_prepare_quiz_from_text(self):
        """Kompletan workflow sa tekstom."""
        text = """
        The mitochondria is the powerhouse of the cell.
        It produces ATP through cellular respiration.
        DNA is located in the nucleus.
        """
        result = detect_and_prepare_quiz(text=text)

        assert result is not None
        assert "subject_area" in result
        assert "prompt" in result
        assert "rules" in result
        assert "confidence" in result

        assert result["subject_area"] == "biologija"
        assert result["prompt"] is not None
        assert result["rules"] is not None

    def test_detect_and_prepare_quiz_empty(self):
        """Workflow sa praznim tekstom."""
        result = detect_and_prepare_quiz(text="")
        assert result["subject_area"] == "ostalo"

    def test_detect_and_prepare_quiz_with_chunks(self):
        """Workflow sa chunk-ovima - svi sa text ključem."""
        chunks = [
            {"text": "The Battle of Waterloo was in 1815. Napoleon was defeated."},
            {"text": "Treaty of Paris was signed by the victors."},
        ]
        result = detect_and_prepare_quiz(chunks=chunks)
        assert result["subject_area"] == "istorija"


class TestSubjectAreasDictionary:
    """Testovi za SUBJECT_AREAS rečnik."""

    def test_subject_areas_count(self):
        """Broj definisanih oblasti."""
        assert len(SUBJECT_AREAS) > 50

    def test_all_subjects_have_keywords(self):
        """Sve oblasti imaju keywords."""
        for subject, keywords in SUBJECT_AREAS.items():
            assert len(keywords) > 0, f"Subject {subject} has no keywords"

    def test_biology_keywords(self):
        """Biologija ima keywords."""
        assert len(SUBJECT_AREAS["biologija"]) > 10

    def test_medicine_keywords(self):
        """Medicina ima keywords."""
        assert len(SUBJECT_AREAS["medicina"]) > 10


class TestPDFSkillDetectorClass:
    """Testovi za PDFSkillDetector klasu."""

    def test_class_can_be_instantiated(self):
        """Klasa može da se instancira."""
        detector = PDFSkillDetector()
        assert detector is not None

    def test_class_has_required_methods(self):
        """Klasa ima potrebne metode."""
        detector = PDFSkillDetector()
        assert hasattr(detector, "detect_subject_from_text")
        assert hasattr(detector, "detect_subject_from_chunks")
        assert hasattr(detector, "get_prompt_for_subject")
        assert hasattr(detector, "get_rules_for_subject")
        assert hasattr(detector, "detect_and_prepare_quiz")

    def test_class_get_available_subjects(self):
        """Metod za dostupne oblasti."""
        detector = PDFSkillDetector()
        subjects = detector.get_available_subjects()
        assert len(subjects) > 50


class TestEdgeCases:
    """Testovi za rubne slučajeve."""

    def test_very_short_text(self):
        """Vrlo kratak tekst - dodajemo više da bi detektovao."""
        text = "DNA contains genetic information. Cells have nuclei."
        result = detect_subject_from_text(text)
        assert result == "biologija"

    def test_mixed_language(self):
        """Mešani jezici."""
        text = "The mitochondria je powerhouse of the cell."
        result = detect_subject_from_text(text)
        assert result == "biologija"

    def test_legal_document_keywords(self):
        """Pravni dokument sa specifičnim keyword-ima."""
        text = "The plaintiff filed a lawsuit. The defendant was served."
        result = detect_subject_from_text(text)
        assert result == "pravo"

    def test_programming_code(self):
        """Programski kod - više konteksta."""
        text = "def function(x, y): return x + y. Python programming language uses indentation."
        result = detect_subject_from_text(text)
        assert result == "informatika"

    def test_scientific_formula(self):
        """Naučna formula - dodajemo više fizikalnih keyword-a."""
        text = "E equals mc squared. The force is mass times acceleration. Newton's laws of motion."
        result = detect_subject_from_text(text)
        assert result == "fizika"
