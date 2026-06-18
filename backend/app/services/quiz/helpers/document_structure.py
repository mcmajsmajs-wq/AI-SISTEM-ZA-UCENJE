# -*- coding: utf-8 -*-
"""
================================================================================
DOCUMENT STRUCTURE DETECTION MODULE
================================================================================

Detekcija strukture dokumenta (test, zadaci, primer, etc.)

Verzija: 1.0.0
================================================================================
"""

from typing import Dict, List


STRUCTURE_PATTERNS: Dict[str, List[str]] = {
    "test": [
        "test",
        "kviz",
        "pitanja",
        "odgovori",
        "ocene",
        "ocenjivanje",
        "prvi test",
        "drugi test",
        "treći test",
        "kolokvijum",
        "ispit",
        "pitanje 1",
        "pitanje 2",
        "tačan odgovor",
        "pogrešan odgovor",
        "više ponuđenih",
        "odaberite",
        "zaokružite",
        "precizno",
    ],
    "zadaci": [
        "zadatak",
        "rešenje",
        "izračunati",
        "koliko iznosi",
        "kolika je",
        "izrazi",
        "dokazati",
        "srediti",
        "pojednostaviti",
        "transformisati",
        "primeniti",
        "pomoću",
        "koristeći",
        "postupak",
        "način",
    ],
    "primer": [
        "primer",
        "ilustracija",
        "primeri",
        "slično",
        "kao što",
        "na primer",
        "na primeru",
        "pokazati",
        "demonstrovati",
        "evidentno",
        " konkretno",
    ],
    "teorija": [
        "teorija",
        "definicija",
        "pojam",
        "objašnjenje",
        "značenje",
        "karakteristike",
        "svojstva",
        "osnovne",
        "bitne",
        "važne",
        "uopšte",
        "generalno",
        "teoretski",
        "koncept",
        "princip",
    ],
    "formula": [
        "formula",
        "jednačina",
        "izraz",
        " jednakost",
        "identitet",
        "simbioz",
        "relacija",
        "jednačina",
        "formula",
        "jednačine",
        "jednačina",
        "izračunava",
        "određuje",
        "definiše",
    ],
    "pregled": [
        "pregled",
        "sadržaj",
        "tabela",
        "šema",
        "dijagram",
        "grafikon",
        "slika",
        "figura",
        "prilog",
        "dodatak",
        "appendix",
        "indeks",
        "sadržaj",
        "kazalo",
        "popis",
        "lista",
        "pregled",
    ],
}


def detect_document_structure(text: str) -> str:
    """
    Detektuje strukturu dokumenta na osnovu ključnih reči.

    Args:
        text: Tekst dokumenta

    Returns:
        str: Tip strukture ("test", "zadaci", "primer", "teorija", etc.)
    """
    text_lower = text.lower()
    structure_scores: Dict[str, int] = {}

    for structure_type, keywords in STRUCTURE_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        structure_scores[structure_type] = score

    if not structure_scores or max(structure_scores.values()) == 0:
        return "opšte"

    return max(structure_scores, key=structure_scores.get)


def get_structure_based_prompt(structure_type: str) -> str:
    """
    Vraća dodatne instrukcije za specifičnu strukturu dokumenta.

    Args:
        structure_type: Tip strukture dokumenta

    Returns:
        str: Dodatne instrukcije za prompt
    """
    prompts = {
        "test": "Fokusiraj se na pitanja koja testiraju znanje. Uključi pitanja sa jednim ili više tačnih odgovora.",
        "zadaci": "Uključi zadatke sa jasnim postupkom rešavanja. Objasni svaki korak detaljno.",
        "primer": "Kreiraj pitanja koja koriste konkretne primere iz teksta za ilustraciju koncepata.",
        "teorija": "Fokusiraj se na definicije i teoretska objašnjenja. Testiraj razumevanje pojmova.",
        "formula": "Uključi pitanja koja zahtevaju primenu formula. Objasni svaki korak u izračunavanju.",
        "pregled": "Kreiraj pitanja koja se odnose na strukturu i organizaciju teksta.",
        "opšte": "Kreiraj raznovrsna pitanja koja pokrivaju sve aspekte teksta.",
    }

    return prompts.get(structure_type, prompts["opšte"])


def get_structure_keywords(structure_type: str) -> List[str]:
    """
    Vraća listu ključnih reči za dati tip strukture.

    Args:
        structure_type: Tip strukture dokumenta

    Returns:
        List[str]: Lista ključnih reči
    """
    return STRUCTURE_PATTERNS.get(structure_type.lower(), [])


def get_all_structures() -> List[str]:
    """
    Vraća listu svih podržanih tipova strukture.

    Returns:
        List[str]: Lista svih tipova strukture
    """
    return list(STRUCTURE_PATTERNS.keys())
