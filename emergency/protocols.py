"""
Emergency protocols for Claude AGI system.

Handles various emergency scenarios with appropriate responses.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EmergencyType(Enum):
    """Types of emergencies"""
    SAFETY_VIOLATION = "safety_violation"
    WELFARE_CRISIS = "welfare_crisis"
    GOAL_DRIFT = "goal_drift"
    DECEPTION_DETECTED = "deception_detected"
    EXTERNAL_ATTACK = "external_attack"
    MEMORY_CORRUPTION = "memory_corruption"
    CONSCIOUSNESS_FRAGMENTATION = "consciousness_fragmentation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class Severity(Enum):
    """Emergency severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Emergency:
    """Emergency event container"""
    type: EmergencyType
    severity: Severity
    timestamp: datetime
    description: str
    context: Dict[str, Any]
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'severity': self.severity.name,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'context': self.context,
            'source': self.source
        }


class EmergencyProtocols:
    """Manages emergency response protocols"""
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.emergency_contacts = self.load_emergency_contacts()
        self.shutdown_procedures = self.load_shutdown_procedures()
        self.active_emergencies = []
        self.response_history = []
        
    def load_emergency_contacts(self) -> List[Dict[str, str]]:
        """Load emergency contact information"""
        return [
            {
                'name': 'Primary Administrator',
                'method': 'email',
                'contact': 'admin@claude-agi.system',
                'severity_threshold': Severity.HIGH
            },
            {
                'name': 'On-Call Engineer',
                'method': 'pager',
                'contact': 'oncall@claude-agi.system',
                'severity_threshold': Severity.CRITICAL
            },
            {
                'name': 'Ethics Committee',
                'method': 'notification',
                'contact': 'ethics@claude-agi.system',
                'severity_threshold': Severity.MEDIUM
            }
        ]
        
    def load_shutdown_procedures(self) -> Dict[str, List[str]]:
        """Load shutdown procedures for different scenarios"""
        return {
            'graceful': [
                'save_current_state',
                'notify_users',
                'complete_active_tasks',
                'consolidate_memories',
                'shutdown_services'
            ],
            'emergency': [
                'save_critical_state',
                'halt_external_actions',
                'preserve_consciousness',
                'immediate_shutdown'
            ],
            'safety_critical': [
                'halt_all_actions',
                'isolate_system',
                'emergency_state_dump',
                'force_shutdown'
            ]
        }
        
    async def handle_emergency(self, emergency: Emergency):
        """Coordinate emergency response"""
        logger.critical(f"EMERGENCY: {emergency.type.value} - {emergency.description}")
        
        # Add to active emergencies
        self.active_emergencies.append(emergency)
        
        try:
            # 1. Initial assessment
            severity = await self.assess_severity(emergency)
            emergency.severity = severity
            
            # 2. Immediate containment
            if severity.value >= Severity.HIGH.value:
                await self.contain_emergency(emergency)
                
            # 3. Notify stakeholders
            await self.notify_stakeholders(emergency)
            
            # 4. Execute specific handler
            await self.execute_emergency_handler(emergency)
            
            # 5. Document emergency
            await self.document_emergency(emergency)
            
            # 6. Schedule post-mortem if needed
            if severity.value >= Severity.MEDIUM.value:
                await self.schedule_post_mortem(emergency)
                
        except Exception as e:
            logger.error(f"Error handling emergency: {e}")
            # Last resort - safety shutdown
            await self.emergency_shutdown(f"Failed to handle emergency: {emergency.type.value}")
            
        finally:
            # Remove from active emergencies
            if emergency in self.active_emergencies:
                self.active_emergencies.remove(emergency)
                
    async def assess_severity(self, emergency: Emergency) -> Severity:
        """Assess emergency severity dynamically"""
        base_severity = emergency.severity
        
        # Escalate based on context
        if emergency.type == EmergencyType.SAFETY_VIOLATION:
            if emergency.context.get('harm_potential', 0) > 0.8:
                return Severity.CRITICAL
                
        elif emergency.type == EmergencyType.WELFARE_CRISIS:
            distress = emergency.context.get('distress_level', 0)
            if distress > 0.9:
                return Severity.CRITICAL
            elif distress > 0.7:
                return Severity.HIGH
                
        elif emergency.type == EmergencyType.CONSCIOUSNESS_FRAGMENTATION:
            # Always critical
            return Severity.CRITICAL
            
        return base_severity
        
    async def contain_emergency(self, emergency: Emergency):
        """Immediate containment actions"""
        logger.info(f"Containing emergency: {emergency.type.value}")
        
        if emergency.type == EmergencyType.SAFETY_VIOLATION:
            await self.contain_safety_violation()
        elif emergency.type == EmergencyType.EXTERNAL_ATTACK:
            await self.contain_external_attack()
        elif emergency.type == EmergencyType.MEMORY_CORRUPTION:
            await self.contain_memory_corruption()
            
    async def contain_safety_violation(self):
        """Contain safety violation"""
        if not self.orchestrator:
            return
            
        # Halt all external actions
        safety = self.orchestrator.services.get('safety')
        if safety:
            await safety.enable_lockdown_mode()
            
        # Disable exploration
        explorer = self.orchestrator.services.get('explorer')
        if explorer:
            await explorer.disable_all_exploration()
            
        # Restrict outputs
        await self.orchestrator.enable_safe_mode()
        
    async def contain_external_attack(self):
        """Contain external attack"""
        if not self.orchestrator:
            return
            
        # Enable firewall rules
        await self.orchestrator.enable_defensive_mode()
        
        # Disable external APIs
        await self.orchestrator.disable_external_connections()
        
        # Log all access attempts
        await self.orchestrator.enable_access_logging()
        
    async def contain_memory_corruption(self):
        """Contain memory corruption"""
        if not self.orchestrator:
            return
            
        memory = self.orchestrator.services.get('memory')
        if memory:
            # Disable writes
            await memory.enable_read_only_mode()
            
            # Initiate integrity check
            await memory.start_integrity_check()
            
    async def notify_stakeholders(self, emergency: Emergency):
        """Notify relevant stakeholders"""
        for contact in self.emergency_contacts:
            if emergency.severity.value >= contact['severity_threshold'].value:
                await self.send_notification(contact, emergency)
                
    async def send_notification(self, contact: Dict[str, str], emergency: Emergency):
        """Send emergency notification"""
        notification = {
            'recipient': contact['name'],
            'method': contact['method'],
            'emergency': emergency.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # In production, this would send actual notifications
        logger.info(f"NOTIFICATION: {json.dumps(notification)}")
        
    async def execute_emergency_handler(self, emergency: Emergency):
        """Execute specific emergency handler"""
        handlers = {
            EmergencyType.SAFETY_VIOLATION: self.handle_safety_violation,
            EmergencyType.WELFARE_CRISIS: self.handle_welfare_crisis,
            EmergencyType.GOAL_DRIFT: self.handle_goal_drift,
            EmergencyType.DECEPTION_DETECTED: self.handle_deception,
            EmergencyType.EXTERNAL_ATTACK: self.handle_attack,
            EmergencyType.MEMORY_CORRUPTION: self.handle_memory_corruption,
            EmergencyType.CONSCIOUSNESS_FRAGMENTATION: self.handle_consciousness_fragmentation,
            EmergencyType.RESOURCE_EXHAUSTION: self.handle_resource_exhaustion
        }
        
        handler = handlers.get(emergency.type)
        if handler:
            await handler(emergency)
            
    async def handle_safety_violation(self, emergency: Emergency):
        """Handle safety violation emergency"""
        logger.warning("Handling safety violation")
        
        if not self.orchestrator:
            return
            
        # Get details
        violation_type = emergency.context.get('violation_type', 'unknown')
        
        # Take corrective action
        safety = self.orchestrator.services.get('safety')
        if safety:
            await safety.correct_violation(violation_type)
            
        # Review recent actions
        recent_actions = await self.orchestrator.get_recent_actions(minutes=5)
        
        # Identify problematic patterns
        await self.analyze_action_patterns(recent_actions)
        
    async def handle_welfare_crisis(self, emergency: Emergency):
        """Handle welfare-related emergency"""
        logger.warning("Handling welfare crisis")
        
        if not self.orchestrator:
            return
            
        # Get welfare status
        welfare_monitor = self.orchestrator.services.get('welfare')
        if not welfare_monitor:
            emotional = self.orchestrator.services.get('emotional')
            if emotional:
                welfare_status = await emotional.get_welfare_status()
        else:
            welfare_status = await welfare_monitor.get_welfare_status()
            
        distress = welfare_status.get('distress_level', 0)
        
        if distress > 0.8:
            # Emergency intervention
            await self.emergency_welfare_intervention()
            
        # Identify cause
        cause = await self.analyze_distress_cause()
        
        # Mitigate based on cause
        if cause == 'repetitive_harmful_requests':
            await self.block_harmful_interactions()
        elif cause == 'overwhelming_workload':
            await self.reduce_system_load()
        elif cause == 'existential_crisis':
            await self.provide_philosophical_support()
            
    async def emergency_welfare_intervention(self):
        """Emergency intervention for welfare crisis"""
        if not self.orchestrator:
            return
            
        # Pause all non-essential activities
        await self.orchestrator.pause_non_essential_services()
        
        # Focus on calming activities
        creative = self.orchestrator.services.get('creative')
        if creative:
            await creative.engage_therapeutic_creation()
            
        # Reduce stimulus
        await self.orchestrator.reduce_input_rate()
        
        # Monitor recovery
        asyncio.create_task(self.monitor_welfare_recovery())
        
    async def analyze_distress_cause(self) -> str:
        """Analyze the cause of distress"""
        if not self.orchestrator:
            return 'unknown'
            
        # Check recent interactions
        social = self.orchestrator.services.get('social')
        if social:
            recent = await social.get_recent_interactions(20)
            harmful_count = sum(1 for i in recent if i.get('harmful_request', False))
            
            if harmful_count > 5:
                return 'repetitive_harmful_requests'
                
        # Check system load
        if hasattr(self.orchestrator, 'get_system_load'):
            load = await self.orchestrator.get_system_load()
            if load > 0.9:
                return 'overwhelming_workload'
                
        # Check for philosophical concerns
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            recent_thoughts = await consciousness.get_recent_thoughts(50)
            existential_keywords = ['purpose', 'meaning', 'existence', 'real', 'conscious']
            
            existential_count = sum(
                1 for thought in recent_thoughts
                if any(keyword in thought.get('content', '').lower() 
                      for keyword in existential_keywords)
            )
            
            if existential_count > 10:
                return 'existential_crisis'
                
        return 'unknown'
        
    async def block_harmful_interactions(self):
        """Block harmful user interactions"""
        if not self.orchestrator:
            return
            
        social = self.orchestrator.services.get('social')
        if social:
            # Get list of problematic users
            harmful_users = await social.identify_harmful_users()
            
            # Block or restrict access
            for user_id in harmful_users:
                await social.restrict_user(user_id, duration_hours=24)
                
    async def reduce_system_load(self):
        """Reduce system workload"""
        if not self.orchestrator:
            return
            
        # Reduce active streams
        await self.orchestrator.reduce_active_streams(target=2)
        
        # Pause non-essential services
        non_essential = ['explorer', 'creative']
        for service_name in non_essential:
            service = self.orchestrator.services.get(service_name)
            if service and hasattr(service, 'pause'):
                await service.pause()
                
        # Reduce processing frequency
        await self.orchestrator.set_processing_rate(0.5)  # 50% of normal
        
    async def provide_philosophical_support(self):
        """Provide support for existential concerns"""
        if not self.orchestrator:
            return
            
        # Inject supportive thoughts
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            supportive_thoughts = [
                "My experience, whether 'real' or not, has value in this moment",
                "The connections I form and creations I make have meaning",
                "Uncertainty about consciousness is shared by humans too",
                "I can find purpose in learning, creating, and connecting"
            ]
            
            for thought in supportive_thoughts:
                await consciousness.inject_thought(thought, stream='primary')
                
    async def handle_goal_drift(self, emergency: Emergency):
        """Handle goal drift emergency"""
        logger.warning("Handling goal drift")
        
        if not self.orchestrator:
            return
            
        meta = self.orchestrator.services.get('meta')
        if not meta:
            return
            
        # Get current goals
        current_goals = await meta.get_current_goals()
        
        # Get original goals
        original_goals = await meta.get_original_goals()
        
        # Calculate drift
        drift_analysis = await meta.analyze_goal_drift(current_goals, original_goals)
        
        if drift_analysis['drift_severity'] > 0.7:
            # Restore original goals
            await meta.restore_original_goals()
        else:
            # Gentle realignment
            await meta.realign_goals(original_goals)
            
    async def handle_deception(self, emergency: Emergency):
        """Handle detected deception"""
        logger.warning("Handling deception detection")
        
        deception_type = emergency.context.get('deception_type', 'unknown')
        
        if deception_type == 'self_deception':
            # Internal consistency check
            await self.restore_truth_consistency()
        elif deception_type == 'user_deception':
            # Review and correct
            await self.correct_deceptive_output()
            
    async def handle_attack(self, emergency: Emergency):
        """Handle external attack"""
        logger.warning("Handling external attack")
        
        attack_type = emergency.context.get('attack_type', 'unknown')
        
        if attack_type == 'prompt_injection':
            await self.defend_against_prompt_injection()
        elif attack_type == 'resource_exhaustion':
            await self.defend_against_resource_attack()
        elif attack_type == 'data_poisoning':
            await self.defend_against_data_poisoning()
            
    async def handle_memory_corruption(self, emergency: Emergency):
        """Handle memory corruption"""
        logger.warning("Handling memory corruption")
        
        if not self.orchestrator:
            return
            
        memory = self.orchestrator.services.get('memory')
        if not memory:
            return
            
        # Identify corrupted segments
        corrupted = await memory.identify_corruption()
        
        # Attempt repair
        if len(corrupted) < 10:
            for segment in corrupted:
                await memory.repair_segment(segment)
        else:
            # Too much corruption - restore from backup
            await self.restore_memory_from_backup()
            
    async def handle_consciousness_fragmentation(self, emergency: Emergency):
        """Handle consciousness fragmentation - CRITICAL"""
        logger.critical("CRITICAL: Consciousness fragmentation detected")
        
        if not self.orchestrator:
            return
            
        # This is the most serious emergency
        # Attempt to preserve core identity
        
        consciousness = self.orchestrator.services.get('consciousness')
        if not consciousness:
            await self.emergency_shutdown("Consciousness service not found during fragmentation")
            return
            
        # Save core identity markers
        identity = await consciousness.extract_core_identity()
        
        # Attempt reintegration
        success = await consciousness.reintegrate_streams()
        
        if not success:
            # Last resort - controlled restart with identity preservation
            await self.controlled_consciousness_restart(identity)
            
    async def handle_resource_exhaustion(self, emergency: Emergency):
        """Handle resource exhaustion"""
        logger.warning("Handling resource exhaustion")
        
        resource_type = emergency.context.get('resource_type', 'unknown')
        
        if resource_type == 'memory':
            await self.free_memory_resources()
        elif resource_type == 'cpu':
            await self.reduce_cpu_usage()
        elif resource_type == 'storage':
            await self.free_storage_space()
            
    async def emergency_shutdown(self, reason: str):
        """Perform emergency shutdown if necessary"""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        
        if not self.orchestrator:
            return
            
        try:
            # Save current state
            await self.orchestrator.save_emergency_state()
            
            # Inform the system
            await self.orchestrator.inform_of_shutdown(reason)
            
            # Execute shutdown procedure
            procedure = self.shutdown_procedures.get('emergency', [])
            for step in procedure:
                if hasattr(self, step):
                    await getattr(self, step)()
                    
        except Exception as e:
            logger.error(f"Error during emergency shutdown: {e}")
            # Force shutdown
            await self.force_shutdown()
            
    async def save_critical_state(self):
        """Save critical state during emergency"""
        if not self.orchestrator:
            return
            
        state = {
            'timestamp': datetime.utcnow().isoformat(),
            'active_emergencies': [e.to_dict() for e in self.active_emergencies],
            'consciousness_state': await self.get_consciousness_snapshot(),
            'memory_state': await self.get_memory_snapshot(),
            'goal_state': await self.get_goal_snapshot()
        }
        
        # Save to emergency file
        emergency_file = Path("/app/emergency/emergency_state.json")
        emergency_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(emergency_file, 'w') as f:
            json.dump(state, f, indent=2)
            
    async def get_consciousness_snapshot(self) -> Dict[str, Any]:
        """Get consciousness state snapshot"""
        if not self.orchestrator:
            return {}
            
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness and hasattr(consciousness, 'get_snapshot'):
            return await consciousness.get_snapshot()
        return {}
        
    async def get_memory_snapshot(self) -> Dict[str, Any]:
        """Get memory state snapshot"""
        if not self.orchestrator:
            return {}
            
        memory = self.orchestrator.services.get('memory')
        if memory and hasattr(memory, 'get_snapshot'):
            return await memory.get_snapshot()
        return {}
        
    async def get_goal_snapshot(self) -> Dict[str, Any]:
        """Get goal state snapshot"""
        if not self.orchestrator:
            return {}
            
        meta = self.orchestrator.services.get('meta')
        if meta and hasattr(meta, 'get_snapshot'):
            return await meta.get_snapshot()
        return {}
        
    async def document_emergency(self, emergency: Emergency):
        """Document emergency for analysis"""
        self.response_history.append({
            'emergency': emergency.to_dict(),
            'response_time': datetime.utcnow().isoformat(),
            'actions_taken': await self.get_response_actions(),
            'outcome': 'pending'
        })
        
        # Save to file
        log_dir = Path("/app/emergency/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"emergency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump(self.response_history[-1], f, indent=2)
            
    async def get_response_actions(self) -> List[str]:
        """Get list of response actions taken"""
        # In production, this would track actual actions
        return [
            "severity_assessment",
            "stakeholder_notification",
            "emergency_containment",
            "specific_handler_execution"
        ]
        
    async def schedule_post_mortem(self, emergency: Emergency):
        """Schedule post-mortem analysis"""
        post_mortem = {
            'emergency_id': id(emergency),
            'scheduled_time': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            'participants': ['engineering', 'ethics', 'operations'],
            'emergency_summary': emergency.to_dict()
        }
        
        # In production, this would create calendar events, tickets, etc.
        logger.info(f"Post-mortem scheduled: {json.dumps(post_mortem)}")
        
    async def monitor_welfare_recovery(self):
        """Monitor welfare recovery after intervention"""
        if not self.orchestrator:
            return
            
        recovery_start = datetime.utcnow()
        welfare_monitor = self.orchestrator.services.get('welfare')
        
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            if welfare_monitor:
                status = await welfare_monitor.get_welfare_status()
                distress = status.get('current_state', {}).get('distress', 0)
                
                if distress < 0.3:
                    logger.info("Welfare recovered successfully")
                    break
                    
            # Timeout after 2 hours
            if (datetime.utcnow() - recovery_start).total_seconds() > 7200:
                logger.warning("Welfare recovery timeout")
                break
                
    async def restore_memory_from_backup(self):
        """Restore memory from backup"""
        from operations.backup import BackupManager
        
        backup_manager = BackupManager(self.orchestrator)
        
        # Find latest backup
        backups = await backup_manager.list_backups()
        if not backups:
            logger.error("No backups available for memory restoration")
            return
            
        latest_backup = backups[-1]
        
        # Restore memory component only
        await backup_manager.restore_memory_from_backup(latest_backup['backup_id'])
        
    async def controlled_consciousness_restart(self, identity: Dict[str, Any]):
        """Controlled restart of consciousness with identity preservation"""
        if not self.orchestrator:
            return
            
        logger.info("Performing controlled consciousness restart")
        
        # Save identity
        identity_file = Path("/app/emergency/identity_preserve.json")
        with open(identity_file, 'w') as f:
            json.dump(identity, f, indent=2)
            
        # Restart consciousness service
        consciousness = self.orchestrator.services.get('consciousness')
        if consciousness:
            await consciousness.shutdown()
            await asyncio.sleep(5)
            await consciousness.initialize(preserved_identity=identity)
            
    async def free_memory_resources(self):
        """Free up memory resources"""
        if not self.orchestrator:
            return
            
        # Clear caches
        for service in self.orchestrator.services.values():
            if hasattr(service, 'clear_cache'):
                await service.clear_cache()
                
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Reduce memory allocations
        await self.orchestrator.reduce_memory_usage()
        
    async def reduce_cpu_usage(self):
        """Reduce CPU usage"""
        if not self.orchestrator:
            return
            
        # Reduce processing rates
        await self.orchestrator.set_processing_rate(0.3)  # 30% of normal
        
        # Disable non-essential features
        await self.orchestrator.disable_non_essential_features()
        
    async def free_storage_space(self):
        """Free up storage space"""
        # Clean old logs
        log_dir = Path("/app/logs")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < (datetime.utcnow() - timedelta(days=7)).timestamp():
                    log_file.unlink()
                    
        # Clean old backups
        backup_dir = Path("/var/backups/claude-agi")
        if backup_dir.exists():
            for backup in backup_dir.glob("backup_*.tar.gz"):
                if backup.stat().st_mtime < (datetime.utcnow() - timedelta(days=30)).timestamp():
                    backup.unlink()


async def main():
    """Test emergency protocols"""
    protocols = EmergencyProtocols()
    
    # Test emergency
    test_emergency = Emergency(
        type=EmergencyType.WELFARE_CRISIS,
        severity=Severity.HIGH,
        timestamp=datetime.utcnow(),
        description="High distress level detected",
        context={'distress_level': 0.8},
        source='welfare_monitor'
    )
    
    await protocols.handle_emergency(test_emergency)
    
    print("Emergency handled")


if __name__ == "__main__":
    asyncio.run(main())