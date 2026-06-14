# -*- coding: utf-8 -*-
"""
===============================================================================
CLAUDE QUIZ CLIENT
===============================================================================
Anthropic Claude provajder za generisanje kviz pitanja.

Verzija: 1.0.0
===============================================================================
"""

import httpx
from typing import Tuple

from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.core.config import settings


class ClaudeQuizClient(BaseQuizClient):
    """
    ================================================================================
    CLAUDE QUIZ CLIENT
    ================================================================================
    Anthropic Claude API provajder za generisanje kviz pitanja.
    Koristi Claude modele (claude-3-sonnet, claude-3-5-sonnet, itd.)
    ================================================================================
    """

    SYSTEM = "You are an expert educator that creates quiz questions. Always respond with valid JSON only — no markdown, no extra text."

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.timeout = getattr(settings, "CLAUDE_TIMEOUT", 45)

    @property
    def provider_name(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        """Proverava da li je Claude API dostupan."""
        return bool(self.api_key)

    def generate(self, text: str, num_questions: int) -> Tuple[bool, str, str]:
        """
        Generiše kviz pitanja koristeći Claude API.

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
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "system": self.SYSTEM,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                r.raise_for_status()
                content = r.json()["content"][0]["text"]
                return True, content, ""
        except Exception as e:
            return False, "", str(e)
