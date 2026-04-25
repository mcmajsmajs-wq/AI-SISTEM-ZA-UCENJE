# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
Storage Service
Verzija: 2.0.0
Autor: Branko Suznjevic
Datum: 2026
================================================================================
"""

import io
import hashlib
import logging
import os
import shutil
from typing import Optional, BinaryIO, Dict, Any
from datetime import timedelta
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, quote

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorageService:
    """
    ================================================================================
    LOCAL STORAGE SERVICE
    ================================================================================
    Servis za upravljanje fajlovima na lokalnom fajl sistemu.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje lokalni storage."""
        self.base_dir = Path(settings.LOCAL_STORAGE_PATH)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at: {self.base_dir}")
    
    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Računa SHA256 checksum fajla."""
        return hashlib.sha256(file_content).hexdigest()
    
    def _get_file_path(self, storage_path: str) -> Path:
        """Kreira punu putanju do fajla."""
        return self.base_dir / storage_path
    
    def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload-uje fajl na lokalni fajl sistem."""
        content = file_content.read()
        file_content.seek(0)
        
        checksum = self.calculate_checksum(content)
        file_ext = Path(filename).suffix
        storage_path = f"{user_id}/{checksum}{file_ext}"
        
        file_path = self._get_file_path(storage_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Uploaded file: {storage_path} ({len(content)} bytes)")
        
        return {
            'storage_path': storage_path,
            'checksum': checksum,
            'size': len(content)
        }
    
    def download_file(self, storage_path: str) -> bytes:
        """Download-uje fajl sa lokalnog fajl sistema."""
        file_path = self._get_file_path(storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    def delete_file(self, storage_path: str) -> bool:
        """Briše fajl sa lokalnog fajl sistema."""
        file_path = self._get_file_path(storage_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {storage_path}")
            return True
        return False
    
    def get_presigned_url(self, storage_path: str, expiration: int = 3600) -> str:
        """Generiše URL za lokalni fajl ( vraća relative path)."""
        return f"/files/{quote(storage_path)}"
    
    def file_exists(self, storage_path: str) -> bool:
        """Proverava da li fajl postoji."""
        return self._get_file_path(storage_path).exists()
    
    def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """Dohvata metadata fajla."""
        file_path = self._get_file_path(storage_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'content_type': 'application/octet-stream',
            'last_modified': datetime.fromtimestamp(stat.st_mtime),
            'metadata': {}
        }


class MinIOStorageService:
    """
    ================================================================================
    MINIO STORAGE SERVICE
    ================================================================================
    Servis za upravljanje fajlovima u MinIO/S3 storage-u.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje MinIO client."""
        import boto3
        from botocore.client import Config
        from botocore.exceptions import ClientError
        
        self._ClientError = ClientError
        self.client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Kreira bucket ako ne postoji."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except self._ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket '{self.bucket_name}'")
                except self._ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Računa SHA256 checksum fajla."""
        return hashlib.sha256(file_content).hexdigest()
    
    def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload-uje fajl u MinIO storage."""
        content = file_content.read()
        file_content.seek(0)
        
        checksum = self.calculate_checksum(content)
        file_ext = Path(filename).suffix
        storage_path = f"{user_id}/{checksum}{file_ext}"
        
        final_metadata = {
            'original-filename': filename,
            'user-id': user_id,
            'content-type': content_type
        }
        if metadata:
            final_metadata.update(metadata)
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=storage_path,
                Body=io.BytesIO(content),
                ContentLength=len(content),
                ContentType=content_type,
                Metadata=final_metadata
            )
            
            logger.info(f"Uploaded file: {storage_path} ({len(content)} bytes)")
            
            return {
                'storage_path': storage_path,
                'checksum': checksum,
                'size': len(content)
            }
            
        except self._ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def download_file(self, storage_path: str) -> bytes:
        """Download-uje fajl iz MinIO storage-a."""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return response['Body'].read()
            
        except self._ClientError as e:
            logger.error(f"Failed to download file {storage_path}: {e}")
            raise
    
    def delete_file(self, storage_path: str) -> bool:
        """Briše fajl iz MinIO storage-a."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            logger.info(f"Deleted file: {storage_path}")
            return True
            
        except self._ClientError as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")
            raise
    
    def get_presigned_url(self, storage_path: str, expiration: int = 3600) -> str:
        """Generiše pre-signed URL za download."""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_path
                },
                ExpiresIn=expiration
            )
            return url
            
        except self._ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def file_exists(self, storage_path: str) -> bool:
        """Proverava da li fajl postoji."""
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except self._ClientError:
            return False
    
    def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """Dohvata metadata fajla."""
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
        except self._ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise


class StorageService:
    """
    ================================================================================
    STORAGE SERVICE (Facade)
    ================================================================================
    Hibridni servis za upravljanje fajlovima - bira implementaciju na osnovu konfiguracije.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje odgovarajući storage service."""
        if settings.STORAGE_BACKEND == "local":
            self._storage = LocalStorageService()
            logger.info("Using LOCAL storage backend")
        else:
            self._storage = MinIOStorageService()
            logger.info("Using MINIO storage backend")
    
    def __getattr__(self, name: str):
        """Prosleđuje pozive ka odgovarajućem storage service-u."""
        return getattr(self._storage, name)
    
    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Računa SHA256 checksum fajla."""
        return hashlib.sha256(file_content).hexdigest()


# Singleton instance
storage_service = StorageService()
