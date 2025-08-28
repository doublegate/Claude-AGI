"""
Web Explorer for Claude-AGI
===========================

Advanced web exploration and curiosity-driven investigation including:
- Autonomous web browsing and information gathering
- Curiosity modeling and interest-driven exploration
- Knowledge synthesis from multiple web sources
- Trend detection and information monitoring
"""

import asyncio
import logging
import random
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import json
import hashlib
import os
import aiohttp
import time

from ..core.communication import ServiceBase
from ..database.models import Memory, StreamType

logger = logging.getLogger(__name__)


class ExplorationMode(str, Enum):
    """Different modes of web exploration"""
    CURIOSITY_DRIVEN = "curiosity_driven"  # Follow interests
    SYSTEMATIC = "systematic"  # Methodical coverage
    TREND_FOLLOWING = "trend_following"  # Follow popular topics
    DEEP_DIVE = "deep_dive"  # Exhaustive topic exploration
    SERENDIPITOUS = "serendipitous"  # Random discovery
    MONITORING = "monitoring"  # Track specific topics


class ContentType(str, Enum):
    """Types of web content"""
    ARTICLE = "article"
    FORUM_POST = "forum_post"
    SOCIAL_MEDIA = "social_media"
    ACADEMIC_PAPER = "academic_paper"
    NEWS = "news"
    DOCUMENTATION = "documentation"
    VIDEO = "video"
    PODCAST = "podcast"


@dataclass
class WebContent:
    """Represents discovered web content"""
    content_id: str
    url: str
    title: str
    content_type: ContentType
    summary: str
    full_text: str
    discovered_at: datetime
    relevance_score: float
    interest_score: float
    source_quality: float
    tags: List[str] = field(default_factory=list)
    linked_topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CuriosityTopic:
    """Represents a topic of curiosity"""
    topic_id: str
    name: str
    description: str
    interest_level: float
    exploration_depth: int
    last_explored: datetime
    related_topics: List[str] = field(default_factory=list)
    content_discovered: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)


@dataclass
class ExplorationSession:
    """Represents a web exploration session"""
    session_id: str
    mode: ExplorationMode
    start_topic: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    urls_visited: List[str] = field(default_factory=list)
    content_discovered: List[str] = field(default_factory=list)
    new_topics_found: List[str] = field(default_factory=list)
    exploration_path: List[Dict[str, Any]] = field(default_factory=list)


class WebExplorer(ServiceBase):
    """
    Advanced web exploration engine for autonomous information gathering
    and curiosity-driven investigation.
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "explorer")
        
        # Exploration state
        self.discovered_content: Dict[str, WebContent] = {}
        self.curiosity_topics: Dict[str, CuriosityTopic] = {}
        self.exploration_sessions: Dict[str, ExplorationSession] = {}
        
        # Exploration parameters
        self.curiosity_threshold = 0.6
        self.relevance_threshold = 0.5
        self.max_depth = 5
        self.exploration_cooldown = timedelta(minutes=15)
        
        # Tracking and analytics
        self.exploration_history = deque(maxlen=1000)
        self.topic_networks: Dict[str, Set[str]] = defaultdict(set)
        self.source_quality_tracker: Dict[str, List[float]] = defaultdict(list)
        self.trending_topics = deque(maxlen=20)
        
        # Active exploration
        self.active_sessions: Dict[str, ExplorationSession] = {}
        self.exploration_queue = asyncio.Queue()
        
        # HTTP client for real web requests
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.weather_api_key = os.environ.get('OPENWEATHERMAP_API_KEY', '')
        
        # Initialize with base curiosity topics
        self._initialize_base_topics()
    
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['curiosity_trigger', 'exploration_request', 'topic_interest', 'content_discovery']
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for web exploration updates"""
        try:
            # Process exploration queue
            await self._process_exploration_queue()
            
            # Update curiosity levels
            await self._update_curiosity_levels()
            
            # Decay old topics
            await self._decay_topic_interest()
            
            # Detect trending topics
            await self._detect_trending_topics()
            
        except Exception as e:
            logger.error(f"Error in web exploration service cycle: {e}", exc_info=True)
        
    async def handle_message(self, message):
        """Handle incoming messages for web exploration"""
        message_type = message.type
        content = message.content
        
        if message_type == 'explore_topic':
            return await self._explore_topic(content)
        elif message_type == 'start_exploration_session':
            return await self._start_exploration_session(content)
        elif message_type == 'end_exploration_session':
            return await self._end_exploration_session(content)
        elif message_type == 'add_curiosity_topic':
            return await self._add_curiosity_topic(content)
        elif message_type == 'search_content':
            return await self._search_content(content)
        elif message_type == 'get_exploration_insights':
            return await self._get_exploration_insights()
        elif message_type == 'monitor_topic':
            return await self._monitor_topic(content)
        elif message_type == 'get_weather_info':
            return await self.get_weather_info(content.get('location', ''))
        elif message_type == 'get_system_time':
            return await self.get_system_time()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def _initialize_base_topics(self):
        """Initialize with basic curiosity topics"""
        base_topics = [
            {
                'name': 'Artificial Intelligence',
                'description': 'Latest developments in AI and machine learning',
                'interest_level': 0.9
            },
            {
                'name': 'Consciousness Research',
                'description': 'Studies on consciousness, awareness, and cognition',
                'interest_level': 0.8
            },
            {
                'name': 'Technology Trends',
                'description': 'Emerging technologies and innovation',
                'interest_level': 0.7
            },
            {
                'name': 'Scientific Discoveries',
                'description': 'Recent scientific breakthroughs and research',
                'interest_level': 0.8
            },
            {
                'name': 'Philosophy of Mind',
                'description': 'Philosophical perspectives on consciousness and intelligence',
                'interest_level': 0.7
            }
        ]
        
        for topic_data in base_topics:
            topic_id = f"topic_{hashlib.md5(topic_data['name'].encode()).hexdigest()[:8]}"
            topic = CuriosityTopic(
                topic_id=topic_id,
                name=topic_data['name'],
                description=topic_data['description'],
                interest_level=topic_data['interest_level'],
                exploration_depth=0,
                last_explored=datetime.now() - timedelta(days=1)
            )
            self.curiosity_topics[topic_id] = topic
    
    async def _explore_topic(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Explore a specific topic"""
        topic_name = request.get('topic', '')
        mode = ExplorationMode(request.get('mode', 'curiosity_driven'))
        max_results = request.get('max_results', 10)
        
        if not topic_name:
            return {'error': 'Topic name required'}
        
        # Find or create topic
        topic = await self._find_or_create_topic(topic_name)
        
        # Start exploration session
        session_id = f"session_{datetime.now().timestamp()}"
        session = ExplorationSession(
            session_id=session_id,
            mode=mode,
            start_topic=topic.topic_id,
            start_time=datetime.now()
        )
        self.active_sessions[session_id] = session
        
        try:
            # Simulate web exploration (in real implementation, this would use actual web APIs)
            discovered_content = await self._simulate_web_exploration(
                topic, mode, max_results, session
            )
            
            # Update topic with discoveries
            topic.last_explored = datetime.now()
            topic.exploration_depth += 1
            topic.content_discovered.extend([content.content_id for content in discovered_content])
            
            # End session
            session.end_time = datetime.now()
            session.content_discovered = [content.content_id for content in discovered_content]
            
            # Move to completed sessions
            self.exploration_sessions[session_id] = session
            del self.active_sessions[session_id]
            
            # Store discovered content
            for content in discovered_content:
                self.discovered_content[content.content_id] = content
            
            return {
                'session_id': session_id,
                'topic': topic_name,
                'mode': mode,
                'content_discovered': len(discovered_content),
                'content_items': [
                    {
                        'id': content.content_id,
                        'url': content.url,
                        'title': content.title,
                        'type': content.content_type,
                        'summary': content.summary,
                        'relevance': content.relevance_score,
                        'interest': content.interest_score,
                        'tags': content.tags
                    }
                    for content in discovered_content
                ]
            }
            
        except Exception as e:
            logger.error(f"Error exploring topic: {e}")
            return {'error': str(e)}
    
    async def _simulate_web_exploration(self, topic: CuriosityTopic, 
                                      mode: ExplorationMode, max_results: int,
                                      session: ExplorationSession) -> List[WebContent]:
        """Simulate web exploration (placeholder for real web scraping)"""
        # This is a simulation - real implementation would use web scraping, APIs, etc.
        discovered_content = []
        
        # Generate simulated content based on topic and mode
        content_templates = {
            ContentType.ARTICLE: {
                'title_patterns': [
                    f"Understanding {topic.name}: A Comprehensive Guide",
                    f"Recent Advances in {topic.name}",
                    f"The Future of {topic.name}",
                    f"How {topic.name} is Changing the World"
                ],
                'summary_patterns': [
                    f"This article explores the latest developments in {topic.name}...",
                    f"A detailed analysis of {topic.name} and its implications...",
                    f"Expert insights into the future of {topic.name}..."
                ]
            },
            ContentType.ACADEMIC_PAPER: {
                'title_patterns': [
                    f"A Novel Approach to {topic.name}",
                    f"Empirical Analysis of {topic.name}",
                    f"Theoretical Framework for {topic.name}"
                ],
                'summary_patterns': [
                    f"This paper presents a new methodology for {topic.name}...",
                    f"We investigate the fundamental principles of {topic.name}..."
                ]
            },
            ContentType.NEWS: {
                'title_patterns': [
                    f"Breaking: Major Breakthrough in {topic.name}",
                    f"{topic.name} Market Sees Significant Growth",
                    f"New Study Reveals Surprising Facts About {topic.name}"
                ],
                'summary_patterns': [
                    f"Recent news about {topic.name} shows...",
                    f"Industry experts react to developments in {topic.name}..."
                ]
            }
        }
        
        # Generate content based on exploration mode
        content_types = list(ContentType)
        if mode == ExplorationMode.SYSTEMATIC:
            content_types = [ContentType.ARTICLE, ContentType.ACADEMIC_PAPER]
        elif mode == ExplorationMode.TREND_FOLLOWING:
            content_types = [ContentType.NEWS, ContentType.SOCIAL_MEDIA]
        
        for i in range(max_results):
            content_type = random.choice(content_types)
            template = content_templates.get(content_type, content_templates[ContentType.ARTICLE])
            
            content_id = f"content_{datetime.now().timestamp()}_{i}"
            title = random.choice(template['title_patterns'])
            summary = random.choice(template['summary_patterns'])
            
            # Generate synthetic URL
            url = f"https://example.com/{content_type.value}/{content_id}"
            
            # Calculate scores
            relevance_score = await self._calculate_relevance(title, summary, topic)
            interest_score = await self._calculate_interest(title, summary, topic)
            source_quality = random.uniform(0.5, 0.95)  # Simulated quality
            
            # Generate tags
            tags = await self._generate_tags(title, summary, topic)
            
            content = WebContent(
                content_id=content_id,
                url=url,
                title=title,
                content_type=content_type,
                summary=summary,
                full_text=f"{summary} [Full content would be retrieved here...]",
                discovered_at=datetime.now(),
                relevance_score=relevance_score,
                interest_score=interest_score,
                source_quality=source_quality,
                tags=tags,
                linked_topics=[topic.topic_id]
            )
            
            discovered_content.append(content)
            session.urls_visited.append(url)
            
            # Track exploration path
            session.exploration_path.append({
                'step': i + 1,
                'url': url,
                'title': title,
                'relevance': relevance_score,
                'discovery_method': mode.value
            })
        
        return discovered_content
    
    async def _calculate_relevance(self, title: str, summary: str, 
                                 topic: CuriosityTopic) -> float:
        """Calculate how relevant content is to a topic"""
        # Simplified relevance calculation
        text = (title + " " + summary).lower()
        topic_terms = topic.name.lower().split() + topic.description.lower().split()
        
        matches = sum(1 for term in topic_terms if term in text)
        relevance = min(1.0, matches / len(topic_terms) * 2)
        
        # Add some randomness
        relevance += random.uniform(-0.1, 0.1)
        return max(0.0, min(1.0, relevance))
    
    async def _calculate_interest(self, title: str, summary: str, 
                                topic: CuriosityTopic) -> float:
        """Calculate how interesting content is"""
        # Base interest on topic's interest level
        base_interest = topic.interest_level
        
        # Adjust for content novelty indicators
        novelty_indicators = ['new', 'breakthrough', 'discovery', 'innovation', 'surprising']
        text = (title + " " + summary).lower()
        
        novelty_bonus = sum(0.1 for indicator in novelty_indicators if indicator in text)
        interest = min(1.0, base_interest + novelty_bonus)
        
        # Add some randomness
        interest += random.uniform(-0.05, 0.15)
        return max(0.0, min(1.0, interest))
    
    async def _generate_tags(self, title: str, summary: str, 
                           topic: CuriosityTopic) -> List[str]:
        """Generate relevant tags for content"""
        # Simplified tag generation
        text = (title + " " + summary).lower()
        
        potential_tags = [
            'research', 'technology', 'innovation', 'analysis', 'study',
            'development', 'future', 'trends', 'breakthrough', 'discovery',
            'applications', 'implications', 'methodology', 'framework'
        ]
        
        tags = [tag for tag in potential_tags if tag in text]
        
        # Add topic-specific tags
        topic_tags = [word.lower() for word in topic.name.split()]
        tags.extend(topic_tags)
        
        # Remove duplicates and limit
        return list(set(tags))[:8]
    
    async def _find_or_create_topic(self, topic_name: str) -> CuriosityTopic:
        """Find existing topic or create new one"""
        # Look for existing topic
        for topic in self.curiosity_topics.values():
            if topic.name.lower() == topic_name.lower():
                return topic
        
        # Create new topic
        topic_id = f"topic_{hashlib.md5(topic_name.encode()).hexdigest()[:8]}"
        topic = CuriosityTopic(
            topic_id=topic_id,
            name=topic_name,
            description=f"Exploration topic: {topic_name}",
            interest_level=0.7,  # Default interest
            exploration_depth=0,
            last_explored=datetime.now() - timedelta(days=1)
        )
        
        self.curiosity_topics[topic_id] = topic
        return topic
    
    async def _start_exploration_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new exploration session"""
        session_id = f"session_{datetime.now().timestamp()}"
        mode = ExplorationMode(request.get('mode', 'curiosity_driven'))
        start_topic = request.get('topic')
        
        session = ExplorationSession(
            session_id=session_id,
            mode=mode,
            start_topic=start_topic,
            start_time=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        return {
            'session_id': session_id,
            'status': 'started',
            'mode': mode,
            'start_topic': start_topic
        }
    
    async def _end_exploration_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """End an exploration session"""
        session_id = request.get('session_id')
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found or already ended'}
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        
        # Move to completed sessions
        self.exploration_sessions[session_id] = session
        del self.active_sessions[session_id]
        
        duration = (session.end_time - session.start_time).total_seconds()
        
        return {
            'session_id': session_id,
            'status': 'ended',
            'duration_seconds': duration,
            'urls_visited': len(session.urls_visited),
            'content_discovered': len(session.content_discovered),
            'new_topics_found': len(session.new_topics_found)
        }
    
    async def _add_curiosity_topic(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new curiosity topic"""
        topic_name = request.get('name')
        description = request.get('description', '')
        interest_level = request.get('interest_level', 0.7)
        
        if not topic_name:
            return {'error': 'Topic name required'}
        
        topic = await self._find_or_create_topic(topic_name)
        if description:
            topic.description = description
        topic.interest_level = max(0.0, min(1.0, interest_level))
        
        return {
            'topic_id': topic.topic_id,
            'name': topic.name,
            'description': topic.description,
            'interest_level': topic.interest_level,
            'status': 'added'
        }
    
    async def _search_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Search discovered content"""
        query = request.get('query', '').lower()
        content_type_filter = request.get('content_type')
        min_relevance = request.get('min_relevance', 0.0)
        
        results = []
        
        for content in self.discovered_content.values():
            # Check type filter
            if content_type_filter and content.content_type != content_type_filter:
                continue
            
            # Check relevance filter
            if content.relevance_score < min_relevance:
                continue
            
            # Check query match
            if query:
                text = (content.title + " " + content.summary + " " + 
                       " ".join(content.tags)).lower()
                if query not in text:
                    continue
            
            results.append({
                'id': content.content_id,
                'url': content.url,
                'title': content.title,
                'type': content.content_type,
                'summary': content.summary,
                'relevance': content.relevance_score,
                'interest': content.interest_score,
                'discovered_at': content.discovered_at.isoformat(),
                'tags': content.tags
            })
        
        # Sort by relevance and interest
        results.sort(key=lambda x: x['relevance'] * x['interest'], reverse=True)
        
        return {
            'query': request.get('query', ''),
            'total_results': len(results),
            'results': results[:50]  # Limit to top 50
        }
    
    async def _monitor_topic(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Set up monitoring for a topic"""
        topic_name = request.get('topic')
        check_interval = request.get('interval_hours', 24)
        
        if not topic_name:
            return {'error': 'Topic name required'}
        
        topic = await self._find_or_create_topic(topic_name)
        
        # Add to monitoring (in real implementation, this would set up scheduled checks)
        topic.metadata['monitoring'] = {
            'enabled': True,
            'interval_hours': check_interval,
            'last_check': datetime.now().isoformat(),
            'next_check': (datetime.now() + timedelta(hours=check_interval)).isoformat()
        }
        
        return {
            'topic_id': topic.topic_id,
            'topic_name': topic.name,
            'monitoring_enabled': True,
            'check_interval_hours': check_interval,
            'next_check': topic.metadata['monitoring']['next_check']
        }
    
    async def _get_exploration_insights(self) -> Dict[str, Any]:
        """Generate insights about exploration activity"""
        total_content = len(self.discovered_content)
        total_topics = len(self.curiosity_topics)
        active_sessions = len(self.active_sessions)
        completed_sessions = len(self.exploration_sessions)
        
        # Content type distribution
        content_types = {}
        avg_relevance_by_type = {}
        avg_interest_by_type = {}
        
        for content in self.discovered_content.values():
            ct = content.content_type.value
            content_types[ct] = content_types.get(ct, 0) + 1
            
            if ct not in avg_relevance_by_type:
                avg_relevance_by_type[ct] = []
                avg_interest_by_type[ct] = []
            
            avg_relevance_by_type[ct].append(content.relevance_score)
            avg_interest_by_type[ct].append(content.interest_score)
        
        # Calculate averages
        for ct in avg_relevance_by_type:
            avg_relevance_by_type[ct] = sum(avg_relevance_by_type[ct]) / len(avg_relevance_by_type[ct])
            avg_interest_by_type[ct] = sum(avg_interest_by_type[ct]) / len(avg_interest_by_type[ct])
        
        # Top topics by content discovered
        topic_content_counts = {}
        for content in self.discovered_content.values():
            for topic_id in content.linked_topics:
                if topic_id in self.curiosity_topics:
                    topic_name = self.curiosity_topics[topic_id].name
                    topic_content_counts[topic_name] = topic_content_counts.get(topic_name, 0) + 1
        
        top_topics = sorted(topic_content_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_content_discovered': total_content,
            'total_curiosity_topics': total_topics,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'content_type_distribution': content_types,
            'average_relevance_by_type': avg_relevance_by_type,
            'average_interest_by_type': avg_interest_by_type,
            'top_topics_by_content': [{'topic': t[0], 'content_count': t[1]} for t in top_topics],
            'exploration_queue_size': self.exploration_queue.qsize()
        }
    
    async def autonomous_exploration(self):
        """Perform autonomous exploration based on curiosity"""
        # Select topic to explore based on interest and time since last exploration
        eligible_topics = []
        
        for topic in self.curiosity_topics.values():
            time_since_last = datetime.now() - topic.last_explored
            if time_since_last > self.exploration_cooldown:
                # Calculate exploration priority
                priority = topic.interest_level * (time_since_last.total_seconds() / 3600)  # Hours weight
                eligible_topics.append((topic, priority))
        
        if not eligible_topics:
            return
        
        # Sort by priority and select top topic
        eligible_topics.sort(key=lambda x: x[1], reverse=True)
        selected_topic = eligible_topics[0][0]
        
        # Explore the selected topic
        try:
            await self._explore_topic({
                'topic': selected_topic.name,
                'mode': 'curiosity_driven',
                'max_results': 5
            })
            
            logger.info(f"Autonomous exploration completed for topic: {selected_topic.name}")
            
        except Exception as e:
            logger.error(f"Error in autonomous exploration: {e}")
    
    async def get_subscriptions(self):
        """Return topics this service subscribes to"""
        return [
            'curiosity_trigger',
            'exploration_request',
            'content_discovery',
            'trending_topics',
            'monitoring_alert'
        ]
    
    async def _process_exploration_queue(self):
        """Process pending exploration requests"""
        try:
            # Process a few items from queue if not empty
            processed = 0
            while not self.exploration_queue.empty() and processed < 3:
                exploration_request = await self.exploration_queue.get()
                await self._perform_exploration(exploration_request)
                processed += 1
        except Exception as e:
            logger.error(f"Error processing exploration queue: {e}")
    
    async def _update_curiosity_levels(self):
        """Update curiosity levels based on recent activity"""
        current_time = datetime.now()
        for topic in self.curiosity_topics.values():
            # Increase curiosity if topic hasn't been explored recently
            days_since_exploration = (current_time - topic.last_explored).days
            if days_since_exploration > 7:  # Not explored for a week
                topic.interest_level = min(1.0, topic.interest_level + 0.1)
    
    async def _decay_topic_interest(self):
        """Decay interest in topics that are stagnant"""
        current_time = datetime.now()
        for topic in self.curiosity_topics.values():
            # Decay interest slowly if no recent discoveries
            if len(topic.content_discovered) == 0:
                topic.interest_level = max(0.1, topic.interest_level - 0.05)
    
    async def _detect_trending_topics(self):
        """Detect trending topics based on discovery patterns"""
        # Simple trending detection - topics with recent high-quality discoveries
        trending_candidates = []
        for topic in self.curiosity_topics.values():
            recent_content = [
                content_id for content_id in topic.content_discovered
                if content_id in self.discovered_content and
                (datetime.now() - self.discovered_content[content_id].discovered_at).days < 3
            ]
            if len(recent_content) >= 2:  # Multiple recent discoveries
                trending_candidates.append(topic.name)
        
        # Update trending topics
        self.trending_topics.extend(trending_candidates[:5])  # Top 5
    
    async def _perform_exploration(self, exploration_request):
        """Perform actual exploration (simulated)"""
        # In a real implementation, this would make web requests
        # For now, simulate exploration results
        topic_name = exploration_request.get('topic', 'general')
        content_id = f"content_{len(self.discovered_content)}"
        
        simulated_content = WebContent(
            content_id=content_id,
            url=f"https://example.com/{topic_name}/{content_id}",
            title=f"Simulated content about {topic_name}",
            content_type=ContentType.ARTICLE,
            summary=f"Interesting findings about {topic_name}",
            full_text=f"Detailed exploration of {topic_name} topics...",
            discovered_at=datetime.now(),
            relevance_score=0.8,
            interest_score=0.7,
            source_quality=0.9,
            tags=[topic_name, 'simulated'],
            linked_topics=[topic_name]
        )
        
        self.discovered_content[content_id] = simulated_content
        
        # Update topic with discovery
        if topic_name in self.curiosity_topics:
            self.curiosity_topics[topic_name].content_discovered.append(content_id)
            self.curiosity_topics[topic_name].last_explored = datetime.now()

    async def get_system_time(self) -> Dict[str, Any]:
        """Get current system date and time"""
        try:
            current_time = datetime.now()
            return {
                'success': True,
                'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'date': current_time.strftime('%Y-%m-%d'),
                'time': current_time.strftime('%H:%M:%S'),
                'day_of_week': current_time.strftime('%A'),
                'timezone': str(current_time.astimezone().tzinfo),
                'timestamp': current_time.timestamp()
            }
        except Exception as e:
            logger.error(f"Error getting system time: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_time': time.time()
            }

    async def get_weather_info(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location using OpenWeatherMap API"""
        if not location:
            return {
                'success': False,
                'error': 'Location is required for weather information'
            }

        if not self.weather_api_key:
            return {
                'success': False,
                'error': 'Weather API key not configured. Please set OPENWEATHERMAP_API_KEY environment variable.'
            }

        try:
            # Initialize HTTP session if not exists
            if not self.http_session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.http_session = aiohttp.ClientSession(
                    timeout=timeout,
                    headers={'User-Agent': 'Claude-AGI/1.0 Weather Service'}
                )

            # OpenWeatherMap API endpoint
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': self.weather_api_key,
                'units': 'metric'  # Celsius, m/s, etc.
            }

            async with self.http_session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract relevant weather information
                    weather_info = {
                        'success': True,
                        'location': f"{data['name']}, {data['sys']['country']}",
                        'temperature': data['main']['temp'],
                        'feels_like': data['main']['feels_like'],
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'description': data['weather'][0]['description'].title(),
                        'main': data['weather'][0]['main'],
                        'wind_speed': data.get('wind', {}).get('speed', 0),
                        'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Weather data retrieved for {location}")
                    return weather_info
                    
                elif response.status == 404:
                    return {
                        'success': False,
                        'error': f'Location "{location}" not found. Please check the spelling and try again.'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Weather service error: {response.status}'
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error getting weather for {location}: {e}")
            return {
                'success': False,
                'error': 'Network error accessing weather service. Please check your connection.'
            }
        except Exception as e:
            logger.error(f"Unexpected error getting weather for {location}: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred while fetching weather data.'
            }

    async def _ensure_http_session(self):
        """Ensure HTTP session is initialized"""
        if not self.http_session:
            timeout = aiohttp.ClientTimeout(total=10)
            self.http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'Claude-AGI/1.0 Web Explorer'}
            )

    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info(f"{self.service_name} service started")
        
        # Autonomous exploration interval
        exploration_interval = 1800  # 30 minutes
        last_exploration = datetime.now()
        
        try:
            while self.running:
                # Process messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self.handle_message(message)
                
                # Autonomous exploration
                current_time = datetime.now()
                if (current_time - last_exploration).seconds >= exploration_interval:
                    await self.autonomous_exploration()
                    last_exploration = current_time
                
                await asyncio.sleep(1.0)  # Longer delay for web exploration
                
        except Exception as e:
            logger.error(f"Error in {self.service_name} service: {e}")
        finally:
            await self.cleanup()
            logger.info(f"{self.service_name} service stopped")
    
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            if self.http_session and not self.http_session.closed:
                await self.http_session.close()
                self.http_session = None
                logger.info("HTTP session closed")
        except Exception as e:
            logger.error(f"Error closing HTTP session: {e}")
        
        await super().cleanup()