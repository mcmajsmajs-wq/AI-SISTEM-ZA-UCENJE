# -*- coding: utf-8 -*-
"""
================================================================================
LOGOVANJE KONFIGURACIJA
================================================================================
Centralizovana konfiguracija za logovanje u aplikaciji.
Podržava JSON i tekstualni format logova.

Verzija: 1.0.0
================================================================================
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    ================================================================================
    JSON FORMATTER
    ================================================================================
    Formatira logove u JSON format za lakšu analizu i obradu.

    Struktura:
        {
            "timestamp": "2024-01-15T10:30:00.123456",
            "level": "INFO",
            "logger": "app.module",
            "message": "Log message",
            "module": "module_name",
            "function": "function_name",
            "line": 42,
            "thread": 12345,
            "extra": { ... }
        }
    ================================================================================
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formatira log record u JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
        }

        # Dodaj exception info ako postoji
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Dodaj extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # Dodaj sve ostale atribute koji počinju sa '_'
        for key, value in record.__dict__.items():
            if key.startswith('_') and key not in ['_name', '_level', '_msg']:
                log_data[key[1:]] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """
    ================================================================================
    COLORED FORMATTER
    ================================================================================
    Formatira logove sa bojama za development.
    Pogodno za čitanje u terminalu.
    ================================================================================
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        """Formatira log record sa bojama."""
        # Dodaj boju
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logging() -> None:
    """
    ================================================================================
    SETUP LOGGING
    ================================================================================
    Inicijalizuje logging sistem za celu aplikaciju.

    Konfiguriše:
        - Root logger sa zadatim log level-om
        - Console handler (sa bojama u dev, bez u prod)
        - File handler (rotating, JSON format)
        - Filters za različite nivoe logova
    ================================================================================
    """
    # Kreiraj logs direktorijum ako ne postoji
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Ukloni postojeće handlere da izbegnemo dupliranje
    root_logger.handlers = []

    # ================================================================================
    # CONSOLE HANDLER
    # ================================================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if settings.DEBUG:
        # Development: colored text format
        console_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Production: simple text format
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_formatter = logging.Formatter(console_format)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ================================================================================
    # FILE HANDLER (JSON)
    # ================================================================================
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    if settings.LOG_FORMAT == "json":
        file_formatter = JSONFormatter()
    else:
        file_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        file_formatter = logging.Formatter(file_format)

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # ================================================================================
    # ERROR FILE HANDLER
    # ================================================================================
    error_file = Path(settings.LOG_FILE).parent / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter() if settings.LOG_FORMAT == "json" else logging.Formatter())
    root_logger.addHandler(error_handler)

    # ================================================================================
    # THIRD-PARTY LOGGER CONFIGURATION
    # ================================================================================
    # Smanji log level za previše verbose biblioteke
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

    # Log successful setup
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.debug(f"Log level: {settings.LOG_LEVEL}")
    logger.debug(f"Log format: {settings.LOG_FORMAT}")
    logger.debug(f"Log file: {settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """
    ================================================================================
    GET LOGGER
    ================================================================================
    Factory funkcija za kreiranje loggera sa dodatnim funkcionalnostima.

    Args:
        name: Ime loggera (obično __name__)

    Returns:
        Logger instanca
    ================================================================================
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    ================================================================================
    LOGGER MIXIN
    ================================================================================
    Mixin klasa za dodavanje loggera bilo kojoj klasi.

    Usage:
        class MyService(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something")
    ================================================================================
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
