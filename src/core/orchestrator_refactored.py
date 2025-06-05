# core/orchestrator_refactored.py

"""
Refactored AGI Orchestrator - Thin coordinator using extracted components.

This refactored version follows the Single Responsibility Principle by
delegating service management, state management, and event handling to
dedicated components.
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional
import random

from core.service_registry import ServiceRegistry
from core.state_manager import StateManager, SystemState
from core.event_bus import EventBus, Message, Event, Priority

logger = logging.getLogger(__name__)


class AGIOrchestrator:
    """
    Thin orchestrator that coordinates between services using dedicated components.
    
    This refactored version delegates responsibilities:
    - Service management -> ServiceRegistry
    - State management -> StateManager
    - Event/Message routing -> EventBus
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.service_registry = ServiceRegistry()
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        
        # Orchestrator state
        self.running = False
        self._idle_task: Optional[asyncio.Task] = None
        
        # Monitoring hooks (optional)
        self.monitoring_hooks = None
        
        # Setup component integration
        self._setup_component_integration()
        
    def _setup_component_integration(self):
        """Setup integration between components"""
        # Register state transition listener to notify services
        self.state_manager.add_transition_listener(self._on_state_transition)
        
        # Register orchestrator as message handler
        self.event_bus.register_message_handler('orchestrator', self._handle_orchestrator_message)
        
    async def initialize(self):
        """Initialize the orchestrator and all services"""
        logger.info("Initializing AGI Orchestrator")
        
        # Start event bus
        await self.event_bus.start()
        
        # Initialize services
        await self._initialize_services()
        
        # Register service message handlers
        self._register_service_handlers()
        
        # Start service tasks
        run_in_test_mode = bool(os.environ.get('CLAUDE_AGI_TEST_MODE'))
        await self.service_registry.start_all_services(run_in_test_mode)
        
        # Transition to idle state
        await self.state_manager.transition_to(SystemState.IDLE, "Initialization complete")
        
        self.running = True
        logger.info("AGI Orchestrator initialized")
        
    async def _initialize_services(self):
        """Initialize and register all cognitive services"""
        # Import services here to avoid circular imports
        from src.memory.manager import MemoryManager
        from src.consciousness.stream import ConsciousnessStream
        from src.safety.enhanced_safety import EnhancedSafetyFramework
        
        # Initialize memory manager
        memory_manager = MemoryManager()
        use_database = self.config.get('database', {}).get('enabled', False)
        await memory_manager.initialize(use_database=use_database)
        self.service_registry.register('memory', memory_manager, {
            'type': 'core',
            'description': 'Memory management service'
        })
        
        # Initialize consciousness stream
        consciousness = ConsciousnessStream(self)
        self.service_registry.register('consciousness', consciousness, {
            'type': 'core',
            'description': 'Consciousness stream service'
        })
        
        # Initialize safety framework
        security_config = self.config.get('security', {})
        safety = EnhancedSafetyFramework(self, security_config)
        self.service_registry.register('safety', safety, {
            'type': 'core',
            'description': 'Safety and security framework'
        })
        
        logger.info("Core services initialized and registered")
        
    def _register_service_handlers(self):
        """Register service message handlers with event bus"""
        for service_name, service in self.service_registry.get_all_services().items():
            # Create a message handler wrapper for the service
            async def service_handler(message: Message, svc=service, name=service_name):
                if message.target == name or message.target == 'broadcast':
                    if hasattr(svc, 'handle_message'):
                        await svc.handle_message(message)
                    elif hasattr(svc, 'process_message'):
                        await svc.process_message(message)
                        
            self.event_bus.register_message_handler(service_name, service_handler)
            
    async def _on_state_transition(self, transition):
        """Handle state transitions by notifying services"""
        # Publish state change event
        await self.event_bus.emit(
            'state_change',
            'orchestrator',
            {
                'old_state': transition.from_state,
                'new_state': transition.to_state,
                'reason': transition.reason,
                'timestamp': transition.timestamp
            }
        )
        
        # Send state change message to all services
        await self.event_bus.send(
            'orchestrator',
            'broadcast',
            'state_change',
            {
                'old_state': transition.from_state,
                'new_state': transition.to_state,
                'reason': transition.reason
            },
            priority=Priority.HIGH.value
        )
        
    async def _handle_orchestrator_message(self, message: Message):
        """Handle messages directed to the orchestrator"""
        if message.type == 'shutdown':
            await self.shutdown()
        elif message.type == 'state_query':
            # Send response if reply_to is specified
            if message.reply_to:
                response = Message(
                    source='orchestrator',
                    target=message.reply_to,
                    type='state_response',
                    content={'state': self.state_manager.current_state},
                    correlation_id=message.correlation_id
                )
                await self.event_bus.send_message(response)
        elif message.type == 'status_query':
            status = self.get_system_status()
            if message.reply_to:
                response = Message(
                    source='orchestrator',
                    target=message.reply_to,
                    type='status_response',
                    content=status,
                    correlation_id=message.correlation_id
                )
                await self.event_bus.send_message(response)
                
    async def run(self):
        """Main orchestrator loop"""
        await self.initialize()
        
        # Start idle task
        self._idle_task = asyncio.create_task(self._idle_loop())
        
        try:
            # Keep running until shutdown
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Orchestrator run cancelled")
        finally:
            if self._idle_task and not self._idle_task.done():
                self._idle_task.cancel()
                try:
                    await self._idle_task
                except asyncio.CancelledError:
                    pass
                    
    async def _idle_loop(self):
        """Idle activities loop"""
        while self.running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if self.state_manager.current_state == SystemState.IDLE:
                    # Trigger exploration or contemplation
                    if random.random() < 0.3:
                        await self.transition_to(SystemState.EXPLORING, "Random exploration")
                    elif random.random() < 0.2:
                        await self.transition_to(SystemState.REFLECTING, "Periodic reflection")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in idle loop: {e}")
                
    async def transition_to(self, new_state: SystemState, reason: str = ""):
        """Request a state transition"""
        success = await self.state_manager.transition_to(new_state, reason)
        if not success:
            logger.warning(f"State transition to {new_state} failed")
        return success
        
    async def send_message(self, message: Message):
        """Send a message through the event bus"""
        await self.event_bus.send_message(message)
        
    async def send_to_service(self, service_name: str, message_type: str, content: Any):
        """Send a message to a specific service"""
        await self.event_bus.send(
            'orchestrator',
            service_name,
            message_type,
            content
        )
        
    async def publish(self, event_type: str, data: Any):
        """Publish an event"""
        await self.event_bus.emit(event_type, 'orchestrator', data)
        
    def subscribe(self, service_name: str, event_type: str):
        """Subscribe a service to an event type"""
        # Create event handler that converts events to messages
        async def event_to_message_handler(event: Event):
            message = Message(
                source='orchestrator',
                target=service_name,
                type='event',
                content={
                    'event_type': event.type,
                    'data': event.data,
                    'metadata': event.metadata
                },
                priority=Priority.NORMAL.value
            )
            await self.event_bus.send_message(message)
            
        self.event_bus.subscribe(event_type, event_to_message_handler)
        
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.service_registry.get(name)
        
    def register_service(self, name: str, service: Any):
        """Register a new service"""
        self.service_registry.register(name, service)
        # Register message handler for the service
        self._register_service_handlers()
        
    async def emergency_stop(self, reason: str):
        """Emergency stop the system"""
        logger.critical(f"EMERGENCY STOP: {reason}")
        await self.state_manager.transition_to(SystemState.SLEEPING, f"Emergency stop: {reason}")
        await self.shutdown()
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'state': self.state_manager.current_state.value,
            'services': self.service_registry.list_services(),
            'service_statuses': self.service_registry.get_all_statuses(),
            'running': self.running,
            'event_bus_metrics': self.event_bus.get_metrics(),
            'state_statistics': self.state_manager.get_state_statistics()
        }
        
    def set_monitoring_hooks(self, monitoring_hooks):
        """Set monitoring hooks for instrumentation"""
        self.monitoring_hooks = monitoring_hooks
        
        # Pass monitoring hooks to components that need them
        if hasattr(self.service_registry, 'set_monitoring_hooks'):
            self.service_registry.set_monitoring_hooks(monitoring_hooks)
        if hasattr(self.state_manager, 'set_monitoring_hooks'):
            self.state_manager.set_monitoring_hooks(monitoring_hooks)
        if hasattr(self.event_bus, 'set_monitoring_hooks'):
            self.event_bus.set_monitoring_hooks(monitoring_hooks)
            
        # Pass to existing services
        for service_name, service in self.service_registry.get_all_services().items():
            if hasattr(service, 'set_monitoring_hooks'):
                service.set_monitoring_hooks(monitoring_hooks)
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        logger.info("Starting orchestrator shutdown")
        self.running = False
        
        # Transition to sleeping state
        await self.state_manager.transition_to(SystemState.SLEEPING, "System shutdown")
        
        # Stop idle task
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass
                
        # Shutdown all services
        await self.service_registry.shutdown_all_services()
        
        # Stop event bus
        await self.event_bus.stop()
        
        logger.info("Orchestrator shutdown complete")
        
    # Compatibility properties for existing code
    @property
    def state(self) -> SystemState:
        """Get current state (for compatibility)"""
        return self.state_manager.current_state
        
    @property
    def services(self) -> Dict[str, Any]:
        """Get services dict (for compatibility)"""
        return self.service_registry.get_all_services()
        
    @property
    def message_queue(self):
        """Get message queue (for compatibility)"""
        return self.event_bus._message_queue