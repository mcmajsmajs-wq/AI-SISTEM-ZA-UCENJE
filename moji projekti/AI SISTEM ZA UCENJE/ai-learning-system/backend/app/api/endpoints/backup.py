# -*- coding: utf-8 -*-
"""
===============================================================================
BACKUP ENDPOINTS
===============================================================================
Endpoint-i za upravljanje backup-ovima.

Verzija: 1.0.0
===============================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user
from app.services.backup import backup_service
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def require_admin(current_user: User):
    """Proverava da li je korisnik admin."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/database")
async def create_database_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    CREATE DATABASE BACKUP
    ================================================================================
    Kreira backup baze podataka.
    ================================================================================
    """
    try:
        result = backup_service.create_database_backup(
            database_url=settings.DATABASE_URL
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "message": "Database backup created successfully",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Backup failed: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/files")
async def create_files_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    CREATE FILES BACKUP
    ================================================================================
    Kreira backup fajlova (upload-ova).
    ================================================================================
    """
    try:
        storage_path = settings.LOCAL_STORAGE_PATH if hasattr(settings, 'LOCAL_STORAGE_PATH') else './storage/uploads'
        
        result = backup_service.create_files_backup(
            source_dir=storage_path
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "message": "Files backup created successfully",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Backup failed: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Files backup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
async def list_backups(
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    LIST BACKUPS
    ================================================================================
    Vraća listu svih backup-ova.
    ================================================================================
    """
    try:
        backups = backup_service.list_backups()
        
        return {
            "status": "success",
            "data": {
                "backups": backups,
                "total": len(backups)
            }
        }
        
    except Exception as e:
        logger.error(f"List backups error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{backup_name}/download")
async def download_backup(
    backup_name: str,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    DOWNLOAD BACKUP
    ================================================================================
    Preuzima backup fajl.
    ================================================================================
    """
    backup_path = backup_service.backup_dir / backup_name
    
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found"
        )
    
    return FileResponse(
        path=str(backup_path),
        filename=backup_name,
        media_type='application/octet-stream'
    )


@router.post("/{backup_name}/restore")
async def restore_backup(
    backup_name: str,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    RESTORE BACKUP
    ================================================================================
    Restauruje backup baze podataka.
    ================================================================================
    """
    try:
        result = backup_service.restore_database_backup(
            backup_name=backup_name,
            database_url=settings.DATABASE_URL
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "message": "Database restored successfully",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Restore failed: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Restore error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{backup_name}/verify")
async def verify_backup(
    backup_name: str,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    VERIFY BACKUP
    ================================================================================
    Verifikuje integritet backup-a.
    ================================================================================
    """
    try:
        result = backup_service.verify_backup(backup_name)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Verify error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{backup_name}")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    DELETE BACKUP
    ================================================================================
    Briše backup fajl.
    ================================================================================
    """
    backup_path = backup_service.backup_dir / backup_name
    
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup file not found"
        )
    
    try:
        backup_path.unlink()
        
        return {
            "status": "success",
            "message": f"Backup {backup_name} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Delete backup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cleanup")
async def cleanup_old_backups(
    retention_days: int = 30,
    current_user: User = Depends(require_admin)
):
    """
    ================================================================================
    CLEANUP OLD BACKUPS
    ================================================================================
    Briše backup-ove starije od određenog broja dana.
    ================================================================================
    """
    try:
        result = backup_service.cleanup_old_backups(retention_days)
        
        return {
            "status": "success",
            "message": f"Cleaned up {result['deleted_count']} old backups",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
