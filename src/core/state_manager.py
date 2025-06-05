# core/state_manager.py

"""
State Manager - Manages system state transitions and history.

This module extracts state management from the AGIOrchestrator to follow
the Single Responsibility Principle and improve maintainability.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """System states for the AGI"""
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


class StateManager:
    """Manages system state, transitions, and state history"""
    
    def __init__(self):
        self._current_state = SystemState.INITIALIZING
        self._state_history: List[StateTransition] = []
        self._transition_rules: Dict[SystemState, Set[SystemState]] = {
            SystemState.INITIALIZING: {SystemState.IDLE, SystemState.SLEEPING},
            SystemState.IDLE: {
                SystemState.THINKING, 
                SystemState.EXPLORING, 
                SystemState.CREATING, 
                SystemState.REFLECTING, 
                SystemState.SLEEPING,
                SystemState.CONVERSING
            },
            SystemState.THINKING: {
                SystemState.IDLE, 
                SystemState.CREATING, 
                SystemState.REFLECTING,
                SystemState.CONVERSING
            },
            SystemState.CONVERSING: {
                SystemState.IDLE,
                SystemState.THINKING,
                SystemState.REFLECTING
            },
            SystemState.EXPLORING: {
                SystemState.IDLE, 
                SystemState.THINKING
            },
            SystemState.CREATING: {
                SystemState.IDLE, 
                SystemState.THINKING,
                SystemState.REFLECTING
            },
            SystemState.REFLECTING: {
                SystemState.IDLE, 
                SystemState.THINKING
            },
            SystemState.SLEEPING: {
                SystemState.IDLE
            }
        }
        self._state_listeners: List[Callable] = []
        self._state_entry_hooks: Dict[SystemState, List[Callable]] = {}
        self._state_exit_hooks: Dict[SystemState, List[Callable]] = {}
        
    @property
    def current_state(self) -> SystemState:
        """Get the current system state"""
        return self._current_state
        
    @property
    def state_history(self) -> List[StateTransition]:
        """Get a copy of the state transition history"""
        return self._state_history.copy()
        
    def get_valid_transitions(self, from_state: Optional[SystemState] = None) -> Set[SystemState]:
        """
        Get valid state transitions from a given state.
        
        Args:
            from_state: State to check transitions from (defaults to current state)
            
        Returns:
            Set of valid target states
        """
        state = from_state or self._current_state
        return self._transition_rules.get(state, set()).copy()
        
    def can_transition_to(self, target_state: SystemState, from_state: Optional[SystemState] = None) -> bool:
        """
        Check if a transition to target state is valid.
        
        Args:
            target_state: Desired target state
            from_state: Starting state (defaults to current state)
            
        Returns:
            True if transition is valid
        """
        state = from_state or self._current_state
        return target_state in self._transition_rules.get(state, set())
        
    async def transition_to(self, target_state: SystemState, reason: str = "", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition to a new state if valid.
        
        Args:
            target_state: Desired target state
            reason: Reason for transition
            metadata: Additional transition metadata
            
        Returns:
            True if transition was successful
        """
        if not self.can_transition_to(target_state):
            logger.warning(
                f"Invalid state transition from {self._current_state.value} "
                f"to {target_state.value}"
            )
            return False
            
        old_state = self._current_state
        
        # Execute exit hooks for current state
        await self._execute_state_hooks(old_state, self._state_exit_hooks)
        
        # Perform transition
        self._current_state = target_state
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=target_state,
            timestamp=datetime.now(),
            reason=reason,
            metadata=metadata or {}
        )
        self._state_history.append(transition)
        
        # Execute entry hooks for new state
        await self._execute_state_hooks(target_state, self._state_entry_hooks)
        
        # Notify listeners
        await self._notify_listeners(transition)
        
        logger.info(
            f"State transition: {old_state.value} -> {target_state.value} "
            f"(reason: {reason})"
        )
        
        return True
        
    async def _execute_state_hooks(self, state: SystemState, hooks_dict: Dict[SystemState, List[Callable]]):
        """Execute hooks for a given state"""
        if state in hooks_dict:
            for hook in hooks_dict[state]:
                try:
                    if asyncio.iscoroutinefunction(hook):
                        await hook(state)
                    else:
                        hook(state)
                except Exception as e:
                    logger.error(f"Error executing state hook: {e}")
                    
    async def _notify_listeners(self, transition: StateTransition):
        """Notify all listeners of state transition"""
        for listener in self._state_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(transition)
                else:
                    listener(transition)
            except Exception as e:
                logger.error(f"Error notifying state listener: {e}")
                
    def add_transition_listener(self, listener: Callable):
        """
        Add a listener to be notified of state transitions.
        
        Args:
            listener: Callable that accepts a StateTransition
        """
        self._state_listeners.append(listener)
        
    def remove_transition_listener(self, listener: Callable):
        """Remove a transition listener"""
        if listener in self._state_listeners:
            self._state_listeners.remove(listener)
            
    def add_state_entry_hook(self, state: SystemState, hook: Callable):
        """
        Add a hook to be called when entering a state.
        
        Args:
            state: State to hook
            hook: Callable to execute on entry
        """
        if state not in self._state_entry_hooks:
            self._state_entry_hooks[state] = []
        self._state_entry_hooks[state].append(hook)
        
    def add_state_exit_hook(self, state: SystemState, hook: Callable):
        """
        Add a hook to be called when exiting a state.
        
        Args:
            state: State to hook
            hook: Callable to execute on exit
        """
        if state not in self._state_exit_hooks:
            self._state_exit_hooks[state] = []
        self._state_exit_hooks[state].append(hook)
        
    def get_state_duration(self, state: SystemState) -> float:
        """
        Get total time spent in a given state.
        
        Args:
            state: State to check
            
        Returns:
            Total seconds spent in state
        """
        total_duration = 0.0
        current_entry = None
        
        for transition in self._state_history:
            if transition.to_state == state:
                current_entry = transition.timestamp
            elif current_entry and transition.from_state == state:
                duration = (transition.timestamp - current_entry).total_seconds()
                total_duration += duration
                current_entry = None
                
        # If currently in the state, add time since entry
        if current_entry and self._current_state == state:
            duration = (datetime.now() - current_entry).total_seconds()
            total_duration += duration
            
        return total_duration
        
    def get_transition_count(self, from_state: Optional[SystemState] = None, 
                            to_state: Optional[SystemState] = None) -> int:
        """
        Count transitions matching criteria.
        
        Args:
            from_state: Source state filter (None for any)
            to_state: Target state filter (None for any)
            
        Returns:
            Number of matching transitions
        """
        count = 0
        for transition in self._state_history:
            if (from_state is None or transition.from_state == from_state) and \
               (to_state is None or transition.to_state == to_state):
                count += 1
        return count
        
    def get_last_transition(self) -> Optional[StateTransition]:
        """Get the most recent state transition"""
        return self._state_history[-1] if self._state_history else None
        
    def add_custom_transition_rule(self, from_state: SystemState, to_state: SystemState):
        """
        Add a custom transition rule.
        
        Args:
            from_state: Source state
            to_state: Allowed target state
        """
        if from_state not in self._transition_rules:
            self._transition_rules[from_state] = set()
        self._transition_rules[from_state].add(to_state)
        
    def remove_custom_transition_rule(self, from_state: SystemState, to_state: SystemState):
        """Remove a custom transition rule"""
        if from_state in self._transition_rules:
            self._transition_rules[from_state].discard(to_state)
            
    def get_state_statistics(self) -> Dict[str, Any]:
        """Get statistics about state usage"""
        stats = {
            'current_state': self._current_state.value,
            'total_transitions': len(self._state_history),
            'state_durations': {},
            'transition_counts': {}
        }
        
        # Calculate durations for each state
        for state in SystemState:
            stats['state_durations'][state.value] = self.get_state_duration(state)
            
        # Count transitions
        for transition in self._state_history:
            key = f"{transition.from_state.value}->{transition.to_state.value}"
            stats['transition_counts'][key] = stats['transition_counts'].get(key, 0) + 1
            
        return stats