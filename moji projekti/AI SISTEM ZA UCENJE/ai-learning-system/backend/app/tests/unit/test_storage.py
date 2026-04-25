# -*- coding: utf-8 -*-
"""
================================================================================
STORAGE SERVICE TESTS
================================================================================
Unit testovi za StorageService - MinIO/S3 integracija.

Pokretanje:
    pytest tests/unit/test_storage.py -v
================================================================================
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from io import BytesIO

from app.services.storage import StorageService


class TestStorageServiceInit:
    """Testovi za inicijalizaciju StorageService."""
    
    def test_init_with_settings(self, test_settings):
        """Test inicijalizacije sa settings."""
        with patch('app.services.storage.Minio') as mock_minio:
            service = StorageService(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket_name="test-bucket",
                use_ssl=False
            )
            
            assert service.bucket_name == "test-bucket"
            mock_minio.assert_called_once()
    
    def test_ensure_bucket_exists(self, mock_minio_client):
        """Test da se bucket kreira ako ne postoji."""
        with patch('app.services.storage.Minio', return_value=mock_minio_client):
            mock_minio_client.bucket_exists.return_value = False
            
            service = StorageService(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket_name="new-bucket",
                use_ssl=False
            )
            
            mock_minio_client.make_bucket.assert_called_once_with("new-bucket")


class TestFileUpload:
    """Testovi za upload fajlova."""
    
    @patch('app.services.storage.Minio')
    def test_upload_file_success(self, mock_minio_class):
        """Test uspesnog upload-a fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        file_content = b"Test file content"
        filename = "test_document.pdf"
        
        result = service.upload_file(
            file_data=BytesIO(file_content),
            filename=filename,
            content_type="application/pdf",
            size=len(file_content)
        )
        
        assert result is not None
        assert filename in result
        mock_client.put_object.assert_called_once()
    
    @patch('app.services.storage.Minio')
    def test_upload_large_file(self, mock_minio_class):
        """Test upload velikog fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        large_content = b"A" * (10 * 1024 * 1024)
        
        result = service.upload_file(
            file_data=BytesIO(large_content),
            filename="large_file.pdf",
            content_type="application/pdf",
            size=len(large_content)
        )
        
        assert result is not None
    
    @patch('app.services.storage.Minio')
    def test_upload_generates_unique_filename(self, mock_minio_class):
        """Test da se generise jedinstveno ime fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        result1 = service.upload_file(
            file_data=BytesIO(b"content1"),
            filename="same_name.pdf",
            content_type="application/pdf",
            size=8
        )
        
        result2 = service.upload_file(
            file_data=BytesIO(b"content2"),
            filename="same_name.pdf",
            content_type="application/pdf",
            size=8
        )
        
        assert result1 != result2


class TestFileDownload:
    """Testovi za download fajlova."""
    
    @patch('app.services.storage.Minio')
    def test_download_file_success(self, mock_minio_class):
        """Test uspesnog download-a fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.get_object.return_value = MagicMock(
            read=lambda: b"Test file content"
        )
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        content = service.download_file("test_document.pdf")
        
        assert content == b"Test file content"
        mock_client.get_object.assert_called_once_with(
            "test-bucket",
            "test_document.pdf"
        )
    
    @patch('app.services.storage.Minio')
    def test_download_nonexistent_file(self, mock_minio_class):
        """Test download nepostojeceg fajla."""
        from minio.error import S3Error
        
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.get_object.side_effect = S3Error(
            "NoSuchKey", "Object does not exist", "", 404, ""
        )
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        with pytest.raises(Exception):
            service.download_file("nonexistent.pdf")


class TestPresignedUrl:
    """Testovi za presigned URL."""
    
    @patch('app.services.storage.Minio')
    def test_get_presigned_url(self, mock_minio_class):
        """Test generisanja presigned URL-a."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://test-url.com/file.pdf?signature=abc"
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        url = service.get_presigned_url("test_document.pdf", expires=3600)
        
        assert url is not None
        assert "test-url.com" in url
        mock_client.presigned_get_object.assert_called_once()
    
    @patch('app.services.storage.Minio')
    def test_get_presigned_url_custom_expiry(self, mock_minio_class):
        """Test presigned URL sa custom expiry."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://test-url.com/file.pdf"
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        url = service.get_presigned_url("test_document.pdf", expires=7200)
        
        assert url is not None


class TestFileDeletion:
    """Testovi za brisanje fajlova."""
    
    @patch('app.services.storage.Minio')
    def test_delete_file_success(self, mock_minio_class):
        """Test uspesnog brisanja fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        service.delete_file("test_document.pdf")
        
        mock_client.remove_object.assert_called_once_with(
            "test-bucket",
            "test_document.pdf"
        )
    
    @patch('app.services.storage.Minio')
    def test_delete_nonexistent_file_no_error(self, mock_minio_class):
        """Test da brisanje nepostojeceg fajla ne baca gresku."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        service.delete_file("nonexistent.pdf")
        
        mock_client.remove_object.assert_called_once()


class TestFileInfo:
    """Testovi za informacije o fajlu."""
    
    @patch('app.services.storage.Minio')
    def test_file_exists_true(self, mock_minio_class):
        """Test provere da fajl postoji."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.return_value = MagicMock(size=1024)
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        exists = service.file_exists("test_document.pdf")
        
        assert exists is True
    
    @patch('app.services.storage.Minio')
    def test_file_exists_false(self, mock_minio_class):
        """Test provere da fajl ne postoji."""
        from minio.error import S3Error
        
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.side_effect = S3Error(
            "NoSuchKey", "Object does not exist", "", 404, ""
        )
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        exists = service.file_exists("nonexistent.pdf")
        
        assert exists is False
    
    @patch('app.services.storage.Minio')
    def test_get_file_size(self, mock_minio_class):
        """Test dohvatanja velicine fajla."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.return_value = MagicMock(size=1024 * 1024)
        mock_minio_class.return_value = mock_client
        
        service = StorageService(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            use_ssl=False
        )
        
        size = service.get_file_size("test_document.pdf")
        
        assert size == 1024 * 1024
