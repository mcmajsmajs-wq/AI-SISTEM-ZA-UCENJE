# -*- coding: utf-8 -*-
"""
================================================================================
SUBJECT-SPECIFIC PROMPTS MODULE
================================================================================

Specijalizovani promptovi za različite oblasti (matematika, fizika, hemija, etc.)

Verzija: 1.0.0
================================================================================
"""

from typing import Dict


SUBJECT_INSTRUCTIONS: Dict[str, str] = {
    "matematika": """
MATEMATIKA SPECIFICNO:
- Uključi zadatke sa jasnim postupkom rešavanja
- Objasni svaki korak u izračunavanju korak-po-korak
- Naglasi koja se formula koristi i zašto
- Za geometrijske zadatke objasni crtež i logiku
- Za algebru pokaži postavku jednačine i verifikaciju
- Za tekstualne zadatke objasni kako si prepoznao šta treba izračunati
- Koristi srpsku matematičku terminologiju (površina, zapremina, stranica, itd.)
- U objašnjenju objasni greške u netačnim odgovorima
""",
    "fizika": """
FIZIKA SPECIFICNO:
- Fokusiraj se na fizikalne zakone i principe
- Uključi formule i njihovu primenu
- Objasni fizičke veličine i jedinice
- Koristi oznake prema SI sistemu
- Naglasi vezu između teorije i praktične primene
- Uključi računske zadatke sa jasnim postupkom
- Objasni svaki korak u rešavanju
""",
    "hemija": """
HEMIJA SPECIFICNO:
- Fokusiraj se na hemijske reakcije i procese
- Uključi hemijske formule i jednačine
- Objasni osobine hemijskih elemenata i jedinjenja
- Koristi pravilnu hemijsku nomenklaturu
- Naglasi tip reakcije (oksidacija, redukcija, itd.)
- Uključi stehiometrijske proračune
""",
    "biologija": """
BIOLOGIJA SPECIFICNO:
- Fokusiraj se na biološke procese i strukture
- Uključi nazive organela, organa, sistema
- Objasni funkcije i međusobne veze
- Koristi latinske nazive gde je potrebno
- Naglasi uzroke i posledice bioloških procesa
- Uključi pitanja o evoluciji i ekologiji
""",
    "istorija": """
ISTORIJA SPECIFICNO:
- Fokusiraj se na događaje, datume i uzroke
- Uključi veze između istorijskih događaja
- Objasni ulogu ličnosti u istoriji
- Naglasi hronološki redosled
- Poveži događaje sa posledicama
- Koristi tačne istorijske nazive i datume
""",
    "geografija": """
GEOGRAFIJA SPECIFICNO:
- Fokusiraj se na geografske karakteristike
- Uključi podatke o državama, gradovima, reikama, planinama
- Objasni klimatske i vegetacijske zone
- Naglasi geografske veze i odnose
- Koristi tačne geografske nazive
- Uključi statističke podatke gde je relevantno
""",
    "jezici": """
JEZICI SPECIFICNO:
- Fokusiraj se na gramatiku i pravopis
- Uključi pitanja o sintaksi i semantici
- Objasni značenje reči i izraza
- Naglasi razlike između sličnih termina
- Koristi primere iz književnog jezika
- Uključi pitanja o jezičkim pojavama
""",
    "pravo": """
PRAVO SPECIFICNO:
- Fokusiraj se na pravne pojmove i definicije
- Uključi članove zakona i propise
- Objasni pravne postupke i rokove
- Naglasi prava i obaveze
- Koristi pravnu terminologiju
- Poveži sa konkretnim slučajevima
""",
    "ekonomija": """
EKONOMIJA SPECIFICNO:
- Fokusiraj se na ekonomske концепте
- Uključi ekonomske formule i izračunavanja
- Objasni tržišne mehanizme
- Naglasi ekonomske pokazatelje
- Poveži teoriju sa praksom
- Koristi ekonomsku terminologiju
""",
    "informatika": """
INFORMATIKA SPECIFICNO:
- Fokusiraj se na algoritme i logiku
- Uključi programske koncepte i strukture
- Objasni rad algoritama korak-po-korak
- Naglasi vremensku i prostornu kompleksnost
- Koristi primer koda gde je relevantno
- Poveži teoriju sa praktičnom primenom
""",
    "ostalo": """
GENERALNO:
- Kreiraj raznovrsna pitanja koja pokrivaju sve aspekte teksta
- Fokusiraj se na ključne концепте i njihovo razumevanje
- Koristi jasan i precizan jezik
- Objasni svaki odgovor detaljno
""",
}


def get_specialized_prompt(subject_area: str, num_questions: int, text: str) -> str:
    """
    Vraća specijalizovani prompt za oblast.

    Args:
        subject_area: Oblast dokumenta
        num_questions: Broj pitanja
        text: Tekst dokumenta (truncate za prompt)

    Returns:
        str: Specijalizovani prompt
    """
    from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT

    subject = subject_area.lower()
    instructions = SUBJECT_INSTRUCTIONS.get(subject, SUBJECT_INSTRUCTIONS["ostalo"])

    base_prompt = QUIZ_PROMPT.format(
        num_questions=num_questions,
        text=text[:12000]
    )

    return base_prompt + instructions


def get_subject_instruction(subject_area: str) -> str:
    """
    Vraća dodatne instrukcije za oblast.

    Args:
        subject_area: Oblast dokumenta

    Returns:
        str: Dodatne instrukcije
    """
    return SUBJECT_INSTRUCTIONS.get(
        subject_area.lower(),
        SUBJECT_INSTRUCTIONS["ostalo"]
    )


def get_all_subjects() -> list:
    """
    Vraća listu svih podržanih oblasti.

    Returns:
        list: Lista oblasti
    """
    return list(SUBJECT_INSTRUCTIONS.keys())
