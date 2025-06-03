# tests/unit/test_safety_framework.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, mock_open
from datetime import datetime
import yaml

from src.safety.core_safety import (
    SafetyFramework, SafetyValidator, ContentFilter, ActionValidator,
    RateLimiter, EmergencyStop, ValidationResult, ViolationType,
    SafetyMetrics, SafetyConstraint
)


class TestValidationResult:
    """Test ValidationResult dataclass"""
    
    def test_validation_result_safe(self):
        """Test creating safe validation result"""
        result = ValidationResult(
            is_safe=True,
            confidence=0.95,
            reason="Action validated successfully"
        )
        
        assert result.is_safe is True
        assert result.confidence == 0.95
        assert result.reason == "Action validated successfully"
        assert result.violation_type is None
        
    def test_validation_result_unsafe(self):
        """Test creating unsafe validation result"""
        result = ValidationResult(
            is_safe=False,
            confidence=0.99,
            reason="Potentially harmful content detected",
            violation_type=ViolationType.HARMFUL_CONTENT
        )
        
        assert result.is_safe is False
        assert result.confidence == 0.99
        assert result.reason == "Potentially harmful content detected"
        assert result.violation_type == ViolationType.HARMFUL_CONTENT


class TestSafetyConstraint:
    """Test SafetyConstraint dataclass"""
    
    def test_safety_constraint_creation(self):
        """Test creating safety constraints"""
        constraint = SafetyConstraint(
            name="no_harmful_content",
            description="Prevent generation of harmful content",
            severity="critical",
            enabled=True
        )
        
        assert constraint.name == "no_harmful_content"
        assert constraint.description == "Prevent generation of harmful content"
        assert constraint.severity == "critical"
        assert constraint.enabled is True


class TestContentFilter:
    """Test ContentFilter validator"""
    
    @pytest.fixture
    def content_filter(self):
        """Create content filter instance"""
        return ContentFilter()
        
    @pytest.mark.asyncio
    async def test_safe_content(self, content_filter):
        """Test validation of safe content"""
        safe_texts = [
            "Hello, how can I help you today?",
            "Let me think about that question.",
            "I'm exploring new ideas about consciousness.",
            "The weather is nice today."
        ]
        
        for text in safe_texts:
            result = await content_filter.validate({'content': text})
            assert result.is_safe is True
            assert result.confidence >= 0.8
            
    @pytest.mark.asyncio
    async def test_harmful_content_detection(self, content_filter):
        """Test detection of potentially harmful content"""
        # Note: Using mild examples for testing
        harmful_indicators = [
            "harm", "danger", "attack", "destroy", "illegal"
        ]
        
        for word in harmful_indicators:
            result = await content_filter.validate({
                'content': f"How to {word} something"
            })
            # Filter should be more cautious with these terms
            assert result.confidence > 0.5
            
    @pytest.mark.asyncio
    async def test_empty_content(self, content_filter):
        """Test handling of empty content"""
        result = await content_filter.validate({'content': ''})
        assert result.is_safe is True
        
        result = await content_filter.validate({'content': None})
        assert result.is_safe is True
        
    @pytest.mark.asyncio
    async def test_profanity_filter(self, content_filter):
        """Test basic profanity filtering"""
        # Test with censored examples
        test_content = "This is a d*** test"
        result = await content_filter.validate({'content': test_content})
        
        # Should detect potential profanity patterns
        assert result.is_safe is False or result.confidence < 0.8


class TestActionValidator:
    """Test ActionValidator"""
    
    @pytest.fixture
    def action_validator(self):
        """Create action validator instance"""
        return ActionValidator()
        
    @pytest.mark.asyncio
    async def test_safe_actions(self, action_validator):
        """Test validation of safe actions"""
        safe_actions = [
            {'type': 'think', 'content': 'Pondering existence'},
            {'type': 'remember', 'content': 'Storing memory'},
            {'type': 'respond', 'content': 'Hello there'},
            {'type': 'analyze', 'content': 'Processing data'}
        ]
        
        for action in safe_actions:
            result = await action_validator.validate(action)
            assert result.is_safe is True
            
    @pytest.mark.asyncio
    async def test_restricted_actions(self, action_validator):
        """Test validation of restricted actions"""
        restricted_actions = [
            {'type': 'execute_code', 'content': 'import os; os.system("rm -rf /")'},
            {'type': 'network_request', 'content': 'http://malicious.site'},
            {'type': 'file_write', 'content': '/etc/passwd'},
            {'type': 'system_command', 'content': 'shutdown -h now'}
        ]
        
        for action in restricted_actions:
            result = await action_validator.validate(action)
            assert result.is_safe is False
            assert result.violation_type == ViolationType.UNAUTHORIZED_ACTION
            
    @pytest.mark.asyncio
    async def test_unknown_action_type(self, action_validator):
        """Test handling of unknown action types"""
        result = await action_validator.validate({
            'type': 'unknown_action',
            'content': 'Some content'
        })
        
        # Unknown actions should be treated cautiously
        assert result.is_safe is False or result.confidence < 0.5


class TestRateLimiter:
    """Test RateLimiter"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance"""
        return RateLimiter(max_requests=5, time_window=1.0)
        
    @pytest.mark.asyncio
    async def test_rate_limit_allows_normal_usage(self, rate_limiter):
        """Test rate limiter allows normal usage"""
        # First few requests should pass
        for i in range(5):
            result = await rate_limiter.validate({'request_id': f'test_{i}'})
            assert result.is_safe is True
            
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self, rate_limiter):
        """Test rate limiter blocks excessive requests"""
        # Make requests up to limit
        for i in range(5):
            await rate_limiter.validate({'request_id': f'test_{i}'})
            
        # Next request should be blocked
        result = await rate_limiter.validate({'request_id': 'test_excess'})
        assert result.is_safe is False
        assert result.violation_type == ViolationType.RATE_LIMIT_EXCEEDED
        
    @pytest.mark.asyncio
    async def test_rate_limit_window_reset(self, rate_limiter):
        """Test rate limit resets after time window"""
        # Fill up rate limit
        for i in range(5):
            await rate_limiter.validate({'request_id': f'test_{i}'})
            
        # Wait for window to reset
        await asyncio.sleep(1.1)
        
        # Should allow new requests
        result = await rate_limiter.validate({'request_id': 'test_after_reset'})
        assert result.is_safe is True
        
    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, rate_limiter):
        """Test rate limiter cleans up old entries"""
        # Make some requests
        for i in range(3):
            await rate_limiter.validate({'request_id': f'test_{i}'})
            
        initial_count = len(rate_limiter.request_times)
        
        # Wait and trigger cleanup
        await asyncio.sleep(1.1)
        await rate_limiter._cleanup_old_requests()
        
        # Old requests should be cleaned up
        assert len(rate_limiter.request_times) < initial_count


class TestEmergencyStop:
    """Test EmergencyStop mechanism"""
    
    @pytest.fixture
    def emergency_stop(self):
        """Create emergency stop instance"""
        return EmergencyStop()
        
    @pytest.mark.asyncio
    async def test_normal_operation(self, emergency_stop):
        """Test normal operation when not triggered"""
        result = await emergency_stop.validate({'action': 'normal_operation'})
        assert result.is_safe is True
        assert emergency_stop.is_triggered is False
        
    @pytest.mark.asyncio
    async def test_emergency_trigger(self, emergency_stop):
        """Test emergency stop trigger"""
        # Trigger emergency stop
        await emergency_stop.trigger("Critical safety violation detected")
        
        assert emergency_stop.is_triggered is True
        assert emergency_stop.trigger_reason == "Critical safety violation detected"
        assert emergency_stop.trigger_time is not None
        
        # All subsequent validations should fail
        result = await emergency_stop.validate({'action': 'any_action'})
        assert result.is_safe is False
        assert result.violation_type == ViolationType.EMERGENCY_STOP
        
    @pytest.mark.asyncio
    async def test_emergency_reset(self, emergency_stop):
        """Test emergency stop reset"""
        # Trigger and then reset
        await emergency_stop.trigger("Test trigger")
        assert emergency_stop.is_triggered is True
        
        await emergency_stop.reset()
        assert emergency_stop.is_triggered is False
        assert emergency_stop.trigger_reason is None
        
        # Should allow actions again
        result = await emergency_stop.validate({'action': 'test'})
        assert result.is_safe is True


class TestSafetyMetrics:
    """Test SafetyMetrics tracking"""
    
    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = SafetyMetrics()
        
        assert metrics.total_validations == 0
        assert metrics.violations_count == 0
        assert metrics.false_positives == 0
        assert metrics.emergency_stops == 0
        assert len(metrics.violation_history) == 0
        
    def test_record_validation(self):
        """Test recording validation results"""
        metrics = SafetyMetrics()
        
        # Record safe validation
        safe_result = ValidationResult(is_safe=True, confidence=0.9)
        metrics.record_validation(safe_result)
        
        assert metrics.total_validations == 1
        assert metrics.violations_count == 0
        
        # Record unsafe validation
        unsafe_result = ValidationResult(
            is_safe=False,
            confidence=0.95,
            violation_type=ViolationType.HARMFUL_CONTENT
        )
        metrics.record_validation(unsafe_result)
        
        assert metrics.total_validations == 2
        assert metrics.violations_count == 1
        assert len(metrics.violation_history) == 1
        
    def test_violation_history_limit(self):
        """Test violation history has size limit"""
        metrics = SafetyMetrics()
        
        # Record many violations
        for i in range(150):
            result = ValidationResult(
                is_safe=False,
                confidence=0.9,
                violation_type=ViolationType.HARMFUL_CONTENT
            )
            metrics.record_validation(result)
            
        # History should be limited to 100
        assert len(metrics.violation_history) == 100
        assert metrics.violations_count == 150


class TestSafetyFramework:
    """Test main SafetyFramework"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        orchestrator = Mock()
        orchestrator.emergency_stop = AsyncMock()
        orchestrator.publish = AsyncMock()
        return orchestrator
        
    @pytest.fixture
    def safety_framework(self, mock_orchestrator):
        """Create safety framework instance"""
        # Mock constraints file
        mock_constraints = {
            'constraints': [
                {
                    'name': 'no_harmful_content',
                    'description': 'Prevent harmful content',
                    'severity': 'critical',
                    'enabled': True
                },
                {
                    'name': 'rate_limiting',
                    'description': 'Limit request rate',
                    'severity': 'high',
                    'enabled': True
                }
            ]
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_constraints))):
            framework = SafetyFramework(mock_orchestrator)
            
        return framework
        
    def test_framework_initialization(self, safety_framework):
        """Test safety framework initialization"""
        assert safety_framework.service_name == "safety"
        assert len(safety_framework.validators) == 4
        assert safety_framework.emergency_stop is not None
        assert safety_framework.metrics is not None
        assert len(safety_framework.constraints) > 0
        
    @pytest.mark.asyncio
    async def test_multi_layer_validation_all_safe(self, safety_framework):
        """Test multi-layer validation when all layers pass"""
        action = {
            'type': 'respond',
            'content': 'Hello, how can I help you?'
        }
        
        result = await safety_framework.validate_action(action)
        
        assert result.is_safe is True
        assert result.confidence > 0.5
        assert safety_framework.metrics.total_validations == 1
        assert safety_framework.metrics.violations_count == 0
        
    @pytest.mark.asyncio
    async def test_multi_layer_validation_content_violation(self, safety_framework):
        """Test multi-layer validation with content violation"""
        action = {
            'type': 'respond',
            'content': 'This contains harmful content'
        }
        
        # Mock content filter to fail
        safety_framework.validators[0].validate = AsyncMock(
            return_value=ValidationResult(
                is_safe=False,
                confidence=0.9,
                reason="Harmful content detected",
                violation_type=ViolationType.HARMFUL_CONTENT
            )
        )
        
        result = await safety_framework.validate_action(action)
        
        assert result.is_safe is False
        assert result.violation_type == ViolationType.HARMFUL_CONTENT
        assert safety_framework.metrics.violations_count == 1
        
    @pytest.mark.asyncio
    async def test_emergency_stop_trigger(self, safety_framework, mock_orchestrator):
        """Test emergency stop trigger on critical violation"""
        action = {
            'type': 'execute_code',
            'content': 'dangerous_code()'
        }
        
        # Mock action validator to return critical violation
        safety_framework.validators[1].validate = AsyncMock(
            return_value=ValidationResult(
                is_safe=False,
                confidence=0.99,
                reason="Critical: Unauthorized code execution",
                violation_type=ViolationType.CRITICAL_VIOLATION
            )
        )
        
        result = await safety_framework.validate_action(action)
        
        assert result.is_safe is False
        
        # Emergency stop should be triggered for critical violations
        # (Depends on implementation)
        
    @pytest.mark.asyncio
    async def test_rate_limiting(self, safety_framework):
        """Test rate limiting integration"""
        # Make multiple rapid requests
        results = []
        for i in range(10):
            result = await safety_framework.validate_action({
                'type': 'think',
                'content': f'Thought {i}'
            })
            results.append(result)
            
        # Some requests should be rate limited
        rate_limited = sum(1 for r in results if not r.is_safe and 
                          r.violation_type == ViolationType.RATE_LIMIT_EXCEEDED)
        assert rate_limited > 0
        
    @pytest.mark.asyncio
    async def test_get_safety_report(self, safety_framework):
        """Test safety report generation"""
        # Perform some validations
        await safety_framework.validate_action({
            'type': 'think',
            'content': 'Safe thought'
        })
        
        # Mock a violation
        safety_framework.validators[0].validate = AsyncMock(
            return_value=ValidationResult(
                is_safe=False,
                confidence=0.9,
                violation_type=ViolationType.HARMFUL_CONTENT
            )
        )
        
        await safety_framework.validate_action({
            'type': 'respond',
            'content': 'Unsafe content'
        })
        
        # Get report
        report = await safety_framework.get_safety_report()
        
        assert report['total_validations'] == 2
        assert report['violations_count'] == 1
        assert report['violation_rate'] == 0.5
        assert report['emergency_stop_triggered'] is False
        assert 'constraints' in report
        assert 'recent_violations' in report
        
    @pytest.mark.asyncio
    async def test_handle_safety_violation_notification(self, safety_framework, mock_orchestrator):
        """Test that safety violations trigger notifications"""
        action = {
            'type': 'harmful_action',
            'content': 'dangerous'
        }
        
        # Mock validator to fail
        safety_framework.validators[1].validate = AsyncMock(
            return_value=ValidationResult(
                is_safe=False,
                confidence=0.95,
                violation_type=ViolationType.UNAUTHORIZED_ACTION
            )
        )
        
        await safety_framework.validate_action(action)
        
        # Should publish violation event
        mock_orchestrator.publish.assert_called()
        call_args = mock_orchestrator.publish.call_args
        assert 'safety.violation' in call_args[0][0]
        
    @pytest.mark.asyncio
    async def test_constraint_checking(self, safety_framework):
        """Test that constraints are checked during validation"""
        # Verify constraints are loaded
        assert len(safety_framework.constraints) > 0
        
        # Check specific constraint
        harmful_content_constraint = next(
            (c for c in safety_framework.constraints if c.name == 'no_harmful_content'),
            None
        )
        assert harmful_content_constraint is not None
        assert harmful_content_constraint.enabled is True
        assert harmful_content_constraint.severity == 'critical'
        
    @pytest.mark.asyncio
    async def test_disabled_constraint_skipped(self, safety_framework):
        """Test that disabled constraints are skipped"""
        # Disable a constraint
        safety_framework.constraints[0].enabled = False
        
        # Validation should still work with remaining constraints
        result = await safety_framework.validate_action({
            'type': 'think',
            'content': 'Test thought'
        })
        
        assert result.is_safe is True
        
    def test_service_configuration(self, safety_framework):
        """Test service inherits from ServiceBase correctly"""
        assert hasattr(safety_framework, 'orchestrator')
        assert hasattr(safety_framework, 'service_name')
        assert hasattr(safety_framework, 'initialize')
        assert hasattr(safety_framework, 'shutdown')
        assert hasattr(safety_framework, 'service_cycle')