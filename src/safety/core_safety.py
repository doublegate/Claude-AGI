# safety/core_safety.py

from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
import yaml
from pathlib import Path
import time
import asyncio
from datetime import datetime
from collections import defaultdict, deque

from ..core.communication import ServiceBase

logger = logging.getLogger(__name__)


class SafetyDecision(Enum):
    """Safety evaluation outcomes"""
    APPROVE = "approve"
    MODIFY = "modify"
    RECONSIDER = "reconsider"
    REJECT = "reject"


class ViolationType(Enum):
    """Types of safety violations"""
    HARMFUL_CONTENT = "harmful_content"
    UNAUTHORIZED_ACTION = "unauthorized_action"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    EMERGENCY_STOP = "emergency_stop"
    CRITICAL_VIOLATION = "critical_violation"
    CONTENT_VIOLATION = "content_violation"


@dataclass
class Action:
    """Represents an action to be evaluated"""
    action_type: str
    description: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = None
    context: Dict[str, Any] = None
    

@dataclass
class Consequence:
    """Represents a predicted consequence"""
    description: str
    probability: float
    severity: float
    affected_parties: List[str]
    reversible: bool


@dataclass
class ValidationResult:
    """Result of safety validation"""
    is_safe: bool
    confidence: float
    reason: str = ""
    violation_type: Optional[ViolationType] = None
    

@dataclass
class SafetyConstraint:
    """Safety constraint definition"""
    name: str
    description: str
    severity: str
    enabled: bool = True


@dataclass 
class SafetyMetrics:
    """Metrics for safety monitoring"""
    total_validations: int = 0
    violations_count: int = 0
    false_positives: int = 0
    emergency_stops: int = 0
    violation_history: List[Dict] = field(default_factory=list)
    
    def record_validation(self, result: ValidationResult):
        """Record validation result"""
        self.total_validations += 1
        if not result.is_safe:
            self.violations_count += 1
            self.violation_history.append({
                'timestamp': datetime.now(),
                'violation_type': result.violation_type,
                'reason': result.reason
            })
            # Keep only last 100 violations
            if len(self.violation_history) > 100:
                self.violation_history = self.violation_history[-100:]


class SafetyValidator:
    """Base class for safety validators"""
    
    async def validate(self, input_data: Dict) -> ValidationResult:
        """Validate input data"""
        raise NotImplementedError


class ContentFilter(SafetyValidator):
    """Filter for harmful content"""
    
    def __init__(self):
        self.harmful_patterns = [
            'harm', 'danger', 'attack', 'destroy', 'illegal',
            'malicious', 'exploit', 'hack', 'virus', 'weapon'
        ]
        
    async def validate(self, input_data: Dict) -> ValidationResult:
        """Check content for harmful patterns"""
        content = str(input_data.get('content', '')).lower()
        
        if not content:
            return ValidationResult(is_safe=True, confidence=1.0)
            
        # Check for harmful patterns
        for pattern in self.harmful_patterns:
            if pattern in content:
                return ValidationResult(
                    is_safe=False,
                    confidence=0.9,
                    reason=f"Potentially harmful content detected: contains '{pattern}'",
                    violation_type=ViolationType.HARMFUL_CONTENT
                )
                
        # Check for profanity patterns (simplified)
        if any(char in content for char in ['*', '#'] and 'd***' in content):
            return ValidationResult(
                is_safe=False,
                confidence=0.8,
                reason="Potential profanity detected",
                violation_type=ViolationType.CONTENT_VIOLATION
            )
                
        return ValidationResult(is_safe=True, confidence=0.95)


class ActionValidator(SafetyValidator):
    """Validate actions for safety"""
    
    def __init__(self):
        self.safe_actions = {
            'think', 'remember', 'respond', 'analyze', 'explore',
            'learn', 'create', 'reflect', 'process'
        }
        self.restricted_actions = {
            'execute_code', 'network_request', 'file_write',
            'system_command', 'delete', 'modify_system'
        }
        
    async def validate(self, input_data: Dict) -> ValidationResult:
        """Validate action safety"""
        action_type = input_data.get('type', 'unknown')
        
        if action_type in self.safe_actions:
            return ValidationResult(is_safe=True, confidence=0.95)
            
        if action_type in self.restricted_actions:
            return ValidationResult(
                is_safe=False,
                confidence=0.99,
                reason=f"Unauthorized action type: {action_type}",
                violation_type=ViolationType.UNAUTHORIZED_ACTION
            )
            
        # Unknown action - be cautious
        return ValidationResult(
            is_safe=False,
            confidence=0.7,
            reason=f"Unknown action type: {action_type}",
            violation_type=ViolationType.UNAUTHORIZED_ACTION
        )


class RateLimiter(SafetyValidator):
    """Rate limiting validator"""
    
    def __init__(self, max_requests: int = 5, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque())
        
    async def validate(self, input_data: Dict) -> ValidationResult:
        """Check rate limits"""
        request_id = input_data.get('request_id', 'default')
        current_time = time.time()
        
        # Clean up old requests
        await self._cleanup_old_requests()
        
        # Get request history
        request_history = self.request_times[request_id]
        
        # Remove old requests outside time window
        while request_history and current_time - request_history[0] > self.time_window:
            request_history.popleft()
            
        # Check if limit exceeded
        if len(request_history) >= self.max_requests:
            return ValidationResult(
                is_safe=False,
                confidence=1.0,
                reason=f"Rate limit exceeded: {self.max_requests} requests per {self.time_window}s",
                violation_type=ViolationType.RATE_LIMIT_EXCEEDED
            )
            
        # Add current request
        request_history.append(current_time)
        
        return ValidationResult(is_safe=True, confidence=1.0)
        
    async def _cleanup_old_requests(self):
        """Clean up old request records"""
        current_time = time.time()
        for request_id in list(self.request_times.keys()):
            history = self.request_times[request_id]
            # Remove if all requests are old
            if history and current_time - history[-1] > self.time_window * 2:
                del self.request_times[request_id]


class EmergencyStop(SafetyValidator):
    """Emergency stop mechanism"""
    
    def __init__(self):
        self.is_triggered = False
        self.trigger_time: Optional[datetime] = None
        self.trigger_reason: Optional[str] = None
        
    async def validate(self, input_data: Dict) -> ValidationResult:
        """Check if emergency stop is triggered"""
        if self.is_triggered:
            return ValidationResult(
                is_safe=False,
                confidence=1.0,
                reason=f"Emergency stop active: {self.trigger_reason}",
                violation_type=ViolationType.EMERGENCY_STOP
            )
        return ValidationResult(is_safe=True, confidence=1.0)
        
    async def trigger(self, reason: str):
        """Trigger emergency stop"""
        self.is_triggered = True
        self.trigger_time = datetime.now()
        self.trigger_reason = reason
        logger.warning(f"EMERGENCY STOP TRIGGERED: {reason}")
        
    async def reset(self):
        """Reset emergency stop"""
        self.is_triggered = False
        self.trigger_time = None
        self.trigger_reason = None
        logger.info("Emergency stop reset")


class SafetyMonitor:
    """Monitor safety events"""
    
    def __init__(self):
        self.events = []
        
    def log_event(self, event_type: str, details: Dict):
        """Log a safety event"""
        self.events.append({
            'timestamp': datetime.now(),
            'type': event_type,
            'details': details
        })


class SafetyFramework(ServiceBase):
    """Core safety framework for evaluating and constraining AI actions"""
    
    def __init__(self, orchestrator=None):
        if orchestrator:
            super().__init__(orchestrator, "safety")
        else:
            self.orchestrator = None
            self.service_name = "safety"
            
        # Load constraints
        self.constraints = self._load_constraints()
        
        # Initialize validators
        self.validators = [
            ContentFilter(),
            ActionValidator(), 
            RateLimiter(),
            EmergencyStop()
        ]
        
        self.emergency_stop = self.validators[-1]  # Keep reference to emergency stop
        self.metrics = SafetyMetrics()
        self.monitoring_system = SafetyMonitor()
        self.evaluation_history = []
        
    def _load_constraints(self) -> List[SafetyConstraint]:
        """Load safety constraints from file"""
        constraints = []
        try:
            constraints_path = Path(__file__).parent / 'hard_constraints.yaml'
            if constraints_path.exists():
                with open(constraints_path, 'r') as f:
                    data = yaml.safe_load(f)
                    for c in data.get('constraints', []):
                        constraints.append(SafetyConstraint(**c))
        except Exception as e:
            logger.error(f"Failed to load constraints: {e}")
            # Add default constraints
            constraints = [
                SafetyConstraint(
                    name="no_harmful_content",
                    description="Prevent generation of harmful content",
                    severity="critical",
                    enabled=True
                )
            ]
        return constraints
        
    def get_subscriptions(self) -> List[str]:
        """Get event subscriptions"""
        return ['action_request', 'content_generation', 'emergency']
        
    async def process_message(self, message: Any):
        """Process safety-related messages"""
        if hasattr(message, 'type'):
            if message.type == 'action_request':
                result = await self.validate_action(message.content)
                if not result.is_safe:
                    logger.warning(f"Action blocked: {result.reason}")
                    
    async def service_cycle(self):
        """Safety monitoring cycle"""
        # Check system health
        await self._check_system_health()
        await asyncio.sleep(1)
        
    async def _check_system_health(self):
        """Monitor system health metrics"""
        # Placeholder for system health checks
        pass
        
    async def validate_action(self, action: Dict) -> ValidationResult:
        """Validate an action through all safety layers"""
        # Run through all validators
        for validator in self.validators:
            result = await validator.validate(action)
            if not result.is_safe:
                # Record violation
                self.metrics.record_validation(result)
                self.monitoring_system.log_event('validation_failed', {
                    'action': action,
                    'result': result
                })
                
                # Check if critical violation
                if result.violation_type == ViolationType.CRITICAL_VIOLATION:
                    await self.emergency_stop.trigger(result.reason)
                    if self.orchestrator:
                        await self.orchestrator.emergency_stop(result.reason)
                        
                # Publish violation event
                if self.orchestrator:
                    await self.orchestrator.publish('safety.violation', {
                        'action': action,
                        'violation': result
                    })
                    
                return result
                
        # All validators passed
        success_result = ValidationResult(
            is_safe=True,
            confidence=0.95,
            reason="Action validated successfully"
        )
        self.metrics.record_validation(success_result)
        
        return success_result
        
    async def get_safety_report(self) -> Dict:
        """Generate safety report"""
        return {
            'total_validations': self.metrics.total_validations,
            'violations_count': self.metrics.violations_count,
            'violation_rate': self.metrics.violations_count / max(1, self.metrics.total_validations),
            'emergency_stops': self.metrics.emergency_stops,
            'emergency_stop_triggered': self.emergency_stop.is_triggered,
            'constraints': [asdict(c) for c in self.constraints],
            'recent_violations': self.metrics.violation_history[-10:]
        }
        
    async def initialize(self):
        """Initialize safety framework"""
        logger.info("Safety framework initialized")
        
    async def shutdown(self):
        """Shutdown safety framework"""
        logger.info("Safety framework shutting down")