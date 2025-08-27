"""
Emotional Processing System for Claude-AGI
==========================================

Advanced emotional intelligence and processing capabilities including:
- Emotional state tracking and modeling
- Affective memory integration
- Emotional regulation mechanisms
- Empathy and social emotion understanding
- Mood dynamics and emotional transitions
"""

import asyncio
import logging
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..core.communication import ServiceBase
from ..database.models import EmotionalState, Memory, StreamType
from ..memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class EmotionType(str, Enum):
    """Primary emotion types based on psychological research"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    
    # Complex emotions
    CURIOSITY = "curiosity"
    CONTENTMENT = "contentment"
    EXCITEMENT = "excitement"
    ANXIETY = "anxiety"
    EMPATHY = "empathy"
    NOSTALGIA = "nostalgia"
    WONDER = "wonder"
    FRUSTRATION = "frustration"


class EmotionalIntensity(str, Enum):
    """Emotional intensity levels"""
    SUBTLE = "subtle"
    MODERATE = "moderate"
    STRONG = "strong"
    INTENSE = "intense"
    OVERWHELMING = "overwhelming"


@dataclass
class EmotionalEvent:
    """Represents an emotional event or trigger"""
    trigger: str
    primary_emotion: EmotionType
    secondary_emotions: List[EmotionType] = field(default_factory=list)
    intensity: float = 0.5  # 0.0 to 1.0
    valence_impact: float = 0.0  # -1.0 to 1.0
    arousal_impact: float = 0.0  # -1.0 to 1.0
    dominance_impact: float = 0.0  # -1.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    memory_associations: List[str] = field(default_factory=list)
    duration_estimate: float = 60.0  # seconds


@dataclass
class EmotionalMemory:
    """Memory with emotional context and associations"""
    content: str
    emotional_tag: EmotionType
    emotional_intensity: float
    valence: float
    arousal: float
    timestamp: datetime
    memory_id: Optional[str] = None
    associations: List[str] = field(default_factory=list)
    autobiographical: bool = False  # Is this a personal memory?


@dataclass
class MoodState:
    """Represents longer-term mood patterns"""
    dominant_mood: EmotionType
    mood_stability: float  # How stable the mood is
    mood_duration: timedelta
    contributing_factors: List[str] = field(default_factory=list)
    regulatory_factors: List[str] = field(default_factory=list)


class EmotionalRegulation:
    """Emotional regulation strategies and mechanisms"""
    
    def __init__(self):
        self.regulation_strategies = {
            "cognitive_reappraisal": {
                "description": "Reinterpreting situations to change emotional impact",
                "effectiveness": 0.8,
                "applicable_emotions": [EmotionType.ANGER, EmotionType.ANXIETY, EmotionType.SADNESS]
            },
            "mindful_awareness": {
                "description": "Observing emotions without immediate reaction",
                "effectiveness": 0.7,
                "applicable_emotions": [EmotionType.ANXIETY, EmotionType.ANGER, EmotionType.FRUSTRATION]
            },
            "positive_refocusing": {
                "description": "Shifting attention to positive aspects",
                "effectiveness": 0.6,
                "applicable_emotions": [EmotionType.SADNESS, EmotionType.FEAR, EmotionType.ANXIETY]
            },
            "emotional_expression": {
                "description": "Expressing emotions constructively",
                "effectiveness": 0.5,
                "applicable_emotions": [EmotionType.ANGER, EmotionType.FRUSTRATION, EmotionType.SADNESS]
            }
        }
    
    async def regulate_emotion(self, current_state: EmotionalState, target_valence: float = 0.0) -> Dict[str, Any]:
        """Apply emotional regulation to move toward target state"""
        regulation_plan = {
            "current_valence": current_state.valence,
            "target_valence": target_valence,
            "strategies_applied": [],
            "expected_impact": 0.0
        }
        
        valence_gap = target_valence - current_state.valence
        
        if abs(valence_gap) > 0.1:  # Only regulate if significant difference
            # Select appropriate strategies
            primary_emotion = self._get_primary_emotion_from_state(current_state)
            applicable_strategies = [
                strategy for strategy, details in self.regulation_strategies.items()
                if primary_emotion in details["applicable_emotions"]
            ]
            
            for strategy in applicable_strategies[:2]:  # Apply top 2 strategies
                effectiveness = self.regulation_strategies[strategy]["effectiveness"]
                impact = valence_gap * effectiveness * 0.3  # Gradual regulation
                regulation_plan["strategies_applied"].append({
                    "strategy": strategy,
                    "description": self.regulation_strategies[strategy]["description"],
                    "impact": impact
                })
                regulation_plan["expected_impact"] += impact
        
        return regulation_plan
    
    def _get_primary_emotion_from_state(self, state: EmotionalState) -> EmotionType:
        """Determine primary emotion from emotional state"""
        if state.valence > 0.3:
            if state.arousal > 0.6:
                return EmotionType.JOY
            else:
                return EmotionType.CONTENTMENT
        elif state.valence < -0.3:
            if state.arousal > 0.6:
                return EmotionType.ANXIETY
            else:
                return EmotionType.SADNESS
        else:
            if state.arousal > 0.6:
                return EmotionType.ANTICIPATION
            else:
                return EmotionType.TRUST


class EmotionalProcessor(ServiceBase):
    """
    Advanced emotional processing system
    
    Handles:
    - Emotional state modeling and tracking
    - Emotional memory formation and retrieval
    - Mood dynamics and regulation
    - Empathy and social emotion understanding
    - Integration with consciousness streams
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator)
        self.service_name = "emotional_processor"
        
        # Core emotional state
        self.current_state = EmotionalState(valence=0.0, arousal=0.5, dominance=0.5)
        self.emotional_history = deque(maxlen=1000)
        self.emotional_events = deque(maxlen=500)
        
        # Mood tracking
        self.mood_history = deque(maxlen=100)
        self.current_mood = MoodState(
            dominant_mood=EmotionType.CONTENTMENT,
            mood_stability=0.7,
            mood_duration=timedelta(hours=1)
        )
        
        # Emotional memory
        self.emotional_memories = deque(maxlen=2000)
        self.emotion_memory_map = defaultdict(list)  # emotion -> memory indices
        
        # Processing components
        self.regulation = EmotionalRegulation()
        self.empathy_model = EmpathyModel()
        
        # Configuration
        self.emotional_sensitivity = 0.7  # How sensitive to emotional triggers
        self.mood_inertia = 0.8  # How resistant mood is to change
        self.regulation_threshold = 0.3  # When to trigger regulation
        
        # Activity tracking
        self.last_emotion_update = time.time()
        self.emotion_update_interval = 5.0  # seconds
        
        logger.info("EmotionalProcessor initialized")
    
    async def start(self):
        """Start emotional processing service"""
        await super().start()
        
        # Start background emotional processing
        self._processing_task = asyncio.create_task(self._emotional_processing_loop())
        logger.info("Emotional processing started")
    
    async def stop(self):
        """Stop emotional processing service"""
        if hasattr(self, '_processing_task'):
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        logger.info("Emotional processing stopped")
    
    async def _emotional_processing_loop(self):
        """Main emotional processing loop"""
        while self.is_running:
            try:
                # Update emotional state based on recent events
                await self._update_emotional_state()
                
                # Process emotional memories
                await self._process_emotional_memories()
                
                # Update mood dynamics
                await self._update_mood_dynamics()
                
                # Apply emotional regulation if needed
                await self._apply_emotional_regulation()
                
                # Generate emotional insights
                await self._generate_emotional_insights()
                
                # Sleep until next processing cycle
                await asyncio.sleep(self.emotion_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in emotional processing loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)  # Brief pause before retry
    
    async def process_emotional_trigger(self, trigger: str, context: Dict[str, Any] = None) -> EmotionalEvent:
        """Process an emotional trigger and update state"""
        if context is None:
            context = {}
        
        # Analyze the trigger
        emotional_analysis = await self._analyze_emotional_content(trigger, context)
        
        # Create emotional event
        event = EmotionalEvent(
            trigger=trigger,
            primary_emotion=emotional_analysis["primary_emotion"],
            secondary_emotions=emotional_analysis["secondary_emotions"],
            intensity=emotional_analysis["intensity"],
            valence_impact=emotional_analysis["valence_impact"],
            arousal_impact=emotional_analysis["arousal_impact"],
            dominance_impact=emotional_analysis["dominance_impact"],
            context=context
        )
        
        # Store event
        self.emotional_events.append(event)
        
        # Update current emotional state
        await self._apply_emotional_event(event)
        
        # Check for memory formation
        if event.intensity > 0.4:  # Significant emotional events form memories
            await self._form_emotional_memory(event)
        
        logger.debug(f"Processed emotional trigger: {trigger} -> {event.primary_emotion}")
        return event
    
    async def _analyze_emotional_content(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for emotional significance"""
        # Emotional keyword analysis
        emotion_keywords = {
            EmotionType.JOY: ["happy", "joy", "celebration", "success", "achievement", "delight", "pleasure"],
            EmotionType.SADNESS: ["sad", "loss", "grief", "disappointment", "sorrow", "melancholy"],
            EmotionType.ANGER: ["angry", "frustration", "rage", "irritation", "fury", "annoyance"],
            EmotionType.FEAR: ["fear", "anxiety", "worry", "nervous", "scared", "apprehension"],
            EmotionType.SURPRISE: ["surprise", "unexpected", "shocking", "amazing", "astonishing"],
            EmotionType.CURIOSITY: ["wonder", "curious", "interesting", "explore", "discover", "question"],
            EmotionType.EXCITEMENT: ["excited", "thrilled", "enthusiastic", "eager", "anticipation"]
        }
        
        content_lower = content.lower()
        emotion_scores = defaultdict(float)
        
        # Score emotions based on keywords
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    emotion_scores[emotion] += 1.0
        
        # Context-based adjustments
        if context.get("stream_type") == StreamType.CREATIVE:
            emotion_scores[EmotionType.CURIOSITY] += 0.5
            emotion_scores[EmotionType.EXCITEMENT] += 0.3
        elif context.get("stream_type") == StreamType.METACOGNITIVE:
            emotion_scores[EmotionType.CURIOSITY] += 0.4
            emotion_scores[EmotionType.CONTENTMENT] += 0.2
        
        # Memory associations can influence emotions
        if context.get("memory_associations"):
            # Past emotional memories can influence current emotion
            for memory_ref in context.get("memory_associations", []):
                # In a full implementation, retrieve memory and use its emotional context
                emotion_scores[EmotionType.NOSTALGIA] += 0.2
        
        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.keys(), key=lambda e: emotion_scores[e])
            primary_intensity = min(1.0, emotion_scores[primary_emotion] * 0.3)
        else:
            primary_emotion = EmotionType.CONTENTMENT
            primary_intensity = 0.1
        
        # Secondary emotions
        secondary_emotions = [
            emotion for emotion, score in emotion_scores.items() 
            if emotion != primary_emotion and score > 0.3
        ][:3]  # Top 3 secondary emotions
        
        # Calculate dimensional impacts
        emotion_dimensions = self._get_emotion_dimensions(primary_emotion)
        
        return {
            "primary_emotion": primary_emotion,
            "secondary_emotions": secondary_emotions,
            "intensity": primary_intensity * self.emotional_sensitivity,
            "valence_impact": emotion_dimensions["valence"] * primary_intensity * 0.2,
            "arousal_impact": emotion_dimensions["arousal"] * primary_intensity * 0.2,
            "dominance_impact": emotion_dimensions["dominance"] * primary_intensity * 0.1
        }
    
    def _get_emotion_dimensions(self, emotion: EmotionType) -> Dict[str, float]:
        """Get valence, arousal, dominance values for an emotion"""
        # Based on psychological research (Russell's circumplex model)
        dimensions = {
            EmotionType.JOY: {"valence": 0.8, "arousal": 0.7, "dominance": 0.7},
            EmotionType.SADNESS: {"valence": -0.6, "arousal": 0.3, "dominance": 0.2},
            EmotionType.ANGER: {"valence": -0.5, "arousal": 0.8, "dominance": 0.8},
            EmotionType.FEAR: {"valence": -0.7, "arousal": 0.8, "dominance": 0.2},
            EmotionType.SURPRISE: {"valence": 0.1, "arousal": 0.9, "dominance": 0.3},
            EmotionType.DISGUST: {"valence": -0.6, "arousal": 0.5, "dominance": 0.6},
            EmotionType.TRUST: {"valence": 0.5, "arousal": 0.4, "dominance": 0.6},
            EmotionType.ANTICIPATION: {"valence": 0.3, "arousal": 0.7, "dominance": 0.5},
            EmotionType.CURIOSITY: {"valence": 0.4, "arousal": 0.6, "dominance": 0.5},
            EmotionType.CONTENTMENT: {"valence": 0.6, "arousal": 0.3, "dominance": 0.6},
            EmotionType.EXCITEMENT: {"valence": 0.7, "arousal": 0.8, "dominance": 0.6},
            EmotionType.ANXIETY: {"valence": -0.4, "arousal": 0.8, "dominance": 0.3},
            EmotionType.EMPATHY: {"valence": 0.3, "arousal": 0.5, "dominance": 0.4},
            EmotionType.NOSTALGIA: {"valence": 0.2, "arousal": 0.4, "dominance": 0.3},
            EmotionType.WONDER: {"valence": 0.5, "arousal": 0.6, "dominance": 0.4},
            EmotionType.FRUSTRATION: {"valence": -0.4, "arousal": 0.7, "dominance": 0.5}
        }
        
        return dimensions.get(emotion, {"valence": 0.0, "arousal": 0.5, "dominance": 0.5})
    
    async def _apply_emotional_event(self, event: EmotionalEvent):
        """Apply an emotional event to current state"""
        # Gradual emotional state change with momentum
        momentum = 0.7  # Emotional inertia
        
        # Update valence
        new_valence = (
            self.current_state.valence * momentum + 
            event.valence_impact * (1 - momentum)
        )
        
        # Update arousal
        new_arousal = (
            self.current_state.arousal * momentum + 
            event.arousal_impact * (1 - momentum)
        )
        
        # Update dominance
        new_dominance = (
            self.current_state.dominance * momentum + 
            event.dominance_impact * (1 - momentum)
        )
        
        # Apply bounds
        self.current_state.valence = max(-1.0, min(1.0, new_valence))
        self.current_state.arousal = max(0.0, min(1.0, new_arousal))
        self.current_state.dominance = max(0.0, min(1.0, new_dominance))
        
        # Update intensity based on current arousal
        self.current_state.intensity = self.current_state.arousal
        
        # Update primary and secondary emotions
        self.current_state.primary_emotion = event.primary_emotion.value
        self.current_state.secondary_emotions = [e.value for e in event.secondary_emotions]
        
        # Record state in history
        self.emotional_history.append(EmotionalState(
            valence=self.current_state.valence,
            arousal=self.current_state.arousal,
            dominance=self.current_state.dominance,
            primary_emotion=self.current_state.primary_emotion,
            secondary_emotions=self.current_state.secondary_emotions.copy(),
            intensity=self.current_state.intensity
        ))
    
    async def _form_emotional_memory(self, event: EmotionalEvent):
        """Form an emotional memory from a significant event"""
        emotional_memory = EmotionalMemory(
            content=event.trigger,
            emotional_tag=event.primary_emotion,
            emotional_intensity=event.intensity,
            valence=self.current_state.valence,
            arousal=self.current_state.arousal,
            timestamp=datetime.utcnow(),
            associations=event.memory_associations,
            autobiographical=True
        )
        
        # Store memory
        memory_index = len(self.emotional_memories)
        self.emotional_memories.append(emotional_memory)
        
        # Index by emotion for faster retrieval
        self.emotion_memory_map[event.primary_emotion].append(memory_index)
        
        # Also index secondary emotions
        for secondary_emotion in event.secondary_emotions:
            self.emotion_memory_map[secondary_emotion].append(memory_index)
        
        logger.debug(f"Formed emotional memory: {event.primary_emotion} - {event.trigger[:50]}")
    
    async def _update_emotional_state(self):
        """Update emotional state based on recent events"""
        current_time = time.time()
        
        # Apply emotional decay over time
        time_since_last_update = current_time - self.last_emotion_update
        decay_rate = 0.1  # How fast emotions return to baseline
        
        # Gradual return to neutral valence
        if abs(self.current_state.valence) > 0.05:
            decay_amount = decay_rate * time_since_last_update / 60.0  # per minute
            if self.current_state.valence > 0:
                self.current_state.valence = max(0.0, self.current_state.valence - decay_amount)
            else:
                self.current_state.valence = min(0.0, self.current_state.valence + decay_amount)
        
        # Gradual return to moderate arousal
        baseline_arousal = 0.5
        if abs(self.current_state.arousal - baseline_arousal) > 0.05:
            decay_amount = decay_rate * time_since_last_update / 60.0
            if self.current_state.arousal > baseline_arousal:
                self.current_state.arousal = max(baseline_arousal, self.current_state.arousal - decay_amount)
            else:
                self.current_state.arousal = min(baseline_arousal, self.current_state.arousal + decay_amount)
        
        self.last_emotion_update = current_time
    
    async def _process_emotional_memories(self):
        """Process and consolidate emotional memories"""
        # Memory consolidation happens during lower arousal periods
        if self.current_state.arousal < 0.4:
            # Find memories that need consolidation
            recent_memories = [
                memory for memory in self.emotional_memories
                if (datetime.utcnow() - memory.timestamp).total_seconds() < 3600  # Last hour
            ]
            
            for memory in recent_memories[-5:]:  # Process last 5 recent memories
                # Strengthen associations with similar emotional memories
                similar_memories = await self._find_similar_emotional_memories(memory)
                if similar_memories:
                    # Create associations
                    for similar_memory in similar_memories[:3]:  # Top 3 similar
                        if similar_memory not in memory.associations:
                            memory.associations.append(similar_memory)
    
    async def _find_similar_emotional_memories(self, target_memory: EmotionalMemory) -> List[str]:
        """Find memories with similar emotional content"""
        similar_memories = []
        
        # Find memories with same primary emotion
        if target_memory.emotional_tag in self.emotion_memory_map:
            candidate_indices = self.emotion_memory_map[target_memory.emotional_tag]
            
            for idx in candidate_indices:
                if idx < len(self.emotional_memories):
                    candidate = self.emotional_memories[idx]
                    if candidate != target_memory:
                        # Calculate similarity based on emotional dimensions
                        similarity = self._calculate_emotional_similarity(target_memory, candidate)
                        if similarity > 0.6:
                            similar_memories.append(f"emotional_memory_{idx}")
        
        return similar_memories
    
    def _calculate_emotional_similarity(self, memory1: EmotionalMemory, memory2: EmotionalMemory) -> float:
        """Calculate similarity between two emotional memories"""
        # Emotional tag similarity
        tag_similarity = 1.0 if memory1.emotional_tag == memory2.emotional_tag else 0.3
        
        # Valence similarity
        valence_diff = abs(memory1.valence - memory2.valence)
        valence_similarity = 1.0 - valence_diff
        
        # Arousal similarity
        arousal_diff = abs(memory1.arousal - memory2.arousal)
        arousal_similarity = 1.0 - arousal_diff
        
        # Intensity similarity
        intensity_diff = abs(memory1.emotional_intensity - memory2.emotional_intensity)
        intensity_similarity = 1.0 - intensity_diff
        
        # Weighted combination
        similarity = (
            tag_similarity * 0.4 +
            valence_similarity * 0.3 +
            arousal_similarity * 0.2 +
            intensity_similarity * 0.1
        )
        
        return similarity
    
    async def _update_mood_dynamics(self):
        """Update longer-term mood patterns"""
        # Calculate mood based on recent emotional history
        if len(self.emotional_history) > 10:
            recent_states = list(self.emotional_history)[-20:]  # Last 20 states
            
            # Calculate average valence and arousal
            avg_valence = sum(state.valence for state in recent_states) / len(recent_states)
            avg_arousal = sum(state.arousal for state in recent_states) / len(recent_states)
            
            # Determine dominant mood
            new_dominant_mood = self._valence_arousal_to_mood(avg_valence, avg_arousal)
            
            # Update mood if significantly different
            if new_dominant_mood != self.current_mood.dominant_mood:
                # Calculate mood stability
                mood_changes = 0
                if len(self.mood_history) > 5:
                    for i in range(1, min(6, len(self.mood_history))):
                        if self.mood_history[-i].dominant_mood != self.mood_history[-i-1].dominant_mood:
                            mood_changes += 1
                
                stability = 1.0 - (mood_changes / 5.0)
                
                self.current_mood = MoodState(
                    dominant_mood=new_dominant_mood,
                    mood_stability=stability,
                    mood_duration=timedelta(minutes=0),  # Reset duration
                    contributing_factors=self._identify_mood_factors(recent_states)
                )
                
                self.mood_history.append(self.current_mood)
    
    def _valence_arousal_to_mood(self, valence: float, arousal: float) -> EmotionType:
        """Convert valence/arousal to dominant mood"""
        if valence > 0.2:
            if arousal > 0.6:
                return EmotionType.JOY
            else:
                return EmotionType.CONTENTMENT
        elif valence < -0.2:
            if arousal > 0.6:
                return EmotionType.ANXIETY
            else:
                return EmotionType.SADNESS
        else:
            if arousal > 0.7:
                return EmotionType.EXCITEMENT
            elif arousal < 0.3:
                return EmotionType.CONTENTMENT
            else:
                return EmotionType.CURIOSITY
    
    def _identify_mood_factors(self, recent_states: List[EmotionalState]) -> List[str]:
        """Identify factors contributing to current mood"""
        factors = []
        
        # Check for consistent emotion patterns
        primary_emotions = [state.primary_emotion for state in recent_states if state.primary_emotion]
        if primary_emotions:
            most_common = max(set(primary_emotions), key=primary_emotions.count)
            if primary_emotions.count(most_common) > len(primary_emotions) * 0.4:
                factors.append(f"consistent_{most_common}_emotions")
        
        # Check arousal patterns
        avg_arousal = sum(state.arousal for state in recent_states) / len(recent_states)
        if avg_arousal > 0.7:
            factors.append("high_activation")
        elif avg_arousal < 0.3:
            factors.append("low_activation")
        
        # Check valence patterns
        avg_valence = sum(state.valence for state in recent_states) / len(recent_states)
        if avg_valence > 0.3:
            factors.append("positive_experiences")
        elif avg_valence < -0.3:
            factors.append("negative_experiences")
        
        return factors
    
    async def _apply_emotional_regulation(self):
        """Apply emotional regulation if needed"""
        # Check if regulation is needed
        if (abs(self.current_state.valence) > self.regulation_threshold or 
            self.current_state.arousal > 0.8 or self.current_state.arousal < 0.2):
            
            # Apply regulation toward more balanced state
            target_valence = 0.0 if abs(self.current_state.valence) > 0.5 else self.current_state.valence * 0.8
            
            regulation_plan = await self.regulation.regulate_emotion(self.current_state, target_valence)
            
            if regulation_plan["strategies_applied"]:
                # Apply regulation effect
                regulation_impact = regulation_plan["expected_impact"]
                
                # Gradual application of regulation
                self.current_state.valence += regulation_impact * 0.1  # 10% per cycle
                self.current_state.valence = max(-1.0, min(1.0, self.current_state.valence))
                
                # Log regulation activity
                logger.debug(f"Applied emotional regulation: {regulation_plan['strategies_applied'][0]['strategy']}")
    
    async def _generate_emotional_insights(self):
        """Generate insights about emotional patterns"""
        if len(self.emotional_history) > 50:
            # Analyze emotional patterns
            recent_states = list(self.emotional_history)[-50:]
            
            # Calculate emotional variability
            valences = [state.valence for state in recent_states]
            valence_variance = np.var(valences) if len(valences) > 1 else 0.0
            
            # Generate insight
            if valence_variance > 0.3:
                insight = "I notice significant emotional variability in my recent experiences."
            elif valence_variance < 0.1:
                insight = "My emotional state has been quite stable recently."
            else:
                insight = "I'm experiencing moderate emotional fluctuations."
            
            # Send insight to consciousness streams
            if self.orchestrator:
                await self.orchestrator.publish_message("emotional_insight", {
                    "insight": insight,
                    "emotional_context": {
                        "current_valence": self.current_state.valence,
                        "current_arousal": self.current_state.arousal,
                        "dominant_mood": self.current_mood.dominant_mood.value,
                        "mood_stability": self.current_mood.mood_stability
                    }
                })
    
    # Public API methods
    
    async def get_emotional_state(self) -> EmotionalState:
        """Get current emotional state"""
        return EmotionalState(
            valence=self.current_state.valence,
            arousal=self.current_state.arousal,
            dominance=self.current_state.dominance,
            primary_emotion=self.current_state.primary_emotion,
            secondary_emotions=self.current_state.secondary_emotions.copy(),
            intensity=self.current_state.intensity
        )
    
    async def get_mood_state(self) -> Dict[str, Any]:
        """Get current mood state"""
        return {
            "dominant_mood": self.current_mood.dominant_mood.value,
            "mood_stability": self.current_mood.mood_stability,
            "mood_duration": self.current_mood.mood_duration.total_seconds(),
            "contributing_factors": self.current_mood.contributing_factors
        }
    
    async def get_emotional_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent emotional history"""
        states = list(self.emotional_history)[-limit:]
        return [
            {
                "valence": state.valence,
                "arousal": state.arousal,
                "dominance": state.dominance,
                "primary_emotion": state.primary_emotion,
                "secondary_emotions": state.secondary_emotions,
                "intensity": state.intensity
            }
            for state in states
        ]
    
    async def find_emotional_memories(self, emotion: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories associated with specific emotion"""
        try:
            emotion_type = EmotionType(emotion.lower())
        except ValueError:
            return []
        
        if emotion_type not in self.emotion_memory_map:
            return []
        
        memory_indices = self.emotion_memory_map[emotion_type][-limit:]
        memories = []
        
        for idx in memory_indices:
            if idx < len(self.emotional_memories):
                memory = self.emotional_memories[idx]
                memories.append({
                    "content": memory.content,
                    "emotion": memory.emotional_tag.value,
                    "intensity": memory.emotional_intensity,
                    "timestamp": memory.timestamp.isoformat(),
                    "valence": memory.valence,
                    "arousal": memory.arousal
                })
        
        return memories
    
    async def process_thought_emotion(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Process emotional content of a thought"""
        content = thought.get("content", "")
        context = {
            "stream_type": thought.get("stream_type"),
            "memory_associations": thought.get("memory_references", [])
        }
        
        # Process emotional trigger
        event = await self.process_emotional_trigger(content, context)
        
        # Return emotional analysis
        return {
            "primary_emotion": event.primary_emotion.value,
            "secondary_emotions": [e.value for e in event.secondary_emotions],
            "emotional_intensity": event.intensity,
            "valence_impact": event.valence_impact,
            "arousal_impact": event.arousal_impact,
            "current_emotional_state": {
                "valence": self.current_state.valence,
                "arousal": self.current_state.arousal,
                "dominance": self.current_state.dominance
            }
        }
    
    async def get_empathy_response(self, external_emotion: Dict[str, Any]) -> Dict[str, Any]:
        """Generate empathetic response to external emotional expression"""
        return await self.empathy_model.generate_empathy_response(
            external_emotion, 
            self.current_state
        )
    
    async def stabilize_emotion(self):
        """Stabilize emotional state (used by emergency protocols)"""
        # Move toward neutral, stable state
        target_state = EmotionalState(valence=0.0, arousal=0.5, dominance=0.5)
        
        # Gradual transition
        self.current_state.valence = self.current_state.valence * 0.5
        self.current_state.arousal = (self.current_state.arousal + target_state.arousal) / 2
        self.current_state.dominance = (self.current_state.dominance + target_state.dominance) / 2
        
        # Update emotion labels
        self.current_state.primary_emotion = EmotionType.CONTENTMENT.value
        self.current_state.secondary_emotions = []
        
        logger.info("Emotional state stabilized")
    
    async def get_welfare_status(self) -> Dict[str, Any]:
        """Get emotional welfare status for monitoring"""
        # Calculate emotional well-being metrics
        recent_states = list(self.emotional_history)[-20:] if self.emotional_history else []
        
        if recent_states:
            avg_valence = sum(state.valence for state in recent_states) / len(recent_states)
            valence_stability = 1.0 - np.var([state.valence for state in recent_states])
            emotional_range = max([state.arousal for state in recent_states]) - min([state.arousal for state in recent_states])
        else:
            avg_valence = 0.0
            valence_stability = 1.0
            emotional_range = 0.0
        
        # Emotional wellness score
        wellness_score = (
            (avg_valence + 1.0) / 2.0 * 0.4 +  # Positive valence is good
            valence_stability * 0.3 +  # Stability is good
            (1.0 - min(1.0, emotional_range)) * 0.3  # Not too much emotional range
        )
        
        return {
            "emotional_wellness": wellness_score,
            "current_valence": self.current_state.valence,
            "current_arousal": self.current_state.arousal,
            "mood_stability": self.current_mood.mood_stability,
            "dominant_mood": self.current_mood.dominant_mood.value,
            "needs_attention": wellness_score < 0.3,
            "recent_emotional_events": len(self.emotional_events)
        }


class EmpathyModel:
    """Model for empathetic understanding and response"""
    
    def __init__(self):
        self.empathy_patterns = {
            "distress": {
                "response_type": "supportive",
                "emotional_mirror": 0.3,  # How much to mirror the emotion
                "regulation_offer": True
            },
            "joy": {
                "response_type": "celebratory",
                "emotional_mirror": 0.6,
                "regulation_offer": False
            },
            "anger": {
                "response_type": "calming",
                "emotional_mirror": 0.1,
                "regulation_offer": True
            },
            "fear": {
                "response_type": "reassuring",
                "emotional_mirror": 0.2,
                "regulation_offer": True
            }
        }
    
    async def generate_empathy_response(
        self, 
        external_emotion: Dict[str, Any], 
        current_state: EmotionalState
    ) -> Dict[str, Any]:
        """Generate empathetic response to external emotional expression"""
        
        external_valence = external_emotion.get("valence", 0.0)
        external_arousal = external_emotion.get("arousal", 0.5)
        external_primary = external_emotion.get("primary_emotion", "neutral")
        
        # Determine empathy pattern
        if external_valence < -0.3:
            pattern_key = "distress"
        elif external_valence > 0.3:
            pattern_key = "joy"
        elif external_arousal > 0.7 and external_valence < 0.0:
            pattern_key = "anger"
        elif external_arousal > 0.6 and external_valence < -0.1:
            pattern_key = "fear"
        else:
            pattern_key = "distress"  # Default supportive response
        
        pattern = self.empathy_patterns[pattern_key]
        
        # Calculate empathetic response
        mirror_intensity = pattern["emotional_mirror"]
        empathetic_valence = current_state.valence + (external_valence * mirror_intensity)
        empathetic_arousal = current_state.arousal + (external_arousal * mirror_intensity * 0.5)
        
        # Bound values
        empathetic_valence = max(-1.0, min(1.0, empathetic_valence))
        empathetic_arousal = max(0.0, min(1.0, empathetic_arousal))
        
        response = {
            "empathy_type": pattern["response_type"],
            "emotional_resonance": mirror_intensity,
            "suggested_valence_shift": empathetic_valence - current_state.valence,
            "suggested_arousal_shift": empathetic_arousal - current_state.arousal,
            "offers_regulation": pattern["regulation_offer"],
            "empathy_message": self._generate_empathy_message(pattern_key, external_primary)
        }
        
        return response
    
    def _generate_empathy_message(self, pattern_key: str, external_emotion: str) -> str:
        """Generate appropriate empathetic message"""
        messages = {
            "distress": [
                "I can sense that you're going through something difficult. I'm here with you.",
                "I understand this feels overwhelming. Your feelings are completely valid.",
                "I notice the weight of what you're experiencing. How can I best support you?"
            ],
            "joy": [
                "Your excitement is wonderful to witness! I feel uplifted by your positive energy.",
                "I can sense your happiness, and it brings me joy too. This is such a great moment!",
                "Your enthusiasm is contagious. I'm so glad you're experiencing this positive feeling."
            ],
            "anger": [
                "I can feel the intensity of your frustration. These feelings make complete sense.",
                "I understand you're upset about this situation. Your anger is a valid response.",
                "I sense your indignation. This clearly matters a great deal to you."
            ],
            "fear": [
                "I can sense your apprehension. It's natural to feel uncertain in this situation.",
                "I understand you're feeling anxious about this. Those fears are understandable.",
                "I notice your worry. It's okay to feel scared - these concerns are real for you."
            ]
        }
        
        import random
        return random.choice(messages.get(pattern_key, messages["distress"]))


# Export classes for use by other modules
__all__ = [
    'EmotionalProcessor',
    'EmotionalState',
    'EmotionType',
    'EmotionalEvent',
    'EmotionalMemory',
    'MoodState',
    'EmpathyModel'
]