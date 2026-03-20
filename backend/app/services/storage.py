# -*- coding: utf-8 -*-
"""
================================================================================
STORAGE SERVICE — Unified storage interface
================================================================================
Supports both local filesystem and S3-compatible (MinIO) storage.
The storage backend is determined by the STORAGE_BACKEND setting.

Verzija: 3.0.0
================================================================================
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import both storage backends
from app.services.storage_local import StorageService as LocalStorageService
from app.services.storage_cloud import CloudStorageService

# Alias for backwards compatibility
from app.services.storage_local import StorageService


def get_storage_service():
    """
    Factory function that returns the appropriate storage service based on configuration.
    """
    backend = getattr(settings, 'STORAGE_BACKEND', 'local') or 'local'
    
    # Check for legacy CLOUD_STORAGE settings
    cloud_endpoint = getattr(settings, 'CLOUD_STORAGE_ENDPOINT', None)
    
    if backend == 's3' or cloud_endpoint:
        logger.info("Using S3/MinIO storage backend")
        # Get settings from CLOUD_STORAGE or fall back to MINIO settings
        # Note: Don't include protocol prefix - the cloud service adds it
        endpoint = getattr(settings, 'CLOUD_STORAGE_ENDPOINT', None)
        if endpoint:
            endpoint = endpoint.replace('http://', '').replace('https://', '')
        endpoint = endpoint or settings.MINIO_ENDPOINT
        access_key = getattr(settings, 'CLOUD_STORAGE_ACCESS_KEY', None) or settings.MINIO_ACCESS_KEY
        secret_key = getattr(settings, 'CLOUD_STORAGE_SECRET_KEY', None) or settings.MINIO_SECRET_KEY
        bucket = getattr(settings, 'CLOUD_STORAGE_BUCKET_NAME', None) or settings.MINIO_BUCKET_NAME
        use_ssl = getattr(settings, 'CLOUD_STORAGE_USE_SSL', None) or settings.MINIO_USE_SSL
        
        return CloudStorageService(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket_name=bucket,
            use_ssl=use_ssl
        )
    else:
        logger.info("Using local storage backend")
        return LocalStorageService()


# Singleton instance - uses the appropriate backend
storage_service = get_storage_service()
