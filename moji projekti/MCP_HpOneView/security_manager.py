#!/usr/bin/env python3
"""
Security Manager for MCP_HpOneView Extended
Handles credential encryption, access control, and execution security
"""

import os
import sys
import json
import base64
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime, timedelta
from pathlib import Path
import secrets

class SecurityLevel(Enum):
    """Security levels for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityManager:
    """Manages security, credentials, and access control"""
    
    def __init__(self, config_file: str = "security_config.json"):
        self.config_file = config_file
        self.logger = self._setup_logging()
        self.config = self._load_config()
        self.fernet = self._initialize_encryption()
        self.session_tokens = {}
        self.audit_log = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup security logging"""
        logger = logging.getLogger("SecurityManager")
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [SECURITY] - %(message)s'
        )
        
        # File handler for security logs
        file_handler = logging.FileHandler("mcp_security.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        default_config = {
            "encryption": {
                "algorithm": "AES256",
                "key_derivation": "PBKDF2",
                "iterations": 100000
            },
            "access_control": {
                "max_failed_attempts": 3,
                "lockout_duration": 900,  # 15 minutes
                "session_timeout": 3600,   # 1 hour
                "require_mfa": False
            },
            "execution": {
                "allow_script_execution": True,
                "restricted_commands": [
                    "rm -rf /",
                    "dd if=/dev/zero",
                    "format",
                    "fdisk"
                ],
                "max_execution_time": 1800,  # 30 minutes
                "require_confirmation": [
                    SecurityLevel.HIGH,
                    SecurityLevel.CRITICAL
                ]
            },
            "audit": {
                "log_all_access": True,
                "log_script_execution": True,
                "log_failed_attempts": True,
                "retention_days": 90
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return {**default_config, **user_config}
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save security configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption with key derivation"""
        # Get or create encryption key
        key_file = "mcp_encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            password = self._get_master_password()
            salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config["encryption"]["iterations"],
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Save key and salt
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Save salt separately
            salt_file = key_file + ".salt"
            with open(salt_file, 'wb') as f:
                f.write(salt)
        
        return Fernet(key)
    
    def _get_master_password(self) -> str:
        """Get master password from environment or user input"""
        password = os.environ.get('MCP_MASTER_PASSWORD')
        if not password:
            # For now, use a default - in production, this should be more secure
            password = "default-mcp-master-password-2024"
            self.logger.warning("Using default master password - set MCP_MASTER_PASSWORD environment variable")
        return password
    
    def encrypt_credential(self, credential: str, credential_type: str = "general") -> str:
        """Encrypt credential and return encrypted string"""
        try:
            # Add metadata
            metadata = {
                "type": credential_type,
                "created": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            
            # Combine metadata and credential
            data = json.dumps({"metadata": metadata, "credential": credential})
            
            # Encrypt
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error encrypting credential: {e}")
            raise
    
    def decrypt_credential(self, encrypted_credential: str) -> str:
        """Decrypt credential and return plain text"""
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_credential.encode('utf-8'))
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(decrypted_data.decode('utf-8'))
            
            # Log access
            self._log_access("credential_decrypt", {
                "type": data.get("metadata", {}).get("type", "unknown"),
                "created": data.get("metadata", {}).get("created", "unknown")
            })
            
            return data["credential"]
            
        except Exception as e:
            self.logger.error(f"Error decrypting credential: {e}")
            raise
    
    def store_credential(self, name: str, credential: str, credential_type: str = "general"):
        """Store encrypted credential"""
        credentials_file = "mcp_credentials.json"
        
        try:
            # Load existing credentials
            credentials = {}
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    credentials = json.load(f)
            
            # Encrypt and store credential
            encrypted_credential = self.encrypt_credential(credential, credential_type)
            credentials[name] = {
                "encrypted": encrypted_credential,
                "type": credential_type,
                "created": datetime.utcnow().isoformat()
            }
            
            # Save credentials
            with open(credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            # Set file permissions (read/write only for owner)
            os.chmod(credentials_file, 0o600)
            
            self.logger.info(f"Credential '{name}' stored successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing credential: {e}")
            raise
    
    def get_credential(self, name: str) -> Optional[str]:
        """Retrieve and decrypt credential"""
        credentials_file = "mcp_credentials.json"
        
        try:
            if not os.path.exists(credentials_file):
                self.logger.error(f"Credentials file not found")
                return None
            
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
            
            if name not in credentials:
                self.logger.error(f"Credential '{name}' not found")
                return None
            
            encrypted_credential = credentials[name]["encrypted"]
            return self.decrypt_credential(encrypted_credential)
            
        except Exception as e:
            self.logger.error(f"Error retrieving credential: {e}")
            return None
    
    def generate_session_token(self, user_id: str, permissions: Optional[List[str]] = None) -> str:
        """Generate session token for user"""
        try:
            # Create token data
            token_data = {
                "user_id": user_id,
                "permissions": permissions or [],
                "created": datetime.utcnow().isoformat(),
                "expires": (datetime.utcnow() + timedelta(seconds=self.config["access_control"]["session_timeout"])).isoformat(),
                "nonce": secrets.token_urlsafe(32)
            }
            
            # Create token
            token_data_str = json.dumps(token_data)
            token = base64.urlsafe_b64encode(token_data_str.encode('utf-8')).decode('utf-8')
            
            # Store session
            self.session_tokens[token] = token_data
            
            self.logger.info(f"Session token generated for user: {user_id}")
            
            return token
            
        except Exception as e:
            self.logger.error(f"Error generating session token: {e}")
            raise
    
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token"""
        try:
            if token not in self.session_tokens:
                return None
            
            token_data = self.session_tokens[token]
            
            # Check expiration
            expires = datetime.fromisoformat(token_data["expires"])
            if datetime.utcnow() > expires:
                del self.session_tokens[token]
                return None
            
            return token_data
            
        except Exception as e:
            self.logger.error(f"Error validating session token: {e}")
            return None
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        token_data = self.validate_session_token(token)
        if not token_data:
            return False
        
        permissions = token_data.get("permissions", [])
        return required_permission in permissions
    
    def validate_script_execution(self, script_path: str, security_level: SecurityLevel) -> bool:
        """Validate if script execution is allowed"""
        try:
            # Check if script execution is allowed
            if not self.config["execution"]["allow_script_execution"]:
                self.logger.warning("Script execution is disabled")
                return False
            
            # Check restricted commands
            restricted_commands = self.config["execution"]["restricted_commands"]
            script_content = self._read_script_content(script_path)
            
            for restricted_cmd in restricted_commands:
                if restricted_cmd in script_content:
                    self.logger.error(f"Restricted command found: {restricted_cmd}")
                    return False
            
            # Check if confirmation is required
            if security_level in self.config["execution"]["require_confirmation"]:
                self.logger.info(f"Confirmation required for security level: {security_level.value}")
                # In production, this would trigger user confirmation
                return self._request_user_confirmation(script_path, security_level)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating script execution: {e}")
            return False
    
    def _read_script_content(self, script_path: str) -> str:
        """Read script content for validation"""
        try:
            with open(script_path, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading script content: {e}")
            return ""
    
    def _request_user_confirmation(self, script_path: str, security_level: SecurityLevel) -> bool:
        """Request user confirmation for script execution"""
        # For now, return True - in production, this would prompt the user
        self.logger.info(f"User confirmation requested for {script_path} (security level: {security_level.value})")
        return True
    
    def _log_access(self, action: str, details: Dict[str, Any] = None):
        """Log security access"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details or {}
        }
        
        self.audit_log.append(log_entry)
        
        # Log to file if enabled
        if self.config["audit"]["log_all_access"]:
            self.logger.info(f"Security access: {action} - {details}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:]
    
    def cleanup_expired_sessions(self):
        """Clean up expired session tokens"""
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, token_data in self.session_tokens.items():
            expires = datetime.fromisoformat(token_data["expires"])
            if current_time > expires:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.session_tokens[token]
        
        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")

# Example usage
if __name__ == "__main__":
    # Test security manager
    security = SecurityManager()
    
    # Test credential encryption/decryption
    test_credential = "test_password_123"
    encrypted = security.encrypt_credential(test_credential, "test")
    decrypted = security.decrypt_credential(encrypted)
    
    print(f"Original: {test_credential}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_credential == decrypted}")
    
    # Test session token
    token = security.generate_session_token("test_user", ["read", "write"])
    print(f"Token: {token}")
    
    token_data = security.validate_session_token(token)
    print(f"Token valid: {token_data is not None}")
    
    if token_data:
        print(f"User ID: {token_data['user_id']}")
        print(f"Permissions: {token_data['permissions']}")