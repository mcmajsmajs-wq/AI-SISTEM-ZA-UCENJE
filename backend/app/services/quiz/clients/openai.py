# -*- coding: utf-8 -*-
"""
===============================================================================
OPENAI QUIZ CLIENT
===============================================================================
OpenAI GPT provajder za generisanje kviz pitanja.

Verzija: 1.0.0
===============================================================================
"""

import httpx
from typing import Tuple

from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.core.config import settings


class OpenAIQuizClient(BaseQuizClient):
    """
    ================================================================================
    OPENAI QUIZ CLIENT
    ================================================================================
    OpenAI API provajder (GPT-4, GPT-4o, itd.)
    za generisanje visoko kvalitetnih kviz pitanja.
    ================================================================================
    """

    SYSTEM = "You are an expert educator that creates quiz questions. Always respond with valid JSON only."

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.timeout = getattr(settings, "OPENAI_TIMEOUT", 120)

    @property
    def provider_name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        """Proverava da li je OpenAI API dostupan."""
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """
        Generiše kviz pitanja koristeći OpenAI API.

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
                    "https://api.openai.com/v1/chat/completions",
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
                        "response_format": {"type": "json_object"}
                        if "gpt-4" in self.model
                        else None,
                    },
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)
