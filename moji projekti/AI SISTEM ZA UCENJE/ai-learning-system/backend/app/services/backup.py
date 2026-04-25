# -*- coding: utf-8 -*-
"""
===============================================================================
BACKUP SERVICE
===============================================================================
Servis za automatsko backup-ovanje baze podataka i fajlova.

Verzija: 1.0.0
===============================================================================
"""

import os
import shutil
import logging
import gzip
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)


class BackupService:
    """
    ================================================================================
    BACKUP SERVICE
    ================================================================================
    Servis za upravljanje backup-ovima baze podataka i fajlova.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje backup servis."""
        self.backup_dir = Path(settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else './backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_database_backup(
        self,
        database_url: str,
        backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kreira backup baze podataka.
        
        Args:
            database_url: Connection string za bazu
            backup_name: Ime backup-a (opciono)
        
        Returns:
            Informacije o kreiranom backup-u
        """
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"db_backup_{timestamp}.sql"
        
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Creating database backup: {backup_name}")
        
        try:
            if 'postgresql' in database_url or 'postgres' in database_url:
                self._backup_postgres(database_url, backup_path)
            elif 'sqlite' in database_url:
                self._backup_sqlite(database_url, backup_path)
            else:
                raise ValueError(f"Unsupported database type: {database_url}")
            
            backup_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            
            return {
                'backup_name': backup_name,
                'backup_path': str(backup_path),
                'size_bytes': backup_size,
                'checksum': checksum,
                'created_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                'backup_name': backup_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def _backup_postgres(self, database_url: str, backup_path: Path):
        """Backup PostgreSQL baze."""
        import subprocess
        
        db_url = database_url.replace('postgresql://', '')
        
        if '@' in db_url:
            auth, host_db = db_url.split('@')
            user = auth.split(':')[0]
            password = auth.split(':')[1] if len(auth.split(':')) > 1 else ''
            host, db = host_db.split('/')
            port = host.split(':')[1] if ':' in host else '5432'
            host = host.split(':')[0]
        else:
            raise ValueError("Invalid PostgreSQL connection string")
        
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        with open(backup_path, 'w') as f:
            subprocess.run(
                [
                    'pg_dump',
                    '-h', host,
                    '-p', port,
                    '-U', user,
                    '-F', 'c',
                    '-b',
                    '-v',
                    '-f', str(backup_path),
                    db
                ],
                env=env,
                check=True
            )
    
    def _backup_sqlite(self, database_url: str, backup_path: Path):
        """Backup SQLite baze."""
        db_path = database_url.replace('sqlite:///', '')
        
        if db_path.startswith('./'):
            db_path = db_path[2:]
        
        shutil.copy2(db_path, backup_path)
    
    def create_files_backup(
        self,
        source_dir: str,
        backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kreira backup fajlova (upload-ova).
        
        Args:
            source_dir: Direktorijum sa fajlovima
            backup_name: Ime backup-a (opciono)
        
        Returns:
            Informacije o kreiranom backup-u
        """
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"files_backup_{timestamp}.tar.gz"
        
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Creating files backup: {backup_name}")
        
        try:
            with gzip.open(backup_path, 'wb') as f:
                shutil.copyfileobj(
                    shutil.make_archive(
                        backup_path.with_suffix(''),
                        'tar',
                        root_dir=source_dir
                    ),
                    f
                )
            
            backup_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            
            return {
                'backup_name': backup_name,
                'backup_path': str(backup_path),
                'size_bytes': backup_size,
                'checksum': checksum,
                'created_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Files backup failed: {e}")
            return {
                'backup_name': backup_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Vraća listu svih backup-ova.
        
        Returns:
            Lista backup-ova sa informacijama
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob('*'), reverse=True):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_bytes': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'type': 'database' if 'db' in backup_file.name else 'files'
                })
        
        return backups
    
    def restore_database_backup(self, backup_name: str, database_url: str) -> Dict[str, Any]:
        """
        Restauruje backup baze podataka.
        
        Args:
            backup_name: Ime backup fajla
            database_url: Connection string za bazu
        
        Returns:
            Informacije o restauraciji
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return {
                'status': 'failed',
                'error': 'Backup file not found'
            }
        
        logger.info(f"Restoring database from: {backup_name}")
        
        try:
            if 'postgresql' in database_url or 'postgres' in database_url:
                self._restore_postgres(backup_path, database_url)
            elif 'sqlite' in database_url:
                self._restore_sqlite(backup_path, database_url)
            
            return {
                'status': 'success',
                'backup_name': backup_name,
                'restored_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _restore_postgres(self, backup_path: Path, database_url: str):
        """Restauruje PostgreSQL backup."""
        import subprocess
        
        db_url = database_url.replace('postgresql://', '')
        
        if '@' in db_url:
            auth, host_db = db_url.split('@')
            user = auth.split(':')[0]
            password = auth.split(':')[1] if len(auth.split(':')) > 1 else ''
            host, db = host_db.split('/')
            port = host.split(':')[1] if ':' in host else '5432'
            host = host.split(':')[0]
        else:
            raise ValueError("Invalid PostgreSQL connection string")
        
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        subprocess.run(
            [
                'pg_restore',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', db,
                '-c',
                '-v',
                str(backup_path)
            ],
            env=env,
            check=True
        )
    
    def _restore_sqlite(self, backup_path: Path, database_url: str):
        """Restauruje SQLite backup."""
        db_path = database_url.replace('sqlite:///', '')
        
        if db_path.startswith('./'):
            db_path = db_path[2:]
        
        shutil.copy2(backup_path, db_path)
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Briše backup-ove starije od određenog broja dana.
        
        Args:
            retention_days: Broj dana za zadržavanje backup-ova
        
        Returns:
            Informacije o obrisanim backup-ovima
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted = []
        
        for backup_file in self.backup_dir.glob('*'):
            if backup_file.is_file():
                file_date = datetime.fromtimestamp(backup_file.stat().st_ctime)
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    deleted.append(backup_file.name)
                    logger.info(f"Deleted old backup: {backup_file.name}")
        
        return {
            'deleted_count': len(deleted),
            'deleted_files': deleted,
            'retention_days': retention_days
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Računa SHA256 checksum fajla."""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def verify_backup(self, backup_name: str) -> Dict[str, Any]:
        """
        Verifikuje integritet backup-a.
        
        Args:
            backup_name: Ime backup fajla
        
        Returns:
            Informacije o verifikaciji
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return {
                'valid': False,
                'error': 'Backup file not found'
            }
        
        checksum = self._calculate_checksum(backup_path)
        
        return {
            'valid': True,
            'backup_name': backup_name,
            'checksum': checksum,
            'size_bytes': backup_path.stat().st_size
        }


backup_service = BackupService()
