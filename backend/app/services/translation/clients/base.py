# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENTS - BASE MODULE
================================================================================
Apstraktna klasa za sve translation client-e.

Verzija: 2.0.0 (FAZA 5 - Modularizacija)
================================================================================
"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class TranslationResult:
    """Rezultat prevoda."""

    success: bool
    translated_text: str = ""
    source_language: str = ""
    target_language: str = ""
    provider: str = ""
    tokens_used: int = 0
    cost: float = 0.0
    error: Optional[str] = None
    duration_ms: float = 0.0


class BaseTranslationClient(ABC):
    """Bazna klasa za translation client-e."""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
    ) -> TranslationResult:
        """Prevodi tekst."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Proverava da li je provajder dostupan."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Vraća ime provajdera."""
        pass
