# -*- coding: utf-8 -*-
"""
================================================================================
DATABASE SESSION
================================================================================
Upravljanje konekcijama ka bazi podataka.
Implementira connection pooling i session management.

Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

# ================================================================================
# ENGINE KONFIGURACIJA
# ================================================================================
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.SQLALCHEMY_POOL_SIZE,
    max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
    pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
    pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
    pool_pre_ping=True,  # Proveri konekciju pre korišćenja
    echo=settings.DEBUG  # Loguj SQL u debug modu
)

# ================================================================================
# SESSION FACTORY
# ================================================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ================================================================================
# DEPENDENCY INJECTION ZA FASTAPI
# ================================================================================
def get_db():
    """
    ================================================================================
    GET DATABASE SESSION
    ================================================================================
    Generator funkcija za FastAPI dependency injection.
    Automatski otvara i zatvara database session.
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    ================================================================================
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# ================================================================================
# HEALTH CHECK
# ================================================================================
def check_database_connection() -> bool:
    """
    ================================================================================
    CHECK DATABASE CONNECTION
    ================================================================================
    Proverava da li je konekcija ka bazi aktivna.
    Koristi se za health check endpoint.
    
    Returns:
        True ako je konekcija uspešna, False inače
    ================================================================================
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
