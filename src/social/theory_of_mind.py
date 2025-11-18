"""
Theory of Mind for Claude-AGI
==============================

Models mental states of users including beliefs, intentions, and emotions.
Enables perspective-taking and empathetic reasoning.
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class BeliefType(Enum):
    """Types of beliefs the user might hold"""
    FACTUAL = "factual"           # Beliefs about facts
    PREFERENTIAL = "preferential"  # Preferences and likes
    NORMATIVE = "normative"        # Beliefs about what should be
    SELF = "self"                  # Beliefs about themselves
    OTHER = "other"                # Beliefs about others


@dataclass
class UserBelief:
    """Represents a belief attributed to a user"""
    content: str
    belief_type: BeliefType
    confidence: float  # How confident we are they believe this (0-1)
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    contradicted: bool = False


@dataclass
class UserIntention:
    """Represents an inferred intention"""
    goal: str
    intention_type: str  # 'immediate', 'session', 'long_term'
    confidence: float
    evidence: List[str] = field(default_factory=list)
    sub_goals: List[str] = field(default_factory=list)
    status: str = "active"  # 'active', 'achieved', 'abandoned'


@dataclass
class EmotionalStateInference:
    """Inferred emotional state of user"""
    emotion: str
    valence: float  # -1 to +1
    arousal: float  # 0 to 1
    confidence: float
    indicators: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerspectiveModel:
    """Model of a user's perspective"""
    user_id: str
    beliefs: Dict[str, UserBelief]
    intentions: Dict[str, UserIntention]
    emotional_history: deque
    knowledge_state: Set[str]  # What they know
    preferences: Dict[str, float]  # Topic -> preference score
    communication_style: Dict[str, Any]
    last_updated: datetime = field(default_factory=datetime.now)


class TheoryOfMind:
    """
    Theory of Mind system for modeling user mental states.
    Tracks beliefs, intentions, knowledge, and emotions.
    """

    def __init__(self):
        # User perspective models
        self.user_models: Dict[str, PerspectiveModel] = {}

        # Conversation context
        self.conversation_history: deque = deque(maxlen=100)

        # Empathy parameters
        self.empathy_threshold = 0.6
        self.confidence_threshold = 0.4

    async def initialize_user_model(self, user_id: str) -> PerspectiveModel:
        """Initialize a perspective model for a new user"""
        if user_id not in self.user_models:
            self.user_models[user_id] = PerspectiveModel(
                user_id=user_id,
                beliefs={},
                intentions={},
                emotional_history=deque(maxlen=50),
                knowledge_state=set(),
                preferences={},
                communication_style={}
            )

        return self.user_models[user_id]

    async def infer_belief(
        self,
        user_id: str,
        statement: str,
        context: Optional[str] = None
    ) -> Optional[UserBelief]:
        """
        Infer a belief from user statement.

        Args:
            user_id: User identifier
            statement: User's statement
            context: Optional conversation context

        Returns:
            Inferred belief or None
        """
        model = await self.initialize_user_model(user_id)

        # Detect belief type
        belief_type = self._detect_belief_type(statement)

        # Extract belief content
        # In production, would use NLP for better extraction
        belief_content = statement.strip()

        # Calculate confidence
        confidence = self._calculate_belief_confidence(statement, context)

        # Create belief
        belief = UserBelief(
            content=belief_content,
            belief_type=belief_type,
            confidence=confidence,
            evidence=[statement]
        )

        # Store in model
        belief_id = f"belief_{len(model.beliefs)}"
        model.beliefs[belief_id] = belief

        logger.info(f"Inferred belief for {user_id}: {belief_content} ({belief_type.value}, confidence: {confidence:.2f})")

        return belief

    def _detect_belief_type(self, statement: str) -> BeliefType:
        """Detect the type of belief from statement"""
        statement_lower = statement.lower()

        # Preferential indicators
        if any(word in statement_lower for word in ['like', 'love', 'hate', 'prefer', 'enjoy']):
            return BeliefType.PREFERENTIAL

        # Normative indicators
        if any(word in statement_lower for word in ['should', 'must', 'ought', 'right', 'wrong']):
            return BeliefType.NORMATIVE

        # Self beliefs
        if any(word in statement_lower for word in ['i am', "i'm", 'i feel', 'i think']):
            return BeliefType.SELF

        # Default to factual
        return BeliefType.FACTUAL

    def _calculate_belief_confidence(
        self,
        statement: str,
        context: Optional[str]
    ) -> float:
        """Calculate confidence in belief inference"""
        confidence = 0.5  # Base confidence

        # Boost for explicit markers
        if any(marker in statement.lower() for marker in ['believe', 'think', 'feel', 'sure']):
            confidence += 0.2

        # Boost for first-person statements
        if any(pronoun in statement.lower() for pronoun in ['i ', 'my ', 'me ']):
            confidence += 0.15

        # Reduce for questions
        if '?' in statement:
            confidence -= 0.2

        # Reduce for hedging language (count each hedge word)
        hedge_words = ['maybe', 'perhaps', 'possibly', 'might', 'could']
        statement_lower = statement.lower()
        hedge_count = sum(1 for hedge in hedge_words if hedge in statement_lower)
        confidence -= 0.15 * hedge_count

        return max(0.0, min(1.0, confidence))

    async def infer_intention(
        self,
        user_id: str,
        utterance: str,
        conversation_context: Optional[List[str]] = None
    ) -> Optional[UserIntention]:
        """
        Infer user intention from utterance.

        Args:
            user_id: User identifier
            utterance: User's utterance
            conversation_context: Recent conversation

        Returns:
            Inferred intention or None
        """
        model = await self.initialize_user_model(user_id)

        # Detect intention markers
        utterance_lower = utterance.lower()

        # Goal-oriented language
        if any(marker in utterance_lower for marker in ['want', 'need', 'would like', 'trying to', 'goal']):
            intention_type = 'immediate'
            confidence = 0.7

        # Question indicates information-seeking intention
        elif '?' in utterance:
            intention_type = 'immediate'
            confidence = 0.8
            utterance = f"Seek information: {utterance}"

        # Command/request indicates action intention
        elif any(marker in utterance_lower for marker in ['please', 'can you', 'could you', 'help me']):
            intention_type = 'immediate'
            confidence = 0.75

        else:
            # No clear intention markers
            return None

        intention = UserIntention(
            goal=utterance.strip(),
            intention_type=intention_type,
            confidence=confidence,
            evidence=[utterance]
        )

        # Store in model
        intention_id = f"intention_{len(model.intentions)}"
        model.intentions[intention_id] = intention

        logger.info(f"Inferred intention for {user_id}: {utterance} (confidence: {confidence:.2f})")

        return intention

    async def infer_emotional_state(
        self,
        user_id: str,
        message: str,
        tone_indicators: Optional[Dict[str, float]] = None
    ) -> EmotionalStateInference:
        """
        Infer user's emotional state from message.

        Args:
            user_id: User identifier
            message: User's message
            tone_indicators: Optional tone analysis results

        Returns:
            Inferred emotional state
        """
        model = await self.initialize_user_model(user_id)

        # Simple sentiment analysis (would use NLP in production)
        valence = self._analyze_valence(message)
        arousal = self._analyze_arousal(message)

        # Calculate confidence
        confidence = 0.5
        indicators = []

        # Check for explicit emotion words first (they override sentiment)
        # Format: word -> (valence, arousal, canonical_emotion)
        emotion_words = {
            'happy': (0.7, 0.6, 'happy'), 'sad': (-0.7, 0.3, 'sad'), 'angry': (-0.6, 0.8, 'angry'),
            'excited': (0.6, 0.9, 'excited'), 'calm': (0.3, 0.2, 'calm'), 'worried': (-0.4, 0.7, 'worried'),
            'frustrated': (-0.5, 0.7, 'frustrated'), 'frustrating': (-0.5, 0.7, 'frustrated'),
            'content': (0.5, 0.3, 'content'), 'terrible': (-0.6, 0.5, 'frustrated')
        }

        explicit_emotion = None
        message_lower = message.lower()
        for word, (v, a, canonical) in emotion_words.items():
            if word in message_lower:
                valence = (valence + v) / 2
                arousal = (arousal + a) / 2
                confidence = 0.8
                indicators.append(f"explicit: {word}")
                explicit_emotion = canonical  # Use the canonical emotion name

        # Check punctuation intensity
        if '!' in message:
            arousal = min(1.0, arousal + 0.2)
            indicators.append("exclamation marks")

        if '...' in message:
            indicators.append("ellipsis (contemplative)")

        # Determine final emotion (prefer explicit if found)
        emotion = explicit_emotion if explicit_emotion else self._map_to_emotion(valence, arousal)

        inference = EmotionalStateInference(
            emotion=emotion,
            valence=valence,
            arousal=arousal,
            confidence=confidence,
            indicators=indicators
        )

        # Store in history
        model.emotional_history.append(inference)

        return inference

    def _analyze_valence(self, text: str) -> float:
        """Analyze emotional valence (positive/negative)"""
        positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'wonderful', 'amazing', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst', 'disappointing', 'frustrating']

        text_lower = text.lower()

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count == 0 and neg_count == 0:
            return 0.0

        return (pos_count - neg_count) / (pos_count + neg_count)

    def _analyze_arousal(self, text: str) -> float:
        """Analyze emotional arousal (energy level)"""
        high_arousal = ['excited', 'angry', 'worried', 'thrilled', 'furious', 'panicked']
        low_arousal = ['calm', 'peaceful', 'tired', 'bored', 'relaxed', 'serene']

        text_lower = text.lower()

        high_count = sum(1 for word in high_arousal if word in text_lower)
        low_count = sum(1 for word in low_arousal if word in text_lower)

        # Exclamation marks indicate high arousal
        high_count += text.count('!') * 0.5

        # Default moderate arousal
        if high_count == 0 and low_count == 0:
            return 0.5

        score = (high_count) / (high_count + low_count)
        return max(0.0, min(1.0, score))

    def _map_to_emotion(self, valence: float, arousal: float) -> str:
        """Map valence-arousal to emotion label"""
        if valence > 0.3 and arousal > 0.6:
            return "excited"
        elif valence > 0.3 and arousal < 0.4:
            return "calm"
        elif valence > 0.3:
            return "happy"
        elif valence < -0.3 and arousal > 0.6:
            return "angry"
        elif valence < -0.3 and arousal < 0.4:
            return "sad"
        elif valence < -0.3:
            return "frustrated"
        elif arousal > 0.7:
            return "anxious"
        else:
            return "neutral"

    async def update_knowledge_state(
        self,
        user_id: str,
        new_knowledge: str,
        confidence: float = 0.8
    ):
        """
        Update what we believe the user knows.

        Args:
            user_id: User identifier
            new_knowledge: Knowledge to attribute to user
            confidence: Confidence in this attribution
        """
        model = await self.initialize_user_model(user_id)

        if confidence > self.confidence_threshold:
            model.knowledge_state.add(new_knowledge)
            logger.info(f"Updated knowledge state for {user_id}: {new_knowledge}")

    async def check_false_belief(
        self,
        user_id: str,
        belief_content: str
    ) -> bool:
        """
        Check if user holds a false belief (theory of mind test).

        Args:
            user_id: User identifier
            belief_content: Content of potential false belief

        Returns:
            True if we model user as having this (potentially false) belief
        """
        model = await self.initialize_user_model(user_id)

        # Check if user believes something that might not be true
        for belief in model.beliefs.values():
            if belief_content.lower() in belief.content.lower():
                return belief.confidence >= 0.5

        return False

    async def perspective_take(
        self,
        user_id: str,
        situation: str
    ) -> Dict[str, Any]:
        """
        Take the user's perspective on a situation.

        Args:
            user_id: User identifier
            situation: Description of the situation

        Returns:
            Dictionary describing user's likely perspective
        """
        model = await self.initialize_user_model(user_id)

        perspective = {
            'situation': situation,
            'likely_beliefs': [],
            'likely_emotions': [],
            'likely_intentions': [],
            'relevant_preferences': [],
        }

        # Find relevant beliefs
        for belief in model.beliefs.values():
            if any(word in situation.lower() for word in belief.content.lower().split()[:5]):
                perspective['likely_beliefs'].append({
                    'content': belief.content,
                    'type': belief.belief_type.value,
                    'confidence': belief.confidence
                })

        # Find relevant preferences
        situation_words = set(situation.lower().split())
        for topic, pref_score in model.preferences.items():
            if topic.lower() in situation.lower():
                perspective['relevant_preferences'].append({
                    'topic': topic,
                    'preference': pref_score
                })

        # Estimate likely emotional response
        if model.emotional_history:
            recent_emotion = list(model.emotional_history)[-1]
            perspective['likely_emotions'].append({
                'emotion': recent_emotion.emotion,
                'valence': recent_emotion.valence,
                'arousal': recent_emotion.arousal
            })

        return perspective

    async def generate_empathetic_response(
        self,
        user_id: str,
        user_message: str
    ) -> str:
        """
        Generate an empathetic response based on user's mental state.

        Args:
            user_id: User identifier
            user_message: User's recent message

        Returns:
            Empathetic response suggestion
        """
        # Infer emotional state
        emotional_state = await self.infer_emotional_state(user_id, user_message)

        # Generate appropriate response based on emotion
        if emotional_state.valence < -0.4:
            # User seems upset/sad
            responses = [
                "I sense you might be feeling frustrated. I'm here to help.",
                "That sounds challenging. Let me try to assist you with this.",
                "I understand this might be difficult. Let's work through it together."
            ]
        elif emotional_state.valence > 0.4 and emotional_state.arousal > 0.6:
            # User seems excited/happy
            responses = [
                "Your enthusiasm is wonderful! Let's explore this together.",
                "I can sense your excitement! This sounds interesting.",
                "Great energy! Let's dive into this."
            ]
        elif emotional_state.arousal > 0.7:
            # User seems anxious/stressed
            responses = [
                "Let's take this step by step. I'm here to help.",
                "No need to worry - we'll figure this out together.",
                "I'm here to support you through this."
            ]
        else:
            # Neutral/calm
            responses = [
                "I'm here to help with whatever you need.",
                "Let's work on this together.",
                "How can I best assist you?"
            ]

        import random
        return random.choice(responses)

    async def get_user_model_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of our model of the user"""
        model = await self.initialize_user_model(user_id)

        return {
            'user_id': user_id,
            'beliefs_count': len(model.beliefs),
            'intentions_count': len(model.intentions),
            'knowledge_items': len(model.knowledge_state),
            'preferences_count': len(model.preferences),
            'emotional_history_size': len(model.emotional_history),
            'recent_emotion': list(model.emotional_history)[-1].emotion if model.emotional_history else None,
            'last_updated': model.last_updated.isoformat()
        }
