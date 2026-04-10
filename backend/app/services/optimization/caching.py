# -*- coding: utf-8 -*-
"""
================================================================================
CACHE SERVICE
================================================================================
FAZA 11: Cache servis sa TTL podrškom za Redis keširanje.

Omogućava keširanje rezultata sa vremenom isteka (TTL).
Podržava različite tipove podataka i automatsko čišćenje.

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-10
================================================================================
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta

import redis
from redis.exceptions import RedisError


class CacheService:
    """Cache servis sa TTL podrškom.

    Koristi Redis za keširanje podataka sa automatskim istekom.
    Podržava različite tipove podataka (JSON, pickle).

    Attributes:
        redis: Redis klijent
        default_ttl: Default vreme trajanja keša u sekundama
        serializer: Tip serializacije ('json' ili 'pickle')
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        serializer: str = "json",
    ):
        """Inicijalizuje cache servis.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL u sekundama (default: 1 sat)
            serializer: Tip serializacije ('json' ili 'pickle')
        """
        if redis_url is None:
            from app.core.config import settings

            redis_url = settings.REDIS_CONNECTION_URL

        self._redis = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = default_ttl
        self.serializer = serializer

    def _serialize(self, value: Any) -> bytes:
        """Serijalizuje vrednost za čuvanje u Redis.

        Args:
            value: Vrednost za serijalizaciju

        Returns:
            Serijalizovani bytes
        """
        if self.serializer == "json":
            return json.dumps(value).encode("utf-8")
        return pickle.dumps(value)

    def _deserialize(self, value: Optional[bytes]) -> Any:
        """Deserijalizuje vrednost iz Redis.

        Args:
            value: Bytes vrednost iz Redis

        Returns:
            Deserijalizovana vrednost
        """
        if value is None:
            return None

        if self.serializer == "json":
            try:
                return json.loads(value.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return None

    def _get_key(self, prefix: str, key: str) -> str:
        """Kreira Redis key sa prefiksom.

        Args:
            prefix: Prefiks za namespace (npr. 'quiz', 'user')
            key: Ključ

        Returns:
            Kompletan Redis key
        """
        return f"cache:{prefix}:{key}"

    def get(self, prefix: str, key: str) -> Optional[Any]:
        """Vraća vrednost iz keša.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ

        Returns:
            Keširana vrednost ili None ako ne postoji
        """
        full_key = self._get_key(prefix, key)

        try:
            value = self._redis.get(full_key)
            return self._deserialize(value)
        except RedisError:
            return None

    def set(
        self,
        prefix: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Čuva vrednost u keš sa TTL.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ
            value: Vrednost za čuvanje
            ttl: TTL u sekundama (default: default_ttl)

        Returns:
            True ako je uspešno sačuvano
        """
        full_key = self._get_key(prefix, key)
        ttl = ttl or self.default_ttl
        serialized = self._serialize(value)

        try:
            self._redis.setex(full_key, ttl, serialized)
            return True
        except RedisError:
            return False

    def delete(self, prefix: str, key: str) -> bool:
        """Briše vrednost iz keša.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ

        Returns:
            True ako je uspešno obrisano
        """
        full_key = self._get_key(prefix, key)

        try:
            self._redis.delete(full_key)
            return True
        except RedisError:
            return False

    def exists(self, prefix: str, key: str) -> bool:
        """Proverava da li key postoji u kešu.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ

        Returns:
            True ako postoji
        """
        full_key = self._get_key(prefix, key)

        try:
            return bool(self._redis.exists(full_key))
        except RedisError:
            return False

    def get_ttl(self, prefix: str, key: str) -> int:
        """Vraća preostalo TTL vreme u sekundama.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ

        Returns:
            Sekunde do isteka (0 ako ne postoji)
        """
        full_key = self._get_key(prefix, key)

        try:
            ttl = self._redis.ttl(full_key)
            return max(0, ttl)
        except RedisError:
            return 0

    def set_ttl(self, prefix: str, key: str, ttl: int) -> bool:
        """Ažurira TTL za postojeći key.

        Args:
            prefix: Prefiks namespace-a
            key: Ključ
            ttl: Novi TTL u sekundama

        Returns:
            True ako je uspešno ažurirano
        """
        full_key = self._get_key(prefix, key)

        try:
            return bool(self._redis.expire(full_key, ttl))
        except RedisError:
            return False

    def clear_prefix(self, prefix: str) -> int:
        """Briše sve keširane vrednosti za dati prefiks.

        Args:
            prefix: Prefiks namespace-a

        Returns:
            Broj obrisanih ključeva
        """
        pattern = f"cache:{prefix}:*"

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except RedisError:
            return 0

    def clear_all(self) -> int:
        """Briše sve keširane vrednosti.

        Returns:
            Broj obrisanih ključeva
        """
        pattern = "cache:*"

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except RedisError:
            return 0

    def get_stats(self) -> dict:
        """Vraća statistike keša.

        Returns:
            Dict sa statistikama
        """
        pattern = "cache:*"

        try:
            keys = self._redis.keys(pattern)
            total_keys = len(keys)

            info = self._redis.info("memory")
            used_memory = info.get("used_memory", 0)

            return {
                "total_keys": total_keys,
                "used_memory_bytes": used_memory,
                "used_memory_mb": round(used_memory / 1024 / 1024, 2),
            }
        except RedisError:
            return {"total_keys": 0, "used_memory_bytes": 0, "used_memory_mb": 0}

    def is_available(self) -> bool:
        """Proverava da li je Redis dostupan.

        Returns:
            True ako je dostupan
        """
        try:
            self._redis.ping()
            return True
        except RedisError:
            return False


class QuizCacheService(CacheService):
    """Specijalizovani cache za quiz servis.

    Automatski kešira česte quiz operacije.
    """

    def __init__(self):
        super().__init__(default_ttl=1800)  # 30 minuta
        self.prefixes = {
            "questions": "quiz:questions",
            "results": "quiz:results",
            "attempts": "quiz:attempts",
            "stats": "quiz:stats",
        }

    def cache_questions(
        self, user_id: str, quiz_id: str, questions: Any, ttl: int = 1800
    ) -> bool:
        """Kešira generisana pitanja.

        Args:
            user_id: ID korisnika
            quiz_id: ID kviza
            questions: Pitanja za keširanje
            ttl: TTL u sekundama

        Returns:
            True ako je keširano
        """
        key = f"{user_id}:{quiz_id}"
        return self.set("questions", key, questions, ttl)

    def get_cached_questions(self, user_id: str, quiz_id: str) -> Optional[Any]:
        """Vraća keširana pitanja.

        Args:
            user_id: ID korisnika
            quiz_id: ID kviza

        Returns:
            Keširana pitanja ili None
        """
        key = f"{user_id}:{quiz_id}"
        return self.get("questions", key)

    def invalidate_quiz(self, quiz_id: str) -> int:
        """Briše sav keš za dati quiz.

        Args:
            quiz_id: ID kviza

        Returns:
            Broj obrisanih ključeva
        """
        count = 0
        for prefix in self.prefixes.values():
            pattern = f"cache:{prefix}:*{quiz_id}"
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    count += self._redis.delete(*keys)
            except RedisError:
                pass
        return count


_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Vraća singleton instancu CacheService.

    Returns:
        CacheService instanca
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
