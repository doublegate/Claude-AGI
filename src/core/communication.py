# core/communication.py

from abc import ABC, abstractmethod
import asyncio
from typing import List, Any, Optional
import json
import time
import logging

# For now, using asyncio queues instead of ZMQ for simplicity
# ZMQ can be integrated later for distributed deployment

logger = logging.getLogger(__name__)

class ServiceBase(ABC):
    """Base class for all AGI services"""
    
    def __init__(self, orchestrator, service_name):
        self.orchestrator = orchestrator
        self.service_name = service_name
        self.running = False
        self.message_queue = asyncio.Queue()
        self._subscriptions = set()
        
    async def setup_communication(self):
        """Setup communication channels"""
        # Register with orchestrator
        self.orchestrator.services[self.service_name] = self
        
        # Set up subscriptions
        subscriptions = self.get_subscriptions()
        self._subscriptions.update(subscriptions)
        
        logger.info(f"{self.service_name} communication setup complete")
        
    async def publish(self, topic: str, data: Any):
        """Publish message to topic"""
        from core.orchestrator import Message
        
        message = Message(
            source=self.service_name,
            target=topic,
            type='publish',
            content={
                'topic': topic,
                'data': data
            }
        )
        
        # Route through orchestrator
        await self.orchestrator.send_message(message)
        
    async def send_to_service(self, target: str, message_type: str, data: Any, priority: int = 5):
        """Send direct message to another service"""
        from core.orchestrator import Message
        
        message = Message(
            source=self.service_name,
            target=target,
            type=message_type,
            content=data,
            priority=priority
        )
        
        await self.orchestrator.send_message(message)
        
    async def handle_message(self, message):
        """Handle incoming messages"""
        await self.message_queue.put(message)
        
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Receive message from queue"""
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=timeout
                )
            else:
                message = await self.message_queue.get()
            return message
        except asyncio.TimeoutError:
            return None
            
    @abstractmethod
    def get_subscriptions(self) -> List[str]:
        """Define which topics this service subscribes to"""
        pass
        
    @abstractmethod
    async def process_message(self, message: Any):
        """Process received messages"""
        pass
        
    @abstractmethod
    async def service_cycle(self):
        """Service-specific processing cycle"""
        pass
        
    async def run(self):
        """Main service loop"""
        await self.setup_communication()
        self.running = True
        
        try:
            while self.running:
                try:
                    # Process messages with timeout
                    message = await self.receive_message(timeout=0.1)
                    if message:
                        try:
                            await self.process_message(message)
                        except Exception as e:
                            logger.error(f"{self.service_name} error processing message: {e}")
                            await self.handle_error(e)
                    
                    # Run service-specific tasks
                    try:
                        await self.service_cycle()
                    except Exception as e:
                        logger.error(f"{self.service_name} error in service cycle: {e}")
                        await self.handle_error(e)
                except asyncio.CancelledError:
                    # Propagate cancellation immediately
                    raise
                    
        except asyncio.CancelledError:
            logger.info(f"{self.service_name} shutting down")
            self.running = False
            await self.cleanup()
            raise
        except Exception as e:
            logger.error(f"{self.service_name} unexpected error: {e}")
            self.running = False
            await self.cleanup()
            raise
            
    async def handle_error(self, error: Exception):
        """Handle service errors"""
        await self.send_to_service(
            'memory',
            'error_log',
            {
                'service': self.service_name,
                'error': str(error),
                'timestamp': time.time()
            },
            priority=2
        )
        
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        self.running = False
        logger.info(f"{self.service_name} cleaned up")
        
    async def close(self):
        """Close service connections"""
        await self.cleanup()


class MessageRouter:
    """Routes messages between services based on topics and subscriptions"""
    
    def __init__(self):
        self.topic_subscribers = {}  # topic -> set of service names
        self.service_topics = {}     # service -> set of topics
        
    def subscribe(self, service_name: str, topics: List[str]):
        """Subscribe a service to topics"""
        if service_name not in self.service_topics:
            self.service_topics[service_name] = set()
            
        for topic in topics:
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()
                
            self.topic_subscribers[topic].add(service_name)
            self.service_topics[service_name].add(topic)
            
    def unsubscribe(self, service_name: str, topics: List[str]):
        """Unsubscribe a service from topics"""
        for topic in topics:
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(service_name)
                
            if service_name in self.service_topics:
                self.service_topics[service_name].discard(topic)
                
    def get_subscribers(self, topic: str) -> List[str]:
        """Get all subscribers for a topic"""
        return list(self.topic_subscribers.get(topic, []))
        
    def get_topics(self, service_name: str) -> List[str]:
        """Get all topics a service is subscribed to"""
        return list(self.service_topics.get(service_name, []))