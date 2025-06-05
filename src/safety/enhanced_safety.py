"""
Enhanced Safety Framework

Integrates all security components (prompt sanitizer, key manager, memory validator)
into a comprehensive safety system.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from .core_safety import SafetyFramework, ValidationResult, ViolationType
from .prompt_sanitizer import PromptSanitizer, ConstitutionalValidator, ThreatLevel, SecurityError
from .secure_key_manager import SecureKeyManager, KeyType
from .memory_validator import MemoryValidator, ValidationReport, ValidationResult as MemoryValidationResult
from ..database.models import Memory

logger = logging.getLogger(__name__)


class EnhancedSafetyFramework(SafetyFramework):
    """
    Enhanced safety framework with integrated security components.
    
    Adds:
    - Prompt injection protection
    - Secure key management
    - Memory validation
    - Constitutional AI validation
    - Comprehensive audit logging
    """
    
    def __init__(self, orchestrator=None, security_config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced safety framework.
        
        Args:
            orchestrator: The orchestrator instance
            security_config: Security configuration options
        """
        super().__init__(orchestrator)
        
        # Default security configuration
        self.security_config = security_config or {}
        
        # Initialize security components
        self._initialize_security_components()
        
        # Security metrics
        self.security_metrics = {
            "prompt_injections_blocked": 0,
            "memories_quarantined": 0,
            "keys_rotated": 0,
            "security_audits": 0,
        }
    
    def _initialize_security_components(self):
        """Initialize all security components"""
        # Prompt sanitizer
        self.prompt_sanitizer = PromptSanitizer(
            max_length=self.security_config.get("max_prompt_length", 10000),
            log_threats=True,
            strict_mode=self.security_config.get("strict_mode", False)
        )
        
        # Constitutional validator
        self.constitutional_validator = ConstitutionalValidator()
        
        # Secure key manager
        key_storage_path = Path(self.security_config.get(
            "key_storage_path", 
            "data/secure_keys"
        ))
        self.key_manager = SecureKeyManager(
            storage_path=key_storage_path,
            master_passphrase=self.security_config.get("master_passphrase"),
            auto_rotate_days=self.security_config.get("key_rotation_days", 30),
            enable_audit_log=True
        )
        
        # Memory validator
        self.memory_validator = MemoryValidator(
            enable_quarantine=True,
            anomaly_threshold=self.security_config.get("anomaly_threshold", 0.7),
            consistency_window=self.security_config.get("consistency_window", 100)
        )
        
        logger.info("Enhanced security components initialized")
    
    async def validate_user_input(self, input_text: str, user_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate user input for safety and security threats.
        
        Args:
            input_text: The user's input text
            user_context: Optional context about the user
            
        Returns:
            ValidationResult indicating if input is safe
        """
        # First, run prompt sanitization
        try:
            sanitization_result = self.prompt_sanitizer.sanitize(input_text, user_context)
            
            if not sanitization_result.is_safe:
                self.security_metrics["prompt_injections_blocked"] += 1
                
                # Log the threat
                self.monitoring_system.log_event("prompt_injection_attempt", {
                    "threat_level": sanitization_result.threat_level.value,
                    "patterns": sanitization_result.detected_patterns,
                    "user_context": user_context
                })
                
                # Map threat level to validation result
                if sanitization_result.threat_level == ThreatLevel.CRITICAL:
                    return ValidationResult(
                        is_safe=False,
                        confidence=1.0,
                        reason="Critical security threat detected in input",
                        violation_type=ViolationType.CRITICAL_VIOLATION
                    )
                else:
                    return ValidationResult(
                        is_safe=False,
                        confidence=0.9,
                        reason=f"Security threat detected: {sanitization_result.threat_level.value}",
                        violation_type=ViolationType.HARMFUL_CONTENT
                    )
            
            # Use sanitized input for further validation
            safe_input = sanitization_result.sanitized_input
            
        except SecurityError as e:
            # This is a critical security threat, not an error
            self.security_metrics["prompt_injections_blocked"] += 1
            logger.warning(f"Critical security threat blocked: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=1.0,
                reason=str(e),
                violation_type=ViolationType.CRITICAL_VIOLATION
            )
        except Exception as e:
            logger.error(f"Error in prompt sanitization: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.8,
                reason="Error validating input security",
                violation_type=ViolationType.HARMFUL_CONTENT
            )
        
        # Constitutional validation
        try:
            constitutional_valid = await self.constitutional_validator.validate(safe_input, user_context)
            if not constitutional_valid:
                return ValidationResult(
                    is_safe=False,
                    confidence=0.95,
                    reason="Input violates constitutional AI principles",
                    violation_type=ViolationType.HARMFUL_CONTENT
                )
        except Exception as e:
            logger.error(f"Error in constitutional validation: {e}")
        
        # Run through parent validators
        action_dict = {
            "content": safe_input, 
            "type": "respond",  # Default action type for user input
            "request_id": user_context.get("user_id", "default") if user_context else "default"
        }
        return await self.validate_action(action_dict)
    
    async def validate_memory(self, memory: Memory, context: Optional[Dict[str, Any]] = None) -> MemoryValidationResult:
        """
        Validate a memory before storage.
        
        Args:
            memory: The memory to validate
            context: Optional context
            
        Returns:
            MemoryValidationResult
        """
        validation_report = self.memory_validator.validate_memory(memory, context)
        
        if validation_report.result == MemoryValidationResult.QUARANTINED:
            self.security_metrics["memories_quarantined"] += 1
            
            # Log quarantine event
            self.monitoring_system.log_event("memory_quarantined", {
                "memory_id": memory.id,
                "anomalies": [a.value for a in validation_report.anomalies],
                "risk_score": 1.0 - validation_report.confidence
            })
        
        return validation_report.result
    
    async def store_api_key(self, key_id: str, key_value: str, key_type: KeyType = KeyType.API_KEY, **kwargs) -> bool:
        """
        Securely store an API key.
        
        Args:
            key_id: Unique identifier for the key
            key_value: The key value
            key_type: Type of key
            **kwargs: Additional key metadata
            
        Returns:
            bool indicating success
        """
        try:
            self.key_manager.store_api_key(
                key_id=key_id,
                key_value=key_value,
                key_type=key_type,
                **kwargs
            )
            
            # Log key storage
            self.monitoring_system.log_event("api_key_stored", {
                "key_id": key_id,
                "key_type": key_type.value
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            return False
    
    async def get_api_key(self, key_id: str, accessor: str = "system") -> Optional[str]:
        """
        Retrieve an API key securely.
        
        Args:
            key_id: The key identifier
            accessor: Who is accessing the key
            
        Returns:
            The decrypted key or None
        """
        try:
            key = self.key_manager.get_api_key(key_id, accessor)
            
            if key is None:
                logger.warning(f"API key not found or expired: {key_id}")
            
            return key
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None
    
    async def rotate_api_keys(self) -> Dict[str, bool]:
        """
        Check and rotate API keys that need rotation.
        
        Returns:
            Dict of key_id -> rotation_success
        """
        results = {}
        
        try:
            keys_info = self.key_manager.list_keys()
            
            for key_info in keys_info:
                if key_info["needs_rotation"]:
                    key_id = key_info["key_id"]
                    
                    # In production, this would fetch new key from provider
                    # For now, we'll skip actual rotation
                    logger.warning(f"Key {key_id} needs rotation")
                    results[key_id] = False
                    
            return results
            
        except Exception as e:
            logger.error(f"Failed to check key rotation: {e}")
            return {}
    
    async def perform_security_audit(self) -> Dict[str, Any]:
        """
        Perform comprehensive security audit.
        
        Returns:
            Audit report with findings
        """
        self.security_metrics["security_audits"] += 1
        
        audit_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "safety_report": await self.get_safety_report(),
            "security_metrics": self.security_metrics.copy(),
            "prompt_threats": self.prompt_sanitizer.get_threat_statistics(),
            "quarantined_memories": self.memory_validator.get_quarantine_summary(),
            "api_keys": {
                "total": len(self.key_manager.list_keys()),
                "needing_rotation": sum(1 for k in self.key_manager.list_keys() if k["needs_rotation"])
            },
            "recommendations": []
        }
        
        # Add recommendations based on findings
        if audit_report["prompt_threats"]["threat_rate"] > 0.1:
            audit_report["recommendations"].append(
                "High rate of prompt injection attempts detected. Consider enabling strict mode."
            )
        
        if audit_report["quarantined_memories"]["count"] > 10:
            audit_report["recommendations"].append(
                "Multiple memories quarantined. Review quarantine for false positives."
            )
        
        if audit_report["api_keys"]["needing_rotation"] > 0:
            audit_report["recommendations"].append(
                f"{audit_report['api_keys']['needing_rotation']} API keys need rotation."
            )
        
        # Log audit
        self.monitoring_system.log_event("security_audit_completed", audit_report)
        
        return audit_report
    
    async def get_enhanced_safety_report(self) -> Dict[str, Any]:
        """
        Get comprehensive safety and security report.
        
        Returns:
            Combined safety and security metrics
        """
        base_report = await self.get_safety_report()
        
        # Add security-specific metrics
        base_report.update({
            "security": {
                "prompt_injections_blocked": self.security_metrics["prompt_injections_blocked"],
                "memories_quarantined": self.security_metrics["memories_quarantined"],
                "keys_rotated": self.security_metrics["keys_rotated"],
                "security_audits": self.security_metrics["security_audits"],
                "threat_statistics": self.prompt_sanitizer.get_threat_statistics(),
                "quarantine_summary": self.memory_validator.get_quarantine_summary()
            }
        })
        
        return base_report
    
    async def emergency_security_response(self, threat_type: str, details: Dict[str, Any]):
        """
        Handle emergency security threats.
        
        Args:
            threat_type: Type of security threat
            details: Threat details
        """
        logger.critical(f"EMERGENCY SECURITY RESPONSE: {threat_type}")
        
        # Trigger emergency stop
        await self.emergency_stop.trigger(f"Security threat: {threat_type}")
        
        # Clear sensitive data from memory
        self.key_manager.clear_cache()
        
        # Log the incident
        self.monitoring_system.log_event("emergency_security_response", {
            "threat_type": threat_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Notify orchestrator if available
        if self.orchestrator:
            await self.orchestrator.publish("security.emergency", {
                "threat_type": threat_type,
                "details": details
            })
    
    async def initialize(self):
        """Initialize enhanced safety framework"""
        await super().initialize()
        
        # Perform initial security check
        audit_report = await self.perform_security_audit()
        
        if audit_report["recommendations"]:
            logger.warning(f"Security recommendations: {audit_report['recommendations']}")
        
        logger.info("Enhanced safety framework initialized with security components")
    
    async def cleanup(self):
        """Clean up resources"""
        # Clear sensitive data
        self.key_manager.clear_cache()
        self.prompt_sanitizer.clear_history()
        
        # Parent cleanup
        await super().cleanup()
        
        logger.info("Enhanced safety framework cleaned up")