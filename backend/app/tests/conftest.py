# -*- coding: utf-8 -*-
"""
================================================================================
PYTEST CONFIGURATION
================================================================================
Konfiguracija za testove - fixtures, hooks, i podesavanja.

Pokretanje testova:
    pytest                           # Svi testovi
    pytest -v                        # Verbose output
    pytest --cov=app                 # Sa coverage
    pytest tests/unit                # Samo unit testovi
    pytest tests/integration         # Samo integration testovi
================================================================================
"""

import os
import sys
from typing import Generator, AsyncGenerator
from datetime import datetime

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base
from app.db.models.user import User, UserSession
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.core.config import settings

# ── SQLite UUID compatibility ─────────────────────────────────────────────────
# PostgreSQL UUID type is not natively supported by SQLite.
# 1) DDL: render UUID columns as VARCHAR(36)
# 2) DML: patch bind_processor so WHERE uuid_col = :val works with str/UUID
import uuid as _uuid_mod
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

if not hasattr(SQLiteTypeCompiler, '_orig_visit_UUID'):
    SQLiteTypeCompiler._orig_visit_UUID = None
    SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: 'VARCHAR(36)'

_orig_pg_bind = PG_UUID.bind_processor

def _sqlite_safe_bind(self, dialect):
    if dialect.name == 'sqlite':
        def process(value):
            if value is None:
                return None
            return str(value)
        return process
    return _orig_pg_bind(self, dialect) if _orig_pg_bind else None

PG_UUID.bind_processor = _sqlite_safe_bind

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Kreira event loop za async testove."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Kreira test database session.
    Koristi in-memory SQLite za brze testove.
    """
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def clean_db(db: Session) -> Session:
    """Clean database - rollback nakon svakog testa."""
    yield db
    db.rollback()


@pytest.fixture
def test_user_data() -> dict:
    """Test podaci za korisnika."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_user(db: Session, test_user_data: dict) -> User:
    """Kreira test korisnika u bazi."""
    from app.services.auth import AuthService
    
    user = User(
        email=test_user_data["email"],
        hashed_password=AuthService.get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Generise JWT token za test korisnika."""
    from app.services.auth import AuthService
    
    token = AuthService.create_access_token(data={"sub": str(test_user.id)})
    return token


@pytest.fixture
def test_refresh_token(test_user: User) -> str:
    """Generise refresh token za test korisnika."""
    from app.services.auth import AuthService
    
    token = AuthService.create_refresh_token(data={"sub": str(test_user.id)})
    return token


@pytest.fixture
def test_file_data() -> dict:
    """Test podaci za fajl."""
    return {
        "original_filename": "Test Document.pdf",
        "storage_path": "uploads/test/test_document.pdf",
        "file_size": 1024 * 1024,  # 1MB
        "mime_type": "application/pdf",
        "checksum": "abc123def456",
        "status": "uploaded"
    }


@pytest.fixture
def test_file(db: Session, test_user: User, test_file_data: dict) -> File:
    """Kreira test fajl u bazi."""
    file = File(
        user_id=test_user.id,
        original_filename=test_file_data["original_filename"],
        storage_path=test_file_data["storage_path"],
        file_size=test_file_data["file_size"],
        mime_type=test_file_data["mime_type"],
        checksum=test_file_data["checksum"],
        status=test_file_data["status"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(file)
    db.commit()
    db.refresh(file)
    
    return file


@pytest.fixture
def test_document_data() -> dict:
    """Test podaci za dokument."""
    return {
        "title": "Test Document",
        "total_pages": 10,
        "total_chunks": 50,
        "source_language": "en",
        "target_language": "sr",
        "status": "completed"
    }


@pytest.fixture
def test_document(db: Session, test_file: File, test_document_data: dict) -> Document:
    """Kreira test dokument u bazi."""
    document = Document(
        file_id=test_file.id,
        user_id=test_file.user_id,
        title=test_document_data["title"],
        total_pages=test_document_data["total_pages"],
        total_chunks=test_document_data["total_chunks"],
        source_language=test_document_data["source_language"],
        target_language=test_document_data["target_language"],
        status=test_document_data["status"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document


@pytest.fixture
def test_chunks(db: Session, test_document: Document) -> list:
    """Kreira test chunks u bazi."""
    chunks = []
    
    for i in range(5):
        chunk = Chunk(
            document_id=test_document.id,
            sequence_number=i,
            content=f"This is test chunk number {i + 1}. It contains some English text for translation testing.",
            translated_content=f"Ovo je test odlomak broj {i + 1}. Sadrzi neki engleski tekst za testiranje prevoda." if i < 3 else None,
            is_translated=1 if i < 3 else 0,
            is_reviewed=0,
            heading_level=1 if i % 2 == 0 else 0,
            parent_heading=f"Section {i + 1}" if i % 2 == 0 else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(chunk)
        chunks.append(chunk)
    
    db.commit()
    
    for chunk in chunks:
        db.refresh(chunk)
    
    return chunks


@pytest.fixture
def mock_minio_client(mocker):
    """Mock MinIO client za testove."""
    mock_client = mocker.MagicMock()
    mock_client.bucket_exists.return_value = True
    mock_client.make_bucket.return_value = None
    mock_client.put_object.return_value = None
    mock_client.get_object.return_value = mocker.MagicMock(read=lambda: b"test content")
    mock_client.remove_object.return_value = None
    mock_client.presigned_get_object.return_value = "http://test-presigned-url.com/file.pdf"
    
    return mock_client


@pytest.fixture
def mock_redis_client(mocker):
    """Mock Redis client za testove."""
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = 0
    
    return mock_client


@pytest.fixture
def mock_ollama_client(mocker):
    """Mock Ollama client za testove."""
    mock_client = mocker.MagicMock()
    mock_client.generate.return_value = {
        "response": "Ovo je test prevod na srpski jezik."
    }
    
    return mock_client


class TestSettings:
    """Test settings override."""
    SECRET_KEY = "test-secret-key-for-testing"
    JWT_SECRET = "test-jwt-secret-key-for-testing"
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    DEBUG = True
    ENVIRONMENT = "testing"


@pytest.fixture
def test_settings():
    """Test settings instance."""
    return TestSettings()
