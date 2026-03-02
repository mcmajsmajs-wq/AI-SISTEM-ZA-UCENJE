# -*- coding: utf-8 -*-
"""
================================================================================
STORAGE SERVICE — Lokalni fajl sistem
================================================================================
Servis za upravljanje fajlovima na lokalnom disku (uploads/).

Interfejs je identičan cloud verziji tako da se po potrebi može zameniti
cloud provajderom (S3, GCS, Azure Blob) bez izmena u ostatku koda.

Cloud storage: videti storage_cloud.py (posebna priča — boto3/S3 implementacija)

Verzija: 2.0.0
================================================================================
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    ================================================================================
    LOCAL STORAGE SERVICE
    ================================================================================
    Čuva fajlove na lokalnom fajl sistemu u UPLOAD_FOLDER direktorijumu.

    Struktura:
        uploads/
          <user_id>/
            <sha256_checksum>.<ext>   ← svaki fajl je jedinstven po sadržaju

    Metode su identične cloud verziji radi lakog prebacivanja.
    ================================================================================
    """

    def __init__(self, base_path: Optional[str] = None):
        """Inicijalizuje lokalni storage u zadatoj putanji."""
        self.base_path = Path(base_path or settings.UPLOAD_FOLDER)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._bucket_ready = True  # uvek True za lokalni storage
        logger.info(f"LocalStorageService initialized: {self.base_path}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Računa SHA256 checksum sadržaja fajla."""
        return hashlib.sha256(file_content).hexdigest()

    def _full_path(self, storage_path: str) -> Path:
        """Vraća apsolutnu putanju za dati storage_path."""
        return self.base_path / storage_path

    # ── Glavne operacije ──────────────────────────────────────────────────────

    def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upisuje fajl na lokalni disk.

        Returns:
            {'storage_path': str, 'checksum': str, 'size': int}
        """
        content = file_content.read()
        checksum = self.calculate_checksum(content)
        ext = Path(filename).suffix.lower()
        storage_path = f"{user_id}/{checksum}{ext}"

        dest = self._full_path(storage_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Ako već postoji isti sadržaj — nema potrebe upisivati ponovo
        if not dest.exists():
            dest.write_bytes(content)
            logger.info(f"Uploaded: {storage_path} ({len(content)} bytes)")
        else:
            logger.debug(f"Already exists (dedup): {storage_path}")

        return {
            'storage_path': storage_path,
            'checksum': checksum,
            'size': len(content)
        }

    def download_file(self, storage_path: str) -> bytes:
        """
        Čita fajl sa lokalnog diska.

        Raises:
            FileNotFoundError: Ako fajl ne postoji
        """
        path = self._full_path(storage_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found in local storage: {storage_path}")
        return path.read_bytes()

    def delete_file(self, storage_path: str) -> bool:
        """
        Briše fajl sa lokalnog diska.

        Returns:
            True (i ako fajl ne postoji — idempotentna operacija)
        """
        path = self._full_path(storage_path)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted: {storage_path}")
        return True

    def get_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600
    ) -> str:
        """
        Vraća URL za direktan download fajla putem API-ja.

        Za lokalni storage ovo je relativni URL na /api/v1/files/serve/{storage_path}.
        Za cloud: zameniti boto3 generate_presigned_url() pozivom.
        """
        # Koristimo API endpoint koji servira fajl direktno
        encoded = storage_path.replace("/", "%2F")
        return f"/api/v1/files/serve/{encoded}"

    def file_exists(self, storage_path: str) -> bool:
        """Proverava da li fajl postoji na disku."""
        return self._full_path(storage_path).exists()

    def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """
        Dohvata metadata fajla sa diska.

        Raises:
            FileNotFoundError: Ako fajl ne postoji
        """
        path = self._full_path(storage_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        stat = path.stat()
        return {
            'size': stat.st_size,
            'content_type': 'application/octet-stream',
            'last_modified': stat.st_mtime,
            'metadata': {}
        }


# Singleton instance
storage_service = StorageService()

