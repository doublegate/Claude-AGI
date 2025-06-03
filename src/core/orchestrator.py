# core/orchestrator.py

import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import random
import time

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
    def __init__(self):
        self.state = SystemState.INITIALIZING
        self.message_queue = asyncio.PriorityQueue()
        self.services = {}
        self.tasks = []
        
    async def initialize(self):
        """Initialize all services and connections"""
        # Import services here to avoid circular imports
        from memory.manager import MemoryManager
        from consciousness.stream import ConsciousnessStream
        from learning.engine import LearningEngine
        from emotional.framework import EmotionalFramework
        from creative.engine import CreativeEngine
        from exploration.engine import WebExplorer
        from social.intelligence import SocialIntelligence
        from meta.cognitive import MetaCognitive
        
        # Initialize core services
        self.services['memory'] = await MemoryManager.create()
        self.services['consciousness'] = ConsciousnessStream(self)
        self.services['learning'] = LearningEngine(self)
        self.services['emotional'] = EmotionalFramework(self)
        self.services['creative'] = CreativeEngine(self)
        self.services['explorer'] = WebExplorer(self)
        self.services['social'] = SocialIntelligence(self)
        self.services['meta'] = MetaCognitive(self)
        
        # Start service tasks
        for name, service in self.services.items():
            task = asyncio.create_task(service.run())
            self.tasks.append(task)
            
        self.state = SystemState.IDLE
        
    async def run(self):
        """Main event loop"""
        await self.initialize()
        
        while True:
            try:
                # Process messages with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self.route_message(message)
                
            except asyncio.TimeoutError:
                # No messages - run idle tasks
                await self.idle_cycle()
                
            except Exception as e:
                await self.handle_error(e)
                
    async def route_message(self, message: Message):
        """Route messages between services"""
        if message.target in self.services:
            await self.services[message.target].handle_message(message)
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
                
    async def transition_state(self, new_state: SystemState):
        """Transition to a new system state"""
        old_state = self.state
        self.state = new_state
        
        # Notify all services of state change
        state_message = Message(
            source='orchestrator',
            target='broadcast',
            type='state_change',
            content={'old_state': old_state, 'new_state': new_state},
            priority=1
        )
        
        for service_name in self.services:
            await self.send_message(state_message._replace(target=service_name))
            
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
        
    async def shutdown(self):
        """Gracefully shutdown all services"""
        self.state = SystemState.SLEEPING
        
        # Cancel all service tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for services to shutdown
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        for service in self.services.values():
            if hasattr(service, 'close'):
                await service.close()