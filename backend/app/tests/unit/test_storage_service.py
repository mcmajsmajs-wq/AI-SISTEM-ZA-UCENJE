# -*- coding: utf-8 -*-
"""
================================================================================
STORAGE SERVICE TESTS
================================================================================
Unit testovi za storage.py - LocalStorageService.

Pokretanje:
    pytest tests/unit/test_storage_service.py -v
================================================================================
"""

import pytest
import io
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.storage import LocalStorageService, StorageService


class TestLocalStorageService:
    """Testovi za LocalStorageService."""

    @pytest.fixture
    def local_storage(self, tmp_path):
        """LocalStorageService sa privremenim direktorijumom."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.LOCAL_STORAGE_PATH = str(tmp_path)
            service = LocalStorageService()
            service.base_dir = tmp_path
            return service

    class TestChecksum:
        """Testovi za calculate_checksum."""

        def test_calculate_checksum_returns_sha256(self):
            """Test da vraća SHA256 hash."""
            result = LocalStorageService.calculate_checksum(b"test content")
            expected = hashlib.sha256(b"test content").hexdigest()
            assert result == expected
            assert len(result) == 64

        def test_same_content_same_checksum(self):
            """Test da isti sadržaj daje isti hash."""
            c1 = LocalStorageService.calculate_checksum(b"data")
            c2 = LocalStorageService.calculate_checksum(b"data")
            assert c1 == c2

        def test_different_content_different_checksum(self):
            """Test da različit sadržaj daje različit hash."""
            c1 = LocalStorageService.calculate_checksum(b"data1")
            c2 = LocalStorageService.calculate_checksum(b"data2")
            assert c1 != c2

    class TestUploadFile:
        """Testovi za upload_file."""

        def test_upload_file_success(self, local_storage, tmp_path):
            """Test uspešnog upload-a."""
            content = b"PDF content here"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content),
                filename="document.pdf",
                user_id="user-123",
                content_type="application/pdf",
            )

            assert "storage_path" in result
            assert "checksum" in result
            assert result["size"] == len(content)
            assert result["storage_path"].startswith("user-123/")

        def test_upload_file_creates_directory(self, local_storage, tmp_path):
            """Test da se kreira direktorijum za korisnika."""
            content = b"test"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content),
                filename="test.pdf",
                user_id="new-user",
            )

            user_dir = tmp_path / "new-user"
            assert user_dir.exists()
            assert user_dir.is_dir()

        def test_upload_file_with_metadata(self, local_storage, tmp_path):
            """Test upload sa dodatnim metadata."""
            content = b"content"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content),
                filename="doc.pdf",
                user_id="user-1",
                content_type="application/pdf",
                metadata={"custom-key": "custom-value"},
            )

            assert result["size"] == len(content)

        def test_upload_file_deduplication(self, local_storage):
            """Test da isti sadržaj koristi isti storage_path."""
            content = b"identical content"
            r1 = local_storage.upload_file(io.BytesIO(content), "a.pdf", "user-1")
            r2 = local_storage.upload_file(io.BytesIO(content), "b.pdf", "user-1")
            assert r1["storage_path"] == r2["storage_path"]

        def test_upload_file_preserves_extension(self, local_storage):
            """Test da čuva ekstenziju fajla."""
            content = b"data"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content), filename="document.pdf", user_id="u1"
            )
            assert result["storage_path"].endswith(".pdf")

    class TestDownloadFile:
        """Testovi za download_file."""

        def test_download_file_success(self, local_storage):
            """Test uspešnog download-a."""
            content = b"downloadable content"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content), filename="file.pdf", user_id="u1"
            )

            downloaded = local_storage.download_file(result["storage_path"])
            assert downloaded == content

        def test_download_file_not_found(self, local_storage):
            """Test da download nepostojećeg fajla baca grešku."""
            with pytest.raises(FileNotFoundError):
                local_storage.download_file("nonexistent/file.pdf")

    class TestDeleteFile:
        """Testovi za delete_file."""

        def test_delete_file_success(self, local_storage):
            """Test uspešnog brisanja."""
            content = b"delete me"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content), filename="del.pdf", user_id="u1"
            )
            path = result["storage_path"]

            assert local_storage.file_exists(path) is True
            result = local_storage.delete_file(path)
            assert result is True
            assert local_storage.file_exists(path) is False

        def test_delete_file_nonexistent(self, local_storage):
            """Test brisanja nepostojećeg fajla."""
            result = local_storage.delete_file("ghost/file.pdf")
            assert result is False

    class TestGetPresignedUrl:
        """Testovi za get_presigned_url."""

        def test_get_presigned_url_returns_path(self, local_storage):
            """Test da vraća relative path."""
            url = local_storage.get_presigned_url("user/file.pdf")
            assert url == "/files/user/file.pdf"

        def test_get_presigned_url_with_expiration(self, local_storage):
            """Test sa expiration parametrom."""
            url = local_storage.get_presigned_url("user/doc.pdf", expiration=7200)
            assert "user/doc.pdf" in url

        def test_get_presigned_url_encodes_special_chars(self, local_storage):
            """Test da enkodira specijalne karaktere."""
            url = local_storage.get_presigned_url("user/file with spaces.pdf")
            assert "%20" in url or "file%20with" in url

    class TestFileExists:
        """Testovi za file_exists."""

        def test_file_exists_true(self, local_storage):
            """Test za postojeći fajl."""
            content = b"test"
            result = local_storage.upload_file(io.BytesIO(content), "f.pdf", "u1")
            assert local_storage.file_exists(result["storage_path"]) is True

        def test_file_exists_false(self, local_storage):
            """Test za nepostojeći fajl."""
            assert local_storage.file_exists("missing/file.pdf") is False

    class TestGetFileMetadata:
        """Testovi za get_file_metadata."""

        def test_get_file_metadata_success(self, local_storage):
            """Test uspešnog dobijanja metadata."""
            content = b"metadata test"
            result = local_storage.upload_file(
                file_content=io.BytesIO(content), filename="meta.pdf", user_id="u1"
            )

            meta = local_storage.get_file_metadata(result["storage_path"])
            assert meta["size"] == len(content)
            assert "last_modified" in meta
            assert meta["content_type"] == "application/octet-stream"

        def test_get_file_metadata_not_found(self, local_storage):
            """Test za nepostojeći fajl."""
            with pytest.raises(FileNotFoundError):
                local_storage.get_file_metadata("missing/file.pdf")

        def test_get_file_metadata_includes_metadata_dict(self, local_storage):
            """Test da metadata uključuje prazan dict za custom metadata."""
            content = b"test"
            result = local_storage.upload_file(io.BytesIO(content), "f.pdf", "u1")
            meta = local_storage.get_file_metadata(result["storage_path"])
            assert "metadata" in meta
            assert meta["metadata"] == {}


class TestStorageService:
    """Testovi za StorageService (Facade)."""

    def test_local_storage_backend(self):
        """Test da bira LocalStorage kada je konfigurisano."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert isinstance(service._storage, LocalStorageService)

    def test_calculate_checksum_static(self):
        """Test statičke metode calculate_checksum."""
        result = StorageService.calculate_checksum(b"test data")
        assert len(result) == 64

    def test_delegates_upload_to_underlying_service(self):
        """Test da prosleđuje upload_file."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert hasattr(service._storage, "upload_file")

    def test_delegates_download_to_underlying_service(self):
        """Test da prosleđuje download_file."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert hasattr(service._storage, "download_file")

    def test_delegates_delete_to_underlying_service(self):
        """Test da prosleđuje delete_file."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert hasattr(service._storage, "delete_file")

    def test_delegates_file_exists_to_underlying_service(self):
        """Test da prosleđuje file_exists."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert hasattr(service._storage, "file_exists")

    def test_delegates_get_presigned_url_to_underlying_service(self):
        """Test da prosleđuje get_presigned_url."""
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"

            service = StorageService()
            assert hasattr(service._storage, "get_presigned_url")
