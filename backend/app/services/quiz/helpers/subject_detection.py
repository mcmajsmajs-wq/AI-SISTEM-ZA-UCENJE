# -*- coding: utf-8 -*-
"""
================================================================================
SUBJECT DETECTION MODULE
================================================================================

Detekcija oblasti dokumenta (matematika, fizika, hemija, etc.)

Verzija: 1.0.0
================================================================================
"""

from typing import Dict, List


SUBJECT_KEYWORDS: Dict[str, List[str]] = {
    "matematika": [
        "matematika", "površina", "zapremina", "formula", "jednačina", "rešenje",
        "trougao", "kvadrat", "krug", "pravougaonik", "zbir", "razlika", "proizvod",
        "količnik", "stepen", "koren", "logaritam", "trigonometrija", "ugao",
        "stranica", "visina", "base", "promenljiva", "funkcija", "grafik",
        "jednačina", "zadatak", "računati", "izvod", "integral", "matrica", "vektor",
    ],
    "fizika": [
        "fizika", "energija", "sila", "brzina", "ubrzanj", "masa", "gustin",
        "temperatura", "pritisak", "toplota", "struja", "magnet", "svetlost",
        "talas", "zvuk", "mehanika", "optika", "elektrika", "termodinamika",
        "električn", "kinetičk", "potencijaln", "gravitacija", "period", "frekvencija",
    ],
    "hemija": [
        "hemija", "atom", "molekul", "reakcija", "element", "jedinjenje",
        "kiselina", "baza", "oksidacija", "redukcija", "hemijski", "periodicna",
        "hemija", "mol", "koncentracija", "supstanca", " rastvor", "precipitat",
    ],
    "biologija": [
        "biologija", "ćelija", "organ", "sistem", "tkivo", "organizam",
        "Dnk", "RNK", "gen", "evolucija", "ekologija", "biljka", "životinja",
        "metabolizam", "enzim", "protein", "organel", "ćelijsk", "mikroskop",
    ],
    "istorija": [
        "istorija", "istorijski", "godina", "vek", "rat", "država", "vladar",
        "car", "kralj", "događaj", "period", "civilizacija", "antički", "srednji vek",
        "istorij", "zapad", "istok", "jug", "sever", "imperija", "republika",
    ],
    "geografija": [
        "geografija", "država", "grad", "reka", "planina", "more", "kontinent",
        "klimat", "populacija", "reljef", "region", "ostrvo", "poluostrvo",
        "geograf", "klima", "vegetacija", "stanovništvo", "privreda",
    ],
    "jezici": [
        "jezik", "gramatika", "syntax", "semantika", "lingvistika", "reč",
        "rečenica", "glagol", "imenica", "pridev", "pravopis", "znacenje",
        "lingvist", "fonetika", "morfo", "dijalekat", "standardni", "književni",
    ],
    "pravo": [
        "pravo", "zakon", "član", "paragraf", "sud", "presuda", "tužba",
        "ugovor", "odluka", "propis", "obaveza", "rok", "potpis", "overa",
        "javni beležnik", "parnica", "krivičn", "građansk", "prekršaj",
    ],
    "ekonomija": [
        "ekonomija", "ekonomski", "tržište", "cena", "profit", "trošak",
        "investicija", "potražnja", "ponuda", "inflacija", "BDP", "deviz",
        "valuta", "banka", "kredit", "dug", "prihod", "rashod", "bilans",
    ],
    "informatika": [
        "informatika", "program", "algoritam", "kod", "funkcija", "varijabla",
        "klasa", "objekat", "baza", "podatak", "mreža", "internet", "softver",
        "programiranje", "računar", "CPU", "memorija", "algoritam", "sistem",
    ],
    "ostalo": [
        "opšte", "opšti", "generalno", "uvod", "zaključak", "sažetak",
    ],
}


def detect_subject_area(text: str, num_samples: int = 20) -> str:
    """
    Detektuje oblast dokumenta na osnovu ključnih reči.

    Args:
        text: Tekst dokumenta
        num_samples: Broj uzoraka za AI detekciju (trenutno ne koristi)

    Returns:
        str: Ime detektovane oblasti (npr. "matematika", "fizika", "hemija")
    """
    text_lower = text.lower()
    subject_scores: Dict[str, int] = {}

    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        subject_scores[subject] = score

    if not subject_scores or max(subject_scores.values()) == 0:
        return "ostalo"

    return max(subject_scores, key=subject_scores.get)


def get_subject_keywords(subject: str) -> List[str]:
    """
    Vraća listu ključnih reči za datu oblast.

    Args:
        subject: Ime oblasti

    Returns:
        List[str]: Lista ključnih reči
    """
    return SUBJECT_KEYWORDS.get(subject.lower(), [])


def get_all_subjects() -> List[str]:
    """
    Vraća listu svih podržanih oblasti.

    Returns:
        List[str]: Lista svih oblasti
    """
    return list(SUBJECT_KEYWORDS.keys())
