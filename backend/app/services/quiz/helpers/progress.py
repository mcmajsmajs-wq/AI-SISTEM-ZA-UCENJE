# -*- coding: utf-8 -*-
"""
================================================================================
REDIS PROGRESS MODULE
================================================================================

Redis-based progress tracking for quiz generation.

Verzija: 1.0.0
================================================================================
"""

import json
import logging
from typing import Any, Dict, Optional

import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_redis() -> redis.Redis:
    """
    Kreira Redis konekciju.

    Returns:
        redis.Redis: Redis klijent
    """
    try:
        return redis.from_url(
            settings.REDIS_CONNECTION_URL,
            decode_responses=True
        )
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def update_quiz_progress(
    task_id: str,
    status: str,
    progress: int = 0,
    message: str = "",
    error: Optional[str] = None,
) -> bool:
    """
    Ažurira progress quiz taska u Redis.

    Args:
        task_id: ID taska
        status: Status ("started", "processing", "completed", "failed")
        progress: Progres (0-100)
        message: Poruka
        error: Greška (ako postoji)

    Returns:
        bool: True ako je uspešno
    """
    try:
        r = _get_redis()
        if not r:
            return False

        data = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "error": error,
        }

        r.setex(
            f"quiz_progress:{task_id}",
            3600,  # 1 hour TTL
            json.dumps(data)
        )

        return True
    except Exception as e:
        logger.error(f"Failed to update quiz progress: {e}")
        return False


def get_quiz_progress(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Dohvata progress quiz taska iz Redis.

    Args:
        task_id: ID taska

    Returns:
        Optional[Dict[str, Any]]: Progress podaci ili None
    """
    try:
        r = _get_redis()
        if not r:
            return None

        data = r.get(f"quiz_progress:{task_id}")
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get quiz progress: {e}")
        return None


def delete_quiz_progress(task_id: str) -> bool:
    """
    Briše progress podatke za task.

    Args:
        task_id: ID taska

    Returns:
        bool: True ako je uspešno
    """
    try:
        r = _get_redis()
        if not r:
            return False

        r.delete(f"quiz_progress:{task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete quiz progress: {e}")
        return False


def set_quiz_cache(user_id: int, key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Čuva podatke u Redis cache za korisnika.

    Args:
        user_id: ID korisnika
        key: Ključ
        value: Vrednost
        ttl: Time-to-live u sekundama

    Returns:
        bool: True ako je uspešno
    """
    try:
        r = _get_redis()
        if not r:
            return False

        cache_key = f"quiz_cache:{user_id}:{key}"
        r.setex(cache_key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Failed to set quiz cache: {e}")
        return False


def get_quiz_cache(user_id: int, key: str) -> Optional[Any]:
    """
    Dohvata podatke iz Redis cache za korisnika.

    Args:
        user_id: ID korisnika
        key: Ključ

    Returns:
        Optional[Any]: Cached vrednost ili None
    """
    try:
        r = _get_redis()
        if not r:
            return None

        cache_key = f"quiz_cache:{user_id}:{key}"
        data = r.get(cache_key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get quiz cache: {e}")
        return None


def clear_quiz_cache(user_id: int) -> bool:
    """
    Briše sve cache podatke za korisnika.

    Args:
        user_id: ID korisnika

    Returns:
        bool: True ako je uspešno
    """
    try:
        r = _get_redis()
        if not r:
            return False

        pattern = f"quiz_cache:{user_id}:*"
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
        return True
    except Exception as e:
        logger.error(f"Failed to clear quiz cache: {e}")
        return False
