# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION PROVIDERS - ENUM
================================================================================
Enum za sve dostupne translation provajdere.

Verzija: 2.0.0 (FAZA 5 - Modularizacija)
================================================================================
"""

from enum import Enum


class TranslationProvider(str, Enum):
    """Dostupni provajderi za prevod."""

    OLLAMA = "ollama"
    DEEPL = "deepl"
    OPENAI = "openai"
    GOOGLE = "google"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    LIBRETRANSLATE = "libretranslate"
    GROQ = "groq"
    MISTRAL = "mistral"
    SIMPLYTRANSLATE = "simplytranslate"
