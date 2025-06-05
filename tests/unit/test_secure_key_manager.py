"""
Unit tests for the secure key manager module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from src.safety.secure_key_manager import (
    SecureKeyManager,
    KeyType,
    KeyMetadata,
    generate_secure_key,
    validate_key_strength
)


class TestSecureKeyManager:
    """Test cases for SecureKeyManager"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create a temporary directory for key storage"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def key_manager(self, temp_storage):
        """Create a key manager instance with temp storage"""
        return SecureKeyManager(
            storage_path=temp_storage,
            master_passphrase="test-passphrase-123",
            enable_audit_log=True
        )
    
    def test_store_and_retrieve_key(self, key_manager):
        """Test basic key storage and retrieval"""
        key_id = "test-api-key"
        key_value = "sk-test123456789"
        
        # Store the key
        key_manager.store_api_key(
            key_id=key_id,
            key_value=key_value,
            description="Test API key"
        )
        
        # Retrieve the key
        retrieved = key_manager.get_api_key(key_id)
        assert retrieved == key_value
    
    def test_key_metadata(self, key_manager):
        """Test that metadata is properly stored and updated"""
        key_id = "metadata-test"
        key_value = "test-value-123"
        
        key_manager.store_api_key(
            key_id=key_id,
            key_value=key_value,
            key_type=KeyType.API_KEY,
            description="Metadata test key"
        )
        
        # List keys to check metadata
        keys = key_manager.list_keys()
        assert len(keys) == 1
        
        key_info = keys[0]
        assert key_info["key_id"] == key_id
        assert key_info["key_type"] == KeyType.API_KEY.value
        assert key_info["description"] == "Metadata test key"
        assert key_info["access_count"] == 0
        
        # Access the key and check updated metadata
        key_manager.get_api_key(key_id)
        keys = key_manager.list_keys()
        assert keys[0]["access_count"] == 1
        assert keys[0]["last_accessed"] is not None
    
    def test_key_expiration(self, key_manager):
        """Test key expiration functionality"""
        key_id = "expiring-key"
        key_value = "expires-soon"
        
        # Store a key that expires in -1 days (already expired)
        key_manager.store_api_key(
            key_id=key_id,
            key_value=key_value,
            expires_in_days=-1
        )
        
        # Try to retrieve expired key
        retrieved = key_manager.get_api_key(key_id)
        assert retrieved is None
    
    def test_key_rotation(self, key_manager):
        """Test key rotation"""
        key_id = "rotating-key"
        old_value = "old-key-value"
        new_value = "new-key-value"
        
        # Store initial key
        key_manager.store_api_key(key_id, old_value)
        
        # Verify old value
        assert key_manager.get_api_key(key_id) == old_value
        
        # Rotate the key
        key_manager.rotate_key(key_id, new_value)
        
        # Verify new value
        assert key_manager.get_api_key(key_id) == new_value
        
        # Check metadata shows rotation
        keys = key_manager.list_keys()
        key_info = next(k for k in keys if k["key_id"] == key_id)
        assert key_info["last_accessed"] is not None
    
    def test_key_deletion(self, key_manager):
        """Test key deletion"""
        key_id = "delete-me"
        key_value = "temporary-key"
        
        # Store and verify
        key_manager.store_api_key(key_id, key_value)
        assert key_manager.get_api_key(key_id) == key_value
        
        # Delete the key
        key_manager.delete_key(key_id)
        
        # Verify it's gone
        assert key_manager.get_api_key(key_id) is None
        assert len(key_manager.list_keys()) == 0
    
    def test_multiple_keys(self, key_manager):
        """Test storing multiple keys"""
        keys = {
            "api-key-1": "value-1",
            "api-key-2": "value-2",
            "db-password": "secret-password",
            "jwt-secret": "jwt-secret-value"
        }
        
        # Store all keys
        for key_id, value in keys.items():
            key_type = KeyType.DATABASE_PASSWORD if "password" in key_id else KeyType.API_KEY
            key_manager.store_api_key(key_id, value, key_type=key_type)
        
        # Verify all keys
        for key_id, expected_value in keys.items():
            assert key_manager.get_api_key(key_id) == expected_value
        
        # Check list
        stored_keys = key_manager.list_keys()
        assert len(stored_keys) == len(keys)
    
    def test_cache_functionality(self, key_manager):
        """Test in-memory caching"""
        key_id = "cached-key"
        key_value = "cache-me"
        
        key_manager.store_api_key(key_id, key_value)
        
        # First access - loads from disk
        assert key_manager.get_api_key(key_id) == key_value
        
        # Second access - should use cache
        assert key_manager.get_api_key(key_id) == key_value
        
        # Clear cache
        key_manager.clear_cache()
        
        # Next access loads from disk again
        assert key_manager.get_api_key(key_id) == key_value
    
    def test_invalid_inputs(self, key_manager):
        """Test validation of invalid inputs"""
        # Empty key ID
        with pytest.raises(ValueError):
            key_manager.store_api_key("", "value")
        
        # Empty key value
        with pytest.raises(ValueError):
            key_manager.store_api_key("key-id", "")
        
        # Non-existent key rotation
        with pytest.raises(ValueError):
            key_manager.rotate_key("non-existent", "new-value")
    
    def test_audit_logging(self, key_manager):
        """Test audit log functionality"""
        key_id = "audited-key"
        key_value = "audit-this"
        
        # Perform various operations
        key_manager.store_api_key(key_id, key_value)
        key_manager.get_api_key(key_id, accessor="user-123")
        key_manager.get_api_key(key_id, accessor="user-456")
        key_manager.rotate_key(key_id, "new-value")
        key_manager.delete_key(key_id)
        
        # Check audit log
        audit_log = key_manager.get_audit_log(key_id)
        assert len(audit_log) >= 5  # At least 5 operations
        
        # Verify log entries
        actions = [entry["action"] for entry in audit_log]
        assert "store" in actions
        assert "retrieve" in actions
        assert "rotate" in actions
        assert "delete" in actions
    
    def test_persistence_across_instances(self, temp_storage):
        """Test that keys persist across manager instances"""
        key_id = "persistent-key"
        key_value = "persist-me"
        
        # Create first manager and store key
        manager1 = SecureKeyManager(
            storage_path=temp_storage,
            master_passphrase="test-pass"
        )
        manager1.store_api_key(key_id, key_value)
        
        # Create second manager and retrieve key
        manager2 = SecureKeyManager(
            storage_path=temp_storage,
            master_passphrase="test-pass"
        )
        assert manager2.get_api_key(key_id) == key_value
    
    def test_rotation_needed_detection(self, key_manager):
        """Test detection of keys needing rotation"""
        # Set auto-rotate to 0 days for immediate rotation need
        key_manager.auto_rotate_days = 0
        
        key_id = "old-key"
        key_manager.store_api_key(key_id, "old-value")
        
        keys = key_manager.list_keys()
        assert keys[0]["needs_rotation"] is True
    
    def test_different_key_types(self, key_manager):
        """Test storing different types of keys"""
        test_keys = [
            ("api-key", "api-value", KeyType.API_KEY),
            ("db-pass", "db-value", KeyType.DATABASE_PASSWORD),
            ("jwt-key", "jwt-value", KeyType.JWT_SECRET),
            ("webhook", "webhook-value", KeyType.WEBHOOK_SECRET),
        ]
        
        for key_id, value, key_type in test_keys:
            key_manager.store_api_key(key_id, value, key_type=key_type)
        
        # Verify all stored with correct types
        stored_keys = key_manager.list_keys()
        for stored_key in stored_keys:
            expected_type = next(
                kt.value for kid, _, kt in test_keys 
                if kid == stored_key["key_id"]
            )
            assert stored_key["key_type"] == expected_type


class TestKeyGeneration:
    """Test key generation utilities"""
    
    def test_generate_secure_key(self):
        """Test secure key generation"""
        # Default length
        key1 = generate_secure_key()
        assert len(key1) > 30  # URL-safe encoding makes it longer
        assert key1 != generate_secure_key()  # Should be random
        
        # Custom length
        key2 = generate_secure_key(length=16)
        assert len(key2) > 15
    
    def test_validate_key_strength(self):
        """Test key strength validation"""
        # Strong keys
        assert validate_key_strength("Str0ng!Pass#2023ABCD") is True  # 20 chars
        assert validate_key_strength("ComplexKey123!@#$%^&*")
        
        # Weak keys
        assert not validate_key_strength("short")  # Too short
        assert not validate_key_strength("alllowercase12345678")  # No complexity
        assert not validate_key_strength("ALLUPPERCASE12345678")  # No complexity
        
        # Edge cases
        assert validate_key_strength("Mixed123CasePassword!")  # Good
        assert not validate_key_strength("a" * 19)  # Just under min length