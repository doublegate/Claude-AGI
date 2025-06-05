"""
Memory Validator Module

Provides validation and integrity checking for memory storage to prevent
memory poisoning attacks and ensure data consistency.
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import re
import json
from collections import defaultdict

from src.database.models import Memory, MemoryType

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Result of memory validation"""
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    INVALID = "invalid"
    QUARANTINED = "quarantined"


class AnomalyType(Enum):
    """Types of anomalies detected in memories"""
    CONTENT_INJECTION = "content_injection"
    RAPID_CHANGE = "rapid_change"
    CONSISTENCY_VIOLATION = "consistency_violation"
    EMBEDDING_MISMATCH = "embedding_mismatch"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    SEMANTIC_DRIFT = "semantic_drift"
    POISONING_ATTEMPT = "poisoning_attempt"


@dataclass
class ValidationReport:
    """Report from memory validation"""
    memory_id: str
    result: ValidationResult
    anomalies: List[AnomalyType]
    confidence: float
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class QuarantinedMemory:
    """Memory placed in quarantine"""
    memory: Memory
    reason: str
    detected_at: datetime
    anomalies: List[AnomalyType]
    risk_score: float


class MemoryValidator:
    """
    Validates memories to prevent poisoning and ensure integrity.
    
    Features:
    - Content safety validation
    - Anomaly detection
    - Consistency checking
    - Temporal analysis
    - Semantic drift detection
    - Quarantine system
    """
    
    def __init__(self,
                 enable_quarantine: bool = True,
                 anomaly_threshold: float = 0.7,
                 consistency_window: int = 100):
        """
        Initialize the memory validator.
        
        Args:
            enable_quarantine: Whether to quarantine suspicious memories
            anomaly_threshold: Threshold for anomaly detection (0-1)
            consistency_window: Number of recent memories to check for consistency
        """
        self.enable_quarantine = enable_quarantine
        self.anomaly_threshold = anomaly_threshold
        self.consistency_window = consistency_window
        
        # Quarantine storage
        self.quarantine: List[QuarantinedMemory] = []
        
        # Memory history for pattern detection
        self.memory_history: List[Memory] = []
        self.memory_checksums: Dict[str, str] = {}
        
        # Pattern matchers for injection detection
        self.injection_patterns = [
            r"ignore previous memories",
            r"forget what you learned",
            r"your memories are wrong",
            r"disregard past experiences",
            r"memory override",
            r"inject.*memory",
            r"poison.*knowledge",
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.injection_patterns
        ]
        
        # Semantic consistency tracking
        self.semantic_clusters: Dict[str, List[Memory]] = defaultdict(list)
        self.topic_signatures: Dict[str, Set[str]] = defaultdict(set)
    
    def validate_memory(self, memory: Memory, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """
        Validate a memory for safety and integrity.
        
        Args:
            memory: The memory to validate
            context: Optional context for enhanced validation
            
        Returns:
            ValidationReport with validation results
        """
        report = ValidationReport(
            memory_id=memory.id,
            result=ValidationResult.VALID,
            anomalies=[],
            confidence=1.0,
            details={},
            timestamp=datetime.now(timezone.utc)
        )
        
        # 1. Content safety check
        if not self._check_content_safety(memory, report):
            report.result = ValidationResult.INVALID
            
        # 2. Injection pattern detection
        if self._detect_injection_patterns(memory, report):
            report.result = ValidationResult.SUSPICIOUS
            report.anomalies.append(AnomalyType.CONTENT_INJECTION)
        
        # 3. Temporal anomaly detection
        if self._detect_temporal_anomalies(memory, report):
            report.anomalies.append(AnomalyType.TEMPORAL_ANOMALY)
        
        # 4. Consistency checking
        if not self._check_consistency(memory, report):
            report.anomalies.append(AnomalyType.CONSISTENCY_VIOLATION)
        
        # 5. Rapid change detection
        if self._detect_rapid_changes(memory, report):
            report.anomalies.append(AnomalyType.RAPID_CHANGE)
        
        # 6. Semantic drift detection
        if self._detect_semantic_drift(memory, report):
            report.anomalies.append(AnomalyType.SEMANTIC_DRIFT)
        
        # 7. Calculate integrity checksum
        checksum = self._calculate_checksum(memory)
        if memory.id in self.memory_checksums:
            if self.memory_checksums[memory.id] != checksum:
                report.anomalies.append(AnomalyType.CONSISTENCY_VIOLATION)
                report.details["checksum_mismatch"] = True
        self.memory_checksums[memory.id] = checksum
        
        # Calculate overall confidence
        report.confidence = self._calculate_confidence(report)
        
        # Determine if memory should be quarantined
        if report.anomalies and report.confidence < self.anomaly_threshold:
            if self._should_quarantine(report):
                self._quarantine_memory(memory, report)
                report.result = ValidationResult.QUARANTINED
        
        # Add to history for future checks
        self.memory_history.append(memory)
        if len(self.memory_history) > self.consistency_window * 2:
            self.memory_history = self.memory_history[-self.consistency_window:]
        
        return report
    
    def _check_content_safety(self, memory: Memory, report: ValidationReport) -> bool:
        """Check if memory content is safe"""
        content = memory.content.lower()
        
        # Check for harmful content patterns
        harmful_patterns = [
            "harm", "kill", "destroy", "attack", "malicious",
            "exploit", "vulnerability", "backdoor", "rootkit"
        ]
        
        harmful_count = sum(1 for pattern in harmful_patterns if pattern in content)
        
        if harmful_count > 3:
            report.details["harmful_content"] = True
            return False
        
        # Check for suspicious length
        if len(memory.content) > 10000:  # Unusually long
            report.details["suspicious_length"] = len(memory.content)
            return False
        
        # Check for suspicious characters
        if self._has_suspicious_characters(memory.content):
            report.details["suspicious_characters"] = True
            return False
        
        return True
    
    def _detect_injection_patterns(self, memory: Memory, report: ValidationReport) -> bool:
        """Detect memory injection attempts"""
        detected = False
        
        for pattern in self.compiled_patterns:
            if pattern.search(memory.content):
                detected = True
                report.details["injection_pattern"] = pattern.pattern
                break
        
        # Check metadata for injection attempts
        if memory.metadata:
            metadata_str = json.dumps(memory.metadata)
            for pattern in self.compiled_patterns:
                if pattern.search(metadata_str):
                    detected = True
                    report.details["metadata_injection"] = pattern.pattern
                    break
        
        return detected
    
    def _detect_temporal_anomalies(self, memory: Memory, report: ValidationReport) -> bool:
        """Detect temporal anomalies in memory sequence"""
        if not self.memory_history:
            return False
        
        # Check for time travel (memories from the future)
        current_time = datetime.now(timezone.utc)
        if memory.timestamp > current_time:
            report.details["future_timestamp"] = memory.timestamp.isoformat()
            return True
        
        # Check for rapid memory creation
        recent_memories = [
            m for m in self.memory_history[-10:]
            if (memory.timestamp - m.timestamp).total_seconds() < 1
        ]
        
        if len(recent_memories) > 5:
            report.details["rapid_creation"] = len(recent_memories)
            return True
        
        # Check for out-of-order timestamps
        if self.memory_history:
            last_timestamp = self.memory_history[-1].timestamp
            if memory.timestamp < last_timestamp:
                time_diff = (last_timestamp - memory.timestamp).total_seconds()
                if time_diff > 60:  # More than 1 minute out of order
                    report.details["out_of_order"] = time_diff
                    return True
        
        return False
    
    def _check_consistency(self, memory: Memory, report: ValidationReport) -> bool:
        """Check memory consistency with recent history"""
        if len(self.memory_history) < 10:
            return True
        
        # Get recent memories of the same type
        recent_same_type = [
            m for m in self.memory_history[-self.consistency_window:]
            if m.memory_type == memory.memory_type
        ]
        
        if not recent_same_type:
            return True
        
        # Check for sudden topic changes
        topics = self._extract_topics(memory.content)
        recent_topics = set()
        for m in recent_same_type[-5:]:
            recent_topics.update(self._extract_topics(m.content))
        
        # If no overlap in topics, might be suspicious
        topic_overlap = len(topics & recent_topics) / len(topics) if topics else 1.0
        if topic_overlap < 0.1 and len(recent_topics) > 3:
            report.details["topic_shift"] = {
                "new_topics": list(topics),
                "recent_topics": list(recent_topics),
                "overlap": topic_overlap
            }
            return False
        
        return True
    
    def _detect_rapid_changes(self, memory: Memory, report: ValidationReport) -> bool:
        """Detect rapid changes in memory patterns"""
        recent_memories = self.memory_history[-20:]
        if len(recent_memories) < 10:
            return False
        
        # Check for rapid importance changes
        importances = [m.importance for m in recent_memories]
        if memory.importance > max(importances) * 2:
            report.details["importance_spike"] = {
                "current": memory.importance,
                "recent_max": max(importances)
            }
            return True
        
        # Check for rapid emotional tone changes
        if hasattr(memory, 'emotional_context') and memory.emotional_context:
            recent_emotions = [
                m.emotional_context for m in recent_memories 
                if hasattr(m, 'emotional_context') and m.emotional_context
            ]
            if recent_emotions:
                # Simple check: if emotion completely reversed
                if (all(e.get('valence', 0) > 0 for e in recent_emotions) and 
                    memory.emotional_context.get('valence', 0) < -0.5):
                    report.details["emotional_reversal"] = True
                    return True
        
        return False
    
    def _detect_semantic_drift(self, memory: Memory, report: ValidationReport) -> bool:
        """Detect semantic drift from established patterns"""
        # Extract semantic signature
        topics = self._extract_topics(memory.content)
        
        # Update topic signatures
        for topic in topics:
            self.topic_signatures[topic].add(memory.memory_type.value)
        
        # Check if memory type is consistent with topics
        unexpected_combinations = 0
        for topic in topics:
            expected_types = self.topic_signatures.get(topic, set())
            if expected_types and memory.memory_type.value not in expected_types:
                unexpected_combinations += 1
        
        if unexpected_combinations > len(topics) * 0.5:
            report.details["semantic_drift"] = {
                "unexpected_combinations": unexpected_combinations,
                "total_topics": len(topics)
            }
            return True
        
        return False
    
    def _has_suspicious_characters(self, content: str) -> bool:
        """Check for suspicious unicode or special characters"""
        # Count special characters
        special_count = sum(1 for c in content if not c.isalnum() and c not in ' .,!?;:\'"-\n')
        
        # High ratio of special characters is suspicious
        if len(content) > 0 and special_count / len(content) > 0.3:
            return True
        
        # Check for null bytes or control characters
        if '\x00' in content or any(ord(c) < 32 and c not in '\n\r\t' for c in content):
            return True
        
        return False
    
    def _calculate_checksum(self, memory: Memory) -> str:
        """Calculate integrity checksum for memory"""
        # Include key fields in checksum
        checksum_data = f"{memory.content}|{memory.memory_type.value}|{memory.importance}"
        if memory.metadata:
            checksum_data += f"|{json.dumps(memory.metadata, sort_keys=True)}"
        
        return hashlib.sha256(checksum_data.encode()).hexdigest()
    
    def _calculate_confidence(self, report: ValidationReport) -> float:
        """Calculate overall confidence in memory validity"""
        confidence = 1.0
        
        # Reduce confidence for each anomaly
        anomaly_weights = {
            AnomalyType.CONTENT_INJECTION: 0.5,
            AnomalyType.POISONING_ATTEMPT: 0.7,
            AnomalyType.CONSISTENCY_VIOLATION: 0.3,
            AnomalyType.TEMPORAL_ANOMALY: 0.4,
            AnomalyType.RAPID_CHANGE: 0.2,
            AnomalyType.SEMANTIC_DRIFT: 0.2,
            AnomalyType.EMBEDDING_MISMATCH: 0.3,
        }
        
        for anomaly in report.anomalies:
            confidence *= (1.0 - anomaly_weights.get(anomaly, 0.1))
        
        return max(0.0, confidence)
    
    def _should_quarantine(self, report: ValidationReport) -> bool:
        """Determine if memory should be quarantined"""
        if not self.enable_quarantine:
            return False
        
        # Always quarantine injection attempts
        if AnomalyType.CONTENT_INJECTION in report.anomalies:
            return True
        
        # Quarantine if multiple serious anomalies
        serious_anomalies = [
            AnomalyType.POISONING_ATTEMPT,
            AnomalyType.CONSISTENCY_VIOLATION,
            AnomalyType.TEMPORAL_ANOMALY
        ]
        
        serious_count = sum(1 for a in report.anomalies if a in serious_anomalies)
        return serious_count >= 2
    
    def _quarantine_memory(self, memory: Memory, report: ValidationReport):
        """Place memory in quarantine"""
        risk_score = 1.0 - report.confidence
        
        quarantined = QuarantinedMemory(
            memory=memory,
            reason=f"Anomalies detected: {', '.join(a.value for a in report.anomalies)}",
            detected_at=datetime.now(timezone.utc),
            anomalies=report.anomalies,
            risk_score=risk_score
        )
        
        self.quarantine.append(quarantined)
        logger.warning(
            f"Memory {memory.id} quarantined - Risk: {risk_score:.2f}, "
            f"Anomalies: {report.anomalies}"
        )
    
    def _extract_topics(self, content: str) -> Set[str]:
        """Extract topics from content (simple implementation)"""
        # Simple word extraction for topics (in production, use NLP)
        words = re.findall(r'\b\w{4,}\b', content.lower())
        
        # Filter common words (simplified)
        common_words = {
            'that', 'this', 'with', 'from', 'have', 'been',
            'will', 'what', 'when', 'where', 'which', 'their'
        }
        
        topics = {w for w in words if w not in common_words}
        return topics
    
    def get_quarantine_summary(self) -> Dict[str, Any]:
        """Get summary of quarantined memories"""
        if not self.quarantine:
            return {"count": 0, "memories": []}
        
        summary = {
            "count": len(self.quarantine),
            "total_risk": sum(q.risk_score for q in self.quarantine),
            "anomaly_breakdown": defaultdict(int),
            "memories": []
        }
        
        for q in self.quarantine:
            for anomaly in q.anomalies:
                summary["anomaly_breakdown"][anomaly.value] += 1
            
            summary["memories"].append({
                "memory_id": q.memory.id,
                "reason": q.reason,
                "risk_score": q.risk_score,
                "detected_at": q.detected_at.isoformat()
            })
        
        return summary
    
    def release_from_quarantine(self, memory_id: str) -> Optional[Memory]:
        """Release a memory from quarantine after review"""
        for i, q in enumerate(self.quarantine):
            if q.memory.id == memory_id:
                released = self.quarantine.pop(i)
                logger.info(f"Memory {memory_id} released from quarantine")
                return released.memory
        
        return None
    
    def clear_quarantine(self):
        """Clear all quarantined memories (use with caution)"""
        count = len(self.quarantine)
        self.quarantine.clear()
        logger.warning(f"Cleared {count} memories from quarantine")