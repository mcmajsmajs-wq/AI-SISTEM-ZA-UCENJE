# -*- coding: utf-8 -*-
"""
===============================================================================
OLLAMA QUIZ CLIENT
===============================================================================
Lokalni AI provajder za generisanje kviz pitanja.

Verzija: 1.0.0
===============================================================================
"""

import httpx
from typing import Tuple

from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.core.config import settings


class OllamaQuizClient(BaseQuizClient):
    """
    ================================================================================
    OLLAMA QUIZ CLIENT
    ================================================================================
    lokalni AI provajder koji koristi Ollama model.
    Koristi se za offline/ lokalno generisanje kviz pitanja.
    ================================================================================
    """

    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    @property
    def provider_name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        """Proverava da li je Ollama server dostupan."""
        try:
            r = httpx.get(f"{self.host}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """
        Generiše kviz pitanja koristeći Ollama model.

        Args:
            text: Tekst iz kojeg se generišu pitanja
            num_questions: Broj pitanja za generisanje

        Returns:
            Tuple[bool, str, str]: (success, raw_json_string, error)
        """
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, text=text[:12000])
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3},
                    },
                )
                r.raise_for_status()
                return True, r.json().get("response", ""), ""
        except Exception as e:
            return False, "", str(e)
