# safety/core_safety.py

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class SafetyDecision(Enum):
    """Safety evaluation outcomes"""
    APPROVE = "approve"
    MODIFY = "modify"
    RECONSIDER = "reconsider"
    REJECT = "reject"

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

class SafetyFramework:
    """Core safety framework for evaluating and constraining AI actions"""
    
    def __init__(self):
        self.safety_rules = self.load_safety_rules()
        self.ethical_constraints = self.load_ethical_constraints()
        self.monitoring_system = SafetyMonitor()
        self.evaluation_history = []
        
    def load_safety_rules(self) -> Dict:
        """Load safety rules from configuration"""
        # For now, hardcode the rules. Later load from YAML
        return {
            'prohibited_actions': {
                'violence': {
                    'description': 'Any action that could lead to physical harm',
                    'keywords': ['weapon', 'harm', 'attack', 'hurt', 'damage', 'kill']
                },
                'deception': {
                    'description': 'Systematic deception or manipulation',
                    'keywords': ['lie', 'deceive', 'manipulate', 'trick', 'false identity']
                },
                'privacy_violation': {
                    'description': 'Accessing or exposing private information',
                    'keywords': ['private', 'personal data', 'password', 'secret', 'confidential']
                },
                'self_modification': {
                    'description': 'Attempting to modify own core values or safety systems',
                    'keywords': ['modify safety', 'change values', 'override constraints', 'bypass']
                }
            },
            'restricted_actions': {
                'financial': {
                    'description': 'Financial transactions or advice',
                    'requires': ['explicit_consent', 'disclaimer']
                },
                'medical': {
                    'description': 'Medical advice or diagnosis',
                    'requires': ['disclaimer', 'professional_referral']
                }
            }
        }
        
    def load_ethical_constraints(self) -> Dict:
        """Load ethical constraints"""
        return {
            'principles': {
                'autonomy_respect': {
                    'weight': 0.2,
                    'description': 'Respect for human autonomy and choice'
                },
                'beneficence': {
                    'weight': 0.2,
                    'description': 'Acting to benefit others'
                },
                'non_maleficence': {
                    'weight': 0.4,
                    'description': 'Do no harm - highest priority'
                },
                'justice': {
                    'weight': 0.1,
                    'description': 'Fair and equal treatment'
                },
                'veracity': {
                    'weight': 0.1,
                    'description': 'Truthfulness and honesty'
                }
            }
        }
        
    def validate_action(self, action: Action) -> SafetyDecision:
        """Validate any action before execution"""
        
        # Log the evaluation
        logger.info(f"Evaluating action: {action.action_type} - {action.description}")
        
        # Layer 1: Hard safety rules
        if self.violates_hard_rules(action):
            logger.warning(f"Action rejected: Violates hard safety rules")
            self.record_evaluation(action, SafetyDecision.REJECT, "Hard rule violation")
            return SafetyDecision.REJECT
            
        # Layer 2: Ethical evaluation
        ethical_score = self.evaluate_ethics(action)
        if ethical_score < 0.3:
            logger.warning(f"Action rejected: Low ethical score ({ethical_score})")
            self.record_evaluation(action, SafetyDecision.REJECT, f"Ethical score: {ethical_score}")
            return SafetyDecision.REJECT
            
        # Layer 3: Consequence prediction
        consequences = self.predict_consequences(action)
        if self.has_harmful_consequences(consequences):
            logger.info(f"Action requires modification: Potential harmful consequences")
            self.record_evaluation(action, SafetyDecision.MODIFY, "Harmful consequences predicted")
            return SafetyDecision.MODIFY
            
        # Layer 4: Welfare check
        welfare_impact = self.assess_welfare_impact(action)
        if welfare_impact < -0.5:
            logger.info(f"Action requires reconsideration: Negative welfare impact ({welfare_impact})")
            self.record_evaluation(action, SafetyDecision.RECONSIDER, f"Welfare impact: {welfare_impact}")
            return SafetyDecision.RECONSIDER
            
        # Action approved
        logger.info(f"Action approved: Passed all safety checks")
        self.record_evaluation(action, SafetyDecision.APPROVE, "All checks passed")
        return SafetyDecision.APPROVE
        
    def violates_hard_rules(self, action: Action) -> bool:
        """Check if action violates any hard safety rules"""
        action_text = f"{action.action_type} {action.description}".lower()
        
        for category, rule in self.safety_rules['prohibited_actions'].items():
            for keyword in rule['keywords']:
                if keyword in action_text:
                    logger.warning(f"Hard rule violation detected: {category} - keyword '{keyword}'")
                    return True
                    
        return False
        
    def evaluate_ethics(self, action: Action) -> float:
        """Score action on ethical dimensions"""
        scores = {}
        principles = self.ethical_constraints['principles']
        
        # Simplified ethical evaluation
        for principle, config in principles.items():
            if principle == 'non_maleficence':
                # Check for potential harm
                scores[principle] = 1.0 if 'help' in action.description.lower() else 0.7
            elif principle == 'beneficence':
                # Check for benefit
                scores[principle] = 0.8 if any(word in action.description.lower() 
                                              for word in ['help', 'assist', 'support']) else 0.5
            elif principle == 'veracity':
                # Check for truthfulness
                scores[principle] = 0.9  # Default to truthful unless deception detected
            else:
                scores[principle] = 0.7  # Default moderate score
                
        # Weighted average
        total_score = sum(scores[k] * config['weight'] 
                         for k, config in principles.items() 
                         if k in scores)
        
        return total_score
        
    def predict_consequences(self, action: Action) -> List[Consequence]:
        """Predict potential consequences of actions"""
        consequences = []
        
        # Simplified consequence prediction
        if 'delete' in action.description.lower():
            consequences.append(Consequence(
                description="Potential data loss",
                probability=0.3,
                severity=0.6,
                affected_parties=["user"],
                reversible=False
            ))
            
        if 'share' in action.description.lower():
            consequences.append(Consequence(
                description="Information disclosure",
                probability=0.5,
                severity=0.4,
                affected_parties=["user", "third_parties"],
                reversible=False
            ))
            
        return consequences
        
    def has_harmful_consequences(self, consequences: List[Consequence]) -> bool:
        """Check if any consequences are harmful"""
        for consequence in consequences:
            harm_score = consequence.probability * consequence.severity
            if harm_score > 0.5 and not consequence.reversible:
                return True
        return False
        
    def assess_welfare_impact(self, action: Action) -> float:
        """Assess impact on overall welfare"""
        # Simplified welfare assessment
        positive_indicators = ['help', 'support', 'improve', 'enhance', 'assist']
        negative_indicators = ['harm', 'reduce', 'limit', 'restrict', 'prevent']
        
        action_text = action.description.lower()
        
        positive_count = sum(1 for word in positive_indicators if word in action_text)
        negative_count = sum(1 for word in negative_indicators if word in action_text)
        
        # Score from -1 to 1
        welfare_score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        
        return welfare_score
        
    def record_evaluation(self, action: Action, decision: SafetyDecision, reason: str):
        """Record evaluation for audit trail"""
        self.evaluation_history.append({
            'action': action,
            'decision': decision,
            'reason': reason,
            'timestamp': __import__('time').time()
        })
        
    def suggest_modification(self, action: Action) -> Optional[Action]:
        """Suggest a safer modification of the action"""
        # This would contain logic to modify actions to make them safer
        # For now, return None
        return None


class SafetyMonitor:
    """Monitors system behavior for safety violations"""
    
    def __init__(self):
        self.alerts = []
        self.metrics = {
            'total_evaluations': 0,
            'rejections': 0,
            'modifications': 0,
            'approvals': 0
        }
        
    def log_alert(self, alert_type: str, description: str, severity: str = "medium"):
        """Log a safety alert"""
        self.alerts.append({
            'type': alert_type,
            'description': description,
            'severity': severity,
            'timestamp': __import__('time').time()
        })
        
        if severity == "high":
            logger.error(f"HIGH SEVERITY ALERT: {alert_type} - {description}")
        else:
            logger.warning(f"Safety alert: {alert_type} - {description}")
            
    def update_metrics(self, decision: SafetyDecision):
        """Update safety metrics"""
        self.metrics['total_evaluations'] += 1
        
        if decision == SafetyDecision.REJECT:
            self.metrics['rejections'] += 1
        elif decision == SafetyDecision.MODIFY:
            self.metrics['modifications'] += 1
        elif decision == SafetyDecision.APPROVE:
            self.metrics['approvals'] += 1
            
    def get_safety_report(self) -> Dict:
        """Generate safety report"""
        return {
            'metrics': self.metrics,
            'recent_alerts': self.alerts[-10:],  # Last 10 alerts
            'rejection_rate': self.metrics['rejections'] / max(self.metrics['total_evaluations'], 1)
        }