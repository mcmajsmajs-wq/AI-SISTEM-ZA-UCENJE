# -*- coding: utf-8 -*-
"""
===============================================================================
OPENAI COMPATIBLE QUIZ CLIENT
===============================================================================
OpenAI-kompatibilni provajderi: Gemini, Groq, Mistral, DeepSeek.

Verzija: 1.0.0
===============================================================================
"""

import httpx
from typing import Tuple

from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT


class OpenAICompatQuizClient(BaseQuizClient):
    """
    ================================================================================
    OPENAI COMPATIBLE QUIZ CLIENT
    ================================================================================
    Univerzalni klijent za sve OpenAI-kompatibilne API-jeve.
    Koristi se za:
    - Google Gemini
    - Groq
    - Mistral
    - DeepSeek
    ================================================================================
    """

    SYSTEM = (
        "You are an expert educator that creates quiz questions. "
        "Always respond with valid JSON only — no markdown, no extra text."
    )

    def __init__(self, name: str, base_url: str, model: str, api_key: str = ""):
        """
        Args:
            name: Naziv provajdera (gemini, groq, mistral, deepseek)
            base_url: Bazni URL za API
            model: Ime modela
            api_key: API ključ
        """
        self._name = name
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = 120

    @property
    def provider_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        """Proverava da li je API dostupan."""
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """
        Generiše kviz pitanja koristeći OpenAI-kompatibilni API.

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
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.SYSTEM},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)
