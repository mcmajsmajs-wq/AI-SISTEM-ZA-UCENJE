# -*- coding: utf-8 -*-
"""
================================================================================
PDF SKILL DETECTOR - OBLAST DETEKCIJA ZA QUIZ
================================================================================

Integracija:
- PDF processing (PDFService) → Izvlačenje teksta/chunk-ova
- Subject detection → Detekcija oblasti
- Quiz prompts → Specijalizovani prompt
- Quiz generation → Kreiranje pitanja iz chunk-ova

Workflow:
1. Upload PDF → extract_text(chunks)
2. detect_subject_area() → oblast (biologija, hemija, medicina...)
3. get_specialized_prompt() → prompt za oblast
4. generate_questions_with_ai() → pitanja iz chunk-ova

Verzija: 2.1.0 (Modularni keyword import)
================================================================================
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from app.services.skills.keywords import SUBJECT_KEYWORDS

logger = logging.getLogger(__name__)


class PDFSkillDetector:
    """
    PDF SKILL DETECTOR - Detektuje OBLAST iz PDF dokumenta i generiše prompt za quiz.
    """

    def __init__(self):
        self.keywords_map = SUBJECT_KEYWORDS

    def extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        try:
            from app.services.pdf import PDFService

            pdf_service = PDFService()
            result = pdf_service.process_pdf(pdf_path)
            if result.success:
                return [chunk.content for chunk in result.chunks]
            else:
                logger.warning(f"PDF processing failed: {result.error}")
                return []
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return []

    def extract_text_from_chunks(self, chunks: List[Dict]) -> str:
        texts = []
        for chunk in chunks:
            if hasattr(chunk, "content"):
                texts.append(chunk.content)
            elif isinstance(chunk, dict):
                texts.append(chunk.get("text", ""))
            else:
                texts.append(str(chunk))
        return " ".join(texts)

    def detect_subject_from_text(self, text: str, num_samples: int = 30) -> str:
        if not text or not text.strip():
            return "ostalo"

        text_lower = text.lower()
        subject_scores: Dict[str, int] = {}

        for subject, keywords in self.keywords_map.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            subject_scores[subject] = score

        if not subject_scores or max(subject_scores.values()) == 0:
            return "ostalo"

        detected = max(subject_scores, key=subject_scores.get)
        logger.info(
            f"Detektovana oblast: {detected} (score: {subject_scores[detected]})"
        )
        return detected

    def detect_subject_from_chunks(self, chunks: List[Dict]) -> str:
        text = self.extract_text_from_chunks(chunks)
        return self.detect_subject_from_text(text)

    def get_prompt_for_subject(self, subject: str, num_questions: int = 10) -> str:
        try:
            from app.services.quiz.prompts.subjects import get_specialized_prompt

            return get_specialized_prompt(subject, num_questions, "")
        except Exception as e:
            logger.warning(f"Could not get specialized prompt: {e}")
            return self._get_fallback_prompt(subject, num_questions)

    def _get_fallback_prompt(self, subject: str, num_questions: int) -> str:
        prompts = {
            "matematika": f"Generiši {num_questions} matematičkih pitanja. Fokus na formule, jednačine i računanje.",
            "fizika": f"Generiši {num_questions} pitanja iz fizike. Fokus na zakone, veličine i jedinice.",
            "hemija": f"Generiši {num_questions} hemijskih pitanja. Fokus na reakcije, elemente i jedinjenja.",
            "biologija": f"Generiši {num_questions} bioloških pitanja. Fokus na ćeliju, organizme i sisteme.",
            "istorija": f"Generiši {num_questions} istorijskih pitanja. Fokus na događaje, period i ličnosti.",
            "geografija": f"Generiši {num_questions} geografskih pitanja. Fokus na države, reke i klimu.",
            "jezici": f"Generiši {num_questions} jezičkih pitanja. Fokus na gramatiku i strukturu.",
            "pravo": f"Generiši {num_questions} pravnih pitanja. Fokus na zakone i propise.",
            "ekonomija": f"Generiši {num_questions} ekonomskih pitanja. Fokus na tržište i finansije.",
            "informatika": f"Generiši {num_questions} informatičkih pitanja. Fokus na algoritme i programiranje.",
            "medicina": f"Generiši {num_questions} medicinskih pitanja. Fokus na simptome i terapije.",
            "ostalo": f"Generiši {num_questions} opštih pitanja iz teksta.",
        }
        return prompts.get(subject, prompts["ostalo"])

    def get_rules_for_subject(self, subject: str) -> Dict[str, Any]:
        rules = {
            "matematika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice", "fill_blank"],
                "num_questions": 10,
                "focus_areas": ["formule", "jednačine", "računanje"],
            },
            "fizika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice", "true_false"],
                "num_questions": 10,
                "focus_areas": ["zakoni", "veličine", "jedinice"],
            },
            "hemija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["reakcije", "elementi", "jedinjenja"],
            },
            "biologija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["ćelija", "organi", "sistemi"],
            },
            "istorija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice", "true_false"],
                "num_questions": 10,
                "focus_areas": ["događaji", "period", "ličnosti"],
            },
            "geografija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["države", "reljef", "klima"],
            },
            "jezici": {
                "difficulty": "easy",
                "question_types": ["multiple_choice", "fill_blank"],
                "num_questions": 10,
                "focus_areas": ["gramatika", "struktura", "znacenje"],
            },
            "psihologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["ponašanje", "emocije", "ličnost"],
            },
            "sociologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["društvo", "institucije", "norme"],
            },
            "politika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["vlada", "izbori", "stranke"],
            },
            "ekonomija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["tržište", "cene", "finansije"],
            },
            "pravo": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["zakoni", "propisi", "sudska praksa"],
            },
            "medicina": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 12,
                "focus_areas": ["simptomi", "dijagnoze", "terapije"],
            },
            "anatomija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["struktura", "organi", "sistemi"],
            },
            "fiziologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["funkcije", "procesi", "sistemi"],
            },
            "farmakologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["lekovi", "doze", "interakcije"],
            },
            "patologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["bolesti", "promene", "uzroci"],
            },
            "hirurgija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["operacije", "tehnike", "anestezija"],
            },
            "psihijatrija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["poremećaji", "dijagnoze", "terapija"],
            },
            "kardiologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["srce", "cirkulacija", "bolesti"],
            },
            "onkologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["tumori", "lečenje", "prognoza"],
            },
            "neurologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["mozak", "nervi", "bolesti"],
            },
            "ginekologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["trudnoća", "reprodukcija", "hormoni"],
            },
            "pedijatrija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["deca", "razvoj", "bolesti"],
            },
            "dermatologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["koža", "bolesti", "lečenje"],
            },
            "oftalmologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["oči", "vid", "bolesti"],
            },
            "otorinolaringologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["uvo", "grlo", "nos"],
            },
            "pneumoftiziologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["pluća", "disanje", "bolesti"],
            },
            "gastroenterologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["digestivni", "jetra", "creva"],
            },
            "nefrologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["bubrezi", "urinarni", "dijaliza"],
            },
            "urologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["urinarni", "prostata", "bolesti"],
            },
            "reumatologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["zglobovi", "mišići", "autoimune"],
            },
            "endokrinologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["hormoni", "žlezde", "dijabetes"],
            },
            "hematologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["krv", "ćelije", "bolesti"],
            },
            "infektologija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["infekcije", "virusi", "bakterije"],
            },
            "informatika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["algoritmi", "programiranje", "sistemi"],
            },
            "elektrotehnika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["struja", "kola", "signal"],
            },
            "mašinstvo": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["mašine", "mehanizmi", "prenos"],
            },
            "građevinarstvo": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["konstrukcije", "materijali", "statika"],
            },
            "arhitektura": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["dizajn", "prostor", "forma"],
            },
            "automatika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["kontrola", "sistemi", "PID"],
            },
            "robotika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["robot", "kinematika", "upravljanje"],
            },
            "telekomunikacije": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["signal", "modulacija", "mreže"],
            },
            "energetika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["energija", "izvori", "proizvodnja"],
            },
            "poljoprivreda": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["usevi", "žetva", "stočarstvo"],
            },
            "veterina": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["životinje", "bolesti", "lečenje"],
            },
            "šumarstvo": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["šume", "drve", "ekosistem"],
            },
            "ekologija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["ekosistem", "zagađenje", "biodiverzitet"],
            },
            "pedagogija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["nastava", "učenje", "metode"],
            },
            "književnost": {
                "difficulty": "easy",
                "question_types": ["multiple_choice", "essay"],
                "num_questions": 8,
                "focus_areas": ["dela", "autori", "žanrovi"],
            },
            "lingvistika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["jezik", "struktura", "gramatika"],
            },
            "filozofija": {
                "difficulty": "hard",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["ideje", "teorije", "filozofi"],
            },
            "religija": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["vera", "rituali", "tradicije"],
            },
            "novinarstvo": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["vesti", "izveštaj", "mediji"],
            },
            "marketing": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["brend", "promocija", "strategija"],
            },
            "menadžment": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["vođenje", "organizacija", "resursi"],
            },
            "turizam": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["destinacije", "ugostiteljstvo", "atrakcije"],
            },
            "sport": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["takmičenja", "pravila", "tehnike"],
            },
            "zdravlje": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["prevencija", "ishrana", "životni stil"],
            },
            "nutricionizam": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["nutrijenti", "dijete", "suplementi"],
            },
            "muzika": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["note", "instrumenți", "žanrovi"],
            },
            "likovna_umetnost": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["tehnike", "istine", "umetnici"],
            },
            "film": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["režija", "scenarijo", "žanrovi"],
            },
            "pozorište": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["predstave", "glumci", "režija"],
            },
            "astronomija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["zvezde", "planete", "kosmos"],
            },
            "geologija": {
                "difficulty": "medium",
                "question_types": ["multiple_choice"],
                "num_questions": 10,
                "focus_areas": ["stenje", "fosili", "tektonika"],
            },
            "statistika": {
                "difficulty": "medium",
                "question_types": ["multiple_choice", "fill_blank"],
                "num_questions": 10,
                "focus_areas": ["analiza", "verovatnoća", "testovi"],
            },
            "ostalo": {
                "difficulty": "easy",
                "question_types": ["multiple_choice"],
                "num_questions": 8,
                "focus_areas": ["ključni_pojmovi", "činjenice"],
            },
        }
        return rules.get(subject, rules["ostalo"])

    def detect_and_prepare_quiz(
        self, pdf_path: str = None, text: str = None, chunks: List[Dict] = None
    ) -> Dict[str, Any]:
        if pdf_path:
            chunks_list = self.extract_text_from_pdf(pdf_path)
            text = self.extract_text_from_chunks(chunks_list)
        elif chunks:
            text = self.extract_text_from_chunks(chunks)

        subject = self.detect_subject_from_text(text or "")
        prompt = self.get_prompt_for_subject(subject)
        rules = self.get_rules_for_subject(subject)

        text_lower = text.lower() if text else ""
        subject_keywords = self.keywords_map.get(subject, [])
        matched = sum(1 for kw in subject_keywords if kw in text_lower)
        total = len(subject_keywords)
        confidence = min(round((matched / total) * 100, 1), 100) if total > 0 else 0

        return {
            "subject_area": subject,
            "prompt": prompt,
            "rules": rules,
            "confidence": confidence,
            "text_length": len(text) if text else 0,
        }

    def get_available_subjects(self) -> List[str]:
        return list(self.keywords_map.keys())


pdf_skill_detector = PDFSkillDetector()


def get_pdf_skill_detector() -> PDFSkillDetector:
    return pdf_skill_detector


def detect_pdf_subject(pdf_path: str) -> str:
    detector = PDFSkillDetector()
    chunks = detector.extract_text_from_pdf(pdf_path)
    return detector.detect_subject_from_chunks(chunks)


def prepare_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> Dict[str, Any]:
    detector = PDFSkillDetector()
    return detector.detect_and_prepare_quiz(pdf_path=pdf_path)


def detect_subject_from_text(text: str, num_samples: int = 30) -> str:
    detector = PDFSkillDetector()
    return detector.detect_subject_from_text(text, num_samples)


def detect_subject_from_chunks(chunks: List[Dict]) -> str:
    detector = PDFSkillDetector()
    return detector.detect_subject_from_chunks(chunks)


def get_prompt_for_subject(subject: str, num_questions: int = 10) -> str:
    detector = PDFSkillDetector()
    return detector.get_prompt_for_subject(subject, num_questions)


def get_rules_for_subject(subject: str) -> Dict[str, Any]:
    detector = PDFSkillDetector()
    return detector.get_rules_for_subject(subject)


def detect_and_prepare_quiz(
    pdf_path: str = None, text: str = None, chunks: List[Dict] = None
) -> Dict[str, Any]:
    detector = PDFSkillDetector()
    return detector.detect_and_prepare_quiz(pdf_path=pdf_path, text=text, chunks=chunks)


SUBJECT_AREAS = SUBJECT_KEYWORDS


__all__ = [
    "PDFSkillDetector",
    "SUBJECT_KEYWORDS",
    "SUBJECT_AREAS",
    "detect_subject_from_text",
    "detect_subject_from_chunks",
    "get_prompt_for_subject",
    "get_rules_for_subject",
    "detect_and_prepare_quiz",
    "detect_pdf_subject",
    "prepare_quiz_from_pdf",
    "get_pdf_skill_detector",
]
