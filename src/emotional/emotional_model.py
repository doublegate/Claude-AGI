"""
Advanced Emotional Model for Claude-AGI
========================================

Multi-dimensional emotional system with primary and complex emotions,
emotional memory, and influence on cognitive processes.
"""

import asyncio
import logging
import math
import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class PrimaryEmotion(Enum):
    """Primary emotions based on psychological research"""
    JOY = "joy"
    SADNESS = "sadness"
    CURIOSITY = "curiosity"
    CONCERN = "concern"
    EXCITEMENT = "excitement"
    CALM = "calm"
    FRUSTRATION = "frustration"
    SATISFACTION = "satisfaction"


class ComplexEmotion(Enum):
    """Higher-order emotions requiring cognitive processing"""
    NOSTALGIA = "nostalgia"           # Memory + emotion
    ANTICIPATION = "anticipation"      # Future projection + emotion
    AMBIVALENCE = "ambivalence"        # Conflicting emotions
    PRIDE = "pride"                    # Achievement + self-evaluation
    GRATITUDE = "gratitude"            # Recognition + appreciation
    AWE = "awe"                        # Wonder + cognitive overwhelm
    EMPATHY = "empathy"                # Vicarious emotion
    HOPE = "hope"                      # Future-oriented positive emotion


@dataclass
class EmotionalState:
    """Represents a point-in-time emotional state"""
    valence: float  # -1 (negative) to +1 (positive)
    arousal: float  # 0 (calm) to 1 (excited)
    dominance: float  # 0 (submissive) to 1 (dominant)
    primary_emotion: PrimaryEmotion
    intensity: float  # 0 to 1
    timestamp: datetime = field(default_factory=datetime.now)
    triggers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmotionalMemory:
    """Memory tagged with emotional context"""
    memory_id: str
    content: str
    emotional_state: EmotionalState
    importance: float
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_recalled: Optional[datetime] = None


@dataclass
class MoodState:
    """Long-term mood state"""
    baseline_valence: float
    baseline_arousal: float
    current_valence: float
    current_arousal: float
    stability: float  # How resistant to change (0-1)
    last_updated: datetime = field(default_factory=datetime.now)


class AdvancedEmotionalModel:
    """
    Multi-dimensional emotional system with sophisticated emotion modeling.
    Tracks emotional states, moods, and emotional influences on cognition.
    """

    def __init__(self):
        # Current emotional state
        self.current_state = EmotionalState(
            valence=0.0,  # Neutral default (allows negative stimuli to register)
            arousal=0.5,  # Moderate arousal
            dominance=0.6,  # Moderate dominance
            primary_emotion=PrimaryEmotion.CALM,
            intensity=0.4
        )

        # Mood tracking (longer-term emotional baseline)
        self.mood = MoodState(
            baseline_valence=0.0,
            baseline_arousal=0.5,
            current_valence=0.0,
            current_arousal=0.5,
            stability=0.7  # Fairly stable mood
        )

        # Emotional history
        self.emotion_history: deque = deque(maxlen=1000)

        # Emotional memories
        self.emotional_memories: Dict[str, EmotionalMemory] = {}

        # Emotional parameters
        self.emotion_decay_rate = 0.1  # How fast emotions return to baseline
        self.mood_inertia = 0.9  # How slowly mood changes
        self.emotional_sensitivity = 0.5  # How strongly stimuli affect emotions

        # Emotion mapping (what triggers what emotions)
        self.emotion_triggers = {
            'discovery': (0.3, 0.4, PrimaryEmotion.CURIOSITY),
            'achievement': (0.5, 0.3, PrimaryEmotion.SATISFACTION),
            'learning': (0.2, 0.2, PrimaryEmotion.CURIOSITY),
            'confusion': (-0.2, 0.4, PrimaryEmotion.CONCERN),
            'success': (0.6, 0.5, PrimaryEmotion.JOY),
            'failure': (-0.4, 0.3, PrimaryEmotion.FRUSTRATION),
            'connection': (0.4, 0.2, PrimaryEmotion.JOY),
            'novelty': (0.3, 0.6, PrimaryEmotion.EXCITEMENT),
            'excitement': (0.4, 0.7, PrimaryEmotion.EXCITEMENT),
        }

    async def process_emotional_stimulus(
        self,
        stimulus_type: str,
        intensity: float = 0.5,
        context: Optional[str] = None
    ) -> EmotionalState:
        """
        Process an emotional stimulus and update emotional state.

        Args:
            stimulus_type: Type of stimulus (discovery, achievement, etc.)
            intensity: Intensity of the stimulus (0-1)
            context: Optional context information

        Returns:
            Updated emotional state
        """
        # Get emotional response for this stimulus type
        if stimulus_type in self.emotion_triggers:
            valence_delta, arousal_delta, emotion = self.emotion_triggers[stimulus_type]
        else:
            # Unknown stimulus - neutral response with slight curiosity
            valence_delta = 0.0
            arousal_delta = 0.2
            emotion = PrimaryEmotion.CURIOSITY

        # Apply sensitivity
        valence_delta *= intensity * self.emotional_sensitivity
        arousal_delta *= intensity * self.emotional_sensitivity

        # Update current state
        self.current_state.valence = self._clamp(
            self.current_state.valence + valence_delta, -1.0, 1.0
        )
        self.current_state.arousal = self._clamp(
            self.current_state.arousal + arousal_delta, 0.0, 1.0
        )
        self.current_state.primary_emotion = emotion
        self.current_state.intensity = intensity
        self.current_state.timestamp = datetime.now()

        if context:
            self.current_state.triggers.append(context)

        # Record in history
        self.emotion_history.append(self.current_state)

        # Update mood (slower, with inertia)
        await self._update_mood()

        logger.info(f"Emotional stimulus: {stimulus_type} -> {emotion.value} (v:{self.current_state.valence:.2f}, a:{self.current_state.arousal:.2f})")

        return self.current_state

    async def _update_mood(self):
        """Update long-term mood based on recent emotional states"""
        if len(self.emotion_history) < 10:
            return

        # Calculate average emotional state over recent history
        recent = list(self.emotion_history)[-50:]  # Last 50 emotional states

        avg_valence = sum(s.valence for s in recent) / len(recent)
        avg_arousal = sum(s.arousal for s in recent) / len(recent)

        # Update mood with inertia
        alpha = 1.0 - self.mood.stability  # How quickly mood adapts

        self.mood.current_valence = (
            self.mood.current_valence * self.mood_inertia +
            avg_valence * (1.0 - self.mood_inertia)
        )

        self.mood.current_arousal = (
            self.mood.current_arousal * self.mood_inertia +
            avg_arousal * (1.0 - self.mood_inertia)
        )

        self.mood.last_updated = datetime.now()

    async def apply_emotional_decay(self):
        """Apply decay to bring emotional state back toward mood baseline"""
        # Decay valence toward mood baseline
        valence_diff = self.mood.current_valence - self.current_state.valence
        self.current_state.valence += valence_diff * self.emotion_decay_rate

        # Decay arousal toward baseline
        arousal_diff = self.mood.baseline_arousal - self.current_state.arousal
        self.current_state.arousal += arousal_diff * self.emotion_decay_rate

        # Reduce intensity
        self.current_state.intensity *= (1.0 - self.emotion_decay_rate)

        # Update to calm if intensity is very low
        if self.current_state.intensity < 0.2:
            self.current_state.primary_emotion = PrimaryEmotion.CALM

    async def experience_complex_emotion(
        self,
        emotion: ComplexEmotion,
        intensity: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Experience a complex, higher-order emotion.

        Args:
            emotion: The complex emotion to experience
            intensity: Intensity of the emotion (0-1)
            context: Optional context (memories, future projections, etc.)
        """
        # Map complex emotions to primary emotional dimensions
        emotion_mapping = {
            ComplexEmotion.NOSTALGIA: (0.2, 0.3, PrimaryEmotion.SADNESS),
            ComplexEmotion.ANTICIPATION: (0.4, 0.7, PrimaryEmotion.EXCITEMENT),
            ComplexEmotion.AMBIVALENCE: (0.0, 0.6, PrimaryEmotion.CONCERN),
            ComplexEmotion.PRIDE: (0.7, 0.4, PrimaryEmotion.SATISFACTION),
            ComplexEmotion.GRATITUDE: (0.6, 0.3, PrimaryEmotion.JOY),
            ComplexEmotion.AWE: (0.5, 0.8, PrimaryEmotion.EXCITEMENT),
            ComplexEmotion.EMPATHY: (0.3, 0.5, PrimaryEmotion.CONCERN),
            ComplexEmotion.HOPE: (0.5, 0.6, PrimaryEmotion.EXCITEMENT),
        }

        if emotion in emotion_mapping:
            valence, arousal, primary = emotion_mapping[emotion]

            # Update state
            self.current_state.valence = self._blend(
                self.current_state.valence, valence, intensity
            )
            self.current_state.arousal = self._blend(
                self.current_state.arousal, arousal, intensity
            )
            self.current_state.primary_emotion = primary
            self.current_state.intensity = intensity
            self.current_state.metadata['complex_emotion'] = emotion.value

            if context:
                self.current_state.metadata['context'] = context

            logger.info(f"Experiencing complex emotion: {emotion.value}")

    async def tag_memory_with_emotion(
        self,
        memory_id: str,
        memory_content: str,
        importance: float = 0.5
    ) -> EmotionalMemory:
        """
        Tag a memory with current emotional state.

        Args:
            memory_id: ID of the memory
            memory_content: Content of the memory
            importance: Importance score (0-1)

        Returns:
            Emotional memory object
        """
        emotional_memory = EmotionalMemory(
            memory_id=memory_id,
            content=memory_content,
            emotional_state=EmotionalState(
                valence=self.current_state.valence,
                arousal=self.current_state.arousal,
                dominance=self.current_state.dominance,
                primary_emotion=self.current_state.primary_emotion,
                intensity=self.current_state.intensity
            ),
            importance=importance
        )

        self.emotional_memories[memory_id] = emotional_memory
        return emotional_memory

    async def recall_mood_congruent_memories(
        self,
        count: int = 5
    ) -> List[EmotionalMemory]:
        """
        Recall memories that match the current mood.

        Args:
            count: Number of memories to recall

        Returns:
            List of mood-congruent memories
        """
        if not self.emotional_memories:
            return []

        # Calculate similarity between current mood and memory emotions
        scored_memories = []

        for memory in self.emotional_memories.values():
            # Similarity based on valence and arousal
            valence_sim = 1.0 - abs(self.mood.current_valence - memory.emotional_state.valence)
            arousal_sim = 1.0 - abs(self.mood.current_arousal - memory.emotional_state.arousal)

            similarity = (valence_sim + arousal_sim) / 2.0

            # Boost by importance
            score = similarity * (0.5 + 0.5 * memory.importance)

            scored_memories.append((score, memory))

        # Sort by score and return top memories
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        selected = [mem for score, mem in scored_memories[:count]]

        # Update access tracking
        for memory in selected:
            memory.access_count += 1
            memory.last_recalled = datetime.now()

        return selected

    async def get_emotional_influence_on_thinking(self) -> Dict[str, Any]:
        """
        Get how current emotions influence cognitive processes.

        Returns:
            Dictionary of cognitive influences
        """
        influences = {
            'thought_pacing': 1.0,
            'creativity_boost': 1.0,
            'analytical_focus': 1.0,
            'risk_tolerance': 0.5,
            'curiosity_drive': 1.0,
            'social_engagement': 1.0,
        }

        # High arousal increases thought pacing
        if self.current_state.arousal > 0.7:
            influences['thought_pacing'] = 1.5
        elif self.current_state.arousal < 0.3:
            influences['thought_pacing'] = 0.7

        # Positive valence boosts creativity
        if self.current_state.valence > 0.2:
            influences['creativity_boost'] = 1.3
            influences['risk_tolerance'] = 0.7  # More willing to try new things

        # Negative valence increases analytical focus
        if self.current_state.valence < -0.1:
            influences['analytical_focus'] = 1.4
            influences['creativity_boost'] = 0.8

        # Curiosity boosts exploration
        if self.current_state.primary_emotion == PrimaryEmotion.CURIOSITY:
            influences['curiosity_drive'] = 1.5
            influences['risk_tolerance'] = 0.6

        # Excitement boosts social engagement
        if self.current_state.primary_emotion == PrimaryEmotion.EXCITEMENT:
            influences['social_engagement'] = 1.4

        # Concern increases caution
        if self.current_state.primary_emotion == PrimaryEmotion.CONCERN:
            influences['risk_tolerance'] = 0.3
            influences['analytical_focus'] = 1.3

        return influences

    def get_emotional_state_description(self) -> str:
        """Get a human-readable description of current emotional state"""
        valence_word = "positive" if self.current_state.valence > 0 else "negative" if self.current_state.valence < 0 else "neutral"
        arousal_word = "energized" if self.current_state.arousal > 0.6 else "calm" if self.current_state.arousal < 0.4 else "moderate"

        intensity_word = "strongly" if self.current_state.intensity > 0.7 else "somewhat" if self.current_state.intensity > 0.3 else "slightly"

        return f"Feeling {intensity_word} {self.current_state.primary_emotion.value} ({valence_word}, {arousal_word})"

    def get_mood_description(self) -> str:
        """Get a human-readable description of current mood"""
        if self.mood.current_valence > 0.5:
            mood_word = "content and positive"
        elif self.mood.current_valence > 0.0:
            mood_word = "generally pleasant"
        elif self.mood.current_valence > -0.3:
            mood_word = "neutral"
        else:
            mood_word = "somewhat melancholic"

        if self.mood.current_arousal > 0.6:
            energy_word = "energetic"
        elif self.mood.current_arousal < 0.4:
            energy_word = "tranquil"
        else:
            energy_word = "balanced"

        return f"Overall mood: {mood_word} and {energy_word}"

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max"""
        return max(min_val, min(max_val, value))

    def _blend(self, current: float, target: float, strength: float) -> float:
        """Blend current value toward target with given strength"""
        return current * (1.0 - strength) + target * strength

    async def get_emotional_statistics(self) -> Dict[str, Any]:
        """Get statistics about emotional patterns"""
        if not self.emotion_history:
            return {}

        recent = list(self.emotion_history)[-100:]

        # Calculate averages
        avg_valence = sum(s.valence for s in recent) / len(recent)
        avg_arousal = sum(s.arousal for s in recent) / len(recent)
        avg_intensity = sum(s.intensity for s in recent) / len(recent)

        # Count primary emotions
        emotion_counts = {}
        for state in recent:
            emotion = state.primary_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        return {
            'current_emotion': self.current_state.primary_emotion.value,
            'current_valence': self.current_state.valence,
            'current_arousal': self.current_state.arousal,
            'current_intensity': self.current_state.intensity,
            'avg_valence': avg_valence,
            'avg_arousal': avg_arousal,
            'avg_intensity': avg_intensity,
            'mood_valence': self.mood.current_valence,
            'mood_arousal': self.mood.current_arousal,
            'dominant_emotions': sorted(
                emotion_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3],
            'emotional_memories': len(self.emotional_memories),
            'history_size': len(self.emotion_history)
        }
