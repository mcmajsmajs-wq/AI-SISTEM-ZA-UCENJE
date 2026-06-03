# -*- coding: utf-8 -*-
"""
================================================================================
CYRILLIC UTILITY
================================================================================
Pomoćne funkcije za konverziju ćirilice u latinicnu i obrnuto.

Verzija: 1.0.0 (2026-04-23)
================================================================================
"""

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "ѓ": "đ",
    "е": "e",
    "ж": "ž",
    "з": "z",
    "и": "i",
    "ђ": "đ",
    "ј": "j",
    "к": "k",
    "л": "l",
    "љ": "lj",
    "м": "m",
    "н": "n",
    "њ": "nj",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "ћ": "ć",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "č",
    "џ": "dž",
    "і": "i",
    "ї": "ji",
    "є": "je",
    "Ѓ": "Đ",
    "Ѐ": "È",
    "Ё": "Ë",
    "Љ": "LJ",
    "Њ": "NJ",
    "Ћ": "Ć",
    "Џ": "DŽ",
    "ш": "š",
    "щ": "št",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "ju",
    "я": "ja",
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Ѓ": "Đ",
    "Ђ": "Đ",
    "Е": "E",
    "Ё": "Ë",
    "Ж": "Ž",
    "З": "Z",
    "И": "I",
    "Й": "J",
    "Ј": "J",
    "К": "K",
    "Л": "L",
    "Љ": "LJ",
    "М": "M",
    "Н": "N",
    "Њ": "NJ",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "Ћ": "Ć",
    "У": "U",
    "Ф": "F",
    "Х": "H",
    "Ц": "C",
    "Ч": "Č",
    "Џ": "DŽ",
    "Ш": "Š",
    "І": "I",
    "Ї": "YI",
    "Є": "JE",
    "Щ": "ŠT",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "JU",
    "Я": "JA",
}

LATIN_TO_CYRILLIC = {v: k for k, v in CYRILLIC_TO_LATIN.items()}


def cyrillic_to_latin(text: str) -> str:
    """
    Konvertuje ćirilični tekst u latinični.

    Args:
        text: Tekst na ćirilici

    Returns:
        Konvertovani tekst na latinici
    """
    if not text:
        return text
    result = []
    for char in text:
        if "\u0400" <= char <= "\u04ff" or char in "ёЁ":
            result.append(CYRILLIC_TO_LATIN.get(char, char))
        else:
            result.append(char)
    return "".join(result)


def latin_to_cyrillic(text: str) -> str:
    """
    Konvertuje latinični tekst u ćirilični.

    Args:
        text: Tekst na latinici

    Returns:
        Konvertovani tekst na ćirilici
    """
    if not text:
        return text
    result = []
    for char in text:
        result.append(LATIN_TO_CYRILLIC.get(char, char))
    return "".join(result)


def transliterate_text(text: str) -> str:
    """
    Automatski detektuje i konvertuje tekst.
    Ako tekst sadrži ćirilična slova -> konvertuje u latinicnu.
    Inače -> konvertuje u ćirilicu (fallback).

    Args:
        text: Tekst za transliteraciju

    Returns:
        Konvertovani tekst
    """
    if not text:
        return text

    has_cyrillic = any(
        ord(c) >= 0x0430 and ord(c) <= 0x044F for c in text if c.isalpha()
    )

    if has_cyrillic:
        return cyrillic_to_latin(text)
    else:
        return latin_to_cyrillic(text)
