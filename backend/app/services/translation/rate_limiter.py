# -*- coding: utf-8 -*-
"""
===============================================================================
RATE LIMITER - Sliding window RPM tracking per provider
===============================================================================
Omogucava paralelne prevode sa kontrolom limita.

Verzija: 1.0.0 (FAZA 2 - Paralelni prevodi)
===============================================================================
"""

import time
import logging
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimitController:
    """
    Sliding window rate limiter per translation provider.

    Thread-safe. Koristi se za kontrolu broja zahteva po minutu (RPM)
    za svakog provajdera.
    """

    DEFAULT_LIMITS: Dict[str, int] = {
        "groq": 30,
        "mistral": 30,
        "gemini": 60,
        "deepseek": 60,
        "openai": 60,
        "claude": 60,
        "ollama": 100,
        "deepl": 30,
        "google": 30,
    }

    WINDOW_SECONDS = 60

    def __init__(self):
        self._limits: Dict[str, int] = dict(self.DEFAULT_LIMITS)
        self._windows: Dict[str, list] = {}
        self._lock = Lock()

    def get_limit(self, provider: str) -> int:
        return self._limits.get(provider, 60)

    def set_limit(self, provider: str, rpm: int) -> None:
        with self._lock:
            self._limits[provider] = rpm

    def record_request(self, provider: str) -> None:
        now = time.time()
        with self._lock:
            if provider not in self._windows:
                self._windows[provider] = []
            self._windows[provider].append(now)

    def request_count(self, provider: str) -> int:
        self._cleanup(provider)
        return len(self._windows.get(provider, []))

    def is_allowed(self, provider: str) -> bool:
        return self.request_count(provider) < self.get_limit(provider)

    def wait_if_needed(self, provider: str, timeout: Optional[float] = None) -> bool:
        """
        Blocks until rate limit slot is available or timeout reached.

        Args:
            provider: Provider name
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            True if slot available, False if timed out
        """
        start = time.time()
        while not self.is_allowed(provider):
            if timeout is not None and (time.time() - start) >= timeout:
                logger.warning(f"Rate limit wait timed out for {provider}")
                return False
            time.sleep(0.1)
        return True

    def reset(self) -> None:
        """Reset all windows and limits to defaults."""
        with self._lock:
            self._windows.clear()
            self._limits = dict(self.DEFAULT_LIMITS)

    def _cleanup(self, provider: str) -> None:
        now = time.time()
        with self._lock:
            if provider not in self._windows:
                return
            cutoff = now - self.WINDOW_SECONDS
            self._windows[provider] = [t for t in self._windows[provider] if t > cutoff]
