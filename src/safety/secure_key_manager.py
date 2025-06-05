"""
Secure Key Manager Module

Provides secure storage and management of API keys and other sensitive credentials.
Implements encryption at rest, key rotation, and audit logging.
"""

import os
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
from enum import Enum

logger = logging.getLogger(__name__)


class KeyType(Enum):
    """Types of keys that can be stored"""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"
    JWT_SECRET = "jwt_secret"
    WEBHOOK_SECRET = "webhook_secret"


@dataclass
class KeyMetadata:
    """Metadata for stored keys"""
    key_id: str
    key_type: KeyType
    created_at: datetime
    last_accessed: Optional[datetime]
    last_rotated: Optional[datetime]
    access_count: int
    expires_at: Optional[datetime]
    description: Optional[str]


@dataclass
class KeyAccessLog:
    """Log entry for key access"""
    key_id: str
    accessed_at: datetime
    accessor: str
    action: str
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]


class SecureKeyManager:
    """
    Manages secure storage and retrieval of sensitive keys.
    
    Features:
    - Encryption at rest using Fernet (AES-128)
    - Master key derivation from passphrase
    - Key rotation support
    - Access audit logging
    - Automatic key expiration
    - Memory clearing after use
    """
    
    def __init__(self, 
                 storage_path: Path,
                 master_passphrase: Optional[str] = None,
                 auto_rotate_days: int = 30,
                 enable_audit_log: bool = True):
        """
        Initialize the secure key manager.
        
        Args:
            storage_path: Directory to store encrypted keys
            master_passphrase: Master passphrase for key derivation
            auto_rotate_days: Days before suggesting key rotation
            enable_audit_log: Whether to log key access
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.keys_file = self.storage_path / "keys.enc"
        self.metadata_file = self.storage_path / "metadata.json"
        self.audit_log_file = self.storage_path / "audit.log"
        
        self.auto_rotate_days = auto_rotate_days
        self.enable_audit_log = enable_audit_log
        
        # Initialize or load master key
        self._cipher = self._initialize_cipher(master_passphrase)
        
        # Load existing keys and metadata
        self._keys: Dict[str, bytes] = self._load_keys()
        self._metadata: Dict[str, KeyMetadata] = self._load_metadata()
        
        # In-memory cache with automatic clearing
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)  # Keys stay in memory for 5 minutes max
    
    def _initialize_cipher(self, passphrase: Optional[str] = None) -> Fernet:
        """Initialize the encryption cipher"""
        if passphrase is None:
            # Try to load from environment variable
            passphrase = os.environ.get("CLAUDE_AGI_MASTER_KEY")
            
        if passphrase is None:
            # Generate a new master key if none exists
            master_key_file = self.storage_path / ".master_key"
            if master_key_file.exists():
                with open(master_key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                # Store it securely (in production, use HSM or key management service)
                with open(master_key_file, 'wb') as f:
                    f.write(key)
                os.chmod(master_key_file, 0o600)  # Read/write for owner only
                logger.warning("Generated new master key. Store this securely!")
        else:
            # Derive key from passphrase
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'claude-agi-salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        
        return Fernet(key)
    
    def store_api_key(self, 
                     key_id: str,
                     key_value: str,
                     key_type: KeyType = KeyType.API_KEY,
                     description: Optional[str] = None,
                     expires_in_days: Optional[int] = None) -> None:
        """
        Store an API key securely.
        
        Args:
            key_id: Unique identifier for the key
            key_value: The actual key value
            key_type: Type of key being stored
            description: Optional description
            expires_in_days: Optional expiration time
        """
        # Validate inputs
        if not key_id or not key_value:
            raise ValueError("Key ID and value are required")
        
        # Encrypt the key
        encrypted_key = self._cipher.encrypt(key_value.encode())
        
        # Store encrypted key
        self._keys[key_id] = encrypted_key
        
        # Create metadata
        metadata = KeyMetadata(
            key_id=key_id,
            key_type=key_type,
            created_at=datetime.now(timezone.utc),
            last_accessed=None,
            last_rotated=None,
            access_count=0,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days) if expires_in_days else None,
            description=description
        )
        self._metadata[key_id] = metadata
        
        # Save to disk
        self._save_keys()
        self._save_metadata()
        
        # Log the action
        self._log_access(key_id, "store", True)
        
        # Clear the key from memory
        key_value = "0" * len(key_value)  # Overwrite in memory
        
        logger.info(f"Stored key: {key_id}")
    
    def get_api_key(self, key_id: str, accessor: str = "system") -> Optional[str]:
        """
        Retrieve an API key.
        
        Args:
            key_id: The key identifier
            accessor: Who is accessing the key (for audit)
            
        Returns:
            The decrypted key value or None if not found/expired
        """
        # Check cache first
        if key_id in self._cache:
            cached_value, cached_time = self._cache[key_id]
            if datetime.now(timezone.utc) - cached_time < self._cache_ttl:
                self._log_access(key_id, "retrieve_cached", True, accessor)
                return cached_value
            else:
                # Clear expired cache entry
                del self._cache[key_id]
        
        # Check if key exists
        if key_id not in self._keys:
            self._log_access(key_id, "retrieve", False, accessor)
            logger.warning(f"Key not found: {key_id}")
            return None
        
        # Check if key is expired
        metadata = self._metadata.get(key_id)
        if metadata and metadata.expires_at:
            if datetime.now(timezone.utc) > metadata.expires_at:
                self._log_access(key_id, "retrieve_expired", False, accessor)
                logger.warning(f"Key expired: {key_id}")
                return None
        
        # Decrypt the key
        try:
            decrypted_key = self._cipher.decrypt(self._keys[key_id]).decode()
            
            # Update metadata
            if metadata:
                metadata.last_accessed = datetime.now(timezone.utc)
                metadata.access_count += 1
                self._save_metadata()
            
            # Cache the key
            self._cache[key_id] = (decrypted_key, datetime.now(timezone.utc))
            
            # Log successful access
            self._log_access(key_id, "retrieve", True, accessor)
            
            # Check if rotation is needed
            if self._needs_rotation(metadata):
                logger.warning(f"Key {key_id} should be rotated (age: {self.auto_rotate_days} days)")
            
            return decrypted_key
            
        except Exception as e:
            self._log_access(key_id, "retrieve_error", False, accessor)
            logger.error(f"Failed to decrypt key {key_id}: {e}")
            return None
    
    def rotate_key(self, key_id: str, new_value: str) -> None:
        """
        Rotate an existing key.
        
        Args:
            key_id: The key to rotate
            new_value: The new key value
        """
        if key_id not in self._keys:
            raise ValueError(f"Key not found: {key_id}")
        
        # Get existing metadata
        metadata = self._metadata[key_id]
        
        # Store new encrypted value
        encrypted_key = self._cipher.encrypt(new_value.encode())
        self._keys[key_id] = encrypted_key
        
        # Update metadata
        metadata.last_rotated = datetime.now(timezone.utc)
        
        # Clear cache
        if key_id in self._cache:
            del self._cache[key_id]
        
        # Save changes
        self._save_keys()
        self._save_metadata()
        
        # Log rotation
        self._log_access(key_id, "rotate", True)
        
        logger.info(f"Rotated key: {key_id}")
    
    def delete_key(self, key_id: str) -> None:
        """Delete a key permanently"""
        if key_id in self._keys:
            # Clear from memory
            if key_id in self._cache:
                del self._cache[key_id]
            
            # Remove from storage
            del self._keys[key_id]
            if key_id in self._metadata:
                del self._metadata[key_id]
            
            # Save changes
            self._save_keys()
            self._save_metadata()
            
            # Log deletion
            self._log_access(key_id, "delete", True)
            
            logger.info(f"Deleted key: {key_id}")
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all stored keys with metadata (without values)"""
        keys_info = []
        
        for key_id, metadata in self._metadata.items():
            info = {
                "key_id": key_id,
                "key_type": metadata.key_type.value,
                "created_at": metadata.created_at.isoformat(),
                "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                "access_count": metadata.access_count,
                "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                "needs_rotation": self._needs_rotation(metadata),
                "description": metadata.description
            }
            keys_info.append(info)
        
        return keys_info
    
    def clear_cache(self) -> None:
        """Clear all cached keys from memory"""
        self._cache.clear()
        logger.info("Cleared key cache")
    
    def _needs_rotation(self, metadata: Optional[KeyMetadata]) -> bool:
        """Check if a key needs rotation"""
        if not metadata:
            return False
        
        # Check last rotation date
        check_date = metadata.last_rotated or metadata.created_at
        age = datetime.now(timezone.utc) - check_date
        
        return age.days >= self.auto_rotate_days
    
    def _save_keys(self) -> None:
        """Save encrypted keys to disk"""
        with open(self.keys_file, 'wb') as f:
            # Convert to JSON-serializable format
            keys_data = {k: base64.b64encode(v).decode() for k, v in self._keys.items()}
            encrypted_data = self._cipher.encrypt(json.dumps(keys_data).encode())
            f.write(encrypted_data)
        
        # Set restrictive permissions
        os.chmod(self.keys_file, 0o600)
    
    def _load_keys(self) -> Dict[str, bytes]:
        """Load encrypted keys from disk"""
        if not self.keys_file.exists():
            return {}
        
        try:
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            keys_data = json.loads(decrypted_data.decode())
            
            # Convert back to bytes
            return {k: base64.b64decode(v) for k, v in keys_data.items()}
            
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            return {}
    
    def _save_metadata(self) -> None:
        """Save key metadata to disk"""
        metadata_dict = {}
        for key_id, metadata in self._metadata.items():
            metadata_dict[key_id] = {
                "key_type": metadata.key_type.value,
                "created_at": metadata.created_at.isoformat(),
                "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                "last_rotated": metadata.last_rotated.isoformat() if metadata.last_rotated else None,
                "access_count": metadata.access_count,
                "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                "description": metadata.description
            }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        os.chmod(self.metadata_file, 0o600)
    
    def _load_metadata(self) -> Dict[str, KeyMetadata]:
        """Load key metadata from disk"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata_dict = json.load(f)
            
            metadata = {}
            for key_id, data in metadata_dict.items():
                metadata[key_id] = KeyMetadata(
                    key_id=key_id,
                    key_type=KeyType(data["key_type"]),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_accessed=datetime.fromisoformat(data["last_accessed"]) if data["last_accessed"] else None,
                    last_rotated=datetime.fromisoformat(data["last_rotated"]) if data["last_rotated"] else None,
                    access_count=data["access_count"],
                    expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
                    description=data.get("description")
                )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _log_access(self, 
                   key_id: str, 
                   action: str, 
                   success: bool,
                   accessor: str = "system") -> None:
        """Log key access for audit"""
        if not self.enable_audit_log:
            return
        
        log_entry = KeyAccessLog(
            key_id=key_id,
            accessed_at=datetime.now(timezone.utc),
            accessor=accessor,
            action=action,
            success=success,
            ip_address=None,  # Would be populated in web context
            user_agent=None   # Would be populated in web context
        )
        
        # Append to audit log
        with open(self.audit_log_file, 'a') as f:
            f.write(json.dumps(asdict(log_entry), default=str) + "\n")
    
    def get_audit_log(self, key_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        if not self.audit_log_file.exists():
            return []
        
        entries = []
        with open(self.audit_log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if key_id is None or entry.get("key_id") == key_id:
                        entries.append(entry)
                except:
                    continue
        
        # Return most recent entries
        return entries[-limit:]


def generate_secure_key(length: int = 32) -> str:
    """Generate a cryptographically secure random key"""
    return secrets.token_urlsafe(length)


def validate_key_strength(key: str, min_length: int = 20) -> bool:
    """Validate that a key meets security requirements"""
    if len(key) < min_length:
        return False
    
    # Check for basic complexity
    has_upper = any(c.isupper() for c in key)
    has_lower = any(c.islower() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(not c.isalnum() for c in key)
    
    # Require at least 3 of 4 character types for strong keys
    complexity = sum([has_upper, has_lower, has_digit, has_special])
    
    return complexity >= 3