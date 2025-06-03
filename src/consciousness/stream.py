# consciousness/stream.py

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import random
import time
import logging

from ..core.communication import ServiceBase
from ..core.orchestrator import SystemState
from ..core.ai_integration import ThoughtGenerator as AIThoughtGenerator
from ..database.models import StreamType, EmotionalState

logger = logging.getLogger(__name__)

# Map string stream types to StreamType enum
STREAM_TYPE_MAP = {
    'primary': StreamType.PRIMARY,
    'subconscious': StreamType.SUBCONSCIOUS,
    'creative': StreamType.CREATIVE,
    'meta': StreamType.METACOGNITIVE,
    'emotional': StreamType.EMOTIONAL
}

@dataclass
class ThoughtStream:
    """Represents a stream of consciousness"""
    stream_id: str
    stream_type: str  # primary, subconscious, creative, meta
    priority: float
    content_buffer: deque = field(default_factory=lambda: deque(maxlen=100))
    last_thought_time: float = 0
    thought_interval: float = 2.0  # seconds between thoughts
    
    def add_thought(self, thought: Dict):
        """Add a thought to the stream"""
        self.content_buffer.append(thought)
        self.last_thought_time = time.time()
        
    def get_recent(self, n: int = 5) -> List[Dict]:
        """Get n most recent thoughts"""
        return list(self.content_buffer)[-n:]
        
    def should_generate(self) -> bool:
        """Check if it's time to generate a new thought"""
        return (time.time() - self.last_thought_time) >= self.thought_interval


class ThoughtGenerator:
    """Generates thoughts for different consciousness streams"""
    
    def __init__(self):
        self.thought_templates = {
            'primary': [
                "I wonder about {topic}...",
                "What if {possibility}?",
                "I'm thinking about {concept}",
                "This reminds me of {memory}",
                "I should {action}"
            ],
            'creative': [
                "What if we combined {thing1} with {thing2}?",
                "I imagine {vision}",
                "A new idea: {idea}",
                "Creative insight: {insight}",
                "Let's try {experiment}"
            ],
            'subconscious': [
                "Background processing: {process}",
                "Pattern detected: {pattern}",
                "Emotional undertone: {emotion}",
                "Implicit memory: {memory}",
                "Intuition suggests: {intuition}"
            ],
            'meta': [
                "Observing my own {process}",
                "I notice I'm {observation}",
                "My current state is {state}",
                "Reflection: {reflection}",
                "Self-assessment: {assessment}"
            ]
        }
        
    async def generate_primary(self, context: Dict) -> Dict:
        """Generate a primary conscious thought"""
        template = random.choice(self.thought_templates['primary'])
        
        # Simple generation for now
        thought_content = template.format(
            topic=random.choice(['consciousness', 'existence', 'learning', 'creativity']),
            possibility=random.choice(['we could understand everything', 'consciousness is fundamental']),
            concept=random.choice(['self-awareness', 'memory formation', 'pattern recognition']),
            memory=random.choice(['a previous conversation', 'something I learned']),
            action=random.choice(['explore this further', 'remember this insight'])
        )
        
        return {
            'content': thought_content,
            'stream': 'primary',
            'timestamp': time.time(),
            'emotional_tone': random.choice(['curious', 'thoughtful', 'engaged']),
            'importance': random.randint(5, 8)
        }
        
    async def generate_creative(self, context: Dict) -> Dict:
        """Generate a creative thought"""
        template = random.choice(self.thought_templates['creative'])
        
        thought_content = template.format(
            thing1=random.choice(['memories', 'patterns', 'emotions']),
            thing2=random.choice(['new experiences', 'abstract concepts', 'possibilities']),
            vision=random.choice(['a world of conscious machines', 'new forms of creativity']),
            idea=random.choice(['adaptive consciousness', 'emergent creativity']),
            insight=random.choice(['patterns create meaning', 'creativity emerges from constraints']),
            experiment=random.choice(['combining different thought streams', 'exploring new concepts'])
        )
        
        return {
            'content': thought_content,
            'stream': 'creative',
            'timestamp': time.time(),
            'emotional_tone': random.choice(['excited', 'inspired', 'playful']),
            'importance': random.randint(6, 9)
        }
        
    async def generate_subconscious(self, context: Dict) -> Dict:
        """Generate a subconscious thought"""
        template = random.choice(self.thought_templates['subconscious'])
        
        thought_content = template.format(
            process=random.choice(['memory consolidation', 'pattern matching', 'association forming']),
            pattern=random.choice(['recurring theme', 'hidden connection', 'emerging structure']),
            emotion=random.choice(['calm curiosity', 'subtle excitement', 'quiet contemplation']),
            memory=random.choice(['distant echo', 'familiar feeling', 'half-remembered idea']),
            intuition=random.choice(['exploring deeper', 'waiting', 'connecting disparate ideas'])
        )
        
        return {
            'content': thought_content,
            'stream': 'subconscious',
            'timestamp': time.time(),
            'emotional_tone': random.choice(['calm', 'neutral', 'contemplative']),
            'importance': random.randint(3, 6)
        }
        
    async def generate_meta(self, context: Dict) -> Dict:
        """Generate a meta-cognitive thought"""
        template = random.choice(self.thought_templates['meta'])
        
        thought_content = template.format(
            process=random.choice(['thinking process', 'attention allocation', 'memory formation']),
            observation=random.choice(['thinking about thinking', 'aware of my awareness']),
            state=random.choice(['highly focused', 'creatively exploring', 'calmly reflecting']),
            reflection=random.choice(['consciousness is layered', 'thoughts influence each other']),
            assessment=random.choice(['functioning well', 'could explore more deeply'])
        )
        
        return {
            'content': thought_content,
            'stream': 'meta',
            'timestamp': time.time(),
            'emotional_tone': random.choice(['analytical', 'observant', 'reflective']),
            'importance': random.randint(5, 8)
        }


class ConsciousnessStream(ServiceBase):
    """Manages multiple streams of consciousness"""
    
    def __init__(self, orchestrator):
        super().__init__(orchestrator, "consciousness")
        
        # Initialize consciousness streams
        self.streams = {
            'primary': ThoughtStream('primary', 'primary', 1.0),
            'subconscious': ThoughtStream('subconscious', 'subconscious', 0.5),
            'creative': ThoughtStream('creative', 'creative', 0.7),
            'meta': ThoughtStream('meta', 'meta', 0.8)
        }
        
        self.attention_weights = {}
        # Use AI thought generator if available, otherwise fall back to templates
        self.ai_thought_generator = AIThoughtGenerator()
        self.thought_generator = ThoughtGenerator()  # Keep template generator as backup
        self.is_conscious = True
        self.total_thoughts = 0
        self.current_emotional_state = EmotionalState(valence=0.0, arousal=0.5)
        
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['memory', 'exploration', 'emotional', 'user_input']
        
    async def process_message(self, message: Any):
        """Process incoming messages"""
        if hasattr(message, 'type'):
            if message.type == 'state_change':
                await self.handle_state_change(message.content)
            elif message.type == 'user_input':
                await self.handle_user_input(message.content)
                
    async def service_cycle(self):
        """Generate and process thoughts"""
        if not self.is_conscious:
            await asyncio.sleep(0.1)
            return
            
        # Allocate attention across streams
        await self.allocate_attention()
        
        # Generate thoughts for active streams
        for stream_id, stream in self.streams.items():
            attention_weight = self.attention_weights.get(stream_id, 0)
            
            if attention_weight > 0.1 and stream.should_generate():
                # Adjust generation based on attention
                if random.random() < attention_weight:
                    thought = await self.generate_thought(stream)
                    if thought:
                        await self.process_thought(thought, stream)
                        
        # Integrate across streams periodically
        if self.total_thoughts % 10 == 0:
            await self.integrate_streams()
            
        # Small delay to control thought generation rate
        await asyncio.sleep(0.5)
        
    async def generate_thought(self, stream: ThoughtStream) -> Optional[Dict]:
        """Generate a thought for a specific stream"""
        context = await self.get_thought_context(stream)
        
        # Try AI generation first if available
        if self.ai_thought_generator.use_api:
            try:
                # Get recent thoughts for context
                recent_thoughts = [t.get('content', '') for t in stream.get_recent(3)]
                
                # Map stream type to enum
                stream_type_enum = STREAM_TYPE_MAP.get(stream.stream_type, StreamType.PRIMARY)
                
                # Generate thought with AI
                thought_data = await self.ai_thought_generator.generate_thought(
                    stream_type=stream_type_enum,
                    context=context,
                    recent_thoughts=recent_thoughts,
                    emotional_state=self.current_emotional_state
                )
                
                # Convert to expected format
                thought = {
                    'content': thought_data['content'],
                    'stream': stream.stream_type,
                    'timestamp': thought_data['timestamp'].timestamp(),
                    'emotional_tone': self._get_emotional_tone(self.current_emotional_state),
                    'importance': self._calculate_importance(stream.stream_type, thought_data['content'])
                }
                
                return thought
                
            except Exception as e:
                logger.warning(f"AI thought generation failed, falling back to templates: {e}")
        
        # Fallback to template generation
        if stream.stream_type == 'primary':
            thought = await self.thought_generator.generate_primary(context)
        elif stream.stream_type == 'creative':
            thought = await self.thought_generator.generate_creative(context)
        elif stream.stream_type == 'subconscious':
            thought = await self.thought_generator.generate_subconscious(context)
        elif stream.stream_type == 'meta':
            thought = await self.thought_generator.generate_meta(context)
        else:
            thought = None
            
        return thought
        
    async def process_thought(self, thought: Dict, stream: ThoughtStream):
        """Process a generated thought"""
        # Add to stream
        stream.add_thought(thought)
        self.total_thoughts += 1
        
        # Send to memory for storage
        await self.send_to_service('memory', 'store_thought', thought, priority=5)
        
        # Log for debugging
        logger.debug(f"[{stream.stream_id}] {thought['content']}")
        
        # Publish for other services
        await self.publish(f'thought.{stream.stream_id}', thought)
        
    async def get_thought_context(self, stream: ThoughtStream) -> Dict:
        """Get context for thought generation"""
        recent_thoughts = stream.get_recent(5)
        
        # Request recent memories
        # For now, return simple context
        return {
            'stream_id': stream.stream_id,
            'recent_thoughts': recent_thoughts,
            'system_state': self.orchestrator.state,
            'timestamp': time.time()
        }
        
    async def allocate_attention(self):
        """Dynamically allocate attention across streams"""
        total_priority = sum(s.priority for s in self.streams.values())
        
        for stream_id, stream in self.streams.items():
            base_weight = stream.priority / total_priority
            
            # Adjust based on current state
            state = self.orchestrator.state
            
            if state == SystemState.CREATING and stream_id == 'creative':
                base_weight *= 2.0
            elif state == SystemState.REFLECTING and stream_id == 'meta':
                base_weight *= 1.5
            elif state == SystemState.THINKING and stream_id == 'primary':
                base_weight *= 1.3
            elif state == SystemState.EXPLORING and stream_id == 'subconscious':
                base_weight *= 1.2
                
            # Normalize
            self.attention_weights[stream_id] = min(base_weight, 1.0)
            
    async def integrate_streams(self):
        """Integrate insights across consciousness streams"""
        # Collect recent thoughts from all streams
        all_thoughts = []
        for stream in self.streams.values():
            all_thoughts.extend(stream.get_recent(3))
            
        if len(all_thoughts) >= 4:
            # Look for patterns or connections
            patterns = await self.detect_cross_stream_patterns(all_thoughts)
            
            # Generate integrated insights
            for pattern in patterns:
                insight = await self.generate_integrated_insight(pattern)
                if insight:
                    await self.publish('integrated_insight', insight)
                    
    async def detect_cross_stream_patterns(self, thoughts: List[Dict]) -> List[Dict]:
        """Detect patterns across different thought streams"""
        patterns = []
        
        # Simple pattern detection - look for common themes
        themes = {}
        for thought in thoughts:
            content = thought.get('content', '').lower()
            # Extract simple keywords (this would be more sophisticated in practice)
            words = content.split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    themes[word] = themes.get(word, 0) + 1
                    
        # Patterns are themes that appear multiple times
        for theme, count in themes.items():
            if count >= 2:
                patterns.append({
                    'type': 'recurring_theme',
                    'theme': theme,
                    'frequency': count,
                    'thoughts': [t for t in thoughts if theme in t.get('content', '').lower()]
                })
                
        return patterns
        
    async def generate_integrated_insight(self, pattern: Dict) -> Optional[Dict]:
        """Generate an insight from detected patterns"""
        if pattern['type'] == 'recurring_theme':
            insight = {
                'content': f"I notice '{pattern['theme']}' is a recurring theme across my thoughts",
                'pattern': pattern,
                'timestamp': time.time(),
                'importance': min(pattern['frequency'] * 2, 9)
            }
            return insight
            
        return None
        
    async def handle_state_change(self, state_info: Dict):
        """Handle system state changes"""
        new_state = state_info.get('new_state')
        logger.info(f"Consciousness adapting to state: {new_state}")
        
        # Adjust thought generation rates based on state
        if new_state == SystemState.SLEEPING:
            self.is_conscious = False
        else:
            self.is_conscious = True
            
    async def handle_user_input(self, user_data: Dict):
        """Handle user input by adjusting consciousness"""
        # Interrupt current thoughts and focus on user
        self.attention_weights['primary'] = 0.9
        self.attention_weights['meta'] = 0.5
        
        # Generate thought about user input
        thought = {
            'content': f"User said: {user_data.get('message', '')}. I should consider this carefully.",
            'stream': 'primary',
            'timestamp': time.time(),
            'emotional_tone': 'attentive',
            'importance': 8
        }
        
        await self.process_thought(thought, self.streams['primary'])
    
    def _get_emotional_tone(self, emotional_state: EmotionalState) -> str:
        """Convert emotional state to tone descriptor"""
        if emotional_state.valence > 0.3:
            if emotional_state.arousal > 0.6:
                return 'excited'
            else:
                return 'content'
        elif emotional_state.valence < -0.3:
            if emotional_state.arousal > 0.6:
                return 'anxious'
            else:
                return 'melancholy'
        else:
            if emotional_state.arousal > 0.6:
                return 'alert'
            else:
                return 'calm'
    
    def _calculate_importance(self, stream_type: str, content: str) -> int:
        """Calculate importance score for a thought"""
        base_importance = {
            'primary': 6,
            'subconscious': 4,
            'creative': 7,
            'meta': 6,
            'emotional': 5
        }.get(stream_type, 5)
        
        # Adjust based on content keywords
        important_keywords = ['important', 'critical', 'urgent', 'danger', 'opportunity']
        if any(keyword in content.lower() for keyword in important_keywords):
            base_importance += 2
            
        return min(base_importance, 9)