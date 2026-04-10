# -*- coding: utf-8 -*-
"""
================================================================================
RATE LIMITER SERVICE
================================================================================
FAZA 11: Rate limiting po korisniku i provideru.

Koristi Redis za čuvanje broja request-ova po korisniku i provideru.
Limit se resetuje svakih 60 sekundi.

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-10
================================================================================
"""

import time
from typing import Optional

import redis
from redis.exceptions import RedisError


class RateLimiter:
    """Rate limiter po korisniku i provideru.

    Koristi Redis za praćenje broja request-ova.
    Default limit: 60 request-ova u 60 sekundi.

    Attributes:
        redis: Redis klijent
        default_limit: Default broj dozvoljenih request-ova
        window_seconds: Vremenski period u sekundama
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_limit: int = 60,
        window_seconds: int = 60,
    ):
        """Inicijalizuje rate limiter.

        Args:
            redis_url: Redis connection URL
            default_limit: Default broj dozvoljenih request-ova
            window_seconds: Vremenski period u sekundama
        """
        if redis_url is None:
            from app.core.config import settings

            redis_url = settings.REDIS_CONNECTION_URL

        self._redis = redis.from_url(redis_url, decode_responses=True)
        self.default_limit = default_limit
        self.window_seconds = window_seconds

    def _get_key(self, user_id: str, provider: str) -> str:
        """Kreira Redis key za praćenje.

        Args:
            user_id: ID korisnika
            provider: Ime providera

        Returns:
            Redis key string
        """
        return f"rate_limit:{user_id}:{provider}"

    def check_limit(
        self, user_id: str, provider: str, limit: Optional[int] = None
    ) -> bool:
        """Proverava da li korisnik ima pravo na request.

        Args:
            user_id: ID korisnika
            provider: Ime providera
            limit: Prilagođeni limit (opciono)

        Returns:
            True ako je request dozvoljen, False ako je limit prekoračen
        """
        limit = limit or self.default_limit
        key = self._get_key(user_id, provider)

        try:
            current = self._redis.get(key)

            if current is None:
                pipe = self._redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window_seconds)
                pipe.execute()
                return True

            if int(current) >= limit:
                return False

            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            pipe.execute()
            return True

        except RedisError:
            return True  # Fail-open - dozvoli request ako Redis nije dostupan

    def get_remaining(self, user_id: str, provider: str) -> int:
        """Vraća broj preostalih request-ova.

        Args:
            user_id: ID korisnika
            provider: Ime providera

        Returns:
            Broj preostalih request-ova
        """
        key = self._get_key(user_id, provider)

        try:
            current = self._redis.get(key)
            if current is None:
                return self.default_limit
            return max(0, self.default_limit - int(current))
        except RedisError:
            return self.default_limit

    def get_reset_time(self, user_id: str, provider: str) -> int:
        """Vraća koliko sekundi do resetovanja limita.

        Args:
            user_id: ID korisnika
            provider: Ime providera

        Returns:
            Broj sekundi do resetovanja
        """
        key = self._get_key(user_id, provider)

        try:
            ttl = self._redis.ttl(key)
            return max(0, ttl)
        except RedisError:
            return 0

    def reset(self, user_id: str, provider: str) -> bool:
        """Resetuje limit za korisnika i providera.

        Args:
            user_id: ID korisnika
            provider: Ime providera

        Returns:
            True ako je uspešno resetovano
        """
        key = self._get_key(user_id, provider)

        try:
            self._redis.delete(key)
            return True
        except RedisError:
            return False

    def is_enabled(self) -> bool:
        """Proverava da li je rate limiting omogućen.

        Returns:
            True ako je Redis dostupan
        """
        try:
            self._redis.ping()
            return True
        except RedisError:
            return False


class QuizRateLimiter:
    """Specijalizovani rate limiter za quiz request-e.

    Podržava različite limite za različite operacije.
    """

    def __init__(self):
        self._limiter = RateLimiter()

        self.limits = {
            "generate_questions": 30,  # 30 quiz-eva u minutu
            "submit_attempt": 100,  # 100 pokušaja u minutu
            "list_quizzes": 200,  # 200 listanja u minutu
        }

    def check_generate(self, user_id: str) -> bool:
        """Proverava limit za generisanje pitanja."""
        return self._limiter.check_limit(
            user_id, "quiz_generate", self.limits["generate_questions"]
        )

    def check_submit(self, user_id: str) -> bool:
        """Proverava limit za submitovanje odgovora."""
        return self._limiter.check_limit(
            user_id, "quiz_submit", self.limits["submit_attempt"]
        )

    def check_list(self, user_id: str) -> bool:
        """Proverava limit za listanje kvizova."""
        return self._limiter.check_limit(
            user_id, "quiz_list", self.limits["list_quizzes"]
        )

    def get_wait_time(self, user_id: str, operation: str) -> int:
        """Vraća vreme čekanja pre ponovnog pokušaja."""
        op_key = {
            "generate_questions": "quiz_generate",
            "submit_attempt": "quiz_submit",
            "list_quizzes": "quiz_list",
        }.get(operation, "quiz_generate")

        return self._limiter.get_reset_time(user_id, op_key)
