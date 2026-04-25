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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base
# Registrovanje svih modela za create_all
from app.db.models.user import User, UserSession  # noqa
from app.db.models.file import File  # noqa
from app.db.models.document import Document, Chunk  # noqa
from app.db.models.quiz import Quiz, Question, QuizAttempt, QuizAnswer  # noqa
from app.db.models.study_plan import StudyPlan, StudyPlanItem  # noqa
from app.db.models.conversation import Conversation, Message  # noqa
from app.workers.celery_app import celery_app  # noqa: ensure celery app is registered

# Import automatic migration utility
from app.utils.database_migration import check_and_add_missing_columns, verify_database_health

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
    
    # Automatska provera i migracija kolona (radi i u produkciji)
    if verify_database_health():
        try:
            check_and_add_missing_columns()
        except Exception as e:
            logger.warning(f"Automatska migracija nije uspela: {e}")
            logger.warning("Aplikacija će pokušati da nastavi bez automatske migracije")
    else:
        logger.error("Baza podataka nije dostupna!")
    
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
# RATE LIMITER
# ================================================================================
limiter = Limiter(key_func=get_remote_address)

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
# ROUTES
# ================================================================================
app.include_router(api_router, prefix=settings.API_V1_STR)

# ================================================================================
# HEALTH CHECK ENDPOINTS
# ================================================================================

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
