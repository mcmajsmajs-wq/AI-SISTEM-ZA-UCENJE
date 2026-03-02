# -*- coding: utf-8 -*-
"""
================================================================================
HEALTH ENDPOINTS
================================================================================
Endpoint-i za proveru zdravlja sistema.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, status
from datetime import datetime
import platform
import sys

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Osnovni health check endpoint.
    Vraća status aplikacije i osnovne informacije.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "python_version": sys.version,
        "platform": platform.platform()
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness probe - proverava da li je aplikacija spremna.
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "not_implemented_yet",
            "redis": "not_implemented_yet"
        }
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe - proverava da li aplikacija treba restart.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
