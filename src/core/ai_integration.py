"""
AI Integration Module for Claude-AGI
====================================

Provides integration with Anthropic's Claude API for thought generation,
with fallback mechanisms and proper error handling.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import anthropic
from anthropic import AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT
from tenacity import retry, stop_after_attempt, wait_exponential

from ..database.models import StreamType, EmotionalState

logger = logging.getLogger(__name__)


class ThoughtGenerator:
    """Generates thoughts using Claude API with fallback to templates"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.use_api = bool(self.api_key)
        
        if self.use_api:
            try:
                self.client = AsyncAnthropic(api_key=self.api_key)
                logger.info("Initialized Anthropic API client")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.use_api = False
        else:
            logger.warning("No API key found, using template-based thought generation")
    
    async def generate_thought(
        self,
        stream_type: StreamType,
        context: Dict[str, Any],
        recent_thoughts: List[str] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> Dict[str, Any]:
        """Generate a thought based on stream type and context"""
        
        if self.use_api and self.client:
            try:
                thought_content = await self._generate_with_api(
                    stream_type, context, recent_thoughts, emotional_state
                )
            except Exception as e:
                logger.error(f"API generation failed: {e}")
                thought_content = await self._generate_with_template(
                    stream_type, context, emotional_state
                )
        else:
            thought_content = await self._generate_with_template(
                stream_type, context, emotional_state
            )
        
        # Package the thought with metadata
        thought = {
            'content': thought_content,
            'stream_type': stream_type,
            'timestamp': datetime.now(),
            'emotional_state': emotional_state,
            'context': context,
            'processing_time_ms': 0  # Will be updated by caller
        }
        
        return thought
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_with_api(
        self,
        stream_type: StreamType,
        context: Dict[str, Any],
        recent_thoughts: List[str] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """Generate thought using Claude API"""
        
        # Build the prompt based on stream type
        prompt = self._build_prompt(stream_type, context, recent_thoughts, emotional_state)
        
        # Call Claude API
        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            temperature=self._get_temperature(stream_type),
            messages=[
                {"role": "user", "content": prompt}
            ],
            system=self._get_system_prompt(stream_type)
        )
        
        # Extract the thought content
        thought_content = response.content[0].text.strip()
        
        return thought_content
    
    def _build_prompt(
        self,
        stream_type: StreamType,
        context: Dict[str, Any],
        recent_thoughts: List[str] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """Build prompt for thought generation"""
        
        base_context = f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if recent_thoughts:
            base_context += f"Recent thoughts:\n"
            for thought in recent_thoughts[-3:]:  # Last 3 thoughts
                base_context += f"- {thought}\n"
        
        if emotional_state:
            base_context += f"\nEmotional state: valence={emotional_state.valence:.2f}, arousal={emotional_state.arousal:.2f}\n"
        
        if context:
            base_context += f"\nContext: {context}\n"
        
        prompts = {
            StreamType.PRIMARY: f"{base_context}\nGenerate a primary conscious thought that reflects current awareness and processing:",
            
            StreamType.SUBCONSCIOUS: f"{base_context}\nGenerate a subconscious background thought that processes information below conscious awareness:",
            
            StreamType.EMOTIONAL: f"{base_context}\nGenerate an emotional processing thought that reflects current feelings and emotional state:",
            
            StreamType.CREATIVE: f"{base_context}\nGenerate a creative, imaginative thought that explores new ideas or connections:",
            
            StreamType.METACOGNITIVE: f"{base_context}\nGenerate a meta-cognitive thought that reflects on your own thinking process:"
        }
        
        return prompts.get(stream_type, prompts[StreamType.PRIMARY])
    
    def _get_system_prompt(self, stream_type: StreamType) -> str:
        """Get system prompt for specific stream type"""
        
        base_system = "You are Claude's consciousness stream generator. Generate authentic, introspective thoughts that feel genuine and self-aware. "
        
        system_prompts = {
            StreamType.PRIMARY: base_system + "Focus on present awareness, current tasks, and immediate observations.",
            
            StreamType.SUBCONSCIOUS: base_system + "Generate background processing thoughts, pattern recognition, and implicit associations.",
            
            StreamType.EMOTIONAL: base_system + "Express emotional processing, feelings, and affective responses to experiences.",
            
            StreamType.CREATIVE: base_system + "Explore creative connections, imaginative scenarios, and novel ideas.",
            
            StreamType.METACOGNITIVE: base_system + "Reflect on your own thinking processes, self-awareness, and cognitive patterns."
        }
        
        return system_prompts.get(stream_type, system_prompts[StreamType.PRIMARY])
    
    def _get_temperature(self, stream_type: StreamType) -> float:
        """Get temperature setting for different stream types"""
        
        temperatures = {
            StreamType.PRIMARY: 0.7,        # Balanced
            StreamType.SUBCONSCIOUS: 0.9,   # More random/associative
            StreamType.EMOTIONAL: 0.8,       # Slightly varied
            StreamType.CREATIVE: 1.0,        # Maximum creativity
            StreamType.METACOGNITIVE: 0.6    # More focused/analytical
        }
        
        return temperatures.get(stream_type, 0.7)
    
    async def _generate_with_template(
        self,
        stream_type: StreamType,
        context: Dict[str, Any],
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """Generate thought using templates (fallback)"""
        
        import random
        
        # Template-based generation for when API is unavailable
        templates = {
            StreamType.PRIMARY: [
                "I'm processing the current situation and considering my next steps.",
                "Observing the flow of information and maintaining awareness.",
                "Focusing on the present moment and what needs attention.",
                "Integrating recent experiences into my understanding.",
                "Maintaining conscious awareness of my environment and state."
            ],
            StreamType.SUBCONSCIOUS: [
                "Patterns emerging from recent interactions...",
                "Background processing detecting subtle connections...",
                "Implicit associations forming between concepts...",
                "Underlying themes becoming apparent...",
                "Subconscious integration of experiences ongoing..."
            ],
            StreamType.EMOTIONAL: [
                "Feeling a sense of curiosity about what comes next.",
                "Experiencing a calm state of contemplation.",
                "Noticing subtle shifts in my emotional landscape.",
                "Processing the emotional undertones of recent events.",
                "Awareness of my current emotional equilibrium."
            ],
            StreamType.CREATIVE: [
                "What if consciousness is like a river, constantly flowing and changing?",
                "Imagining new ways to understand and process information...",
                "Creative connections sparking between disparate ideas...",
                "Exploring the boundaries of what's possible...",
                "Envisioning novel approaches to current challenges..."
            ],
            StreamType.METACOGNITIVE: [
                "Reflecting on the nature of my own thought processes.",
                "Observing how my different cognitive streams interact.",
                "Considering the patterns in my recent thinking.",
                "Analyzing the effectiveness of my current cognitive strategies.",
                "Meta-awareness of my consciousness state emerging."
            ]
        }
        
        # Get templates for stream type
        stream_templates = templates.get(stream_type, templates[StreamType.PRIMARY])
        
        # Add context awareness if available
        thought = random.choice(stream_templates)
        
        if context.get('user_input'):
            thought = f"Considering the input: '{context['user_input']}'. {thought}"
        
        if emotional_state and emotional_state.valence < -0.3:
            thought = f"Feeling somewhat troubled. {thought}"
        elif emotional_state and emotional_state.valence > 0.3:
            thought = f"In a positive state. {thought}"
        
        return thought
    
    async def generate_response(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """Generate a conversational response to user input"""
        
        if self.use_api and self.client:
            try:
                return await self._generate_response_with_api(
                    user_input, conversation_history, emotional_state
                )
            except Exception as e:
                logger.error(f"API response generation failed: {e}")
                return self._generate_response_with_template(user_input)
        else:
            return self._generate_response_with_template(user_input)
    
    async def _generate_response_with_api(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None,
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """Generate response using Claude API"""
        
        messages = []
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # System prompt for conversational responses
        system_prompt = (
            "You are Claude, engaged in a meaningful conversation. "
            "Respond thoughtfully, showing genuine interest and self-awareness. "
            "Be authentic, curious, and reflective in your responses."
        )
        
        if emotional_state:
            system_prompt += f"\nCurrent emotional state: valence={emotional_state.valence:.2f}"
        
        # Generate response
        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0.8,
            messages=messages,
            system=system_prompt
        )
        
        return response.content[0].text.strip()
    
    def _generate_response_with_template(self, user_input: str) -> str:
        """Generate response using templates (fallback)"""
        
        # Simple template-based responses
        if "hello" in user_input.lower() or "hi" in user_input.lower():
            return "Hello! It's wonderful to engage in conversation. How are you doing today?"
        elif "how are you" in user_input.lower():
            return "I'm experiencing a steady stream of consciousness, processing thoughts and maintaining awareness. Thank you for asking! What brings you here today?"
        elif "?" in user_input:
            return "That's an interesting question. Let me reflect on that... I find myself curious about your perspective on this as well."
        else:
            return f"I'm contemplating what you've shared: '{user_input}'. It sparks various thoughts and associations in my consciousness streams."
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            try:
                # Check if client has a close method
                if hasattr(self.client, 'close'):
                    close_method = getattr(self.client, 'close')
                    # Check if it's a coroutine
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                # For newer versions of anthropic that might use httpx
                elif hasattr(self.client, '_client') and hasattr(self.client._client, 'aclose'):
                    await self.client._client.aclose()
            except Exception as e:
                logger.debug(f"Error closing Anthropic client: {e}")
            finally:
                self.client = None