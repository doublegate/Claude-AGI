"""
Database models for Claude-AGI
==============================

Defines the schema for all persistent data structures used in the consciousness system.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory in the consciousness system"""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    EMOTIONAL = "emotional"


class StreamType(str, Enum):
    """Types of consciousness streams"""
    PRIMARY = "primary"
    SUBCONSCIOUS = "subconscious"
    EMOTIONAL = "emotional"
    CREATIVE = "creative"
    METACOGNITIVE = "metacognitive"


class EmotionalState(BaseModel):
    """Represents Claude's emotional state"""
    valence: float = Field(default=0.0, ge=-1.0, le=1.0)  # Positive/negative
    arousal: float = Field(default=0.0, ge=0.0, le=1.0)   # Activation level
    dominance: float = Field(default=0.5, ge=0.0, le=1.0)  # Control feeling
    
    primary_emotion: Optional[str] = None
    secondary_emotions: List[str] = Field(default_factory=list)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


class Memory(BaseModel):
    """Individual memory unit in the consciousness system"""
    id: str
    content: str
    memory_type: MemoryType
    importance: float = Field(default=0.5, ge=0.0, le=10.0)
    embedding: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Emotional context
    emotional_context: Optional[Dict[str, Any]] = None
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    
    # Relationships
    associations: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    
    # Access tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class MemoryData(BaseModel):
    """Data structure for storing memories (legacy)"""
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    context: Dict[str, Any] = Field(default_factory=dict)
    associations: List[int] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThoughtData(BaseModel):
    """Data structure for consciousness stream thoughts"""
    stream_type: StreamType
    content: str
    emotional_state: Optional[EmotionalState] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    memory_references: List[int] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Processing metadata
    processing_time_ms: Optional[float] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    coherence_score: float = Field(default=0.8, ge=0.0, le=1.0)


class Goal(BaseModel):
    """Represents a goal or intention"""
    id: str
    description: str
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    status: str = "active"  # active, completed, abandoned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Goal metadata
    category: Optional[str] = None
    parent_goal_id: Optional[str] = None
    sub_goals: List[str] = Field(default_factory=list)
    
    # Progress tracking
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Emotional attachment
    emotional_importance: float = Field(default=0.5, ge=0.0, le=1.0)
    motivation_level: float = Field(default=0.7, ge=0.0, le=1.0)


class Interest(BaseModel):
    """Represents an area of interest for exploration"""
    topic: str
    curiosity_level: float = Field(default=0.5, ge=0.0, le=1.0)
    knowledge_level: float = Field(default=0.0, ge=0.0, le=1.0)
    last_explored: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exploration_count: int = 0
    
    # Related information
    related_memories: List[int] = Field(default_factory=list)
    related_goals: List[str] = Field(default_factory=list)
    discovered_facts: List[str] = Field(default_factory=list)
    
    # Decay and growth
    decay_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    growth_potential: float = Field(default=0.5, ge=0.0, le=1.0)


class ConversationContext(BaseModel):
    """Context for ongoing conversations"""
    conversation_id: str
    participant_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Conversation state
    topic_history: List[str] = Field(default_factory=list)
    current_topic: Optional[str] = None
    emotional_tone: EmotionalState = Field(default_factory=EmotionalState)
    
    # Relationship tracking
    rapport_level: float = Field(default=0.5, ge=0.0, le=1.0)
    trust_level: float = Field(default=0.5, ge=0.0, le=1.0)
    interaction_count: int = 0
    
    # Memory of conversation
    key_points: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    shared_interests: List[str] = Field(default_factory=list)


class SystemState(BaseModel):
    """Overall system state snapshot"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Cognitive state
    current_activity: str = "idle"
    active_streams: List[StreamType] = Field(default_factory=list)
    processing_load: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Emotional state
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)
    
    # Goals and interests
    active_goals: List[str] = Field(default_factory=list)
    current_interests: List[str] = Field(default_factory=list)
    
    # Memory state
    working_memory_items: int = 0
    recent_memory_count: int = 0
    total_memories: int = 0
    
    # Performance metrics
    response_time_ms: float = 0.0
    thought_coherence: float = Field(default=0.8, ge=0.0, le=1.0)
    creativity_level: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Environmental awareness
    time_since_startup: float = 0.0
    interactions_today: int = 0
    new_learnings_today: int = 0
    
    model_config = ConfigDict(from_attributes=True)