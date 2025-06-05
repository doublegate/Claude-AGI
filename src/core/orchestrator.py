# core/orchestrator.py

import asyncio
import os
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import time
import logging

logger = logging.getLogger(__name__)

class SystemState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    CONVERSING = "conversing"
    EXPLORING = "exploring"
    CREATING = "creating"
    REFLECTING = "reflecting"
    SLEEPING = "sleeping"


@dataclass
class StateTransition:
    """Records a state transition event"""
    from_state: SystemState
    to_state: SystemState
    timestamp: datetime
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    source: str
    target: str
    type: str
    content: Any
    priority: int = 5
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def __lt__(self, other):
        """For priority queue ordering (lower priority number = higher priority)"""
        return self.priority < other.priority

class AGIOrchestrator:
    def __init__(self, config=None):
        self.state = SystemState.INITIALIZING
        self.message_queue = asyncio.PriorityQueue()
        self.services = {}
        self.tasks = []
        self.config = config or {}
        self.state_history: List[StateTransition] = []
        self.subscribers: Dict[str, Set[str]] = {}
        self.running = False
        
    async def initialize(self):
        """Initialize all services and connections"""
        await self._initialize_services()
        
        # Start service tasks only for services that have run method
        # Skip in CI/test environments to prevent hanging
        if not os.environ.get('CLAUDE_AGI_TEST_MODE'):
            for name, service in self.services.items():
                if hasattr(service, 'run') and callable(getattr(service, 'run')):
                    task = asyncio.create_task(service.run())
                    self.tasks.append(task)
            
        self.state = SystemState.IDLE
        
    async def _initialize_services(self):
        """Initialize all cognitive services"""
        # Import services here to avoid circular imports
        from src.memory.manager import MemoryManager
        from src.consciousness.stream import ConsciousnessStream
        from src.safety.enhanced_safety import EnhancedSafetyFramework
        
        # Initialize core services
        memory_manager = MemoryManager()
        # Enable database if configured
        use_database = self.config.get('database', {}).get('enabled', False)
        await memory_manager.initialize(use_database=use_database)
        self.services['memory'] = memory_manager
        
        self.services['consciousness'] = ConsciousnessStream(self)
        
        # Use enhanced safety framework with security configuration
        security_config = self.config.get('security', {})
        self.services['safety'] = EnhancedSafetyFramework(self, security_config)
        
        # Comment out services that don't exist yet
        # self.services['learning'] = LearningEngine(self)
        # self.services['emotional'] = EmotionalFramework(self)
        # self.services['creative'] = CreativeEngine(self)
        # self.services['explorer'] = WebExplorer(self)
        # self.services['social'] = SocialIntelligence(self)
        # self.services['meta'] = MetaCognitive(self)
        
    async def run(self):
        """Main event loop"""
        await self.initialize()
        
        while self.running:
            try:
                # Process messages with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self.route_message(message)
                
            except asyncio.TimeoutError:
                # No messages - run idle tasks
                if self.running:
                    await self.idle_cycle()
                
            except asyncio.CancelledError:
                # Task cancelled, exit gracefully
                logger.info("Orchestrator task cancelled")
                break
                
            except Exception as e:
                if self.running:
                    await self.handle_error(e)
                
    async def route_message(self, message: Message):
        """Route messages between services"""
        if message.target in self.services:
            service = self.services[message.target]
            if hasattr(service, 'handle_message'):
                await service.handle_message(message)
            elif hasattr(service, 'process_message'):
                await service.process_message(message)
            else:
                logger.warning(f"Service {message.target} has no message handler")
        elif message.target == 'orchestrator':
            await self.handle_orchestrator_message(message)
            
    async def idle_cycle(self):
        """Activities during idle time"""
        if self.state == SystemState.IDLE:
            # Trigger exploration or contemplation
            if random.random() < 0.3:
                await self.transition_state(SystemState.EXPLORING)
            elif random.random() < 0.2:
                await self.transition_state(SystemState.REFLECTING)
                
    async def transition_state(self, new_state: SystemState, reason: str = ""):
        """Transition to a new system state"""
        old_state = self.state
        self.state = new_state
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(),
            reason=reason
        )
        self.state_history.append(transition)
        
        # Notify all services of state change
        state_message = Message(
            source='orchestrator',
            target='broadcast',
            type='state_change',
            content={'old_state': old_state, 'new_state': new_state, 'reason': reason},
            priority=1
        )
        
        for service_name in self.services:
            # Create a new message for each service
            service_message = Message(
                source=state_message.source,
                target=service_name,
                type=state_message.type,
                content=state_message.content,
                priority=state_message.priority
            )
            await self.send_message(service_message)
            
    async def send_message(self, message: Message):
        """Add message to the queue"""
        await self.message_queue.put(message)
        
    async def handle_orchestrator_message(self, message: Message):
        """Handle messages directed to the orchestrator"""
        if message.type == 'shutdown':
            await self.shutdown()
        elif message.type == 'state_query':
            return self.state
            
    async def handle_error(self, error: Exception):
        """Handle system errors"""
        error_message = Message(
            source='orchestrator',
            target='memory',
            type='error_log',
            content={'error': str(error), 'state': self.state},
            priority=2
        )
        await self.send_message(error_message)
        
    async def publish(self, event_type: str, data: Any):
        """Publish an event to subscribers"""
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                await self.send_message(Message(
                    source='orchestrator',
                    target=subscriber,
                    type='event',
                    content={'event_type': event_type, 'data': data},
                    priority=3
                ))
                
    def subscribe(self, service_name: str, event_type: str):
        """Subscribe a service to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(service_name)
        
    def unsubscribe(self, service_name: str, event_type: str):
        """Unsubscribe a service from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(service_name)
            
    async def emergency_stop(self, reason: str):
        """Emergency stop the system"""
        logger.critical(f"EMERGENCY STOP: {reason}")
        await self.transition_state(SystemState.SLEEPING, f"Emergency stop: {reason}")
        await self.shutdown()
        
    async def transition_to(self, new_state: SystemState):
        """Public method to transition state"""
        valid_transitions = {
            SystemState.IDLE: [SystemState.THINKING, SystemState.EXPLORING, SystemState.CREATING, SystemState.REFLECTING, SystemState.SLEEPING],
            SystemState.THINKING: [SystemState.IDLE, SystemState.CREATING, SystemState.REFLECTING],
            SystemState.EXPLORING: [SystemState.IDLE, SystemState.THINKING],
            SystemState.CREATING: [SystemState.IDLE, SystemState.THINKING],
            SystemState.REFLECTING: [SystemState.IDLE, SystemState.THINKING],
            SystemState.SLEEPING: [SystemState.IDLE]
        }
        
        if self.state in valid_transitions and new_state in valid_transitions[self.state]:
            await self.transition_state(new_state, f"User requested transition to {new_state}")
        else:
            logger.warning(f"Invalid state transition from {self.state} to {new_state}")
            
    def get_state_history(self) -> List[StateTransition]:
        """Get state transition history"""
        return self.state_history.copy()

    def register_service(self, name: str, service: Any):
        """Register a new service"""
        self.services[name] = service
        
    async def send_to_service(self, service_name: str, message_type: str, content: Any):
        """Send a message to a specific service"""
        if service_name in self.services:
            message = Message(
                source='orchestrator',
                target=service_name,
                type=message_type,
                content=content,
                priority=5
            )
            await self.send_message(message)
        else:
            logger.warning(f"Service {service_name} not found")
            
    async def process_events_queue(self):
        """Process all pending events in the queue"""
        while not self.message_queue.empty():
            try:
                message = await self.message_queue.get()
                await self.route_message(message)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'state': self.state.value,
            'services': list(self.services.keys()),
            'running': self.running,
            'queue_size': self.message_queue.qsize(),
            'state_history_length': len(self.state_history)
        }

    async def shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("Starting orchestrator shutdown")
        self.running = False
        self.state = SystemState.SLEEPING
        
        # Cancel all service tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        for service_name, service in self.services.items():
            if hasattr(service, 'close'):
                await service.close()