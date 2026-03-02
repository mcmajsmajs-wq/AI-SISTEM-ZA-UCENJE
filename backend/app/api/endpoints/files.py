# -*- coding: utf-8 -*-
"""
================================================================================
FILES ENDPOINTS
================================================================================
Endpoint-i za upravljanje fajlovima.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid
from pathlib import Path
from io import BytesIO

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.file import File as FileModel
from app.schemas.file import FileResponse, FileUploadResponse, FileListResponse
from app.core.config import settings
from app.services.auth import get_current_user
from app.services.storage import storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {'.pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    UPLOAD FAJLA
    ================================================================================
    Uploaduje PDF fajl za obradu.
    
    Validacije:
        - Mora biti PDF format
        - Maksimalna veličina: 50MB
        - Provera na malware (todo)
    
    Args:
        file: UploadFile objekat
        current_user: Trenutno ulogovani korisnik
        db: Database session
    
    Returns:
        FileUploadResponse sa ID-jem i statusom
    ================================================================================
    """
    logger.info(f"File upload started: {file.filename} by user {current_user.email}")
    
    # Validacija ekstenzije
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Invalid file extension: {file_ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
        )
    
    # Čitanje sadržaja
    content = await file.read()
    file_size = len(content)
    
    # Validacija veličine
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB. Got: {file_size // 1024 // 1024}MB"
        )
    
    # Upload u MinIO
    try:
        upload_result = storage_service.upload_file(
            file_content=BytesIO(content),
            filename=file.filename,
            user_id=str(current_user.id),
            content_type=file.content_type or "application/pdf"
        )
    except Exception as e:
        logger.error(f"Failed to upload to storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
    
    # Kreiranje zapisa u bazi
    db_file = FileModel(
        user_id=current_user.id,
        original_filename=file.filename,
        storage_path=upload_result['storage_path'],
        file_size=file_size,
        mime_type=file.content_type or "application/pdf",
        checksum=upload_result['checksum'],
        status="uploaded",
        metadata={
            'original_size': file_size,
            'upload_source': 'web'
        }
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info(f"File uploaded successfully: {db_file.id}")
    
    return FileUploadResponse(
        id=str(db_file.id),
        filename=db_file.original_filename,
        size=db_file.file_size,
        status=db_file.status,
        message="File uploaded successfully"
    )


@router.get("/", response_model=FileListResponse)
async def list_files(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    LIST FILES
    ================================================================================
    Vraća listu fajlova korisnika sa paginacijom.
    ================================================================================
    """
    logger.debug(f"Listing files for user: {current_user.email}")
    
    # Query za ukupan broj
    total = db.query(FileModel).filter(
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).count()
    
    # Query sa paginacijom
    files = db.query(FileModel).filter(
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).order_by(FileModel.created_at.desc()).offset(skip).limit(limit).all()
    
    return FileListResponse(
        items=[
            FileResponse(
                id=str(f.id),
                filename=f.original_filename,
                size=f.file_size,
                mime_type=f.mime_type,
                status=f.status,
                created_at=f.created_at
            )
            for f in files
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET FILE DETAILS
    ================================================================================
    Vraća detalje o fajlu.
    ================================================================================
    """
    logger.debug(f"Fetching file: {file_id}")
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    db_file = db.query(FileModel).filter(
        FileModel.id == file_uuid,
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        id=str(db_file.id),
        filename=db_file.original_filename,
        size=db_file.file_size,
        mime_type=db_file.mime_type,
        status=db_file.status,
        created_at=db_file.created_at
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    DOWNLOAD FILE
    ================================================================================
    Preuzima fajl iz MinIO storage-a.
    ================================================================================
    """
    logger.info(f"Download requested for file: {file_id}")
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    db_file = db.query(FileModel).filter(
        FileModel.id == file_uuid,
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        content = storage_service.download_file(db_file.storage_path)
    except Exception as e:
        logger.error(f"Failed to download from storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )
    
    return StreamingResponse(
        BytesIO(content),
        media_type=db_file.mime_type,
        headers={
            'Content-Disposition': f'attachment; filename="{db_file.original_filename}"'
        }
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    DELETE FILE
    ================================================================================
    Briše fajl (soft delete).
    ================================================================================
    """
    logger.warning(f"File deletion requested: {file_id}")
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    db_file = db.query(FileModel).filter(
        FileModel.id == file_uuid,
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Soft delete
    from datetime import datetime
    db_file.deleted_at = datetime.utcnow()
    db_file.status = "deleted"
    db.commit()
    
    logger.info(f"File soft deleted: {file_id}")
    
    return None


@router.get("/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET FILE STATUS
    ================================================================================
    Vraća status obrade fajla.
    ================================================================================
    """
    logger.debug(f"Checking status for file: {file_id}")
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    db_file = db.query(FileModel).filter(
        FileModel.id == file_uuid,
        FileModel.user_id == current_user.id
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {
        "file_id": str(db_file.id),
        "filename": db_file.original_filename,
        "status": db_file.status,
        "progress": 100 if db_file.status == "uploaded" else 0,
        "message": f"File is {db_file.status}",
        "created_at": db_file.created_at.isoformat() if db_file.created_at else None,
        "updated_at": db_file.updated_at.isoformat() if db_file.updated_at else None
    }


@router.get("/{file_id}/presigned-url")
async def get_presigned_url(
    file_id: str,
    expiration: int = 3600,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ================================================================================
    GET PRESIGNED URL
    ================================================================================
    Generiše pre-signed URL za direktan download.
    ================================================================================
    """
    logger.debug(f"Generating presigned URL for file: {file_id}")
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    db_file = db.query(FileModel).filter(
        FileModel.id == file_uuid,
        FileModel.user_id == current_user.id,
        FileModel.deleted_at.is_(None)
    ).first()
    
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        url = storage_service.get_presigned_url(
            db_file.storage_path,
            expiration=expiration
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )
    
    return {
        "url": url,
        "expires_in": expiration,
        "filename": db_file.original_filename
    }
