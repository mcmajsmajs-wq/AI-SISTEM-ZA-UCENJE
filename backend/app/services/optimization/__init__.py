# -*- coding: utf-8 -*-
"""
================================================================================
OPTIMIZATION SERVICES
================================================================================
FAZA 11: Performance Optimizations - Rate limiting, caching, connection pooling.

Modul za optimizaciju performansi sistema:
- Rate limiting po korisniku i provideru
- Caching sa TTL
- HTTP connection pooling

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-10
================================================================================
"""

from .rate_limiter import RateLimiter
from .caching import CacheService
from .connection_pool import ConnectionPool, get_http_client

__all__ = [
    "RateLimiter",
    "CacheService",
    "ConnectionPool",
    "get_http_client",
]
