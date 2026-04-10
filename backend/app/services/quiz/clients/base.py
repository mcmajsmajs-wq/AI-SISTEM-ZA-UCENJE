# -*- coding: utf-8 -*-
"""
===============================================================================
BASE QUIZ CLIENT
===============================================================================
Apstraktna klasa za sve AI provajdere kviz servisa.

Verzija: 1.0.0
===============================================================================
"""

from abc import ABC, abstractmethod
from typing import Tuple


class BaseQuizClient(ABC):
    """
    ================================================================================
    BASE QUIZ CLIENT
    ================================================================================
    Apstraktna baza za sve quiz AI klijente.
    Svi provajderi moraju implementirati generate() i is_available() metode.
    ================================================================================
    """

    @abstractmethod
    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """
        Generiše kviz pitanja iz teksta.

        Args:
            text: Tekst iz kojeg se generišu pitanja
            num_questions: Broj pitanja za generisanje

        Returns:
            Tuple[bool, str, str]: (success, raw_json_string, error)
                - success: True ako je uspešno, False ako nije
                - raw_json_string: JSON string sa pitanjima ili prazan string
                - error: Poruka greške ili prazan string
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Proverava da li je provajder dostupan.

        Returns:
            bool: True ako je dostupan, False ako nije
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Vraća naziv provajdera.

        Returns:
            str: Naziv provajdera (npr. "ollama", "openai", "claude")
        """
        pass
