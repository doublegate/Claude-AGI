"""
Creative Engine for Claude-AGI
==============================

Advanced creative capabilities including:
- Creative ideation and brainstorming
- Artistic and literary generation
- Innovation and novel solution creation
- Creative process modeling and enhancement
"""

import asyncio
import logging
import random
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json

from ..core.communication import ServiceBase
from ..database.models import Memory, StreamType

logger = logging.getLogger(__name__)


class CreativeMode(str, Enum):
    """Different modes of creative thinking"""
    DIVERGENT = "divergent"  # Generate many ideas
    CONVERGENT = "convergent"  # Refine and combine ideas
    LATERAL = "lateral"  # Unexpected connections
    ANALOGICAL = "analogical"  # Draw from other domains
    EXPERIMENTAL = "experimental"  # Try novel approaches
    COLLABORATIVE = "collaborative"  # Build on other ideas


class CreativeCategory(str, Enum):
    """Categories of creative output"""
    CONCEPTUAL = "conceptual"  # Ideas and concepts
    ARTISTIC = "artistic"  # Creative expression
    TECHNICAL = "technical"  # Novel solutions
    NARRATIVE = "narrative"  # Stories and scenarios
    DESIGN = "design"  # Visual and structural
    PHILOSOPHICAL = "philosophical"  # Deep thinking


@dataclass
class CreativeIdea:
    """Represents a creative idea or concept"""
    idea_id: str
    content: str
    category: CreativeCategory
    originality_score: float
    feasibility_score: float
    inspiration_sources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    refinements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CreativeSession:
    """Represents a creative thinking session"""
    session_id: str
    prompt: str
    mode: CreativeMode
    ideas_generated: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    inspiration_used: List[str] = field(default_factory=list)


class CreativeEngine(ServiceBase):
    """
    Advanced creative engine for ideation, artistic generation,
    and innovative problem solving.
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "creative")
        
        # Creative state
        self.ideas: Dict[str, CreativeIdea] = {}
        self.sessions: Dict[str, CreativeSession] = {}
        self.inspiration_bank: List[Dict[str, Any]] = []
        
        # Creative parameters
        self.originality_threshold = 0.7
        self.idea_combination_rate = 0.3
        self.inspiration_decay = 0.1
        
        # Creative process tracking
        self.active_sessions: Dict[str, CreativeSession] = {}
        self.idea_networks: Dict[str, List[str]] = defaultdict(list)
        self.creative_patterns: Dict[str, int] = defaultdict(int)
        
        # Initialize inspiration bank with diverse content
        self._initialize_inspiration_bank()
    
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['creative_request', 'inspiration_input', 'idea_feedback', 'creative_collaboration']
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for creative updates"""
        try:
            # Update inspiration bank
            await self._update_inspiration_bank()
            
            # Process active creative sessions
            await self._process_active_sessions()
            
            # Generate spontaneous ideas
            await self._generate_spontaneous_ideas()
            
            # Update idea networks
            await self._update_idea_networks()
            
        except Exception as e:
            logger.error(f"Error in creative service cycle: {e}", exc_info=True)
        
    async def handle_message(self, message):
        """Handle incoming messages for creative operations"""
        message_type = message.type
        content = message.content
        
        if message_type == 'generate_ideas':
            return await self._generate_ideas(content)
        elif message_type == 'start_creative_session':
            return await self._start_creative_session(content)
        elif message_type == 'end_creative_session':
            return await self._end_creative_session(content)
        elif message_type == 'refine_idea':
            return await self._refine_idea(content)
        elif message_type == 'combine_ideas':
            return await self._combine_ideas(content)
        elif message_type == 'add_inspiration':
            await self._add_inspiration(content)
        elif message_type == 'get_creative_insights':
            return await self._get_creative_insights()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def _initialize_inspiration_bank(self):
        """Initialize the inspiration bank with diverse creative prompts"""
        self.inspiration_bank = [
            {
                'type': 'metaphor',
                'content': 'like a river flowing through time',
                'domain': 'nature',
                'energy': 0.8
            },
            {
                'type': 'constraint',
                'content': 'using only circular shapes',
                'domain': 'design',
                'energy': 0.7
            },
            {
                'type': 'perspective',
                'content': 'from the viewpoint of an ant',
                'domain': 'viewpoint',
                'energy': 0.6
            },
            {
                'type': 'combination',
                'content': 'mixing music with mathematics',
                'domain': 'fusion',
                'energy': 0.9
            },
            {
                'type': 'transformation',
                'content': 'what if gravity worked backwards',
                'domain': 'physics',
                'energy': 0.8
            },
            {
                'type': 'emotion',
                'content': 'expressing pure joy',
                'domain': 'feeling',
                'energy': 0.7
            }
        ]
    
    async def _generate_ideas(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative ideas based on a prompt"""
        prompt = request.get('prompt', '')
        category = CreativeCategory(request.get('category', 'conceptual'))
        mode = CreativeMode(request.get('mode', 'divergent'))
        count = request.get('count', 5)
        
        ideas = []
        session_id = f"session_{datetime.now().timestamp()}"
        
        # Start creative session
        session = CreativeSession(
            session_id=session_id,
            prompt=prompt,
            mode=mode
        )
        self.active_sessions[session_id] = session
        
        try:
            # Generate ideas using different creative modes
            for i in range(count):
                idea = await self._create_idea(prompt, category, mode, session)
                if idea:
                    ideas.append(idea)
                    session.ideas_generated.append(idea.idea_id)
                    self.ideas[idea.idea_id] = idea
            
            # End session
            session.end_time = datetime.now()
            self.sessions[session_id] = session
            del self.active_sessions[session_id]
            
            return {
                'ideas': [
                    {
                        'id': idea.idea_id,
                        'content': idea.content,
                        'category': idea.category,
                        'originality': idea.originality_score,
                        'feasibility': idea.feasibility_score,
                        'sources': idea.inspiration_sources
                    }
                    for idea in ideas
                ],
                'session_id': session_id,
                'mode': mode,
                'total_generated': len(ideas)
            }
            
        except Exception as e:
            logger.error(f"Error generating ideas: {e}")
            return {'error': str(e), 'ideas': []}
    
    async def _create_idea(self, prompt: str, category: CreativeCategory, 
                          mode: CreativeMode, session: CreativeSession) -> Optional[CreativeIdea]:
        """Create a single creative idea"""
        try:
            idea_id = f"idea_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
            
            # Select inspiration based on mode
            inspiration = await self._select_inspiration(mode, category)
            session.inspiration_used.extend([insp['content'] for insp in inspiration])
            
            # Generate idea content based on mode
            content = await self._generate_idea_content(prompt, category, mode, inspiration)
            
            # Calculate scores
            originality = await self._calculate_originality(content, category)
            feasibility = await self._calculate_feasibility(content, category)
            
            idea = CreativeIdea(
                idea_id=idea_id,
                content=content,
                category=category,
                originality_score=originality,
                feasibility_score=feasibility,
                inspiration_sources=[insp['content'] for insp in inspiration]
            )
            
            # Track creative patterns
            pattern_key = f"{mode}_{category}"
            self.creative_patterns[pattern_key] += 1
            
            return idea
            
        except Exception as e:
            logger.error(f"Error creating idea: {e}")
            return None
    
    async def _select_inspiration(self, mode: CreativeMode, 
                                category: CreativeCategory) -> List[Dict[str, Any]]:
        """Select appropriate inspiration sources for the creative mode"""
        inspiration_count = 2 if mode == CreativeMode.DIVERGENT else 1
        
        # Filter inspiration by relevance and energy
        available = [
            insp for insp in self.inspiration_bank
            if insp['energy'] > 0.5
        ]
        
        # Mode-specific selection
        if mode == CreativeMode.ANALOGICAL:
            # Prefer different domains for analogical thinking
            available = [insp for insp in available if insp['domain'] != category.value]
        elif mode == CreativeMode.LATERAL:
            # Prefer unexpected combinations
            available = [insp for insp in available if insp['type'] == 'combination']
        
        # Random selection with energy weighting
        selected = []
        for _ in range(min(inspiration_count, len(available))):
            if not available:
                break
            weights = [insp['energy'] for insp in available]
            choice = random.choices(available, weights=weights)[0]
            selected.append(choice)
            available.remove(choice)
        
        return selected
    
    async def _generate_idea_content(self, prompt: str, category: CreativeCategory,
                                   mode: CreativeMode, inspiration: List[Dict[str, Any]]) -> str:
        """Generate the actual idea content"""
        # This is a simplified version - in a real implementation,
        # this would use more sophisticated creative algorithms
        
        base_prompts = {
            CreativeCategory.CONCEPTUAL: [
                f"A new way to think about {prompt}",
                f"What if {prompt} was completely reimagined",
                f"The hidden connections in {prompt}"
            ],
            CreativeCategory.ARTISTIC: [
                f"An artistic expression of {prompt}",
                f"A visual representation that captures {prompt}",
                f"A performance piece about {prompt}"
            ],
            CreativeCategory.TECHNICAL: [
                f"An innovative solution for {prompt}",
                f"A technical approach that revolutionizes {prompt}",
                f"A system that makes {prompt} more efficient"
            ],
            CreativeCategory.NARRATIVE: [
                f"A story where {prompt} is the central theme",
                f"A character whose life revolves around {prompt}",
                f"A world where {prompt} changes everything"
            ],
            CreativeCategory.DESIGN: [
                f"A design that embodies {prompt}",
                f"A structure inspired by {prompt}",
                f"An interface that makes {prompt} intuitive"
            ],
            CreativeCategory.PHILOSOPHICAL: [
                f"The deeper meaning of {prompt}",
                f"How {prompt} relates to human existence",
                f"The philosophical implications of {prompt}"
            ]
        }
        
        # Select base prompt
        base_options = base_prompts.get(category, [f"A creative approach to {prompt}"])
        base = random.choice(base_options)
        
        # Add inspiration influence
        if inspiration:
            insp = random.choice(inspiration)
            if mode == CreativeMode.ANALOGICAL:
                content = f"{base}, drawing inspiration from {insp['content']}"
            elif mode == CreativeMode.LATERAL:
                content = f"{base}, but {insp['content']}"
            elif mode == CreativeMode.EXPERIMENTAL:
                content = f"{base} by experimenting with {insp['content']}"
            else:
                content = f"{base} with elements of {insp['content']}"
        else:
            content = base
        
        return content
    
    async def _calculate_originality(self, content: str, category: CreativeCategory) -> float:
        """Calculate how original an idea is"""
        # Simplified originality calculation
        # In reality, this would use semantic similarity and novelty detection
        
        # Check against existing ideas
        similarity_scores = []
        for existing_idea in self.ideas.values():
            if existing_idea.category == category:
                # Simple word overlap calculation
                content_words = set(content.lower().split())
                existing_words = set(existing_idea.content.lower().split())
                
                if len(content_words) > 0:
                    overlap = len(content_words & existing_words) / len(content_words)
                    similarity_scores.append(overlap)
        
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            originality = max(0.1, 1.0 - avg_similarity)
        else:
            originality = 0.8  # Default for first idea in category
        
        # Add some randomness for creativity
        originality += random.uniform(-0.1, 0.1)
        return max(0.0, min(1.0, originality))
    
    async def _calculate_feasibility(self, content: str, category: CreativeCategory) -> float:
        """Calculate how feasible an idea is to implement"""
        # Simplified feasibility calculation
        # In reality, this would analyze complexity, resources needed, etc.
        
        feasibility_weights = {
            CreativeCategory.CONCEPTUAL: 0.8,
            CreativeCategory.ARTISTIC: 0.7,
            CreativeCategory.TECHNICAL: 0.6,
            CreativeCategory.NARRATIVE: 0.9,
            CreativeCategory.DESIGN: 0.7,
            CreativeCategory.PHILOSOPHICAL: 0.8
        }
        
        base_feasibility = feasibility_weights.get(category, 0.7)
        
        # Adjust based on content complexity (simplified)
        word_count = len(content.split())
        complexity_factor = max(0.5, 1.0 - (word_count - 10) * 0.02)
        
        feasibility = base_feasibility * complexity_factor
        
        # Add some variation
        feasibility += random.uniform(-0.1, 0.1)
        return max(0.0, min(1.0, feasibility))
    
    async def _start_creative_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new creative session"""
        session_id = f"session_{datetime.now().timestamp()}"
        prompt = request.get('prompt', '')
        mode = CreativeMode(request.get('mode', 'divergent'))
        
        session = CreativeSession(
            session_id=session_id,
            prompt=prompt,
            mode=mode
        )
        
        self.active_sessions[session_id] = session
        
        return {
            'session_id': session_id,
            'status': 'started',
            'mode': mode,
            'prompt': prompt
        }
    
    async def _end_creative_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """End a creative session"""
        session_id = request.get('session_id')
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found or already ended'}
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        
        # Move to completed sessions
        self.sessions[session_id] = session
        del self.active_sessions[session_id]
        
        duration = (session.end_time - session.start_time).total_seconds()
        
        return {
            'session_id': session_id,
            'status': 'ended',
            'duration_seconds': duration,
            'ideas_generated': len(session.ideas_generated),
            'inspiration_used': len(session.inspiration_used)
        }
    
    async def _refine_idea(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Refine an existing idea"""
        idea_id = request.get('idea_id')
        refinement = request.get('refinement', '')
        
        if idea_id not in self.ideas:
            return {'error': 'Idea not found'}
        
        idea = self.ideas[idea_id]
        idea.refinements.append(refinement)
        
        # Update scores based on refinement
        idea.feasibility_score = min(1.0, idea.feasibility_score + 0.1)
        
        return {
            'idea_id': idea_id,
            'status': 'refined',
            'refinement_count': len(idea.refinements),
            'updated_feasibility': idea.feasibility_score
        }
    
    async def _combine_ideas(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple ideas into a new one"""
        idea_ids = request.get('idea_ids', [])
        
        if len(idea_ids) < 2:
            return {'error': 'Need at least 2 ideas to combine'}
        
        # Get existing ideas
        ideas_to_combine = [self.ideas[id] for id in idea_ids if id in self.ideas]
        
        if len(ideas_to_combine) < 2:
            return {'error': 'Not all ideas found'}
        
        # Create combined idea
        combined_content = f"Combining: {' + '.join([idea.content for idea in ideas_to_combine])}"
        combined_category = ideas_to_combine[0].category  # Use first idea's category
        
        # Calculate combined scores
        avg_originality = sum(idea.originality_score for idea in ideas_to_combine) / len(ideas_to_combine)
        avg_feasibility = sum(idea.feasibility_score for idea in ideas_to_combine) / len(ideas_to_combine)
        
        # Bonus for combination
        combined_originality = min(1.0, avg_originality + 0.2)
        combined_feasibility = max(0.1, avg_feasibility - 0.1)  # Combinations are often less feasible
        
        new_idea_id = f"combined_{datetime.now().timestamp()}"
        combined_idea = CreativeIdea(
            idea_id=new_idea_id,
            content=combined_content,
            category=combined_category,
            originality_score=combined_originality,
            feasibility_score=combined_feasibility,
            inspiration_sources=[f"combination of {len(ideas_to_combine)} ideas"]
        )
        
        self.ideas[new_idea_id] = combined_idea
        
        # Track combination in network
        for idea_id in idea_ids:
            self.idea_networks[idea_id].append(new_idea_id)
            self.idea_networks[new_idea_id].append(idea_id)
        
        return {
            'new_idea_id': new_idea_id,
            'content': combined_content,
            'originality': combined_originality,
            'feasibility': combined_feasibility,
            'combined_from': idea_ids
        }
    
    async def _add_inspiration(self, inspiration_data: Dict[str, Any]):
        """Add new inspiration to the bank"""
        inspiration = {
            'type': inspiration_data.get('type', 'general'),
            'content': inspiration_data.get('content', ''),
            'domain': inspiration_data.get('domain', 'general'),
            'energy': inspiration_data.get('energy', 0.7)
        }
        
        self.inspiration_bank.append(inspiration)
        
        # Keep bank size manageable
        if len(self.inspiration_bank) > 100:
            # Remove lowest energy inspirations
            self.inspiration_bank.sort(key=lambda x: x['energy'])
            self.inspiration_bank = self.inspiration_bank[10:]  # Keep top 90
    
    async def _get_creative_insights(self) -> Dict[str, Any]:
        """Generate insights about creative activity"""
        total_ideas = len(self.ideas)
        active_sessions = len(self.active_sessions)
        completed_sessions = len(self.sessions)
        
        # Category distribution
        category_counts = {}
        originality_by_category = {}
        feasibility_by_category = {}
        
        for idea in self.ideas.values():
            cat = idea.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            if cat not in originality_by_category:
                originality_by_category[cat] = []
                feasibility_by_category[cat] = []
            
            originality_by_category[cat].append(idea.originality_score)
            feasibility_by_category[cat].append(idea.feasibility_score)
        
        # Calculate averages
        avg_originality_by_cat = {
            cat: sum(scores) / len(scores)
            for cat, scores in originality_by_category.items()
        }
        avg_feasibility_by_cat = {
            cat: sum(scores) / len(scores)
            for cat, scores in feasibility_by_category.items()
        }
        
        # Most creative patterns
        top_patterns = sorted(
            self.creative_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_ideas': total_ideas,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'category_distribution': category_counts,
            'average_originality_by_category': avg_originality_by_cat,
            'average_feasibility_by_category': avg_feasibility_by_cat,
            'top_creative_patterns': [{'pattern': p[0], 'count': p[1]} for p in top_patterns],
            'inspiration_bank_size': len(self.inspiration_bank),
            'idea_network_connections': sum(len(connections) for connections in self.idea_networks.values())
        }
    
    async def _update_inspiration_bank(self):
        """Update and refresh inspiration bank"""
        await self.decay_inspiration_energy()
    
    async def _process_active_sessions(self):
        """Process active creative sessions"""
        current_time = datetime.now()
        for session in list(self.active_sessions.values()):
            # Close sessions that have been active for too long
            if (current_time - session.start_time).total_seconds() > 3600:  # 1 hour
                session.end_time = current_time
                del self.active_sessions[session.session_id]
    
    async def _generate_spontaneous_ideas(self):
        """Generate spontaneous creative ideas"""
        if len(self.inspiration_bank) > 10 and len(self.ideas) < 100:
            # Occasionally generate spontaneous ideas from inspiration
            import random
            if random.random() < 0.1:  # 10% chance per cycle
                inspiration = random.choice(self.inspiration_bank)
                await self._generate_ideas({
                    'prompt': f"Spontaneous idea from: {inspiration['content'][:50]}",
                    'mode': 'divergent',
                    'count': 1
                })
    
    async def _update_idea_networks(self):
        """Update connections between related ideas"""
        # Simple network update - connect ideas with similar themes
        idea_keys = list(self.ideas.keys())
        for i, idea1_id in enumerate(idea_keys):
            for idea2_id in idea_keys[i+1:]:
                idea1 = self.ideas[idea1_id]
                idea2 = self.ideas[idea2_id]
                if self._ideas_are_related(idea1, idea2):
                    if idea2_id not in self.idea_networks[idea1_id]:
                        self.idea_networks[idea1_id].append(idea2_id)
                    if idea1_id not in self.idea_networks[idea2_id]:
                        self.idea_networks[idea2_id].append(idea1_id)
    
    def _ideas_are_related(self, idea1: CreativeIdea, idea2: CreativeIdea) -> bool:
        """Check if two ideas are related"""
        # Check if they share inspiration sources or categories
        return (idea1.category == idea2.category or 
                bool(set(idea1.inspiration_sources).intersection(set(idea2.inspiration_sources))))

    async def decay_inspiration_energy(self):
        """Decay energy of unused inspirations"""
        for inspiration in self.inspiration_bank:
            inspiration['energy'] = max(0.1, inspiration['energy'] - self.inspiration_decay * 0.01)
    
    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info(f"{self.service_name} service started")
        
        # Periodic inspiration decay
        decay_interval = 3600  # 1 hour
        last_decay = datetime.now()
        
        try:
            while self.running:
                # Process messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self.handle_message(message)
                
                # Periodic inspiration energy decay
                current_time = datetime.now()
                if (current_time - last_decay).seconds >= decay_interval:
                    await self.decay_inspiration_energy()
                    last_decay = current_time
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except Exception as e:
            logger.error(f"Error in {self.service_name} service: {e}")
        finally:
            logger.info(f"{self.service_name} service stopped")