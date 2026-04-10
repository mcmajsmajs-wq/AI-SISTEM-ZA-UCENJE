# -*- coding: utf-8 -*-
"""
================================================================================
STORAGE SERVICE TESTS — Lokalni fajl sistem
================================================================================
Unit testovi za StorageService (lokalni disk, bez mock-ova).

Pokretanje:
    pytest tests/unit/test_storage.py -v
================================================================================
"""

import pytest
import tempfile
import os
from io import BytesIO
from pathlib import Path

from app.services.storage_local import StorageService


@pytest.fixture
def tmp_storage(tmp_path):
    """StorageService koji koristi privremeni direktorijum za testove."""
    return StorageService(base_path=str(tmp_path))


class TestStorageServiceInit:
    """Testovi za inicijalizaciju StorageService."""

    def test_init_creates_base_dir(self, tmp_path):
        """Test da __init__ kreira base direktorijum ako ne postoji."""
        new_dir = tmp_path / "new_storage"
        service = StorageService(base_path=str(new_dir))
        assert new_dir.exists()
        assert service._bucket_ready is True

    def test_init_with_existing_dir(self, tmp_path):
        """Test inicijalizacije sa postojećim direktorijumom."""
        service = StorageService(base_path=str(tmp_path))
        assert service.base_path == tmp_path


class TestFileUpload:
    """Testovi za upload fajlova."""

    def test_upload_file_success(self, tmp_storage, tmp_path):
        """Test uspešnog upload-a fajla."""
        content = b"Test PDF content"
        result = tmp_storage.upload_file(
            file_content=BytesIO(content),
            filename="test.pdf",
            user_id="user-123",
            content_type="application/pdf",
        )

        assert "storage_path" in result
        assert "checksum" in result
        assert result["size"] == len(content)
        assert result["storage_path"].startswith("user-123/")
        assert result["storage_path"].endswith(".pdf")

    def test_upload_creates_file_on_disk(self, tmp_storage):
        """Test da se fajl fizički upisuje na disk."""
        content = b"File content here"
        result = tmp_storage.upload_file(
            file_content=BytesIO(content), filename="doc.pdf", user_id="user-abc"
        )

        full_path = tmp_storage.base_path / result["storage_path"]
        assert full_path.exists()
        assert full_path.read_bytes() == content

    def test_upload_deduplication(self, tmp_storage):
        """Test da isti sadržaj daje isti storage_path (deduplikacija)."""
        content = b"Same content"
        r1 = tmp_storage.upload_file(BytesIO(content), "a.pdf", "user-1")
        r2 = tmp_storage.upload_file(BytesIO(content), "b.pdf", "user-1")
        assert r1["storage_path"] == r2["storage_path"]

    def test_upload_different_content_different_path(self, tmp_storage):
        """Test da različit sadržaj daje različit storage_path."""
        r1 = tmp_storage.upload_file(BytesIO(b"content1"), "a.pdf", "user-1")
        r2 = tmp_storage.upload_file(BytesIO(b"content2"), "a.pdf", "user-1")
        assert r1["storage_path"] != r2["storage_path"]

    def test_upload_large_file(self, tmp_storage):
        """Test upload velikog fajla (10MB)."""
        content = b"A" * (10 * 1024 * 1024)
        result = tmp_storage.upload_file(BytesIO(content), "large.pdf", "user-1")
        assert result["size"] == len(content)


class TestFileDownload:
    """Testovi za download fajlova."""

    def test_download_success(self, tmp_storage):
        """Test uspešnog download-a fajla."""
        content = b"Download me"
        result = tmp_storage.upload_file(BytesIO(content), "file.pdf", "u1")

        downloaded = tmp_storage.download_file(result["storage_path"])
        assert downloaded == content

    def test_download_nonexistent_raises(self, tmp_storage):
        """Test da download nepostojećeg fajla diže FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            tmp_storage.download_file("nonexistent/file.pdf")


class TestPresignedUrl:
    """Testovi za presigned URL."""

    def test_get_presigned_url_returns_string(self, tmp_storage):
        """Test da get_presigned_url vraća string URL."""
        content = b"content"
        result = tmp_storage.upload_file(BytesIO(content), "f.pdf", "u1")
        url = tmp_storage.get_presigned_url(result["storage_path"])
        assert isinstance(url, str)
        assert len(url) > 0

    def test_presigned_url_contains_path(self, tmp_storage):
        """Test da URL sadrži storage path."""
        url = tmp_storage.get_presigned_url("user-1/abc123.pdf")
        assert "abc123" in url


class TestFileDeletion:
    """Testovi za brisanje fajlova."""

    def test_delete_success(self, tmp_storage):
        """Test uspešnog brisanja fajla."""
        content = b"delete me"
        result = tmp_storage.upload_file(BytesIO(content), "del.pdf", "u1")
        full_path = tmp_storage.base_path / result["storage_path"]

        assert full_path.exists()
        ret = tmp_storage.delete_file(result["storage_path"])
        assert ret is True
        assert not full_path.exists()

    def test_delete_nonexistent_is_idempotent(self, tmp_storage):
        """Test da brisanje nepostojećeg fajla ne baca grešku."""
        ret = tmp_storage.delete_file("ghost/file.pdf")
        assert ret is True


class TestFileInfo:
    """Testovi za informacije o fajlu."""

    def test_file_exists_true(self, tmp_storage):
        """Test da file_exists vraća True za postojeći fajl."""
        content = b"exists"
        result = tmp_storage.upload_file(BytesIO(content), "e.pdf", "u1")
        assert tmp_storage.file_exists(result["storage_path"]) is True

    def test_file_exists_false(self, tmp_storage):
        """Test da file_exists vraća False za nepostojeći fajl."""
        assert tmp_storage.file_exists("no/such/file.pdf") is False

    def test_get_file_metadata(self, tmp_storage):
        """Test dohvatanja metadata fajla."""
        content = b"metadata test"
        result = tmp_storage.upload_file(BytesIO(content), "m.pdf", "u1")

        meta = tmp_storage.get_file_metadata(result["storage_path"])
        assert meta["size"] == len(content)
        assert "last_modified" in meta

    def test_get_file_metadata_nonexistent_raises(self, tmp_storage):
        """Test da metadata nepostojećeg fajla diže FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            tmp_storage.get_file_metadata("missing/file.pdf")


class TestChecksum:
    """Testovi za checksum računanje."""

    def test_checksum_is_sha256(self, tmp_storage):
        """Test da je checksum SHA256 (64 hex karaktera)."""
        checksum = StorageService.calculate_checksum(b"test data")
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_same_content_same_checksum(self, tmp_storage):
        """Test da isti sadržaj daje isti checksum."""
        c1 = StorageService.calculate_checksum(b"same")
        c2 = StorageService.calculate_checksum(b"same")
        assert c1 == c2

    def test_different_content_different_checksum(self, tmp_storage):
        """Test da različit sadržaj daje različit checksum."""
        c1 = StorageService.calculate_checksum(b"content1")
        c2 = StorageService.calculate_checksum(b"content2")
        assert c1 != c2
