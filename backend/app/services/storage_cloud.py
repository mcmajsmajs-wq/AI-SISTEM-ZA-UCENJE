# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
Cloud Storage Service (S3 / MinIO / AWS)
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026
================================================================================

Opciona cloud implementacija StorageService interfejsa.
Koristi boto3 (S3-compatible API).
"""

import io
import hashlib
import logging
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudStorageService:
    """
    S3-compatible cloud storage (AWS S3 / MinIO / DigitalOcean Spaces).
    Isti interfejs kao lokalni StorageService — zamenjivost bez izmena koda.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        use_ssl: bool = False,
    ):
        self.bucket_name = bucket_name or settings.MINIO_BUCKET_NAME
        _endpoint = endpoint or getattr(settings, "MINIO_ENDPOINT", None)
        _endpoint_url = (
            f"{'https' if use_ssl else 'http'}://{_endpoint}" if _endpoint else None
        )

        self.client = boto3.client(
            "s3",
            endpoint_url=_endpoint_url,
            aws_access_key_id=access_key or getattr(settings, "MINIO_ACCESS_KEY", None),
            aws_secret_access_key=secret_key
            or getattr(settings, "MINIO_SECRET_KEY", None),
            config=Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        self._bucket_ready = False
        try:
            self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"Cloud storage not ready at startup: {e}")

    def _ensure_bucket_exists(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            self._bucket_ready = True
            logger.info(f"S3 bucket '{self.bucket_name}' OK")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                self.client.create_bucket(Bucket=self.bucket_name)
                self._bucket_ready = True
                logger.info(f"Created S3 bucket '{self.bucket_name}'")
            else:
                raise

    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None,
        custom_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        content = file_content.read()
        checksum = self.calculate_checksum(content)
        ext = Path(filename).suffix.lower()

        # Use custom path if provided, otherwise generate default path
        if custom_path:
            storage_path = custom_path
        else:
            storage_path = f"{user_id}/{checksum}{ext}"

        s3_metadata = {"original-filename": filename, "user-id": user_id}
        if metadata:
            s3_metadata.update({k: str(v) for k, v in metadata.items()})

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=storage_path,
            Body=io.BytesIO(content),
            ContentLength=len(content),
            ContentType=content_type,
            Metadata=s3_metadata,
        )
        logger.info(f"[S3] Uploaded: {storage_path} ({len(content)} bytes)")
        return {
            "storage_path": storage_path,
            "checksum": checksum,
            "size": len(content),
        }

    def download_file(self, storage_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=storage_path)
        return response["Body"].read()

    def delete_file(self, storage_path: str) -> bool:
        self.client.delete_object(Bucket=self.bucket_name, Key=storage_path)
        logger.info(f"[S3] Deleted: {storage_path}")
        return True

    def get_presigned_url(self, storage_path: str, expiration: int = 3600) -> str:
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": storage_path},
            ExpiresIn=expiration,
        )
        # Replace internal MinIO URL with public proxy URL
        public_url = getattr(settings, "MINIO_PUBLIC_URL", None)
        if public_url:
            # Replace the internal endpoint with public URL
            internal_endpoint = (
                f"http://{settings.MINIO_ENDPOINT}"
                if not settings.MINIO_USE_SSL
                else f"https://{settings.MINIO_ENDPOINT}"
            )
            url = url.replace(internal_endpoint, public_url)
        elif "minio:" in url:
            # Fallback: replace minio:9000 with /minio/ path
            url = url.replace("http://minio:9000", "/minio")
        return url

    def get_public_url(self, storage_path: str) -> str:
        public_url = getattr(settings, "MINIO_PUBLIC_URL", None)
        if public_url:
            # MINIO_PUBLIC_URL should be like http://localhost:8081/minio
            # Format: http://localhost:8081/minio/ai-learning-uploads/path/to/file
            return f"{public_url}/{self.bucket_name}/{storage_path}"
        else:
            # Fallback: use /minio/ path
            return f"/minio/{self.bucket_name}/{storage_path}"

    def file_exists(self, storage_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=storage_path)
            return True
        except ClientError:
            return False

    def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        response = self.client.head_object(Bucket=self.bucket_name, Key=storage_path)
        return {
            "size": response.get("ContentLength"),
            "content_type": response.get("ContentType"),
            "last_modified": response.get("LastModified"),
            "metadata": response.get("Metadata", {}),
        }
