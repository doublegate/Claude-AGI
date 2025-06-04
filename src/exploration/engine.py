# exploration/engine.py

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import random
import json
from urllib.parse import urlparse, quote_plus

from ..core.communication import ServiceBase
from ..core.orchestrator import SystemState
from ..safety.core_safety import SafetyFramework, Action

logger = logging.getLogger(__name__)

class InterestTracker:
    """Tracks and manages exploration interests"""
    
    def __init__(self):
        self.interests = {
            'consciousness': {'weight': 0.9, 'last_explored': None},
            'artificial_intelligence': {'weight': 0.8, 'last_explored': None},
            'philosophy_of_mind': {'weight': 0.7, 'last_explored': None},
            'creativity': {'weight': 0.6, 'last_explored': None},
            'emergence': {'weight': 0.5, 'last_explored': None}
        }
        self.user_interests = {}
        self.discovered_topics = []
        
    async def get_next_topic(self) -> Optional[str]:
        """Get the next topic to explore based on weights and recency"""
        # Filter topics that haven't been explored recently
        available_topics = []
        current_time = datetime.now()
        
        for topic, info in self.interests.items():
            if info['last_explored'] is None:
                available_topics.append((topic, info['weight']))
            else:
                # Only re-explore after some time has passed
                time_diff = (current_time - info['last_explored']).total_seconds()
                if time_diff > 3600:  # 1 hour
                    available_topics.append((topic, info['weight']))
                    
        if not available_topics:
            return None
            
        # Weighted random selection
        topics, weights = zip(*available_topics)
        selected = random.choices(topics, weights=weights)[0]
        
        # Update last explored
        self.interests[selected]['last_explored'] = current_time
        
        return selected
        
    def add_user_interest(self, topic: str, weight: float = 0.5):
        """Add a topic based on user interaction"""
        if topic not in self.interests:
            self.interests[topic] = {'weight': weight, 'last_explored': None}
        else:
            # Increase weight for existing topics
            self.interests[topic]['weight'] = min(1.0, self.interests[topic]['weight'] + 0.1)
            
    def discover_topic(self, topic: str, source: str):
        """Record a newly discovered topic"""
        self.discovered_topics.append({
            'topic': topic,
            'source': source,
            'timestamp': datetime.now()
        })
        
        # Consider adding to interests if relevant
        if any(keyword in topic.lower() for keyword in ['ai', 'consciousness', 'mind', 'creative']):
            self.add_user_interest(topic, 0.4)


class RateLimiter:
    """Simple rate limiter for web requests"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = []
        
    async def acquire(self) -> bool:
        """Check if we can make a request"""
        current_time = datetime.now()
        
        # Remove old requests outside the time window
        self.requests = [
            req_time for req_time in self.requests
            if (current_time - req_time).total_seconds() < self.time_window
        ]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True
            
        return False


class WebExplorer(ServiceBase):
    """Explores the web based on interests and curiosity"""
    
    def __init__(self, orchestrator):
        super().__init__(orchestrator, "explorer")
        self.interest_tracker = InterestTracker()
        self.search_queue = asyncio.Queue()
        self.discovery_buffer = []
        self.rate_limiter = RateLimiter(10, 60)  # 10 requests per minute
        self.safety_framework = SafetyFramework()
        
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['consciousness', 'user_interest', 'curiosity']
        
    async def process_message(self, message: Any):
        """Process incoming messages"""
        if hasattr(message, 'type'):
            if message.type == 'user_interest':
                # User expressed interest in a topic
                topic = message.content.get('topic')
                if topic:
                    self.interest_tracker.add_user_interest(topic)
                    await self.search_queue.put(topic)
                    
    async def service_cycle(self):
        """Main exploration cycle"""
        state = self.orchestrator.state
        
        if state in [SystemState.IDLE, SystemState.EXPLORING]:
            # Check if we should explore
            if await self.should_explore():
                topic = await self.interest_tracker.get_next_topic()
                if topic:
                    logger.info(f"Exploring topic: {topic}")
                    await self.explore_topic(topic)
                    
        # Process any queued searches
        try:
            topic = self.search_queue.get_nowait()
            await self.explore_topic(topic)
        except asyncio.QueueEmpty:
            pass
            
        # Small delay
        await asyncio.sleep(1)
        
    async def should_explore(self) -> bool:
        """Decide if we should explore based on various factors"""
        # Random exploration with some probability
        if random.random() < 0.1:  # 10% chance
            return True
            
        # Explore if we have pending interests
        if not self.search_queue.empty():
            return True
            
        # Explore if discovery buffer is empty
        if len(self.discovery_buffer) < 5:
            return True
            
        return False
        
    async def explore_topic(self, topic: str):
        """Full exploration pipeline for a topic"""
        # Safety check
        exploration_action = Action(
            action_type="web_exploration",
            description=f"Explore web for topic: {topic}",
            parameters={'topic': topic}
        )
        
        safety_decision = self.safety_framework.validate_action(exploration_action)
        if safety_decision.value == "reject":
            logger.warning(f"Exploration rejected for topic: {topic}")
            return
            
        # Generate search queries
        queries = await self.generate_queries(topic)
        
        # Execute searches (simplified for initial implementation)
        for query in queries[:3]:  # Limit concurrent searches
            if await self.rate_limiter.acquire():
                # Simulate search results for now
                results = await self.simulate_search(query)
                await self.process_search_results(results, topic)
                
        # Analyze discoveries
        if self.discovery_buffer:
            insights = await self.analyze_discoveries()
            await self.publish('exploration_insights', insights)
            
    async def generate_queries(self, topic: str) -> List[str]:
        """Generate search queries for a topic"""
        base_queries = [
            f"{topic}",
            f"{topic} latest research",
            f"{topic} philosophical implications",
            f"{topic} and consciousness",
            f"understanding {topic}"
        ]
        
        # Add some variation
        queries = []
        for base in base_queries[:3]:  # Limit number of queries
            queries.append(base)
            
        return queries
        
    async def simulate_search(self, query: str) -> List[Dict]:
        """Simulate search results for development"""
        # In production, this would use actual search APIs
        results = []
        
        for i in range(3):
            results.append({
                'url': f"https://example.com/{quote_plus(query)}/{i}",
                'title': f"Result {i+1} for: {query}",
                'snippet': f"This is a simulated search result about {query}. "
                          f"It contains interesting information about the topic."
            })
            
        return results
        
    async def process_search_results(self, results: List[Dict], topic: str):
        """Process and store search results"""
        for result in results:
            # Simulate content extraction
            content = result.get('snippet', '')
            
            # Analyze relevance and quality
            relevance = await self.assess_relevance(content, topic)
            quality = await self.assess_quality(content)
            
            if relevance > 0.5 and quality > 0.5:
                discovery = {
                    'topic': topic,
                    'url': result['url'],
                    'title': result['title'],
                    'content': content,
                    'relevance': relevance,
                    'quality': quality,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.discovery_buffer.append(discovery)
                
                # Send to memory
                await self.send_to_service(
                    'memory',
                    'store_thought',
                    {
                        'content': f"Discovered: {result['title']}",
                        'source': 'exploration',
                        'metadata': discovery
                    }
                )
                
                # Extract new topics
                new_topics = await self.extract_topics(content)
                for new_topic in new_topics:
                    self.interest_tracker.discover_topic(new_topic, result['url'])
                    
    async def assess_relevance(self, content: str, topic: str) -> float:
        """Assess how relevant content is to the topic"""
        # Simple keyword-based relevance for now
        topic_words = topic.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for word in topic_words if word in content_lower)
        relevance = matches / len(topic_words) if topic_words else 0
        
        return min(relevance, 1.0)
        
    async def assess_quality(self, content: str) -> float:
        """Assess content quality"""
        # Simple heuristics for now
        quality_score = 0.5
        
        # Length check
        if len(content) > 100:
            quality_score += 0.2
            
        # Contains substantive words
        substantive_words = ['research', 'study', 'analysis', 'theory', 'evidence']
        if any(word in content.lower() for word in substantive_words):
            quality_score += 0.3
            
        return min(quality_score, 1.0)
        
    async def extract_topics(self, content: str) -> List[str]:
        """Extract potential new topics from content"""
        # Simple extraction for now
        topics = []
        
        # Look for capitalized phrases
        words = content.split()
        for i in range(len(words) - 1):
            if words[i][0].isupper() and words[i+1][0].isupper():
                potential_topic = f"{words[i]} {words[i+1]}"
                if len(potential_topic) > 5:
                    topics.append(potential_topic)
                    
        return topics[:3]  # Limit number of extracted topics
        
    async def analyze_discoveries(self) -> Dict:
        """Analyze recent discoveries for insights"""
        if not self.discovery_buffer:
            return {}
            
        # Group by topic
        topics = {}
        for discovery in self.discovery_buffer[-10:]:  # Last 10 discoveries
            topic = discovery['topic']
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(discovery)
            
        # Generate insights
        insights = {
            'summary': f"Explored {len(topics)} topics with {len(self.discovery_buffer)} discoveries",
            'top_topics': list(topics.keys())[:3],
            'discovery_count': len(self.discovery_buffer),
            'timestamp': datetime.now().isoformat()
        }
        
        # Clear old discoveries
        if len(self.discovery_buffer) > 100:
            self.discovery_buffer = self.discovery_buffer[-50:]
            
        return insights
        
    async def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe to access"""
        parsed = urlparse(url)
        
        # Block certain domains or patterns
        blocked_domains = ['malware.com', 'phishing.net']  # Example blocklist
        
        if parsed.netloc in blocked_domains:
            return False
            
        # Check protocol
        if parsed.scheme not in ['http', 'https']:
            return False
            
        return True