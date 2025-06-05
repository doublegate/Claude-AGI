# core/event_bus.py

"""
Event Bus - Manages publish-subscribe messaging and event routing.

This module extracts event management from the AGIOrchestrator to create
a dedicated messaging system following the Single Responsibility Principle.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import weakref
from collections import defaultdict

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Message priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 5
    LOW = 8
    BACKGROUND = 10


@dataclass
class Message:
    """Message structure for inter-service communication"""
    source: str
    target: str
    type: str
    content: Any
    priority: int = Priority.NORMAL.value
    timestamp: float = field(default_factory=time.time)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def __lt__(self, other):
        """For priority queue ordering (lower priority number = higher priority)"""
        return self.priority < other.priority


@dataclass
class Event:
    """Event structure for pub-sub system"""
    type: str
    source: str
    data: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Centralized event bus for publish-subscribe messaging"""
    
    def __init__(self):
        self._message_queue = asyncio.PriorityQueue()
        self._subscribers: Dict[str, Set[weakref.ref]] = defaultdict(set)
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_handlers: Dict[str, Callable] = {}
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        self._metrics = {
            'messages_sent': 0,
            'messages_processed': 0,
            'events_published': 0,
            'errors': 0
        }
        
    async def start(self):
        """Start the event bus message processing"""
        if self._running:
            logger.warning("Event bus is already running")
            return
            
        self._running = True
        self._processing_task = asyncio.create_task(self._process_messages())
        logger.info("Event bus started")
        
    async def stop(self):
        """Stop the event bus"""
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Event bus stopped")
        
    async def _process_messages(self):
        """Main message processing loop"""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._route_message(message)
                self._metrics['messages_processed'] += 1
                
            except asyncio.TimeoutError:
                # No messages, continue
                continue
                
            except asyncio.CancelledError:
                logger.info("Message processing cancelled")
                break
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self._metrics['errors'] += 1
                
    async def _route_message(self, message: Message):
        """Route a message to its target handler"""
        if message.target == 'broadcast':
            # Broadcast to all registered handlers
            for handler_name, handler in self._message_handlers.items():
                if handler_name != message.source:  # Don't send to source
                    await self._deliver_message(handler, message)
        elif message.target in self._message_handlers:
            # Direct message to specific handler
            handler = self._message_handlers[message.target]
            await self._deliver_message(handler, message)
        else:
            logger.warning(f"No handler registered for target: {message.target}")
            
    async def _deliver_message(self, handler: Callable, message: Message):
        """Deliver a message to a handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
        except Exception as e:
            logger.error(f"Error delivering message to handler: {e}")
            self._metrics['errors'] += 1
            
    def register_message_handler(self, name: str, handler: Callable):
        """
        Register a message handler.
        
        Args:
            name: Unique handler name
            handler: Callable that accepts a Message
        """
        self._message_handlers[name] = handler
        logger.debug(f"Registered message handler: {name}")
        
    def unregister_message_handler(self, name: str):
        """Remove a message handler"""
        if name in self._message_handlers:
            del self._message_handlers[name]
            logger.debug(f"Unregistered message handler: {name}")
            
    async def send_message(self, message: Message):
        """
        Send a message through the event bus.
        
        Args:
            message: Message to send
        """
        await self._message_queue.put(message)
        self._metrics['messages_sent'] += 1
        
    async def send(self, source: str, target: str, type: str, content: Any, 
                   priority: int = Priority.NORMAL.value, **kwargs):
        """
        Convenience method to send a message.
        
        Args:
            source: Message source
            target: Message target
            type: Message type
            content: Message content
            priority: Message priority
            **kwargs: Additional message attributes
        """
        message = Message(
            source=source,
            target=target,
            type=type,
            content=content,
            priority=priority,
            **kwargs
        )
        await self.send_message(message)
        
    def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Callable that accepts an Event
        """
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event type: {event_type}")
        
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._event_handlers:
            handlers = self._event_handlers[event_type]
            if handler in handlers:
                handlers.remove(handler)
                logger.debug(f"Unsubscribed handler from event type: {event_type}")
                
    async def publish(self, event: Event):
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        handlers = self._event_handlers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                self._metrics['errors'] += 1
                
        self._metrics['events_published'] += 1
        
    async def emit(self, event_type: str, source: str, data: Any, **metadata):
        """
        Convenience method to emit an event.
        
        Args:
            event_type: Type of event
            source: Event source
            data: Event data
            **metadata: Additional event metadata
        """
        event = Event(
            type=event_type,
            source=source,
            data=data,
            metadata=metadata
        )
        await self.publish(event)
        
    async def request(self, source: str, target: str, type: str, content: Any,
                     timeout: float = 5.0) -> Optional[Message]:
        """
        Send a request and wait for a response.
        
        Args:
            source: Request source
            target: Request target
            type: Request type
            content: Request content
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None if timeout
        """
        # Create response queue
        response_queue = asyncio.Queue(maxsize=1)
        correlation_id = f"{source}-{target}-{time.time()}"
        
        # Temporary handler for response
        async def response_handler(message: Message):
            if message.correlation_id == correlation_id:
                await response_queue.put(message)
                
        # Register temporary handler
        temp_handler_name = f"_response_{correlation_id}"
        self.register_message_handler(temp_handler_name, response_handler)
        
        try:
            # Send request
            request_message = Message(
                source=source,
                target=target,
                type=type,
                content=content,
                correlation_id=correlation_id,
                reply_to=temp_handler_name
            )
            await self.send_message(request_message)
            
            # Wait for response
            response = await asyncio.wait_for(
                response_queue.get(),
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {source} -> {target}")
            return None
            
        finally:
            # Clean up temporary handler
            self.unregister_message_handler(temp_handler_name)
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return {
            **self._metrics,
            'queue_size': self._message_queue.qsize(),
            'registered_handlers': len(self._message_handlers),
            'event_subscriptions': sum(len(handlers) for handlers in self._event_handlers.values())
        }
        
    async def flush_queue(self):
        """Process all pending messages immediately"""
        while not self._message_queue.empty():
            try:
                message = self._message_queue.get_nowait()
                await self._route_message(message)
                self._metrics['messages_processed'] += 1
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"Error flushing queue: {e}")
                self._metrics['errors'] += 1