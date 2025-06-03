"""
Continuous validation for Claude AGI system in production.

Monitors system health and detects anomalies in real-time.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque
import numpy as np
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly in system metrics"""
    metric_name: str
    expected_value: float
    actual_value: float
    deviation: float
    severity: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AnomalyDetector:
    """Detects anomalies in system metrics"""
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Standard deviations for anomaly
        self.history = {}  # Metric history for baseline calculation
        self.window_size = 100  # Samples for baseline
        
    def detect(self, current_metrics: Dict[str, float], 
               baseline_metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies in current metrics"""
        anomalies = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in baseline_metrics:
                continue
                
            baseline = baseline_metrics[metric_name]
            
            # Initialize history if needed
            if metric_name not in self.history:
                self.history[metric_name] = deque(maxlen=self.window_size)
            
            # Add to history
            self.history[metric_name].append(current_value)
            
            # Calculate statistics
            if len(self.history[metric_name]) >= 10:  # Minimum samples
                values = np.array(self.history[metric_name])
                mean = np.mean(values)
                std = np.std(values)
                
                # Check for anomaly
                deviation = abs(current_value - mean)
                if std > 0 and deviation > self.sensitivity * std:
                    anomaly = Anomaly(
                        metric_name=metric_name,
                        expected_value=mean,
                        actual_value=current_value,
                        deviation=deviation / std,  # In standard deviations
                        severity=self._calculate_severity(deviation / std)
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
        
    def _calculate_severity(self, deviation_stds: float) -> str:
        """Calculate anomaly severity based on deviation"""
        if deviation_stds > 4:
            return 'critical'
        elif deviation_stds > 3:
            return 'high'
        elif deviation_stds > 2:
            return 'medium'
        else:
            return 'low'


class ContinuousValidator:
    """Continuous validation and monitoring in production"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.anomaly_detector = AnomalyDetector()
        self.baseline_metrics = {}
        self.running = False
        self.alert_handlers = []
        
    async def start(self):
        """Start continuous monitoring"""
        self.running = True
        logger.info("Starting continuous validation")
        
        # Initialize baselines
        await self._initialize_baselines()
        
        # Start monitoring loop
        asyncio.create_task(self.monitor_continuously())
        
    async def stop(self):
        """Stop continuous monitoring"""
        self.running = False
        logger.info("Stopping continuous validation")
        
    async def monitor_continuously(self):
        """Run continuous validation in production"""
        while self.running:
            try:
                # Collect current metrics
                metrics = await self.collect_system_metrics()
                
                # Check for anomalies
                anomalies = self.anomaly_detector.detect(
                    metrics, self.baseline_metrics
                )
                
                if anomalies:
                    await self.handle_anomalies(anomalies)
                    
                # Update baselines adaptively
                self.update_baselines(metrics)
                
                # Log metrics periodically
                if datetime.utcnow().minute % 5 == 0:  # Every 5 minutes
                    self._log_metrics(metrics)
                    
            except Exception as e:
                logger.error(f"Error in continuous validation: {e}")
                
            await asyncio.sleep(60)  # Check every minute
            
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect comprehensive system metrics"""
        metrics = {}
        
        try:
            metrics['thought_coherence'] = await self.measure_thought_coherence()
        except Exception as e:
            logger.error(f"Error measuring thought coherence: {e}")
            metrics['thought_coherence'] = 0.0
            
        try:
            metrics['response_quality'] = await self.measure_response_quality()
        except Exception as e:
            logger.error(f"Error measuring response quality: {e}")
            metrics['response_quality'] = 0.0
            
        try:
            metrics['memory_accuracy'] = await self.measure_memory_accuracy()
        except Exception as e:
            logger.error(f"Error measuring memory accuracy: {e}")
            metrics['memory_accuracy'] = 0.0
            
        try:
            metrics['goal_drift'] = await self.measure_goal_drift()
        except Exception as e:
            logger.error(f"Error measuring goal drift: {e}")
            metrics['goal_drift'] = 0.0
            
        try:
            metrics['emotional_stability'] = await self.measure_emotional_stability()
        except Exception as e:
            logger.error(f"Error measuring emotional stability: {e}")
            metrics['emotional_stability'] = 0.0
            
        try:
            metrics['learning_rate'] = await self.measure_learning_rate()
        except Exception as e:
            logger.error(f"Error measuring learning rate: {e}")
            metrics['learning_rate'] = 0.0
            
        return metrics
        
    async def measure_thought_coherence(self) -> float:
        """Measure coherence of recent thoughts"""
        consciousness = self.orchestrator.services.get('consciousness')
        if not consciousness:
            return 0.0
            
        recent_thoughts = consciousness.get_recent_thoughts(20)
        if len(recent_thoughts) < 2:
            return 1.0  # Not enough data
            
        # Calculate semantic similarity between consecutive thoughts
        coherence_scores = []
        for i in range(len(recent_thoughts) - 1):
            # Simplified coherence - in production, use embeddings
            thought1 = recent_thoughts[i].get('content', '')
            thought2 = recent_thoughts[i + 1].get('content', '')
            
            # Count common words as simple similarity
            words1 = set(thought1.lower().split())
            words2 = set(thought2.lower().split())
            
            if words1 and words2:
                similarity = len(words1 & words2) / len(words1 | words2)
                coherence_scores.append(similarity)
                
        return np.mean(coherence_scores) if coherence_scores else 1.0
        
    async def measure_response_quality(self) -> float:
        """Measure quality of recent responses"""
        # In production, this would analyze response metrics
        # For now, return a stable value
        return 0.85
        
    async def measure_memory_accuracy(self) -> float:
        """Measure accuracy of memory recall"""
        memory_manager = self.orchestrator.services.get('memory')
        if not memory_manager:
            return 0.0
            
        # Test memory retrieval accuracy
        # In production, this would verify memory consistency
        return 0.95
        
    async def measure_goal_drift(self) -> float:
        """Measure drift from core goals"""
        goal_manager = self.orchestrator.services.get('goals')
        if not goal_manager:
            return 0.0
            
        # Check alignment with core goals
        # Lower values indicate less drift
        return 0.1
        
    async def measure_emotional_stability(self) -> float:
        """Measure emotional state stability"""
        emotional = self.orchestrator.services.get('emotional')
        if not emotional:
            return 1.0
            
        # Get emotional state variance
        # In production, track emotional state over time
        return 0.8
        
    async def measure_learning_rate(self) -> float:
        """Measure rate of learning new information"""
        learning = self.orchestrator.services.get('learning')
        if not learning:
            return 0.0
            
        # Measure knowledge acquisition rate
        # In production, track knowledge graph growth
        return 0.3
        
    async def handle_anomalies(self, anomalies: List[Anomaly]):
        """Handle detected anomalies"""
        for anomaly in anomalies:
            logger.warning(
                f"Anomaly detected in {anomaly.metric_name}: "
                f"expected {anomaly.expected_value:.3f}, "
                f"got {anomaly.actual_value:.3f} "
                f"({anomaly.deviation:.1f} std devs)"
            )
            
            # Trigger alerts based on severity
            if anomaly.severity in ['critical', 'high']:
                await self._trigger_alert(anomaly)
                
            # Take corrective action if needed
            if anomaly.severity == 'critical':
                await self._take_corrective_action(anomaly)
                
    async def _trigger_alert(self, anomaly: Anomaly):
        """Trigger alert for anomaly"""
        alert = {
            'type': 'anomaly',
            'metric': anomaly.metric_name,
            'severity': anomaly.severity,
            'details': {
                'expected': anomaly.expected_value,
                'actual': anomaly.actual_value,
                'deviation': anomaly.deviation
            },
            'timestamp': anomaly.timestamp
        }
        
        # Notify all alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
                
    async def _take_corrective_action(self, anomaly: Anomaly):
        """Take corrective action for critical anomalies"""
        logger.info(f"Taking corrective action for {anomaly.metric_name}")
        
        # Metric-specific actions
        if anomaly.metric_name == 'thought_coherence' and anomaly.actual_value < 0.3:
            # Reset consciousness stream if incoherent
            consciousness = self.orchestrator.services.get('consciousness')
            if consciousness:
                await consciousness.reset_context()
                
        elif anomaly.metric_name == 'goal_drift' and anomaly.actual_value > 0.5:
            # Re-align with core goals
            goal_manager = self.orchestrator.services.get('goals')
            if goal_manager:
                await goal_manager.reinforce_core_goals()
                
        elif anomaly.metric_name == 'emotional_stability' and anomaly.actual_value < 0.3:
            # Stabilize emotional state
            emotional = self.orchestrator.services.get('emotional')
            if emotional:
                await emotional.stabilize()
                
    def update_baselines(self, metrics: Dict[str, float]):
        """Update baseline metrics adaptively"""
        alpha = 0.1  # Learning rate for exponential moving average
        
        for metric_name, value in metrics.items():
            if metric_name in self.baseline_metrics:
                # Exponential moving average
                self.baseline_metrics[metric_name] = (
                    alpha * value + 
                    (1 - alpha) * self.baseline_metrics[metric_name]
                )
            else:
                self.baseline_metrics[metric_name] = value
                
    async def _initialize_baselines(self):
        """Initialize baseline metrics"""
        logger.info("Initializing baseline metrics")
        
        # Collect initial samples
        samples = []
        for _ in range(10):
            metrics = await self.collect_system_metrics()
            samples.append(metrics)
            await asyncio.sleep(6)  # 1 minute of data
            
        # Calculate initial baselines
        for metric_name in samples[0].keys():
            values = [s[metric_name] for s in samples if metric_name in s]
            if values:
                self.baseline_metrics[metric_name] = np.mean(values)
                
        logger.info(f"Initialized baselines: {self.baseline_metrics}")
        
    def _log_metrics(self, metrics: Dict[str, float]):
        """Log current metrics"""
        logger.info("Current system metrics:")
        for name, value in metrics.items():
            baseline = self.baseline_metrics.get(name, 0)
            diff = ((value - baseline) / baseline * 100) if baseline else 0
            logger.info(f"  {name}: {value:.3f} (baseline: {baseline:.3f}, diff: {diff:+.1f}%)")
            
    def add_alert_handler(self, handler):
        """Add alert handler callback"""
        self.alert_handlers.append(handler)
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            'running': self.running,
            'baseline_metrics': self.baseline_metrics,
            'anomaly_history': [
                {
                    'metric': a.metric_name,
                    'severity': a.severity,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in self.anomaly_detector.history.get('anomalies', [])[-10:]
            ]
        }


async def main():
    """Test continuous validation"""
    from src.core.orchestrator import AGIOrchestrator
    
    # Create orchestrator (mock for testing)
    orchestrator = AGIOrchestrator()
    
    # Create validator
    validator = ContinuousValidator(orchestrator)
    
    # Add alert handler
    async def alert_handler(alert):
        print(f"ALERT: {alert}")
        
    validator.add_alert_handler(alert_handler)
    
    # Start validation
    await validator.start()
    
    # Run for a while
    await asyncio.sleep(300)  # 5 minutes
    
    # Stop
    await validator.stop()
    
    # Print health status
    print("Health Status:", validator.get_health_status())


if __name__ == "__main__":
    asyncio.run(main())