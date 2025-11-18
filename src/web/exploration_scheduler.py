"""
Web Exploration Scheduler
==========================

Schedules and manages autonomous web exploration in different modes:
- Active mode: Focused exploration (30 min sessions)
- Idle mode: Background exploration (5 min sessions)
- Dream mode: Deep exploratory dives (1 hour sessions)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class ExplorationMode(Enum):
    """Modes of exploration"""
    ACTIVE = "active"        # Focused, goal-driven (30 min)
    IDLE = "idle"            # Light background (5 min)
    DREAM = "dream"          # Deep exploratory (60 min)
    PAUSED = "paused"        # No exploration


@dataclass
class ExplorationSession:
    """An exploration session"""
    session_id: str
    mode: ExplorationMode
    start_time: datetime
    duration_minutes: int
    topics: List[str] = field(default_factory=list)
    urls_explored: List[str] = field(default_factory=list)
    concepts_learned: int = 0
    discoveries: List[Dict] = field(default_factory=list)
    end_time: Optional[datetime] = None
    completed: bool = False


@dataclass
class ExplorationSchedule:
    """Schedule for exploration activities"""
    schedule_id: str
    active_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 14, 15, 16])  # Business hours
    idle_frequency_minutes: int = 30
    dream_frequency_hours: int = 24
    last_active_session: Optional[datetime] = None
    last_idle_session: Optional[datetime] = None
    last_dream_session: Optional[datetime] = None


class ExplorationScheduler:
    """
    Manages scheduling and execution of web exploration sessions.
    """

    def __init__(
        self,
        curiosity_engine=None,
        content_pipeline=None,
        credibility_checker=None
    ):
        self.curiosity_engine = curiosity_engine
        self.content_pipeline = content_pipeline
        self.credibility_checker = credibility_checker

        self.current_mode = ExplorationMode.PAUSED
        self.current_session: Optional[ExplorationSession] = None
        self.schedule = ExplorationSchedule(schedule_id=str(uuid.uuid4()))
        self.session_history: List[ExplorationSession] = []

        # Mode parameters
        self.mode_config = {
            ExplorationMode.ACTIVE: {
                'duration_minutes': 30,
                'max_urls': 20,
                'depth': 'focused',
                'priority_threshold': 0.7
            },
            ExplorationMode.IDLE: {
                'duration_minutes': 5,
                'max_urls': 5,
                'depth': 'shallow',
                'priority_threshold': 0.5
            },
            ExplorationMode.DREAM: {
                'duration_minutes': 60,
                'max_urls': 50,
                'depth': 'deep',
                'priority_threshold': 0.3
            }
        }

    async def start_session(
        self,
        mode: ExplorationMode,
        topics: Optional[List[str]] = None
    ) -> ExplorationSession:
        """
        Start a new exploration session.

        Args:
            mode: Exploration mode
            topics: Optional specific topics to explore

        Returns:
            Started session
        """
        if mode == ExplorationMode.PAUSED:
            logger.warning("Cannot start session in PAUSED mode")
            return None

        config = self.mode_config[mode]

        session = ExplorationSession(
            session_id=str(uuid.uuid4()),
            mode=mode,
            start_time=datetime.now(),
            duration_minutes=config['duration_minutes'],
            topics=topics or []
        )

        self.current_session = session
        self.current_mode = mode

        logger.info(
            f"Started {mode.value} exploration session "
            f"({config['duration_minutes']} min)"
        )

        # Schedule session end
        asyncio.create_task(
            self._auto_end_session(session, config['duration_minutes'])
        )

        # Start exploration
        asyncio.create_task(self._run_exploration_loop(session, config))

        return session

    async def _auto_end_session(
        self,
        session: ExplorationSession,
        duration_minutes: int
    ):
        """Automatically end session after duration"""
        await asyncio.sleep(duration_minutes * 60)

        if self.current_session and self.current_session.session_id == session.session_id:
            await self.end_session()

    async def _run_exploration_loop(
        self,
        session: ExplorationSession,
        config: Dict
    ):
        """Run the exploration loop for a session"""
        try:
            max_urls = config['max_urls']
            priority_threshold = config['priority_threshold']

            while (
                self.current_session
                and self.current_session.session_id == session.session_id
                and len(session.urls_explored) < max_urls
            ):
                # Generate exploration targets
                targets = await self._generate_exploration_targets(
                    session,
                    priority_threshold
                )

                if not targets:
                    logger.info("No exploration targets found")
                    await asyncio.sleep(30)
                    continue

                # Explore targets
                for target in targets[:5]:  # Process in batches
                    if len(session.urls_explored) >= max_urls:
                        break

                    await self._explore_target(session, target)

                await asyncio.sleep(10)  # Brief pause between batches

        except Exception as e:
            logger.error(f"Exploration loop error: {e}")

    async def _generate_exploration_targets(
        self,
        session: ExplorationSession,
        priority_threshold: float
    ) -> List[Dict]:
        """Generate exploration targets based on curiosity and interests"""
        targets = []

        # Get curiosity-driven questions
        if self.curiosity_engine:
            questions = await self.curiosity_engine.generate_questions(
                context=", ".join(session.topics) if session.topics else None,
                max_questions=10
            )

            for question in questions:
                if question.priority >= priority_threshold:
                    targets.append({
                        'type': 'curiosity',
                        'question': question.question,
                        'priority': question.priority,
                        'concepts': question.related_concepts
                    })

        # Get topic-based targets
        for topic in session.topics:
            targets.append({
                'type': 'topic',
                'question': f"What's new about {topic}?",
                'priority': 0.8,
                'concepts': [topic]
            })

        return targets

    async def _explore_target(
        self,
        session: ExplorationSession,
        target: Dict
    ):
        """Explore a single target"""
        try:
            # Simulate web search and extraction
            # In production, would use real search API
            search_query = target['question']
            logger.info(f"Exploring: {search_query}")

            # Simulated URL
            url = f"https://example.com/search?q={search_query.replace(' ', '+')}"

            # Extract content
            if self.content_pipeline:
                result = await self.content_pipeline.extract(url)

                if result.success:
                    session.urls_explored.append(url)
                    session.concepts_learned += len(result.content.key_concepts)

                    # Check credibility
                    if self.credibility_checker:
                        assessment = await self.credibility_checker.assess_credibility(url)

                        if assessment.overall_score >= 0.7:
                            # Add to discoveries
                            session.discoveries.append({
                                'url': url,
                                'title': result.content.title,
                                'concepts': result.content.key_concepts,
                                'credibility': assessment.overall_score,
                                'timestamp': datetime.now()
                            })

        except Exception as e:
            logger.error(f"Error exploring target: {e}")

    async def end_session(self) -> Optional[ExplorationSession]:
        """End the current exploration session"""
        if not self.current_session:
            return None

        session = self.current_session
        session.end_time = datetime.now()
        session.completed = True

        # Update schedule
        if session.mode == ExplorationMode.ACTIVE:
            self.schedule.last_active_session = session.start_time
        elif session.mode == ExplorationMode.IDLE:
            self.schedule.last_idle_session = session.start_time
        elif session.mode == ExplorationMode.DREAM:
            self.schedule.last_dream_session = session.start_time

        # Add to history
        self.session_history.append(session)

        logger.info(
            f"Ended {session.mode.value} session: "
            f"{len(session.urls_explored)} URLs, "
            f"{session.concepts_learned} concepts, "
            f"{len(session.discoveries)} discoveries"
        )

        self.current_session = None
        self.current_mode = ExplorationMode.PAUSED

        return session

    async def should_start_active_session(self) -> bool:
        """Check if an active session should start"""
        current_hour = datetime.now().hour

        # Check if in active hours
        if current_hour not in self.schedule.active_hours:
            return False

        # Check if recent session
        if self.schedule.last_active_session:
            time_since = datetime.now() - self.schedule.last_active_session
            if time_since < timedelta(hours=1):
                return False

        return True

    async def should_start_idle_session(self) -> bool:
        """Check if an idle session should start"""
        if not self.schedule.last_idle_session:
            return True

        time_since = datetime.now() - self.schedule.last_idle_session
        return time_since >= timedelta(minutes=self.schedule.idle_frequency_minutes)

    async def should_start_dream_session(self) -> bool:
        """Check if a dream session should start"""
        if not self.schedule.last_dream_session:
            return True

        time_since = datetime.now() - self.schedule.last_dream_session
        return time_since >= timedelta(hours=self.schedule.dream_frequency_hours)

    async def auto_schedule(self):
        """Automatically schedule and start sessions"""
        while True:
            try:
                # Check if currently in session
                if self.current_session:
                    await asyncio.sleep(60)
                    continue

                # Check for dream session (highest priority)
                if await self.should_start_dream_session():
                    await self.start_session(ExplorationMode.DREAM)
                    continue

                # Check for active session
                elif await self.should_start_active_session():
                    await self.start_session(ExplorationMode.ACTIVE)
                    continue

                # Check for idle session
                elif await self.should_start_idle_session():
                    await self.start_session(ExplorationMode.IDLE)
                    continue

                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Auto-schedule error: {e}")
                await asyncio.sleep(60)

    def get_session_statistics(self) -> Dict[str, any]:
        """Get statistics about exploration sessions"""
        total = len(self.session_history)

        by_mode = {}
        total_urls = 0
        total_concepts = 0
        total_discoveries = 0

        for session in self.session_history:
            mode = session.mode.value
            by_mode[mode] = by_mode.get(mode, 0) + 1
            total_urls += len(session.urls_explored)
            total_concepts += session.concepts_learned
            total_discoveries += len(session.discoveries)

        return {
            'total_sessions': total,
            'sessions_by_mode': by_mode,
            'total_urls_explored': total_urls,
            'total_concepts_learned': total_concepts,
            'total_discoveries': total_discoveries,
            'current_mode': self.current_mode.value,
            'session_active': self.current_session is not None
        }


async def demo():
    """Demo exploration scheduler"""
    scheduler = ExplorationScheduler()

    # Start active session
    print("Starting ACTIVE exploration session...")
    session = await scheduler.start_session(
        ExplorationMode.ACTIVE,
        topics=["machine learning", "neural networks"]
    )

    # Let it run for a bit
    await asyncio.sleep(5)

    # End session
    ended = await scheduler.end_session()

    print(f"\n=== Session Results ===")
    print(f"Mode: {ended.mode.value}")
    print(f"Duration: {ended.duration_minutes} minutes")
    print(f"URLs explored: {len(ended.urls_explored)}")
    print(f"Concepts learned: {ended.concepts_learned}")
    print(f"Discoveries: {len(ended.discoveries)}")

    # Statistics
    stats = scheduler.get_session_statistics()
    print(f"\n=== Statistics ===")
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"By mode: {stats['sessions_by_mode']}")


if __name__ == "__main__":
    asyncio.run(demo())
