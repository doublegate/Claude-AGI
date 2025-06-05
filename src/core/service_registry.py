# core/service_registry.py

"""
Service Registry - Manages service registration and lifecycle.

This module extracts service management from the AGIOrchestrator to follow
the Single Responsibility Principle and reduce the god object anti-pattern.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ServiceInterface(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the service"""
        pass
    
    async def handle_message(self, message: Any):
        """Handle incoming messages"""
        pass
    
    async def run(self):
        """Run the service (optional)"""
        pass
    
    async def close(self):
        """Cleanup and close the service"""
        pass


class ServiceRegistry:
    """Manages service registration, discovery, and lifecycle"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_tasks: Dict[str, asyncio.Task] = {}
        self._service_metadata: Dict[str, Dict[str, Any]] = {}
        
    def register(self, name: str, service: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        Register a service with the registry.
        
        Args:
            name: Unique service identifier
            service: Service instance
            metadata: Optional service metadata
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
            
        self._services[name] = service
        self._service_metadata[name] = metadata or {}
        logger.info(f"Registered service: {name}")
        
    def unregister(self, name: str):
        """
        Unregister a service from the registry.
        
        Args:
            name: Service identifier
        """
        if name in self._services:
            del self._services[name]
            del self._service_metadata[name]
            logger.info(f"Unregistered service: {name}")
            
    def get(self, name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance or None if not found
        """
        return self._services.get(name)
        
    def exists(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services
        
    def list_services(self) -> List[str]:
        """Get list of all registered service names"""
        return list(self._services.keys())
        
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services"""
        return self._services.copy()
        
    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a service"""
        return self._service_metadata.get(name)
        
    async def start_service(self, name: str, run_in_test_mode: bool = False) -> Optional[asyncio.Task]:
        """
        Start a service's run method if it has one.
        
        Args:
            name: Service identifier
            run_in_test_mode: Whether to start services in test mode
            
        Returns:
            Asyncio task if service was started, None otherwise
        """
        service = self.get(name)
        if not service:
            logger.warning(f"Cannot start service '{name}': not registered")
            return None
            
        # Check if service has a run method
        if hasattr(service, 'run') and callable(getattr(service, 'run')):
            # Don't start in test mode unless explicitly requested
            if not run_in_test_mode and asyncio.get_event_loop().get_debug():
                logger.debug(f"Skipping service start for '{name}' in test mode")
                return None
                
            # Create and store task
            task = asyncio.create_task(service.run())
            self._service_tasks[name] = task
            logger.info(f"Started service: {name}")
            return task
        else:
            logger.debug(f"Service '{name}' has no run method")
            return None
            
    async def stop_service(self, name: str):
        """
        Stop a running service.
        
        Args:
            name: Service identifier
        """
        if name in self._service_tasks:
            task = self._service_tasks[name]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._service_tasks[name]
            logger.info(f"Stopped service: {name}")
            
    async def start_all_services(self, run_in_test_mode: bool = False) -> List[asyncio.Task]:
        """
        Start all registered services that have run methods.
        
        Args:
            run_in_test_mode: Whether to start services in test mode
            
        Returns:
            List of started tasks
        """
        tasks = []
        for name in self._services:
            task = await self.start_service(name, run_in_test_mode)
            if task:
                tasks.append(task)
        return tasks
        
    async def stop_all_services(self):
        """Stop all running services"""
        service_names = list(self._service_tasks.keys())
        for name in service_names:
            await self.stop_service(name)
            
    async def shutdown_all_services(self):
        """Shutdown all services (stop tasks and call close methods)"""
        # First stop all running tasks
        await self.stop_all_services()
        
        # Then call close on all services that have it
        for name, service in self._services.items():
            if hasattr(service, 'close') and callable(getattr(service, 'close')):
                try:
                    await service.close()
                    logger.info(f"Closed service: {name}")
                except Exception as e:
                    logger.error(f"Error closing service '{name}': {e}")
                    
    def get_service_status(self, name: str) -> Dict[str, Any]:
        """
        Get status information for a service.
        
        Args:
            name: Service identifier
            
        Returns:
            Status dictionary
        """
        if name not in self._services:
            return {'exists': False}
            
        status = {
            'exists': True,
            'has_run_method': hasattr(self._services[name], 'run'),
            'is_running': name in self._service_tasks and not self._service_tasks[name].done(),
            'metadata': self._service_metadata.get(name, {})
        }
        
        return status
        
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all services"""
        return {name: self.get_service_status(name) for name in self._services}