"""
Conversation Coordinator for Claude-AGI TUI
===========================================

Handles conversation processing, response generation, and system queries.
Extracted from TUIController to follow Single Responsibility Principle.
"""

import asyncio
import logging
import random
import re
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationCoordinator:
    """
    Coordinates conversation handling for the TUI

    Responsibilities:
    - Handle user message input
    - Generate AI responses
    - Manage conversation history
    - Handle system information queries (time, weather)
    - Validate and sanitize user input
    """

    def __init__(self, thought_generator, orchestrator, add_chat_line_callback: Callable):
        """
        Initialize conversation coordinator

        Args:
            thought_generator: ThoughtGenerator for AI responses
            orchestrator: AGI orchestrator for system queries
            add_chat_line_callback: Callback to add lines to chat pane
        """
        self.thought_generator = thought_generator
        self.orchestrator = orchestrator
        self.add_chat_line = add_chat_line_callback

        # Conversation state
        self.conversation_history = deque(maxlen=20)
        self.in_conversation = False

        # Emotional state callback
        self.current_emotional_state = None
        self.ui_update_callback: Optional[Callable] = None

    def set_emotional_state(self, emotional_state):
        """Set current emotional state for context"""
        self.current_emotional_state = emotional_state

    def set_ui_update_callback(self, callback: Callable):
        """Set callback for immediate UI updates"""
        self.ui_update_callback = callback

    async def handle_user_message(self, message: str):
        """Handle user message input with security validation"""
        try:
            # Validate and sanitize input
            if not self._validate_user_input(message):
                self.add_chat_line("Invalid input detected. Please try again with different content.")
                return

            # Sanitize the message
            sanitized_message = self._sanitize_input(message)
            if not sanitized_message:
                self.add_chat_line("Empty message after sanitization.")
                return

            # Add user message to chat
            self.add_chat_line(f"You: {sanitized_message}")

            # Force immediate UI refresh for user message (EXACT original behavior)
            if self.ui_update_callback:
                await self.ui_update_callback()

            # Add to conversation context
            self.conversation_history.append({"role": "user", "content": sanitized_message})
            self.in_conversation = True

            # Generate response
            response = await self._generate_response(sanitized_message)

            # Add response to chat
            self.add_chat_line(f"Claude: {response}")

            # Force immediate UI refresh for response (EXACT original behavior)
            if self.ui_update_callback:
                await self.ui_update_callback()

            # Add to conversation context
            self.conversation_history.append({"role": "assistant", "content": response})

        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            self.add_chat_line(f"Error processing message: Unable to handle request safely")

    async def _generate_response(self, user_input: str) -> str:
        """Generate response to user input with system information preprocessing"""
        try:
            # First check if this is a system information query
            system_info_response = await self._check_system_information_query(user_input)
            if system_info_response:
                return system_info_response

            # Use thought generator for conversation (it has generate_response method)
            if self.thought_generator and hasattr(self.thought_generator, 'generate_response'):
                # Debug: Check API configuration
                logger.debug(f"ThoughtGenerator API status: use_api={self.thought_generator.use_api}, has_client={bool(self.thought_generator.client)}")

                # Prepare conversation context properly
                history = []
                for item in self.conversation_history:
                    if isinstance(item, dict) and 'role' in item:
                        history.append(item)
                    else:
                        # Convert old format to proper conversation format
                        history.append({
                            "role": "user" if str(item).startswith("You:") else "assistant",
                            "content": str(item).replace("You: ", "").replace("Claude: ", ""),
                            "timestamp": datetime.now().isoformat()
                        })

                try:
                    logger.debug(f"Attempting to generate response for: {user_input[:50]}...")
                    response = await self.thought_generator.generate_response(
                        user_input=user_input,
                        conversation_history=history,
                        emotional_state=self.current_emotional_state
                    )
                    if response:
                        logger.debug(f"Generated response: {response[:50]}...")
                        return response
                    else:
                        logger.warning("AI response generation returned empty response")
                except Exception as e:
                    logger.error(f"AI response generation failed with exception: {e}")
                    # Add to chat to show the error to user for debugging
                    self.add_chat_line(f"SYSTEM: Error generating response - {str(e)}")

            # Fallback response if AI fails
            fallback_responses = [
                "That's an interesting point. Let me think about it.",
                "I understand what you're saying. Could you tell me more?",
                "I'm processing your input and considering various perspectives.",
                "Thank you for sharing that with me. What would you like to explore further?",
                "I appreciate your question. Let me reflect on that."
            ]

            return random.choice(fallback_responses)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble processing that right now, but I'm here and listening."

    async def _check_system_information_query(self, user_input: str) -> Optional[str]:
        """Check if query requires system information and handle it accordingly"""
        user_input_lower = user_input.lower()

        # Check for time/date queries
        time_patterns = [
            'what time is it', 'current time', 'what\'s the time', 'time now',
            'what date is it', 'current date', 'what\'s the date', 'today\'s date',
            'what day is it', 'what day', 'day of the week'
        ]

        if any(pattern in user_input_lower for pattern in time_patterns):
            return await self._handle_time_query()

        # Check for weather queries
        weather_patterns = [
            'weather', 'temperature', 'forecast', 'climate', 'rain', 'snow',
            'sunny', 'cloudy', 'humid', 'wind'
        ]

        if any(pattern in user_input_lower for pattern in weather_patterns):
            location = self._extract_location_from_query(user_input)
            if location:
                return await self._handle_weather_query(location)
            else:
                return "I can help you with weather information! Please specify a location, for example: 'What's the weather in New York?' or 'Tell me the temperature in London.'"

        return None  # No system information query detected

    async def _handle_time_query(self) -> str:
        """Handle time/date queries by calling WebExplorer service"""
        try:
            if self.orchestrator and 'explorer' in self.orchestrator.services:
                explorer = self.orchestrator.services['explorer']
                time_data = await explorer.get_system_time()

                if time_data.get('success'):
                    return (f"The current time is {time_data['current_time']} on {time_data['day_of_week']}. "
                           f"Today's date is {time_data['date']}.")
                else:
                    error_msg = time_data.get('error', 'Unknown error')
                    return f"I'm having trouble accessing the system time right now: {error_msg}"
            else:
                return "I don't have access to the system time service at the moment."

        except Exception as e:
            logger.error(f"Error handling time query: {e}")
            return "I encountered an error while trying to get the current time. Please try again."

    async def _handle_weather_query(self, location: str) -> str:
        """Handle weather queries by calling WebExplorer service"""
        try:
            if self.orchestrator and 'explorer' in self.orchestrator.services:
                explorer = self.orchestrator.services['explorer']
                weather_data = await explorer.get_weather_info(location)

                if weather_data.get('success'):
                    temp = weather_data['temperature']
                    feels_like = weather_data['feels_like']
                    description = weather_data['description']
                    humidity = weather_data['humidity']
                    location_name = weather_data['location']

                    return (f"The weather in {location_name} is currently {description.lower()} "
                           f"with a temperature of {temp}°C (feels like {feels_like}°C). "
                           f"The humidity is {humidity}%.")
                else:
                    error_msg = weather_data.get('error', 'Unknown error')
                    return f"I couldn't get weather information: {error_msg}"
            else:
                return "I don't have access to the weather service at the moment."

        except Exception as e:
            logger.error(f"Error handling weather query: {e}")
            return "I encountered an error while trying to get weather information. Please try again."

    def _extract_location_from_query(self, user_input: str) -> Optional[str]:
        """Extract location from weather query"""
        # Look for "weather in [location]" patterns
        patterns = [
            r'weather (?:in|for|at) ([^?]+)',
            r'temperature (?:in|for|at) ([^?]+)',
            r'forecast (?:in|for|at) ([^?]+)',
            r'climate (?:in|for|of) ([^?]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                location = match.group(1).strip()
                # Clean up common punctuation
                location = re.sub(r'[?.!,]$', '', location)
                return location

        # Look for location at the end of the query
        location_pattern = r'(?:weather|temperature|forecast|climate)\s+(.+?)(?:\?|$)'
        match = re.search(location_pattern, user_input.lower())
        if match:
            location = match.group(1).strip()
            # Remove common words
            location = re.sub(r'^(?:in|for|at|of)\s+', '', location)
            location = re.sub(r'[?.!,]$', '', location)
            if location and len(location) > 1:
                return location

        return None

    def _validate_user_input(self, user_input: str) -> bool:
        """Validate user input for security and safety"""
        if not user_input or not isinstance(user_input, str):
            return False

        # Check input length limits (prevent buffer overflow)
        if len(user_input) > 1000:
            logger.warning(f"Input too long: {len(user_input)} characters")
            return False

        # Check for potential command injection patterns
        dangerous_patterns = [
            r'[;&|`$]',  # Command separators and shell metacharacters
            r'\.\.\/',    # Path traversal attempts
            r'<script',  # Script injection attempts
            r'javascript:', # JavaScript protocol
            r'data:',    # Data URLs
            r'file://',  # File protocol
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Potentially dangerous input detected: {user_input[:50]}...")
                return False

        return True

    def _sanitize_input(self, user_input: str) -> str:
        """Sanitize user input by removing or escaping dangerous characters"""
        if not user_input:
            return ""

        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', user_input)

        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())

        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."

        return sanitized
