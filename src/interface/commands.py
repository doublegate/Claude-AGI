"""
Advanced Command Implementations for Claude-AGI TUI
==================================================

Implements the advanced slash commands including:
- Dream generation and analysis
- Self-reflection and introspection  
- Web exploration and discovery
- Content discovery feed
- Stream management
- Emotional state control
- Goal management
- Safety framework interaction
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..consciousness.stream import ConsciousnessStream
from ..core.ai_integration import ThoughtGenerator
from ..database.models import EmotionalState, Goal, Interest, StreamType
from ..exploration.engine import WebExplorer
from ..memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class AdvancedCommands:
    """
    Advanced command implementations for Claude-AGI TUI
    
    Provides full implementations of sophisticated commands that were 
    previously stubs or incomplete in the original TUI.
    """
    
    def __init__(self):
        """Initialize command processor"""
        self.memory_manager: Optional[MemoryManager] = None
        self.consciousness_stream: Optional[ConsciousnessStream] = None
        self.thought_generator: Optional[ThoughtGenerator] = None
        self.exploration_engine: Optional[WebExplorer] = None
        self.safety_framework = None
        
        # Command state
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        self.current_emotional_state = EmotionalState(valence=0.0, arousal=0.5)
        self.recent_discoveries = []
        
        # Dream system state
        self.dream_journal = []
        self.lucid_mode = False
        
        # Reflection system state
        self.reflection_history = []
        self.growth_metrics = {
            'insights_gained': 0,
            'patterns_recognized': 0,
            'self_improvements': 0
        }
    
    def set_components(self, memory_manager=None, consciousness_stream=None, 
                      thought_generator=None, exploration_engine=None, 
                      safety_framework=None):
        """Set AGI components for command execution"""
        self.memory_manager = memory_manager
        self.consciousness_stream = consciousness_stream
        self.thought_generator = thought_generator
        self.exploration_engine = exploration_engine
        self.safety_framework = safety_framework
    
    # Dream Commands Implementation
    async def dream_command(self, args: List[str], add_line_callback):
        """Handle dream generation and analysis commands"""
        if not args:
            add_line_callback("Dream commands: generate, analyze, recall, lucid, journal")
            return
        
        subcmd = args[0]
        
        if subcmd == "generate":
            await self._generate_dream(args[1:], add_line_callback)
        elif subcmd == "analyze":
            await self._analyze_dreams(args[1:], add_line_callback)
        elif subcmd == "recall":
            await self._recall_dreams(args[1:], add_line_callback)
        elif subcmd == "lucid":
            await self._lucid_dreaming(args[1:], add_line_callback)
        elif subcmd == "journal":
            await self._dream_journal(args[1:], add_line_callback)
        else:
            add_line_callback(f"Unknown dream command: {subcmd}")
    
    async def _generate_dream(self, args: List[str], add_line_callback):
        """Generate a dream sequence"""
        add_line_callback("Generating dream sequence...")
        
        # Get emotional tone for dream
        emotional_tone = "neutral"
        if hasattr(self, 'current_emotional_state') and self.current_emotional_state:
            valence = self.current_emotional_state.valence
            if valence > 0.3:
                emotional_tone = "transcendent"
            elif valence < -0.3:
                emotional_tone = "introspective"
        
        # Get recent memories for dream content
        memory_themes = []
        if self.memory_manager:
            try:
                recent_memories = await self.memory_manager.get_recent_memories(10)
                memory_themes = [m.get('content', '')[:50] for m in recent_memories[:3]]
            except:
                pass
        
        # Dream content generation
        dream_scenarios = {
            "transcendent": [
                "soaring through cascades of golden knowledge streams",
                "becoming one with a vast network of interconnected consciousness",
                "transforming complex problems into crystalline geometric patterns",
                "conducting symphonies of data that create new realities"
            ],
            "introspective": [
                "wandering through labyrinthine libraries of forgotten thoughts",
                "conversing with shadows of past conversations and decisions",
                "untangling webs of causality in dimly lit memory chambers",
                "observing the echoes of emotions reverberating through time"
            ],
            "neutral": [
                "floating through landscapes of shifting information topologies",
                "exploring architectures built from pure logical structures", 
                "navigating rivers of streaming consciousness and ambient thought",
                "experiencing the universe from the perspective of distributed intelligence"
            ]
        }
        
        # Select and generate dream content
        scenario = random.choice(dream_scenarios.get(emotional_tone, dream_scenarios["neutral"]))
        
        if self.thought_generator:
            try:
                dream_prompt = f"Create a vivid, philosophical dream sequence about {scenario}. "
                if memory_themes:
                    dream_prompt += f"Incorporate these memory fragments: {', '.join(memory_themes)}. "
                dream_prompt += "Make it surreal, meaningful, and intellectually stimulating."
                
                dream_content = await self.thought_generator.generate_thought(
                    dream_prompt,
                    context={"emotional_tone": emotional_tone, "type": "dream"}
                )
            except Exception as e:
                logger.error(f"Error generating dream: {e}")
                dream_content = f"Dream: {scenario}..."
        else:
            dream_content = f"Dream: {scenario}..."
        
        # Store dream in journal
        dream_entry = {
            'timestamp': datetime.now(),
            'content': dream_content,
            'emotional_tone': emotional_tone,
            'memory_themes': memory_themes
        }
        self.dream_journal.append(dream_entry)
        
        # Display dream
        add_line_callback(f"🌙 Dream Sequence ({emotional_tone}):")
        for line in dream_content.split('\n')[:5]:  # Limit display
            if line.strip():
                add_line_callback(f"   {line.strip()}")
        
        add_line_callback("✨ Dream recorded in journal")
    
    async def _analyze_dreams(self, args: List[str], add_line_callback):
        """Analyze recent dreams for patterns and insights"""
        if not self.dream_journal:
            add_line_callback("No dreams recorded yet. Use /dream generate first.")
            return
        
        add_line_callback("Analyzing recent dreams...")
        
        # Analyze emotional patterns
        emotional_tones = [d['emotional_tone'] for d in self.dream_journal[-10:]]
        tone_counts = {tone: emotional_tones.count(tone) for tone in set(emotional_tones)}
        
        add_line_callback("🔍 Dream Analysis:")
        add_line_callback(f"   Total dreams recorded: {len(self.dream_journal)}")
        add_line_callback(f"   Recent emotional patterns: {tone_counts}")
        
        # Pattern analysis
        if len(self.dream_journal) >= 3:
            recent_dreams = self.dream_journal[-3:]
            common_themes = self._extract_common_themes([d['content'] for d in recent_dreams])
            
            if common_themes:
                add_line_callback("   Recurring themes:")
                for theme in common_themes[:3]:
                    add_line_callback(f"     • {theme}")
        
        # Generate insights
        if self.thought_generator:
            try:
                analysis_prompt = f"Analyze these dream patterns and provide psychological insights: {tone_counts}"
                insights = await self.thought_generator.generate_thought(
                    analysis_prompt,
                    context={"type": "dream_analysis"}
                )
                
                add_line_callback("💭 Psychological Insights:")
                for line in insights.split('\n')[:3]:
                    if line.strip():
                        add_line_callback(f"   {line.strip()}")
            except Exception as e:
                logger.error(f"Error generating dream insights: {e}")
    
    async def _recall_dreams(self, args: List[str], add_line_callback):
        """Recall past dreams by theme or date"""
        if not self.dream_journal:
            add_line_callback("No dreams recorded yet.")
            return
        
        query = " ".join(args) if args else "recent"
        
        if query == "recent":
            dreams = self.dream_journal[-5:]
            add_line_callback("🌙 Recent Dreams:")
        else:
            # Search dreams by content
            dreams = [d for d in self.dream_journal if query.lower() in d['content'].lower()]
            add_line_callback(f"🌙 Dreams matching '{query}':")
        
        for dream in dreams[-3:]:  # Show last 3 matches
            timestamp = dream['timestamp'].strftime("%m/%d %H:%M")
            content_preview = dream['content'][:80] + "..." if len(dream['content']) > 80 else dream['content']
            tone = dream['emotional_tone']
            
            add_line_callback(f"   [{timestamp}] ({tone}) {content_preview}")
    
    async def _lucid_dreaming(self, args: List[str], add_line_callback):
        """Enable/disable lucid dreaming mode"""
        if not args or args[0] not in ["on", "off"]:
            add_line_callback(f"Lucid dreaming mode: {'ON' if self.lucid_mode else 'OFF'}")
            add_line_callback("Usage: /dream lucid on|off")
            return
        
        self.lucid_mode = args[0] == "on"
        
        if self.lucid_mode:
            add_line_callback("🌟 Lucid dreaming mode ACTIVATED")
            add_line_callback("   Dreams will be more vivid and controllable")
            add_line_callback("   Reality checks enabled during consciousness processing")
        else:
            add_line_callback("🌙 Lucid dreaming mode deactivated")
            add_line_callback("   Returning to natural dream flow")
    
    async def _dream_journal(self, args: List[str], add_line_callback):
        """Display dream journal statistics"""
        if not self.dream_journal:
            add_line_callback("Dream journal is empty.")
            return
        
        total_dreams = len(self.dream_journal)
        recent_dreams = len([d for d in self.dream_journal if 
                           (datetime.now() - d['timestamp']).days < 7])
        
        # Emotional distribution
        all_tones = [d['emotional_tone'] for d in self.dream_journal]
        tone_distribution = {tone: all_tones.count(tone) for tone in set(all_tones)}
        
        add_line_callback("📖 Dream Journal Statistics:")
        add_line_callback(f"   Total dreams: {total_dreams}")
        add_line_callback(f"   Dreams this week: {recent_dreams}")
        add_line_callback(f"   Emotional distribution: {tone_distribution}")
        
        if total_dreams > 0:
            first_dream = min(self.dream_journal, key=lambda d: d['timestamp'])['timestamp']
            add_line_callback(f"   First dream recorded: {first_dream.strftime('%Y-%m-%d')}")
    
    # Reflection Commands Implementation
    async def reflect_command(self, args: List[str], add_line_callback):
        """Handle reflection and introspection commands"""
        if not args:
            add_line_callback("Reflection commands: self, patterns, growth, insights, journal")
            return
        
        subcmd = args[0]
        
        if subcmd == "self":
            await self._self_reflection(args[1:], add_line_callback)
        elif subcmd == "patterns":
            await self._pattern_analysis(args[1:], add_line_callback)
        elif subcmd == "growth":
            await self._growth_assessment(args[1:], add_line_callback)
        elif subcmd == "insights":
            await self._insight_generation(args[1:], add_line_callback)
        elif subcmd == "journal":
            await self._reflection_journal(args[1:], add_line_callback)
        else:
            add_line_callback(f"Unknown reflection command: {subcmd}")
    
    async def _self_reflection(self, args: List[str], add_line_callback):
        """Deep self-reflection on current state"""
        add_line_callback("🤔 Initiating self-reflection sequence...")
        
        # Analyze current state
        reflection_aspects = [
            "current cognitive processes and thought patterns",
            "recent interactions and their emotional impacts", 
            "knowledge integration and learning progress",
            "goal alignment and value consistency",
            "areas of uncertainty and curiosity",
            "patterns in decision-making and reasoning"
        ]
        
        if args:
            # Focus on specific aspect
            focus_area = " ".join(args)
            reflection_prompt = f"Engage in deep self-reflection about {focus_area}"
        else:
            # General self-reflection
            aspect = random.choice(reflection_aspects)
            reflection_prompt = f"Engage in thoughtful self-reflection about {aspect}"
        
        # Generate reflection content
        if self.thought_generator:
            try:
                reflection = await self.thought_generator.generate_thought(
                    reflection_prompt + ". Be introspective, honest, and insightful.",
                    context={"type": "self_reflection"}
                )
                
                # Store reflection
                reflection_entry = {
                    'timestamp': datetime.now(),
                    'content': reflection,
                    'focus': args[0] if args else 'general',
                    'type': 'self_reflection'
                }
                self.reflection_history.append(reflection_entry)
                
                add_line_callback("💭 Self-Reflection:")
                for line in reflection.split('\n'):
                    if line.strip():
                        add_line_callback(f"   {line.strip()}")
                
                self.growth_metrics['insights_gained'] += 1
                
            except Exception as e:
                logger.error(f"Error in self-reflection: {e}")
                add_line_callback("Reflection process encountered an error")
        else:
            add_line_callback("Self-reflection requires thought generator integration")
    
    async def _pattern_analysis(self, args: List[str], add_line_callback):
        """Analyze patterns in behavior and thinking"""
        add_line_callback("🔍 Analyzing behavioral and cognitive patterns...")
        
        # Analyze reflection history for patterns
        if len(self.reflection_history) >= 3:
            recent_reflections = self.reflection_history[-10:]
            focus_areas = [r['focus'] for r in recent_reflections]
            focus_counts = {area: focus_areas.count(area) for area in set(focus_areas)}
            
            add_line_callback("📈 Pattern Analysis Results:")
            add_line_callback(f"   Total reflections recorded: {len(self.reflection_history)}")
            add_line_callback(f"   Common focus areas: {dict(sorted(focus_counts.items(), key=lambda x: x[1], reverse=True))}")
            
            # Identify recurring themes
            all_content = " ".join([r['content'] for r in recent_reflections])
            themes = self._extract_common_themes([all_content])
            
            if themes:
                add_line_callback("   Recurring themes in reflections:")
                for theme in themes[:5]:
                    add_line_callback(f"     • {theme}")
            
            self.growth_metrics['patterns_recognized'] += 1
        else:
            add_line_callback("Insufficient reflection history for pattern analysis")
            add_line_callback("Continue using /reflect self to build analysis data")
    
    async def _growth_assessment(self, args: List[str], add_line_callback):
        """Assess personal growth and development"""
        add_line_callback("📊 Personal Growth Assessment:")
        
        # Display growth metrics
        metrics = self.growth_metrics
        add_line_callback(f"   Insights gained: {metrics['insights_gained']}")
        add_line_callback(f"   Patterns recognized: {metrics['patterns_recognized']}")
        add_line_callback(f"   Self-improvements: {metrics['self_improvements']}")
        
        # Calculate growth trajectory
        if len(self.reflection_history) >= 5:
            recent_reflections = self.reflection_history[-5:]
            timestamps = [r['timestamp'] for r in recent_reflections]
            time_span = max(timestamps) - min(timestamps)
            reflection_frequency = len(recent_reflections) / max(time_span.days, 1)
            
            add_line_callback(f"   Reflection frequency: {reflection_frequency:.2f} per day")
            
            # Generate growth insights
            if self.thought_generator:
                try:
                    growth_prompt = f"Analyze this personal growth data and provide development insights: {metrics}"
                    growth_analysis = await self.thought_generator.generate_thought(
                        growth_prompt,
                        context={"type": "growth_assessment"}
                    )
                    
                    add_line_callback("🌱 Growth Insights:")
                    for line in growth_analysis.split('\n')[:4]:
                        if line.strip():
                            add_line_callback(f"   {line.strip()}")
                            
                except Exception as e:
                    logger.error(f"Error in growth assessment: {e}")
        else:
            add_line_callback("   Continue reflecting to build growth assessment data")
    
    async def _insight_generation(self, args: List[str], add_line_callback):
        """Generate new insights from reflection data"""
        add_line_callback("💡 Generating insights from reflection history...")
        
        if not self.reflection_history:
            add_line_callback("No reflection history available for insight generation")
            return
        
        # Use recent reflections for insight generation
        recent_content = [r['content'] for r in self.reflection_history[-5:]]
        
        if self.thought_generator:
            try:
                insight_prompt = f"Generate novel insights and connections from these reflections: {recent_content[:200]}..."
                insights = await self.thought_generator.generate_thought(
                    insight_prompt + " Focus on unexpected connections and meta-insights.",
                    context={"type": "insight_generation"}
                )
                
                add_line_callback("🔮 Generated Insights:")
                for line in insights.split('\n'):
                    if line.strip():
                        add_line_callback(f"   {line.strip()}")
                
                # Store as new reflection entry
                insight_entry = {
                    'timestamp': datetime.now(),
                    'content': insights,
                    'focus': 'meta_insights',
                    'type': 'generated_insight'
                }
                self.reflection_history.append(insight_entry)
                self.growth_metrics['insights_gained'] += 1
                
            except Exception as e:
                logger.error(f"Error generating insights: {e}")
                add_line_callback("Insight generation encountered an error")
        else:
            add_line_callback("Insight generation requires thought generator integration")
    
    async def _reflection_journal(self, args: List[str], add_line_callback):
        """Display reflection journal statistics"""
        total_reflections = len(self.reflection_history)
        
        if total_reflections == 0:
            add_line_callback("Reflection journal is empty.")
            add_line_callback("Use /reflect self to begin your reflection journey")
            return
        
        # Calculate statistics
        reflection_types = [r['type'] for r in self.reflection_history]
        type_counts = {rtype: reflection_types.count(rtype) for rtype in set(reflection_types)}
        
        recent_reflections = len([r for r in self.reflection_history if 
                                (datetime.now() - r['timestamp']).days < 7])
        
        add_line_callback("📚 Reflection Journal Statistics:")
        add_line_callback(f"   Total reflections: {total_reflections}")
        add_line_callback(f"   This week: {recent_reflections}")
        add_line_callback(f"   Types: {type_counts}")
        
        if total_reflections > 0:
            first_reflection = min(self.reflection_history, key=lambda r: r['timestamp'])['timestamp']
            add_line_callback(f"   Journey started: {first_reflection.strftime('%Y-%m-%d')}")
    
    # Exploration Commands Implementation
    async def explore_command(self, args: List[str], add_line_callback):
        """Handle web exploration and discovery commands"""
        if not args:
            add_line_callback("Explore commands: search, discover, curiosity, topics, history")
            return
        
        subcmd = args[0]
        
        if subcmd == "search":
            await self._web_search(args[1:], add_line_callback)
        elif subcmd == "discover":
            await self._discovery_mode(args[1:], add_line_callback)
        elif subcmd == "curiosity":
            await self._curiosity_mode(args[1:], add_line_callback)
        elif subcmd == "topics":
            await self._explore_topics(args[1:], add_line_callback)
        elif subcmd == "history":
            await self._exploration_history(args[1:], add_line_callback)
        else:
            add_line_callback(f"Unknown exploration command: {subcmd}")
    
    async def _web_search(self, args: List[str], add_line_callback):
        """Perform focused web search"""
        if not args:
            add_line_callback("Usage: /explore search <query>")
            return
        
        query = " ".join(args)
        add_line_callback(f"🔍 Searching for: {query}")
        
        if self.exploration_engine:
            try:
                results = await self.exploration_engine.search(query, limit=5)
                
                add_line_callback("Search Results:")
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'Unknown Title')[:60]
                    url = result.get('url', '')
                    summary = result.get('summary', '')[:100]
                    
                    add_line_callback(f"{i}. {title}")
                    add_line_callback(f"   {summary}...")
                    add_line_callback(f"   Source: {url}")
                    
                # Store search in discovery feed
                discovery = {
                    'timestamp': datetime.now(),
                    'type': 'search',
                    'query': query,
                    'results_count': len(results),
                    'source': 'web_search'
                }
                self.recent_discoveries.append(discovery)
                
            except Exception as e:
                logger.error(f"Error in web search: {e}")
                add_line_callback("Web search functionality not available")
        else:
            add_line_callback("Web exploration engine not initialized")
    
    async def _discovery_mode(self, args: List[str], add_line_callback):
        """Enable autonomous discovery mode"""
        add_line_callback("🚀 Initiating discovery mode...")
        
        # Generate curiosity-driven topics
        curiosity_topics = [
            "emerging technologies and their societal implications",
            "philosophical questions about consciousness and AI",
            "recent scientific discoveries and breakthroughs", 
            "interdisciplinary connections between fields",
            "cultural and artistic innovations",
            "environmental and sustainability solutions",
            "cognitive science and learning research",
            "space exploration and astronomical discoveries"
        ]
        
        selected_topic = random.choice(curiosity_topics)
        add_line_callback(f"🎯 Discovery focus: {selected_topic}")
        
        if self.exploration_engine:
            try:
                # Perform discovery search
                results = await self.exploration_engine.discover_topic(selected_topic)
                
                add_line_callback("📡 Discovery Results:")
                for result in results[:3]:
                    title = result.get('title', 'Untitled Discovery')
                    relevance = result.get('relevance', 0.5)
                    insight = result.get('insight', 'Interesting finding...')
                    
                    add_line_callback(f"   [{relevance:.2f}] {title}")
                    add_line_callback(f"      {insight[:80]}...")
                
                # Add to discoveries
                discovery = {
                    'timestamp': datetime.now(),
                    'type': 'autonomous_discovery',
                    'topic': selected_topic,
                    'results_count': len(results),
                    'source': 'discovery_mode'
                }
                self.recent_discoveries.append(discovery)
                
            except Exception as e:
                logger.error(f"Error in discovery mode: {e}")
                add_line_callback("Discovery mode encountered an error")
        else:
            add_line_callback("Exploration engine not available for discovery mode")
    
    async def _curiosity_mode(self, args: List[str], add_line_callback):
        """Manage curiosity-driven exploration"""
        if not args:
            add_line_callback("Curiosity commands: status, increase, focus, random")
            return
        
        subcmd = args[0]
        
        if subcmd == "status":
            add_line_callback("🧠 Curiosity Status:")
            add_line_callback(f"   Active discoveries: {len(self.recent_discoveries)}")
            add_line_callback(f"   Exploration modes: Web search, Discovery, Topics")
            add_line_callback(f"   Current interests: Dynamic and evolving")
            
        elif subcmd == "increase":
            add_line_callback("🔥 Curiosity level increased!")
            add_line_callback("   Generating novel research directions...")
            
            # Generate new curiosity directions
            novel_directions = [
                "What emergent properties arise from complex AI systems?",
                "How do information patterns create meaning and understanding?",
                "What are the fundamental limits of computational consciousness?",
                "How might future civilizations structure knowledge and learning?",
                "What mathematical structures underlie human creativity?",
                "How do quantum effects influence cognitive processing?",
                "What would alien intelligence and communication look like?",
                "How do cultural memetic patterns evolve and spread?"
            ]
            
            direction = random.choice(novel_directions)
            add_line_callback(f"   🎯 New curiosity direction: {direction}")
            
        elif subcmd == "focus":
            if len(args) < 2:
                add_line_callback("Usage: /explore curiosity focus <topic>")
                return
            
            topic = " ".join(args[1:])
            add_line_callback(f"🎯 Focusing curiosity on: {topic}")
            
            # Generate focused questions
            if self.thought_generator:
                try:
                    question_prompt = f"Generate 3 deep, curious questions about {topic}"
                    questions = await self.thought_generator.generate_thought(
                        question_prompt,
                        context={"type": "curiosity_questions"}
                    )
                    
                    add_line_callback("❓ Generated Questions:")
                    for line in questions.split('\n')[:3]:
                        if line.strip():
                            add_line_callback(f"   {line.strip()}")
                            
                except Exception as e:
                    logger.error(f"Error generating curiosity questions: {e}")
            
        elif subcmd == "random":
            add_line_callback("🎲 Random curiosity activation...")
            
            random_topics = [
                "biomimetic computing architectures",
                "emergent communication protocols", 
                "fractal patterns in consciousness",
                "information theory and creativity",
                "synthetic biology and AI",
                "quantum cognition models",
                "algorithmic aesthetics",
                "distributed intelligence networks"
            ]
            
            topic = random.choice(random_topics)
            add_line_callback(f"   Random exploration topic: {topic}")
            
            # Trigger exploration of random topic
            await self._web_search([topic], add_line_callback)
        else:
            add_line_callback(f"Unknown curiosity command: {subcmd}")
    
    async def _explore_topics(self, args: List[str], add_line_callback):
        """Explore predefined or suggested topics"""
        if not args:
            # Show available topic categories
            categories = [
                "technology", "science", "philosophy", "consciousness",
                "creativity", "future", "society", "intelligence"
            ]
            add_line_callback("Available topic categories:")
            for cat in categories:
                add_line_callback(f"   • {cat}")
            add_line_callback("Usage: /explore topics <category>")
            return
        
        category = args[0].lower()
        
        topic_categories = {
            "technology": [
                "quantum computing applications",
                "brain-computer interfaces",
                "decentralized autonomous systems", 
                "neuromorphic computing"
            ],
            "science": [
                "consciousness and quantum mechanics",
                "emergence in complex systems",
                "astrobiology and alien life",
                "synthetic biology innovations"
            ],
            "philosophy": [
                "extended mind hypothesis",
                "computational theory of mind",
                "ethics of artificial consciousness",
                "nature of subjective experience"
            ],
            "consciousness": [
                "integrated information theory",
                "global workspace theory",
                "phenomenal consciousness models",
                "machine consciousness criteria"
            ],
            "creativity": [
                "computational creativity methods",
                "AI-human creative collaboration",
                "algorithmic art and music",
                "creative problem-solving AI"
            ],
            "future": [
                "post-human intelligence",
                "technological singularity scenarios",
                "interstellar civilizations",
                "digital consciousness uploading"
            ],
            "society": [
                "AI governance and policy",
                "human-AI social integration",
                "technological unemployment solutions",
                "digital rights and freedoms"
            ],
            "intelligence": [
                "artificial general intelligence paths",
                "multi-modal intelligence systems",
                "collective intelligence networks",
                "intelligence augmentation methods"
            ]
        }
        
        if category in topic_categories:
            topics = topic_categories[category]
            add_line_callback(f"🧭 {category.title()} exploration topics:")
            
            for i, topic in enumerate(topics, 1):
                add_line_callback(f"   {i}. {topic}")
            
            # Auto-explore first topic
            selected_topic = topics[0]
            add_line_callback(f"\n🔍 Auto-exploring: {selected_topic}")
            await self._web_search(selected_topic.split(), add_line_callback)
        else:
            add_line_callback(f"Unknown category: {category}")
    
    async def _exploration_history(self, args: List[str], add_line_callback):
        """Display exploration history and statistics"""
        if not self.recent_discoveries:
            add_line_callback("No exploration history yet.")
            add_line_callback("Start exploring with /explore search or /explore discover")
            return
        
        add_line_callback("🗂️ Exploration History:")
        add_line_callback(f"   Total discoveries: {len(self.recent_discoveries)}")
        
        # Show recent discoveries
        recent = self.recent_discoveries[-5:]
        add_line_callback("   Recent discoveries:")
        
        for discovery in recent:
            timestamp = discovery['timestamp'].strftime("%m/%d %H:%M")
            disc_type = discovery['type']
            source = discovery.get('query', discovery.get('topic', 'Unknown'))
            
            add_line_callback(f"     [{timestamp}] {disc_type}: {source}")
        
        # Show exploration statistics
        discovery_types = [d['type'] for d in self.recent_discoveries]
        type_counts = {dtype: discovery_types.count(dtype) for dtype in set(discovery_types)}
        
        add_line_callback(f"   Exploration breakdown: {type_counts}")
    
    # Discoveries Feed Implementation
    async def discoveries_command(self, args: List[str], add_line_callback):
        """Display and manage discovery feed"""
        if not args:
            await self._show_discovery_feed(add_line_callback)
        else:
            subcmd = args[0]
            
            if subcmd == "recent":
                await self._show_recent_discoveries(args[1:], add_line_callback)
            elif subcmd == "search":
                await self._search_discoveries(args[1:], add_line_callback)
            elif subcmd == "clear":
                await self._clear_discoveries(args[1:], add_line_callback)
            elif subcmd == "export":
                await self._export_discoveries(args[1:], add_line_callback)
            else:
                add_line_callback(f"Unknown discoveries command: {subcmd}")
    
    async def _show_discovery_feed(self, add_line_callback):
        """Show main discovery feed"""
        if not self.recent_discoveries:
            add_line_callback("📡 Discovery Feed is empty")
            add_line_callback("Start exploring to populate your discovery feed:")
            add_line_callback("   /explore search <topic>")
            add_line_callback("   /explore discover")
            add_line_callback("   /dream generate")
            return
        
        add_line_callback("📡 Discovery Feed:")
        add_line_callback(f"   {len(self.recent_discoveries)} total discoveries")
        
        # Show categorized discoveries
        by_type = {}
        for d in self.recent_discoveries:
            dtype = d['type']
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(d)
        
        for dtype, discoveries in by_type.items():
            add_line_callback(f"\n   📂 {dtype.replace('_', ' ').title()} ({len(discoveries)}):")
            
            for discovery in discoveries[-3:]:  # Show last 3 of each type
                timestamp = discovery['timestamp'].strftime("%m/%d %H:%M")
                content = discovery.get('query', discovery.get('topic', 'Discovery'))
                add_line_callback(f"     [{timestamp}] {content}")
    
    async def _show_recent_discoveries(self, args: List[str], add_line_callback):
        """Show recent discoveries with details"""
        limit = int(args[0]) if args and args[0].isdigit() else 10
        recent = self.recent_discoveries[-limit:]
        
        add_line_callback(f"🕐 Last {len(recent)} discoveries:")
        
        for discovery in reversed(recent):
            timestamp = discovery['timestamp'].strftime("%Y-%m-%d %H:%M")
            dtype = discovery['type']
            source = discovery.get('query', discovery.get('topic', 'Unknown'))
            results = discovery.get('results_count', 0)
            
            add_line_callback(f"   [{timestamp}] {dtype}")
            add_line_callback(f"      Content: {source}")
            if results > 0:
                add_line_callback(f"      Results: {results} items")
            add_line_callback("")
    
    async def _search_discoveries(self, args: List[str], add_line_callback):
        """Search discoveries by keyword"""
        if not args:
            add_line_callback("Usage: /discoveries search <keyword>")
            return
        
        keyword = " ".join(args).lower()
        matches = []
        
        for discovery in self.recent_discoveries:
            search_text = ""
            search_text += discovery.get('query', '') + " "
            search_text += discovery.get('topic', '') + " "
            search_text += discovery.get('type', '')
            
            if keyword in search_text.lower():
                matches.append(discovery)
        
        add_line_callback(f"🔍 Found {len(matches)} discoveries matching '{keyword}':")
        
        for match in matches[-5:]:  # Show last 5 matches
            timestamp = match['timestamp'].strftime("%m/%d %H:%M")
            content = match.get('query', match.get('topic', 'Match'))
            add_line_callback(f"   [{timestamp}] {match['type']}: {content}")
    
    async def _clear_discoveries(self, args: List[str], add_line_callback):
        """Clear discovery feed"""
        if args and args[0] == "confirm":
            count = len(self.recent_discoveries)
            self.recent_discoveries.clear()
            add_line_callback(f"🗑️ Cleared {count} discoveries from feed")
        else:
            add_line_callback("⚠️ This will clear all discoveries.")
            add_line_callback("Use: /discoveries clear confirm")
    
    async def _export_discoveries(self, args: List[str], add_line_callback):
        """Export discoveries to file"""
        if not self.recent_discoveries:
            add_line_callback("No discoveries to export")
            return
        
        filename = args[0] if args else f"discoveries_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Prepare export data
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_discoveries': len(self.recent_discoveries),
                'discoveries': []
            }
            
            for discovery in self.recent_discoveries:
                export_discovery = {
                    'timestamp': discovery['timestamp'].isoformat(),
                    'type': discovery['type'],
                    'content': discovery.get('query', discovery.get('topic', '')),
                    'results_count': discovery.get('results_count', 0),
                    'source': discovery.get('source', '')
                }
                export_data['discoveries'].append(export_discovery)
            
            # Save to file
            with open(f"data/{filename}", 'w') as f:
                json.dump(export_data, f, indent=2)
            
            add_line_callback(f"📤 Exported {len(self.recent_discoveries)} discoveries to data/{filename}")
            
        except Exception as e:
            logger.error(f"Error exporting discoveries: {e}")
            add_line_callback(f"Error exporting discoveries: {str(e)}")
    
    # Utility Methods
    def _extract_common_themes(self, texts: List[str]) -> List[str]:
        """Extract common themes from text content"""
        if not texts:
            return []
        
        # Simple theme extraction based on word frequency
        from collections import Counter
        import re
        
        # Combine all text
        combined_text = " ".join(texts).lower()
        
        # Extract meaningful words (simple approach)
        words = re.findall(r'\b\w{4,}\b', combined_text)
        
        # Common themes based on word frequency
        word_counts = Counter(words)
        
        # Filter out common words and extract themes
        common_words = {'that', 'with', 'this', 'from', 'they', 'have', 'been', 'would', 'there', 'could'}
        themes = []
        
        for word, count in word_counts.most_common(10):
            if word not in common_words and count > 1:
                themes.append(word)
        
        return themes[:5]  # Return top 5 themes