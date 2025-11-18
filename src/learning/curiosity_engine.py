"""
Curiosity Engine for Autonomous Learning
==========================================

Implements multiple curiosity types (epistemic, perceptual, specific, diversive)
to drive autonomous exploration and learning.
"""

import asyncio
import logging
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CuriosityType(Enum):
    """Types of curiosity that drive exploration"""
    EPISTEMIC = "epistemic"          # Understanding how things work
    PERCEPTUAL = "perceptual"        # Discovering what's new
    SPECIFIC = "specific"            # Answering targeted questions
    DIVERSIVE = "diversive"          # Broad exploratory scanning


@dataclass
class CuriosityQuestion:
    """Represents a question driven by curiosity"""
    question: str
    curiosity_type: CuriosityType
    priority: float
    context: str
    related_concepts: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    answered: bool = False
    answer: Optional[str] = None


@dataclass
class KnowledgeGap:
    """Represents an identified gap in knowledge"""
    topic: str
    gap_type: str  # 'missing_concept', 'weak_understanding', 'contradiction'
    evidence: str
    importance: float
    related_concepts: List[str] = field(default_factory=list)


@dataclass
class InterestTopic:
    """Represents a topic of interest"""
    name: str
    weight: float
    last_explored: datetime
    total_explorations: int = 0
    satisfaction_score: float = 0.5
    decay_rate: float = 0.05


class CuriosityEngine:
    """
    Drives autonomous curiosity-based exploration and learning.
    Generates questions, identifies knowledge gaps, and prioritizes exploration.
    """

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph

        # Question tracking
        self.pending_questions: List[CuriosityQuestion] = []
        self.answered_questions: deque = deque(maxlen=1000)

        # Knowledge gap tracking
        self.known_gaps: Dict[str, KnowledgeGap] = {}

        # Interest tracking
        self.interests: Dict[str, InterestTopic] = {}

        # Exploration history
        self.exploration_history: deque = deque(maxlen=500)

        # Curiosity parameters
        self.epistemic_weight = 0.4
        self.perceptual_weight = 0.3
        self.specific_weight = 0.2
        self.diversive_weight = 0.1

        # Serendipity factor (random exploration)
        self.serendipity_factor = 0.15

    async def generate_questions(
        self,
        context: Optional[str] = None,
        max_questions: int = 10
    ) -> List[CuriosityQuestion]:
        """
        Generate curiosity-driven questions.

        Args:
            context: Optional context to focus question generation
            max_questions: Maximum number of questions to generate

        Returns:
            List of curiosity questions
        """
        questions = []

        # Epistemic questions (understanding)
        epistemic = await self._generate_epistemic_questions(context, max_questions // 4)
        questions.extend(epistemic)

        # Perceptual questions (novelty)
        perceptual = await self._generate_perceptual_questions(context, max_questions // 4)
        questions.extend(perceptual)

        # Specific questions (targeted)
        specific = await self._generate_specific_questions(context, max_questions // 4)
        questions.extend(specific)

        # Diversive questions (broad)
        diversive = await self._generate_diversive_questions(context, max_questions // 4)
        questions.extend(diversive)

        # Sort by priority
        questions.sort(key=lambda q: q.priority, reverse=True)

        # Store pending questions
        self.pending_questions.extend(questions[:max_questions])

        return questions[:max_questions]

    async def _generate_epistemic_questions(
        self,
        context: Optional[str],
        count: int
    ) -> List[CuriosityQuestion]:
        """Generate 'how/why' questions about mechanisms and explanations"""
        questions = []

        # Questions about known concepts
        if self.knowledge_graph:
            # Get concepts with few connections (weak understanding)
            weak_concepts = []
            for concept_id, concept in self.knowledge_graph.concepts.items():
                connection_count = (
                    len(self.knowledge_graph.outgoing_edges.get(concept_id, []))
                    + len(self.knowledge_graph.incoming_edges.get(concept_id, []))
                )

                if connection_count < 3:  # Weakly connected
                    weak_concepts.append(concept)

            # Generate questions about weak concepts
            for concept in weak_concepts[:count]:
                question_templates = [
                    f"How does {concept.name} work?",
                    f"Why is {concept.name} important?",
                    f"What are the mechanisms behind {concept.name}?",
                    f"How does {concept.name} relate to other concepts?",
                ]

                question_text = random.choice(question_templates)

                questions.append(CuriosityQuestion(
                    question=question_text,
                    curiosity_type=CuriosityType.EPISTEMIC,
                    priority=0.7 + (random.random() * 0.3),
                    context=context or "",
                    related_concepts=[concept.name]
                ))

        # Questions about knowledge gaps
        for gap in list(self.known_gaps.values())[:count]:
            questions.append(CuriosityQuestion(
                question=f"How does {gap.topic} work?",
                curiosity_type=CuriosityType.EPISTEMIC,
                priority=gap.importance,
                context=gap.evidence,
                related_concepts=gap.related_concepts
            ))

        return questions[:count]

    async def _generate_perceptual_questions(
        self,
        context: Optional[str],
        count: int
    ) -> List[CuriosityQuestion]:
        """Generate 'what's new' questions about novel information"""
        questions = []

        # Questions about recently discovered concepts
        if self.knowledge_graph:
            recent_concepts = sorted(
                self.knowledge_graph.concepts.values(),
                key=lambda c: c.created_at,
                reverse=True
            )[:count]

            for concept in recent_concepts:
                question_templates = [
                    f"What's new about {concept.name}?",
                    f"What are the latest developments in {concept.name}?",
                    f"What's interesting about {concept.name}?",
                    f"What should I know about {concept.name}?",
                ]

                question_text = random.choice(question_templates)

                questions.append(CuriosityQuestion(
                    question=question_text,
                    curiosity_type=CuriosityType.PERCEPTUAL,
                    priority=0.6 + (random.random() * 0.3),
                    context=context or "",
                    related_concepts=[concept.name]
                ))

        # Questions about trending interests
        trending_interests = sorted(
            self.interests.values(),
            key=lambda i: i.total_explorations,
            reverse=True
        )[:count]

        for interest in trending_interests:
            questions.append(CuriosityQuestion(
                question=f"What's new in {interest.name}?",
                curiosity_type=CuriosityType.PERCEPTUAL,
                priority=interest.weight * 0.8,
                context=context or "",
                related_concepts=[interest.name]
            ))

        return questions[:count]

    async def _generate_specific_questions(
        self,
        context: Optional[str],
        count: int
    ) -> List[CuriosityQuestion]:
        """Generate targeted questions to fill knowledge gaps"""
        questions = []

        # Questions for high-priority gaps
        high_priority_gaps = sorted(
            self.known_gaps.values(),
            key=lambda g: g.importance,
            reverse=True
        )[:count]

        for gap in high_priority_gaps:
            if gap.gap_type == 'missing_concept':
                question = f"What is {gap.topic}?"
            elif gap.gap_type == 'weak_understanding':
                question = f"Can you explain {gap.topic} in detail?"
            elif gap.gap_type == 'contradiction':
                question = f"What's the truth about {gap.topic}?"
            else:
                question = f"Tell me more about {gap.topic}"

            questions.append(CuriosityQuestion(
                question=question,
                curiosity_type=CuriosityType.SPECIFIC,
                priority=gap.importance,
                context=gap.evidence,
                related_concepts=gap.related_concepts
            ))

        return questions[:count]

    async def _generate_diversive_questions(
        self,
        context: Optional[str],
        count: int
    ) -> List[CuriosityQuestion]:
        """Generate broad exploratory questions"""
        questions = []

        # Random topic exploration
        broad_topics = [
            "science", "technology", "philosophy", "history",
            "art", "culture", "nature", "space", "psychology",
            "mathematics", "literature", "music", "society"
        ]

        for _ in range(count):
            topic = random.choice(broad_topics)

            question_templates = [
                f"What's interesting in {topic} today?",
                f"What are the biggest questions in {topic}?",
                f"What should I explore in {topic}?",
                f"What's surprising about {topic}?",
            ]

            question_text = random.choice(question_templates)

            questions.append(CuriosityQuestion(
                question=question_text,
                curiosity_type=CuriosityType.DIVERSIVE,
                priority=0.3 + (random.random() * 0.3),
                context=context or "",
                related_concepts=[topic]
            ))

        return questions

    async def identify_knowledge_gap(
        self,
        topic: str,
        gap_type: str,
        evidence: str,
        importance: float = 0.5,
        related_concepts: Optional[List[str]] = None
    ):
        """
        Identify and register a knowledge gap.

        Args:
            topic: The topic with a knowledge gap
            gap_type: Type of gap ('missing_concept', 'weak_understanding', 'contradiction')
            evidence: Evidence for the gap
            importance: Importance score (0-1)
            related_concepts: Related concept names
        """
        gap = KnowledgeGap(
            topic=topic,
            gap_type=gap_type,
            evidence=evidence,
            importance=importance,
            related_concepts=related_concepts or []
        )

        self.known_gaps[topic] = gap
        logger.info(f"Identified knowledge gap: {topic} ({gap_type})")

    async def update_interest(
        self,
        topic: str,
        weight_change: float = 0.0,
        exploration_occurred: bool = False,
        satisfaction: Optional[float] = None
    ):
        """
        Update interest in a topic based on exploration outcomes.

        Args:
            topic: Topic name
            weight_change: Change in interest weight (-1 to +1)
            exploration_occurred: Whether exploration just occurred
            satisfaction: Satisfaction score from exploration (0-1)
        """
        if topic not in self.interests:
            self.interests[topic] = InterestTopic(
                name=topic,
                weight=0.5,
                last_explored=datetime.now(),
                total_explorations=0
            )

        interest = self.interests[topic]

        # Update weight
        if weight_change != 0:
            interest.weight = max(0.0, min(1.0, interest.weight + weight_change))

        # Update exploration tracking
        if exploration_occurred:
            interest.last_explored = datetime.now()
            interest.total_explorations += 1

        # Update satisfaction
        if satisfaction is not None:
            # Exponential moving average
            alpha = 0.3
            interest.satisfaction_score = (
                alpha * satisfaction + (1 - alpha) * interest.satisfaction_score
            )

            # Adjust weight based on satisfaction
            if satisfaction > 0.7:
                interest.weight = min(1.0, interest.weight + 0.1)
            elif satisfaction < 0.3:
                interest.weight = max(0.0, interest.weight - 0.1)

    async def apply_interest_decay(self):
        """Apply time-based decay to interests"""
        now = datetime.now()

        for interest in self.interests.values():
            # Calculate time since last exploration
            time_delta = (now - interest.last_explored).total_seconds() / 86400  # days

            # Apply decay
            decay = interest.decay_rate * time_delta
            interest.weight = max(0.0, interest.weight - decay)

    async def get_next_exploration_target(self) -> Optional[str]:
        """
        Get the next topic to explore based on curiosity and interests.

        Returns:
            Topic name to explore, or None if no targets
        """
        # Apply serendipity - sometimes explore randomly
        if random.random() < self.serendipity_factor:
            if self.interests:
                return random.choice(list(self.interests.keys()))

        # Otherwise, choose based on weighted interests and gaps
        candidates = []

        # Add interests as candidates
        for interest in self.interests.values():
            if interest.weight > 0.1:  # Minimum threshold
                # Boost score if not explored recently
                recency_boost = 1.0
                time_since = (datetime.now() - interest.last_explored).total_seconds() / 3600
                if time_since > 24:
                    recency_boost = 1.5

                score = interest.weight * recency_boost
                candidates.append((interest.name, score))

        # Add knowledge gaps as candidates
        for gap in self.known_gaps.values():
            score = gap.importance * 1.2  # Boost gaps slightly
            candidates.append((gap.topic, score))

        if not candidates:
            return None

        # Sort by score and return top candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    async def mark_question_answered(
        self,
        question: CuriosityQuestion,
        answer: str,
        satisfaction: float
    ):
        """
        Mark a question as answered and update curiosity state.

        Args:
            question: The answered question
            answer: The answer text
            satisfaction: How satisfying the answer was (0-1)
        """
        question.answered = True
        question.answer = answer

        # Move to answered questions
        self.answered_questions.append(question)

        # Update interests based on satisfaction
        for concept in question.related_concepts:
            await self.update_interest(
                concept,
                exploration_occurred=True,
                satisfaction=satisfaction
            )

        # If answer is unsatisfying, create follow-up gap
        if satisfaction < 0.5 and question.related_concepts:
            await self.identify_knowledge_gap(
                topic=question.related_concepts[0],
                gap_type='weak_understanding',
                evidence=f"Question '{question.question}' not satisfactorily answered",
                importance=0.6
            )

    async def get_curiosity_statistics(self) -> Dict[str, Any]:
        """Get statistics about curiosity-driven exploration"""
        total_questions = len(self.pending_questions) + len(self.answered_questions)

        if total_questions > 0:
            answer_rate = len(self.answered_questions) / total_questions
        else:
            answer_rate = 0.0

        return {
            'pending_questions': len(self.pending_questions),
            'answered_questions': len(self.answered_questions),
            'total_questions': total_questions,
            'answer_rate': answer_rate,
            'knowledge_gaps': len(self.known_gaps),
            'active_interests': len([i for i in self.interests.values() if i.weight > 0.1]),
            'total_interests': len(self.interests),
            'exploration_history_size': len(self.exploration_history),
            'curiosity_types_distribution': {
                'epistemic': self.epistemic_weight,
                'perceptual': self.perceptual_weight,
                'specific': self.specific_weight,
                'diversive': self.diversive_weight
            }
        }


class ExplorationScheduler:
    """
    Schedules and manages exploration sessions based on system state and priorities.
    """

    def __init__(self, curiosity_engine: CuriosityEngine):
        self.curiosity_engine = curiosity_engine
        self.active_session: Optional[Dict[str, Any]] = None
        self.session_history: deque = deque(maxlen=100)

    async def start_exploration_session(
        self,
        mode: str,
        duration_minutes: int,
        focus_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start an exploration session.

        Args:
            mode: 'active', 'idle', or 'dream'
            duration_minutes: How long the session should run
            focus_topics: Optional topics to focus on

        Returns:
            Session metadata
        """
        session = {
            'id': f"session_{datetime.now().timestamp()}",
            'mode': mode,
            'start_time': datetime.now(),
            'duration_minutes': duration_minutes,
            'focus_topics': focus_topics or [],
            'discoveries': [],
            'questions_explored': 0,
            'satisfaction_scores': []
        }

        self.active_session = session
        logger.info(f"Started {mode} exploration session for {duration_minutes} minutes")

        return session

    async def end_exploration_session(self) -> Optional[Dict[str, Any]]:
        """End the current exploration session and generate summary"""
        if not self.active_session:
            return None

        session = self.active_session
        session['end_time'] = datetime.now()

        # Calculate statistics
        if session['satisfaction_scores']:
            session['average_satisfaction'] = sum(session['satisfaction_scores']) / len(session['satisfaction_scores'])
        else:
            session['average_satisfaction'] = 0.0

        session['duration_actual'] = (session['end_time'] - session['start_time']).total_seconds() / 60

        # Store in history
        self.session_history.append(session)

        self.active_session = None
        logger.info(f"Ended exploration session {session['id']}")

        return session

    async def record_discovery(self, discovery: str, satisfaction: float):
        """Record a discovery during the active session"""
        if self.active_session:
            self.active_session['discoveries'].append(discovery)
            self.active_session['satisfaction_scores'].append(satisfaction)
            self.active_session['questions_explored'] += 1

    def is_session_active(self) -> bool:
        """Check if an exploration session is currently active"""
        return self.active_session is not None

    def should_explore_now(self, system_state: str, user_present: bool) -> Tuple[bool, str]:
        """
        Determine if exploration should happen now.

        Args:
            system_state: Current system state ('IDLE', 'THINKING', etc.)
            user_present: Whether user is actively engaged

        Returns:
            (should_explore, recommended_mode)
        """
        if user_present:
            # Background exploration only when user is present
            if system_state == 'IDLE':
                return True, 'idle'  # Short explorations
        else:
            # More extensive exploration when user is away
            if system_state == 'IDLE':
                return True, 'active'  # Longer explorations
            elif system_state == 'SLEEPING':
                return True, 'dream'  # Deep exploratory sessions

        return False, ''
