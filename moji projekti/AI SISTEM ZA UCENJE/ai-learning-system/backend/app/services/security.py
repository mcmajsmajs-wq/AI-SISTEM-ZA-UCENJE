# -*- coding: utf-8 -*-
"""
===============================================================================
SECURITY SERVICE
===============================================================================
Servis za sigurnosne funkcionalnosti: rate limiting, JWT blacklist, input sanitization.

Verzija: 1.0.0
===============================================================================
"""

import time
import logging
import hashlib
import re
from typing import Optional, Set, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Konfiguracija za rate limiting."""
    max_requests: int
    window_seconds: int
    block_duration: int = 300


class RateLimiter:
    """
    ================================================================================
    RATE LIMITER
    ================================================================================
    Implementacija rate limiting-a za API endpointe.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje rate limiter."""
        self._requests: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, datetime] = {}
        self._config = RateLimitConfig(
            max_requests=settings.RATE_LIMIT_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW,
        )
    
    def _get_client_id(self, user_id: Optional[str] = None, ip: Optional[str] = None) -> str:
        """Generiše jedinstven ID za klijenta."""
        if user_id:
            return f"user:{user_id}"
        elif ip:
            return f"ip:{ip}"
        return "anonymous"
    
    def is_blocked(self, client_id: str) -> bool:
        """Proverava da li je klijent blokiran."""
        if client_id in self._blocked:
            if datetime.now() < self._blocked[client_id]:
                return True
            else:
                del self._blocked[client_id]
        return False
    
    def get_remaining_time(self, client_id: str) -> int:
        """Vraća preostalo vreme do deblokade u sekundama."""
        if client_id in self._blocked:
            remaining = (self._blocked[client_id] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
    
    def check_rate_limit(
        self,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> tuple[bool, int]:
        """
        Proverava rate limit za klijenta.
        
        Returns:
            (is_allowed, remaining_requests)
        """
        client_id = self._get_client_id(user_id, ip)
        
        if self.is_blocked(client_id):
            return False, 0
        
        now = time.time()
        window_start = now - self._config.window_seconds
        
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > window_start
        ]
        
        if len(self._requests[client_id]) >= self._config.max_requests:
            self._blocked[client_id] = datetime.now() + timedelta(
                seconds=self._config.block_duration
            )
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False, 0
        
        self._requests[client_id].append(now)
        
        remaining = self._config.max_requests - len(self._requests[client_id])
        return True, remaining
    
    def reset(self, client_id: str):
        """Resetuje rate limit za klijenta."""
        if client_id in self._requests:
            del self._requests[client_id]
        if client_id in self._blocked:
            del self._blocked[client_id]


class JWTBlacklist:
    """
    ================================================================================
    JWT BLACKLIST
    ================================================================================
    Upravljanje crnom listom JWT token-a.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje JWT blacklist."""
        self._blacklist: Set[str] = set()
        self._expiry: Dict[str, datetime] = {}
    
    def add(self, token_jti: str, expires_at: datetime):
        """Dodaje token na crnu listu."""
        self._blacklist.add(token_jti)
        self._expiry[token_jti] = expires_at
        logger.info(f"Token added to blacklist: {token_jti}")
    
    def is_blacklisted(self, token_jti: str) -> bool:
        """Proverava da li je token na crnoj listi."""
        if token_jti not in self._blacklist:
            return False
        
        if token_jti in self._expiry:
            if datetime.now() > self._expiry[token_jti]:
                self._blacklist.discard(token_jti)
                self._expiry.pop(token_jti, None)
                return False
        
        return True
    
    def cleanup(self):
        """Čisti istekle unose iz crne liste."""
        now = datetime.now()
        expired = [
            jti for jti, expiry in self._expiry.items()
            if now > expiry
        ]
        
        for jti in expired:
            self._blacklist.discard(jti)
            self._expiry.pop(jti, None)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tokens from blacklist")


class InputSanitizer:
    """
    ================================================================================
    INPUT SANITIZER
    ================================================================================
    Sanitizacija korisničkog unosa.
    ================================================================================
    """
    
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>',
    ]
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Uklanja opasne HTML elemente."""
        sanitized = text
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        return sanitized
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitizuje ime fajla."""
        sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
        sanitized = re.sub(r'[\s]+', '_', sanitized)
        return sanitized[:255]
    
    @classmethod
    def sanitize_sql(cls, text: str) -> str:
        """Escapuje SQL karaktere (kao dodatna zaštita)."""
        return text.replace("'", "''").replace(";", "")
    
    @classmethod
    def truncate(cls, text: str, max_length: int = 10000) -> str:
        """Ograničava dužinu teksta."""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text


class SecurityHeaders:
    """
    ================================================================================
    SECURITY HEADERS
    ================================================================================
    Klasa za generisanje sigurnosnih hedera.
    ================================================================================
    """
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Vraća sigurnosne hedere."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }


rate_limiter = RateLimiter()
jwt_blacklist = JWTBlacklist()
security_headers = SecurityHeaders()
