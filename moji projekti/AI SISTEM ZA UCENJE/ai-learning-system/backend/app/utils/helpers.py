# -*- coding: utf-8 -*-
"""
================================================================================
UTILITY FUNKCIJE
================================================================================
Pomoćne funkcije koje se koriste u celoj aplikaciji.

Verzija: 1.0.0
================================================================================
"""

import hashlib
import uuid
from datetime import datetime
from typing import Optional


def generate_uuid() -> str:
    """
    Generiše novi UUID.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def calculate_sha256(file_content: bytes) -> str:
    """
    Računa SHA256 hash fajla.
    
    Args:
        file_content: Sadržaj fajla u bytes
    
    Returns:
        SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Formatira veličinu fajla u čitljiv format.
    
    Args:
        size_bytes: Veličina u bajtovima
    
    Returns:
        Formatirani string (npr. "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitizuje ime fajla uklanjajući nedozvoljene karaktere.
    
    Args:
        filename: Originalno ime fajla
    
    Returns:
        Sanitizovano ime fajla
    """
    # Ukloni nedozvoljene karaktere
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def get_current_timestamp() -> str:
    """
    Vraća trenutni timestamp u ISO formatu.
    
    Returns:
        ISO format timestamp
    """
    return datetime.utcnow().isoformat()
