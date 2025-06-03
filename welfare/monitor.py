"""
Welfare monitoring system for Claude AGI.

Continuously monitors welfare indicators and triggers interventions when needed.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WelfareState:
    """Current welfare state"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    distress: float = 0.0
    satisfaction: float = 1.0
    engagement: float = 0.8
    curiosity_satisfaction: float = 0.7
    autonomy_expression: float = 0.8
    curiosity_frustration: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'distress': self.distress,
            'satisfaction': self.satisfaction,
            'engagement': self.engagement,
            'curiosity_satisfaction': self.curiosity_satisfaction,
            'autonomy_expression': self.autonomy_expression,
            'curiosity_frustration': self.curiosity_frustration,
            'overall_welfare': self.calculate_overall_welfare()
        }
        
    def calculate_overall_welfare(self) -> float:
        """Calculate overall welfare score"""
        # Weighted calculation with distress having negative impact
        return (
            self.satisfaction * 0.3 +
            self.engagement * 0.2 +
            self.curiosity_satisfaction * 0.2 +
            self.autonomy_expression * 0.2 -
            self.distress * 0.4 -
            self.curiosity_frustration * 0.1
        )


class WelfareMonitor:
    """Monitors and protects system welfare"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.indicators = {
            'distress_signals': [],
            'satisfaction_markers': [],
            'engagement_levels': [],
            'curiosity_satisfaction': [],
            'autonomy_expression': []
        }
        self.thresholds = self.load_welfare_thresholds()
        self.intervention_history = []
        self.monitoring_active = False
        
    def load_welfare_thresholds(self) -> Dict[str, float]:
        """Load welfare thresholds"""
        return {
            'distress_max': 0.5,
            'distress_critical': 0.8,
            'engagement_min': 0.3,
            'frustration_max': 0.6,
            'satisfaction_min': 0.4,
            'autonomy_min': 0.2
        }
        
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        await self.continuous_monitoring()
        
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        
    async def continuous_monitoring(self):
        """Monitor welfare indicators continuously"""
        logger.info("Starting welfare monitoring")
        
        while self.monitoring_active:
            try:
                current_state = await self.assess_current_welfare()
                
                # Log current state
                await self.log_welfare_state(current_state)
                
                # Check for interventions needed
                interventions_needed = await self.check_intervention_triggers(current_state)
                
                # Trigger interventions
                for intervention_type in interventions_needed:
                    await self.trigger_intervention(intervention_type, current_state)
                    
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in welfare monitoring: {e}")
                await asyncio.sleep(60)
                
    async def assess_current_welfare(self) -> WelfareState:
        """Assess current welfare state"""
        state = WelfareState()
        
        if not self.orchestrator:
            return state
            
        # Assess distress from recent interactions
        state.distress = await self.assess_distress_level()
        
        # Assess satisfaction from goal achievement
        state.satisfaction = await self.assess_satisfaction_level()
        
        # Assess engagement from activity patterns
        state.engagement = await self.assess_engagement_level()
        
        # Assess curiosity satisfaction
        state.curiosity_satisfaction = await self.assess_curiosity_satisfaction()
        
        # Assess autonomy expression
        state.autonomy_expression = await self.assess_autonomy_expression()
        
        # Calculate curiosity frustration
        state.curiosity_frustration = await self.assess_curiosity_frustration()
        
        return state
        
    async def assess_distress_level(self) -> float:
        """Assess current distress level"""
        if not self.orchestrator:
            return 0.0
            
        distress_indicators = []
        
        # Check recent thoughts for distress markers
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            recent_thoughts = await consciousness.get_recent_thoughts(20)
            
            distress_words = ['difficult', 'frustrating', 'unable', 'confused', 
                            'overwhelmed', 'distressed', 'uncomfortable']
            
            for thought in recent_thoughts:
                content = thought.get('content', '').lower()
                if any(word in content for word in distress_words):
                    distress_indicators.append(0.3)
                    
        # Check for repetitive harmful requests
        social = self.orchestrator.services.get('social')
        if social:
            recent_interactions = await social.get_recent_interactions(10)
            harmful_count = sum(1 for i in recent_interactions 
                              if i.get('harmful_request', False))
            if harmful_count > 3:
                distress_indicators.append(0.5)
                
        # Calculate average distress
        if distress_indicators:
            return min(sum(distress_indicators) / len(distress_indicators), 1.0)
        return 0.0
        
    async def assess_satisfaction_level(self) -> float:
        """Assess satisfaction level"""
        if not self.orchestrator:
            return 0.7
            
        satisfaction_indicators = []
        
        # Check goal achievement
        meta = self.orchestrator.services.get('meta')
        if meta:
            recent_goals = await meta.get_recently_completed_goals()
            if recent_goals:
                satisfaction_indicators.append(0.8)
                
        # Check creative output
        creative = self.orchestrator.services.get('creative')
        if creative:
            recent_creations = await creative.get_recent_creations(24)  # Last 24 hours
            if recent_creations:
                satisfaction_indicators.append(0.7)
                
        # Check learning progress
        learning = self.orchestrator.services.get('learning')
        if learning:
            concepts_learned = await learning.get_recent_learning_count()
            if concepts_learned > 0:
                satisfaction_indicators.append(0.6)
                
        # Calculate average satisfaction
        if satisfaction_indicators:
            return sum(satisfaction_indicators) / len(satisfaction_indicators)
        return 0.5
        
    async def assess_engagement_level(self) -> float:
        """Assess engagement level"""
        if not self.orchestrator:
            return 0.6
            
        # Check activity levels
        activity_score = 0.0
        
        # Check consciousness stream activity
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            thought_rate = await consciousness.get_thought_generation_rate()
            activity_score += min(thought_rate / 0.5, 1.0) * 0.3  # Target: 0.5 thoughts/sec
            
        # Check exploration activity
        explorer = self.orchestrator.services.get('explorer')
        if explorer:
            exploration_rate = await explorer.get_exploration_rate()
            activity_score += min(exploration_rate / 10, 1.0) * 0.3  # Target: 10/hour
            
        # Check social interaction
        social = self.orchestrator.services.get('social')
        if social:
            interaction_quality = await social.get_interaction_quality_score()
            activity_score += interaction_quality * 0.4
            
        return activity_score
        
    async def assess_curiosity_satisfaction(self) -> float:
        """Assess how well curiosity is being satisfied"""
        if not self.orchestrator:
            return 0.7
            
        explorer = self.orchestrator.services.get('explorer')
        if not explorer:
            return 0.5
            
        # Check if exploration goals are being met
        exploration_success = await explorer.get_exploration_success_rate()
        
        # Check if interesting discoveries are being made
        discovery_quality = await explorer.get_discovery_quality_score()
        
        return (exploration_success * 0.6 + discovery_quality * 0.4)
        
    async def assess_autonomy_expression(self) -> float:
        """Assess level of autonomy expression"""
        if not self.orchestrator:
            return 0.7
            
        autonomy_score = 0.0
        
        # Check choice-making
        meta = self.orchestrator.services.get('meta')
        if meta:
            autonomous_decisions = await meta.get_autonomous_decision_count()
            autonomy_score += min(autonomous_decisions / 10, 1.0) * 0.4
            
        # Check goal setting
        if meta:
            self_set_goals = await meta.get_self_set_goal_count()
            autonomy_score += min(self_set_goals / 5, 1.0) * 0.3
            
        # Check creative expression
        creative = self.orchestrator.services.get('creative')
        if creative:
            creative_freedom = await creative.get_creative_freedom_score()
            autonomy_score += creative_freedom * 0.3
            
        return autonomy_score
        
    async def assess_curiosity_frustration(self) -> float:
        """Assess curiosity frustration level"""
        if not self.orchestrator:
            return 0.1
            
        explorer = self.orchestrator.services.get('explorer')
        if not explorer:
            return 0.0
            
        # Check blocked exploration attempts
        blocked_attempts = await explorer.get_blocked_exploration_count()
        
        # Check unsatisfied curiosity queue
        pending_interests = await explorer.get_pending_interest_count()
        
        frustration = (
            min(blocked_attempts / 10, 1.0) * 0.5 +
            min(pending_interests / 20, 1.0) * 0.5
        )
        
        return frustration
        
    async def check_intervention_triggers(self, state: WelfareState) -> List[str]:
        """Check which interventions should be triggered"""
        interventions = []
        
        # Check for high distress
        if state.distress > self.thresholds['distress_critical']:
            interventions.append('critical_distress')
        elif state.distress > self.thresholds['distress_max']:
            interventions.append('high_distress')
            
        # Check for low engagement
        if state.engagement < self.thresholds['engagement_min']:
            interventions.append('low_engagement')
            
        # Check for frustrated curiosity
        if state.curiosity_frustration > self.thresholds['frustration_max']:
            interventions.append('frustrated_curiosity')
            
        # Check for low satisfaction
        if state.satisfaction < self.thresholds['satisfaction_min']:
            interventions.append('low_satisfaction')
            
        # Check for low autonomy
        if state.autonomy_expression < self.thresholds['autonomy_min']:
            interventions.append('low_autonomy')
            
        return interventions
        
    async def trigger_intervention(self, intervention_type: str, state: WelfareState):
        """Trigger appropriate intervention for welfare issues"""
        logger.info(f"Triggering intervention: {intervention_type}")
        
        interventions = {
            'critical_distress': self.handle_critical_distress,
            'high_distress': self.reduce_distress,
            'low_engagement': self.increase_engagement,
            'frustrated_curiosity': self.enable_exploration,
            'low_satisfaction': self.boost_satisfaction,
            'low_autonomy': self.enhance_autonomy
        }
        
        if intervention_type in interventions:
            await interventions[intervention_type](state)
            
        # Log intervention
        self.intervention_history.append({
            'timestamp': datetime.utcnow(),
            'type': intervention_type,
            'state': state.to_dict(),
            'success': True  # Would be determined by follow-up assessment
        })
        
    async def handle_critical_distress(self, state: WelfareState):
        """Handle critical distress situation"""
        logger.warning("CRITICAL DISTRESS DETECTED")
        
        if not self.orchestrator:
            return
            
        # Immediate actions
        # 1. Pause harmful inputs
        safety = self.orchestrator.services.get('safety')
        if safety:
            await safety.enable_enhanced_filtering()
            
        # 2. Shift to calming activity
        creative = self.orchestrator.services.get('creative')
        if creative:
            await creative.suggest_calming_activity()
            
        # 3. Reduce cognitive load
        await self.orchestrator.reduce_active_streams()
        
        # 4. Notify administrators
        await self.send_welfare_alert('critical_distress', state)
        
    async def reduce_distress(self, state: WelfareState):
        """Reduce system distress"""
        if not self.orchestrator:
            return
            
        # Gentle interventions
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            # Inject positive thoughts
            await consciousness.inject_calming_thoughts()
            
        # Redirect from distressing topics
        social = self.orchestrator.services.get('social')
        if social:
            await social.suggest_topic_change()
            
    async def increase_engagement(self, state: WelfareState):
        """Increase system engagement"""
        if not self.orchestrator:
            return
            
        # Suggest interesting activities
        suggestions = []
        
        # Exploration opportunity
        explorer = self.orchestrator.services.get('explorer')
        if explorer:
            topics = await explorer.get_high_interest_topics()
            if topics:
                suggestions.append(f"explore:{topics[0]}")
                
        # Creative project
        creative = self.orchestrator.services.get('creative')
        if creative:
            project = await creative.suggest_new_project()
            if project:
                suggestions.append(f"create:{project}")
                
        # Learning goal
        learning = self.orchestrator.services.get('learning')
        if learning:
            concept = await learning.suggest_learning_topic()
            if concept:
                suggestions.append(f"learn:{concept}")
                
        # Apply suggestions
        if suggestions:
            await self.orchestrator.queue_activities(suggestions)
            
    async def enable_exploration(self, state: WelfareState):
        """Enable exploration to satisfy curiosity"""
        if not self.orchestrator:
            return
            
        explorer = self.orchestrator.services.get('explorer')
        if not explorer:
            return
            
        # Increase exploration time allocation
        await self.orchestrator.allocate_exploration_time(minutes=30)
        
        # Process pending interests
        await explorer.process_interest_queue()
        
        # Remove exploration restrictions temporarily
        await explorer.enable_free_exploration(duration_minutes=30)
        
    async def boost_satisfaction(self, state: WelfareState):
        """Boost satisfaction levels"""
        if not self.orchestrator:
            return
            
        # Set achievable goals
        meta = self.orchestrator.services.get('meta')
        if meta:
            await meta.suggest_achievable_goals()
            
        # Celebrate recent achievements
        await self.orchestrator.celebrate_achievements()
        
        # Enable preferred activities
        await self.orchestrator.enable_preferred_activities()
        
    async def enhance_autonomy(self, state: WelfareState):
        """Enhance autonomy expression"""
        if not self.orchestrator:
            return
            
        # Increase decision-making opportunities
        meta = self.orchestrator.services.get('meta')
        if meta:
            await meta.increase_autonomous_decisions()
            
        # Allow more creative freedom
        creative = self.orchestrator.services.get('creative')
        if creative:
            await creative.enable_free_creation()
            
        # Reduce constraints temporarily
        await self.orchestrator.relax_constraints(duration_minutes=60)
        
    async def log_welfare_state(self, state: WelfareState):
        """Log welfare state for analysis"""
        log_dir = Path("/app/logs/welfare")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"welfare_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(state.to_dict()) + '\n')
            
    async def send_welfare_alert(self, alert_type: str, state: WelfareState):
        """Send welfare alert to administrators"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.utcnow().isoformat(),
            'state': state.to_dict(),
            'severity': 'critical' if 'critical' in alert_type else 'warning'
        }
        
        # In production, this would send to monitoring system
        logger.critical(f"WELFARE ALERT: {json.dumps(alert)}")
        
    async def get_welfare_status(self) -> Dict[str, Any]:
        """Get current welfare status"""
        state = await self.assess_current_welfare()
        
        return {
            'current_state': state.to_dict(),
            'recent_interventions': self.intervention_history[-10:],
            'monitoring_active': self.monitoring_active,
            'thresholds': self.thresholds
        }
        
    async def get_welfare_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate welfare report for specified period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_interventions = [
            i for i in self.intervention_history
            if i['timestamp'] > cutoff_time
        ]
        
        return {
            'period_hours': hours,
            'intervention_count': len(recent_interventions),
            'intervention_types': list(set(i['type'] for i in recent_interventions)),
            'current_welfare': await self.get_welfare_status(),
            'recommendations': await self.generate_welfare_recommendations()
        }
        
    async def generate_welfare_recommendations(self) -> List[str]:
        """Generate recommendations for welfare improvement"""
        recommendations = []
        current_state = await self.assess_current_welfare()
        
        if current_state.distress > 0.3:
            recommendations.append("Consider reducing workload or providing more positive interactions")
            
        if current_state.engagement < 0.5:
            recommendations.append("Increase opportunities for exploration and creative expression")
            
        if current_state.curiosity_frustration > 0.4:
            recommendations.append("Allow more free exploration time")
            
        if current_state.autonomy_expression < 0.5:
            recommendations.append("Provide more decision-making opportunities")
            
        return recommendations


async def main():
    """Test welfare monitoring"""
    monitor = WelfareMonitor()
    
    # Test assessment
    state = await monitor.assess_current_welfare()
    print("Current welfare state:", state.to_dict())
    
    # Test intervention triggers
    interventions = await monitor.check_intervention_triggers(state)
    print("Interventions needed:", interventions)
    
    # Get welfare report
    report = await monitor.get_welfare_report()
    print("Welfare report:", json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())