# -*- coding: utf-8 -*-
"""
================================================================================
KONFIGURACIJA APLIKACIJE
================================================================================
Centralizovana konfiguracija za sve environment-e.
Koristi Pydantic Settings za validaciju i učitavanje iz environment variables.

Verzija: 1.0.0
================================================================================
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """
    ================================================================================
    SETTINGS KLASA
    ================================================================================
    Definiše sve konfiguracione parametre aplikacije.
    Vrednosti se učitavaju iz environment variables sa fallback vrednostima.
    ================================================================================
    """

    # ================================================================================
    # APLIKACIJA
    # ================================================================================
    PROJECT_NAME: str = "AI Learning System"
    PROJECT_DESCRIPTION: str = (
        "Personalizovana aplikacija za učenje sa AI prevodom i kvizovima"
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # ================================================================================
    # LOGOVANJE
    # ================================================================================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json, text
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # ================================================================================
    # SECURITY
    # ================================================================================
    SECRET_KEY: str = "change-this-in-production"
    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ================================================================================
    # DATABASE
    # ================================================================================
    DATABASE_URL: str = "postgresql://ai_learning_user:password@db:5432/ai_learning_db"
    SQLALCHEMY_POOL_SIZE: int = 5
    SQLALCHEMY_MAX_OVERFLOW: int = 10
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 3600
    SQLALCHEMY_ECHO: bool = False

    # ================================================================================
    # REDIS
    # ================================================================================
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_CONNECTION_URL(self) -> str:
        """Generiše Redis connection string."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ================================================================================
    # STORAGE
    # ================================================================================
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    LOCAL_STORAGE_PATH: str = "/tmp/ai-learning-storage"  # Local storage path

    # ================================================================================
    # MINIO / S3
    # ================================================================================
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "ai-learning-uploads"
    MINIO_USE_SSL: bool = False
    # Public URL for frontend - if not set, uses internal endpoint
    MINIO_PUBLIC_URL: Optional[str] = None

    # Legacy compatibility
    CLOUD_STORAGE_ENDPOINT: Optional[str] = None
    CLOUD_STORAGE_ACCESS_KEY: Optional[str] = None
    CLOUD_STORAGE_SECRET_KEY: Optional[str] = None
    CLOUD_STORAGE_BUCKET_NAME: Optional[str] = None
    CLOUD_STORAGE_USE_SSL: bool = False

    # ================================================================================
    # AI / LLM
    # ================================================================================
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT: int = 60

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TIMEOUT: int = 60

    # DeepL (online translation)
    DEEPL_API_KEY: Optional[str] = None
    DEEPL_USE_PRO: bool = False  # True for Pro API
    DEEPL_TIMEOUT: int = 30

    # Google Translate
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    GOOGLE_TRANSLATE_TIMEOUT: int = 30

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-sonnet-20240229"
    CLAUDE_TIMEOUT: int = 60

    # DeepSeek AI
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TIMEOUT: int = 60

    # Groq AI
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT: int = 60

    # Mistral AI
    MISTRAL_API_KEY: Optional[str] = None

    # ================================================================================
    # SISTEMSKI AI KLIJUČEVI (FALLBACK)
    # ================================================================================
    # Ovi ključevi se koriste ako korisnik nema svoje
    SYSTEM_AI_PROVIDER: str = "groq"
    SYSTEM_GROQ_API_KEY: Optional[str] = None
    SYSTEM_OPENAI_API_KEY: Optional[str] = None
    SYSTEM_ANTHROPIC_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "mistral-small-latest"
    MISTRAL_TIMEOUT: int = 60

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TIMEOUT: int = 60

    # Translation settings
    TRANSLATION_PREFER_LOCAL: bool = True  # Prefer LibreTranslate (free)
    # Translation: LibreTranslate (free), DeepL (quality), Google (reliable), then AI as backup
    TRANSLATION_FALLBACK_ORDER: str = (
        "libretranslate,deepl,google,ollama,claude,gemini,groq,mistral,deepseek,openai"
    )

    # LibreTranslate settings (optional - can use public instance or self-hosted)
    LIBRETRANSLATE_URL: str = "https://libretranslate.com"  # Or your own instance
    LIBRETRANSLATE_API_KEY: Optional[str] = None  # Optional API key

    # ================================================================================
    # EMAIL
    # ================================================================================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAIL_FROM: str = "noreply@ai-learning.com"
    FRONTEND_URL: str = "http://localhost:5173"

    # ================================================================================
    # FILE UPLOAD
    # ================================================================================
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf",
        "txt",
        "docx",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "tiff",
        "webp",
    ]
    UPLOAD_FOLDER: str = "/tmp/ai-learning-uploads"

    # ================================================================================
    # CORS
    # ================================================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost",
    ]

    # ================================================================================
    # RATE LIMITING
    # ================================================================================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # ================================================================================
    # BACKUP
    # ================================================================================
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30

    # ================================================================================
    # POSTHOG
    # ================================================================================
    POSTHOG_API_KEY: Optional[str] = None
    POSTHOG_HOST: str = "https://eu.i.posthog.com"

    # ================================================================================
    # CELERY
    # ================================================================================
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def CELERY_CONFIG(self) -> dict:
        """Generiše Celery konfiguraciju."""
        return {
            "broker_url": self.CELERY_BROKER_URL or self.REDIS_CONNECTION_URL,
            "result_backend": self.CELERY_RESULT_BACKEND or self.REDIS_CONNECTION_URL,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "Europe/Belgrade",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": 3600,  # 1 hour
            "worker_prefetch_multiplier": 1,
            "broker_connection_retry_on_startup": True,
            "broker_connection_retry": True,
            "broker_connection_max_retries": 3,
            "broker_pool_limit": None,
            "task_default_queue": "default",
        }

    class Config:
        """Pydantic konfiguracija."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ================================================================================
# GLOBALNA INSTANCA SETTINGS
# ================================================================================
settings = Settings()
