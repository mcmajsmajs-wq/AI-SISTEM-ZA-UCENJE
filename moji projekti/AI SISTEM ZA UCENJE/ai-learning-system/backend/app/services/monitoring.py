# -*- coding: utf-8 -*-
"""
===============================================================================
MONITORING SERVICE
===============================================================================
Servis za prikupljanje metrika za Prometheus/Grafana.

Verzija: 1.0.0
===============================================================================
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response

from app.core.config import settings

logger = logging.getLogger(__name__)


request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users_total',
    'Total number of active users'
)

documents_processed = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['status']
)

quiz_attempts = Counter(
    'quiz_attempts_total',
    'Total number of quiz attempts',
    ['result']
)

translation_tokens = Counter(
    'translation_tokens_total',
    'Total number of translation tokens used',
    ['provider']
)

storage_usage_bytes = Gauge(
    'storage_usage_bytes',
    'Storage usage in bytes',
    ['storage_type']
)

task_duration = Histogram(
    'task_duration_seconds',
    'Task processing duration in seconds',
    ['task_type']
)


def track_request(method: str, endpoint: str):
    """Dekorator za praćenje HTTP zahteva."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(method=method, endpoint=endpoint, status=status).inc()
                request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        return wrapper
    return decorator


def record_document_processed(status: str):
    """Beleži obrađeni dokument."""
    documents_processed.labels(status=status).inc()


def record_quiz_attempt(result: str):
    """Beleži pokušaj kviza."""
    quiz_attempts.labels(result=result).inc()


def record_translation_tokens(provider: str, tokens: int):
    """Beleži potrošene tokene za prevod."""
    translation_tokens.labels(provider=provider).inc(tokens)


def set_active_users(count: int):
    """Postavlja broj aktivnih korisnika."""
    active_users.set(count)


def set_storage_usage(storage_type: str, bytes_used: int):
    """Postavlja korišćenje storage-a."""
    storage_usage_bytes.labels(storage_type=storage_type).set(bytes_used)


def track_task_duration(task_type: str):
    """Dekorator za praćenje trajanja zadataka."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                task_duration.labels(task_type=task_type).observe(duration)
                logger.debug(f"Task {task_type} took {duration:.2f}s")
        return wrapper
    return decorator


def create_metrics_app() -> FastAPI:
    """Kreira FastAPI app za metrics endpoint."""
    metrics_app = FastAPI()
    
    @metrics_app.get("/metrics")
    async def metrics():
        """Vraća Prometheus metrike."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    @metrics_app.get("/health")
    async def health():
        """Health check za metrics service."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return metrics_app


metrics_app = create_metrics_app()
