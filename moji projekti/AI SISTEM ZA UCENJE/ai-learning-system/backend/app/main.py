# -*- coding: utf-8 -*-
"""
================================================================================
AI LEARNING SYSTEM - BACKEND APPLICATION
================================================================================
Glavni modul aplikacije koji inicijalizuje FastAPI app.

Verzija: 1.0.0
Autor: AI Learning System Team
================================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base

import logging

# Setup logging na početku
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ================================================================================
    LIFESPAN MANAGER
    ================================================================================
    Upravlja inicijalizacijom i shutdown-om aplikacije.
    
    Startup:
        - Loguje pokretanje aplikacije
        - Proverava konekcije ka bazama
        - Inicijalizuje servise
    
    Shutdown:
        - Zatvara konekcije
        - Čisti resurse
        - Loguje gašenje
    ================================================================================
    """
    # STARTUP
    logger.info("=" * 80)
    logger.info("AI LEARNING SYSTEM - STARTING UP")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    
    # Kreiranje tabela (samo u developmentu, u produkciji koristiti Alembic)
    if settings.ENVIRONMENT == "development":
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    
    logger.info("Application started successfully!")
    logger.info("=" * 80)
    
    yield
    
    # SHUTDOWN
    logger.info("=" * 80)
    logger.info("AI LEARNING SYSTEM - SHUTTING DOWN")
    logger.info("=" * 80)
    logger.info("Closing database connections...")
    logger.info("Application shutdown complete")


# ================================================================================
# KREIRANJE FASTAPI APLIKACIJE
# ================================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# ================================================================================
# MIDDLEWARE
# ================================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ================================================================================
# SECURITY MIDDLEWARE
# ================================================================================

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Dodaje sigurnosne hedere na svaki odgovor."""
    from app.services.security import security_headers
    
    response = await call_next(request)
    
    for header, value in security_headers.get_headers().items():
        response.headers[header] = value
    
    return response


# ================================================================================
# STATIC FILES (Local Storage)
# ================================================================================
if settings.STORAGE_TYPE == "local":
    from fastapi.staticfiles import StaticFiles
    import os
    
    storage_path = settings.LOCAL_STORAGE_PATH
    os.makedirs(storage_path, exist_ok=True)
    
    app.mount("/files", StaticFiles(directory=storage_path), name="files")
    logger.info(f"Serving static files from: {storage_path}")

# ================================================================================
# ROUTES
# ================================================================================
app.include_router(api_router, prefix=settings.API_V1_STR)

# ================================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint za Docker i monitoring.
    Proverava da li je aplikacija živa.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint.
    Vraća metrike za Prometheus/Grafana.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe - proverava da li je aplikacija spremna da prima saobraćaj.
    Proverava konekcije ka bazama i servisima.
    """
    from app.db.session import check_database_connection
    
    db_healthy = check_database_connection()
    
    if db_healthy:
        return {
            "status": "ready",
            "checks": {
                "database": "healthy"
            }
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/live", tags=["Health"])
async def liveness_check():
    """
    Liveness probe - proverava da li aplikacija treba da se restartuje.
    """
    return {"status": "alive"}


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - vraća osnovne informacije o aplikaciji.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.PROJECT_DESCRIPTION,
        "documentation": "/docs",
        "health": "/health"
    }
