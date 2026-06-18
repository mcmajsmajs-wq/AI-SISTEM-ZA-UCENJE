# -*- coding: utf-8 -*-
"""
===============================================================================
SKILL DETECTOR
===============================================================================
Automatska detekcija tipa dokumenta na osnovu sadržaja.

SkillDetector:
- analyze_text(): Analizira tekst i vraća detektovanu kategoriju
- get_category_confidence(): Vraća confidence score za svaku kategoriju
- detect_from_chunks(): Detektuje tip iz više chunks-a

Verzija: 1.0.0 (FAZA 6 - Skill Sistem)
===============================================================================
"""

import logging
from typing import List, Dict, Any

from app.services.skills.templates import DOCUMENT_TYPE_KEYWORDS

logger = logging.getLogger(__name__)


class SkillDetector:
    """
    ================================================================================
    SKILL DETECTOR
    ================================================================================
    Automatski detektuje tip dokumenta na osnovu sadržaja.

    Koristi keyword matching i pattern recognition za identifikaciju
    kategorije dokumenta (legal, technical, medical, academic, textbook, general).
    ================================================================================
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 50

    def __init__(self, confidence_threshold: int = None):
        """
        Inicijalizuje SkillDetector.

        Args:
            confidence_threshold: Minimalni confidence za detekciju (default: 70)
        """
        self.confidence_threshold = (
            confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD
        )
        self.keywords_map = DOCUMENT_TYPE_KEYWORDS

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analizira tekst i vraća detektovanu kategoriju.

        Args:
            text: Tekst dokumenta za analizu

        Returns:
            Dict sa:
                - category: Detektovana kategorija
                - confidence: Confidence score (0-100)
                - scores: Dict svih kategorija sa confidence score-ovima
                - matched_keywords: Lista poklopljenih keywords

        Primer:
            >>> detector = SkillDetector()
            >>> result = detector.analyze_text("This contract establishes...")
            >>> print(result["category"])
            "legal"
        """
        if not text or not text.strip():
            return self._empty_result()

        text_lower = text.lower()
        scores = {}
        matched_keywords = {}

        for category, config in self.keywords_map.items():
            keywords = config.get("keywords", [])
            category_score = 0
            category_keywords = []

            for keyword in keywords:
                if keyword.lower() in text_lower:
                    category_score += 1
                    category_keywords.append(keyword)

            max_keywords = len(keywords)
            if max_keywords > 0:
                normalized_score = (category_score / max_keywords) * 100
            else:
                normalized_score = 0

            scores[category] = round(normalized_score, 2)
            matched_keywords[category] = category_keywords

        # Get category with highest score, or use "general" if threshold not met
        best_category = max(scores.items(), key=lambda x: x[1])

        if best_category[1] >= self.confidence_threshold:
            category = best_category[0]
            confidence = scores[category]
        elif best_category[1] > 0:
            category = best_category[0]
            confidence = best_category[1]
        else:
            category = "general"
            confidence = 0

        return {
            "category": category,
            "confidence": confidence,
            "scores": scores,
            "matched_keywords": matched_keywords,
            "threshold_used": self.confidence_threshold,
        }

    def get_category_confidence(self, text: str, category: str) -> float:
        """
        Vraća confidence score za specifičnu kategoriju.

        Args:
            text: Tekst dokumenta
            category: Kategorija za koju se računa score

        Returns:
            Confidence score (0-100)
        """
        result = self.analyze_text(text)
        return result["scores"].get(category, 0.0)

    def detect_from_chunks(self, chunks: List[str]) -> Dict[str, Any]:
        """
        Detektuje tip dokumenta iz više chunks-a.

        Koristi agregaciju rezultata iz svih chunks-a za bolju detekciju.

        Args:
            chunks: Lista tekst chunks-a iz dokumenta

        Returns:
            Dict sa agregiranim rezultatima
        """
        if not chunks:
            return self._empty_result()

        all_scores = {}
        all_matched = {}

        for chunk in chunks:
            result = self.analyze_text(chunk)

            for category, score in result["scores"].items():
                if category not in all_scores:
                    all_scores[category] = []
                    all_matched[category] = []

                if score > 0:
                    all_scores[category].append(score)
                    all_matched[category].extend(
                        result["matched_keywords"].get(category, [])
                    )

        avg_scores = {}
        for category, scores_list in all_scores.items():
            if scores_list:
                avg_scores[category] = sum(scores_list) / len(scores_list)

        best = (
            max(avg_scores.items(), key=lambda x: x[1])
            if avg_scores
            else ("general", 0)
        )
        category = best[0] if best[1] >= self.confidence_threshold else "general"

        return {
            "category": category,
            "confidence": round(avg_scores.get(category, 0), 2),
            "scores": {k: round(v, 2) for k, v in avg_scores.items()},
            "matched_keywords": all_matched,
            "chunks_analyzed": len(chunks),
        }

    def detect_from_title(self, title: str) -> Dict[str, Any]:
        """
        Detektuje tip dokumenta iz naslova.

        Koristi pattern matching za prepoznavanje tipa iz naslova.

        Args:
            title: Naslov dokumenta

        Returns:
            Dict sa detektovanom kategorijom
        """
        if not title:
            return self._empty_result()

        title_lower = title.lower()
        category_scores = {}

        for category, config in self.keywords_map.items():
            keywords = config.get("keywords", [])
            matches = sum(1 for kw in keywords if kw.lower() in title_lower)
            if matches > 0:
                category_scores[category] = matches

        if category_scores:
            best = max(category_scores.items(), key=lambda x: x[1])
            return {
                "category": best[0],
                "confidence": min(best[1] * 20, 100),
                "source": "title",
            }

        return {"category": "general", "confidence": 50, "source": "title"}

    def _empty_result(self) -> Dict[str, Any]:
        """Vraća prazan rezultat."""
        return {
            "category": "general",
            "confidence": 0,
            "scores": {},
            "matched_keywords": {},
        }

    def get_available_categories(self) -> List[str]:
        """
        Vraća listu dostupnih kategorija.

        Returns:
            List kategorija
        """
        return list(self.keywords_map.keys())


def detect_document_type(text: str) -> str:
    """
    Helper funkcija za brzu detekciju tipa dokumenta.

    Args:
        text: Tekst dokumenta

    Returns:
        Detektovana kategorija (legal, technical, medical, academic, textbook, general)
    """
    detector = SkillDetector()
    result = detector.analyze_text(text)
    return result["category"]


def detect_from_file(filename: str, text: str) -> Dict[str, Any]:
    """
    Detektuje tip dokumenta iz imena fajla i sadržaja.

    Args:
        filename: Ime fajla
        text: Sadržaj fajla

    Returns:
        Dict sa rezultatima detekcije
    """
    detector = SkillDetector()

    filename_indicators = {
        "legal": ["contract", "agreement", "terms", "conditions", "law", "act"],
        "technical": ["manual", "guide", "spec", "api", "documentation"],
        "medical": ["clinical", "protocol", "guideline", "medical"],
        "academic": ["paper", "research", "study", "thesis"],
        "textbook": ["chapter", "textbook", "lecture"],
    }

    filename_lower = filename.lower()
    filename_scores = {}
    for category, indicators in filename_indicators.items():
        matches = sum(1 for ind in indicators if ind in filename_lower)
        if matches > 0:
            filename_scores[category] = matches * 30

    text_result = detector.analyze_text(text)

    combined_scores = {**text_result["scores"]}
    for category, score in filename_scores.items():
        if category in combined_scores:
            combined_scores[category] = min(combined_scores[category] + score, 100)
        else:
            combined_scores[category] = score

    best = (
        max(combined_scores.items(), key=lambda x: x[1])
        if combined_scores
        else ("general", 0)
    )

    return {
        "category": best[0],
        "confidence": round(min(best[1], 100), 2),
        "scores": {k: round(v, 2) for k, v in combined_scores.items()},
        "source": "filename_and_text",
    }
