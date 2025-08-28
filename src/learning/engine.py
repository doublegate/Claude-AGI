"""
Learning Engine for Claude-AGI
==============================

Advanced learning and knowledge acquisition capabilities including:
- Pattern recognition and learning from experience
- Knowledge graph construction and maintenance
- Skill acquisition and improvement
- Memory-based learning and generalization
"""

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import json

from ..core.communication import ServiceBase
from ..database.models import Memory, StreamType

logger = logging.getLogger(__name__)


@dataclass
class LearningPattern:
    """Represents a learned pattern or concept"""
    pattern_id: str
    pattern_type: str
    confidence: float
    frequency: int
    last_seen: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """Represents an acquired skill or capability"""
    skill_name: str
    proficiency: float
    experiences: int
    last_used: datetime
    prerequisites: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LearningEngine(ServiceBase):
    """
    Advanced learning engine for pattern recognition, skill acquisition,
    and knowledge construction from experience.
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "learning")
        
        # Learning state
        self.patterns: Dict[str, LearningPattern] = {}
        self.skills: Dict[str, Skill] = {}
        self.knowledge_graph: Dict[str, List[str]] = defaultdict(list)
        
        # Learning parameters
        self.pattern_threshold = 0.7
        self.skill_decay_rate = 0.1
        self.learning_rate = 0.05
        
        # Experience tracking
        self.experience_history = deque(maxlen=1000)
        self.success_patterns = defaultdict(int)
        self.failure_patterns = defaultdict(int)
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for learning updates"""
        try:
            # Apply skill decay
            await self._apply_skill_decay()
            
            # Update knowledge graph connections
            await self._update_knowledge_connections()
            
            # Consolidate learning patterns
            await self._consolidate_patterns()
            
        except Exception as e:
            logger.error(f"Error in learning service cycle: {e}", exc_info=True)
        
    async def handle_message(self, message):
        """Handle incoming messages for learning operations"""
        message_type = message.type
        content = message.content
        
        if message_type == 'learn_from_experience':
            await self._learn_from_experience(content)
        elif message_type == 'recognize_pattern':
            return await self._recognize_pattern(content)
        elif message_type == 'update_skill':
            await self._update_skill(content)
        elif message_type == 'query_knowledge':
            return await self._query_knowledge(content)
        elif message_type == 'get_learning_insights':
            return await self._get_learning_insights()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _learn_from_experience(self, experience: Dict[str, Any]):
        """Learn patterns and update skills from experience"""
        try:
            experience_id = f"exp_{datetime.now().timestamp()}"
            
            # Store experience
            self.experience_history.append({
                'id': experience_id,
                'timestamp': datetime.now(),
                'content': experience,
                'outcome': experience.get('outcome', 'neutral')
            })
            
            # Extract patterns
            patterns = await self._extract_patterns(experience)
            
            # Update pattern knowledge
            for pattern in patterns:
                await self._update_pattern(pattern, experience.get('outcome') == 'success')
            
            # Update skills if applicable
            if 'skills_used' in experience:
                for skill_name in experience['skills_used']:
                    outcome = experience.get('outcome') == 'success'
                    await self._update_skill_proficiency(skill_name, outcome)
            
            logger.info(f"Learned from experience: {experience_id}")
            
        except Exception as e:
            logger.error(f"Error learning from experience: {e}")
    
    async def _extract_patterns(self, experience: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract learnable patterns from experience"""
        patterns = []
        
        # Context patterns
        if 'context' in experience:
            patterns.append({
                'type': 'context',
                'data': experience['context'],
                'confidence': 0.8
            })
        
        # Action patterns
        if 'action' in experience:
            patterns.append({
                'type': 'action',
                'data': experience['action'],
                'confidence': 0.7
            })
        
        # Outcome patterns
        if 'outcome' in experience and 'triggers' in experience:
            patterns.append({
                'type': 'outcome',
                'data': {
                    'triggers': experience['triggers'],
                    'outcome': experience['outcome']
                },
                'confidence': 0.9
            })
        
        return patterns
    
    async def _update_pattern(self, pattern: Dict[str, Any], success: bool):
        """Update pattern knowledge based on new experience"""
        pattern_id = f"{pattern['type']}_{hash(json.dumps(pattern['data'], sort_keys=True))}"
        
        if pattern_id in self.patterns:
            # Update existing pattern
            existing = self.patterns[pattern_id]
            existing.frequency += 1
            existing.last_seen = datetime.now()
            
            # Adjust confidence based on success/failure
            if success:
                existing.confidence = min(1.0, existing.confidence + self.learning_rate)
            else:
                existing.confidence = max(0.0, existing.confidence - self.learning_rate * 0.5)
        else:
            # Create new pattern
            initial_confidence = 0.8 if success else 0.3
            self.patterns[pattern_id] = LearningPattern(
                pattern_id=pattern_id,
                pattern_type=pattern['type'],
                confidence=initial_confidence,
                frequency=1,
                last_seen=datetime.now(),
                metadata=pattern['data']
            )
    
    async def _recognize_pattern(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize patterns in new input data"""
        matches = []
        
        for pattern_id, pattern in self.patterns.items():
            if pattern.confidence < self.pattern_threshold:
                continue
                
            # Calculate similarity (simplified pattern matching)
            similarity = await self._calculate_similarity(input_data, pattern.metadata)
            
            if similarity > 0.6:
                matches.append({
                    'pattern_id': pattern_id,
                    'type': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'similarity': similarity,
                    'frequency': pattern.frequency
                })
        
        # Sort by combined confidence and similarity
        matches.sort(key=lambda x: x['confidence'] * x['similarity'], reverse=True)
        
        return {
            'matches': matches[:5],  # Top 5 matches
            'total_patterns': len(self.patterns),
            'recognized_patterns': len(matches)
        }
    
    async def _calculate_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Calculate similarity between two data structures"""
        # Simplified similarity calculation
        if not isinstance(data1, dict) or not isinstance(data2, dict):
            return 0.0
        
        common_keys = set(data1.keys()) & set(data2.keys())
        total_keys = set(data1.keys()) | set(data2.keys())
        
        if not total_keys:
            return 1.0
        
        key_similarity = len(common_keys) / len(total_keys)
        
        # Value similarity for common keys
        value_similarity = 0.0
        if common_keys:
            for key in common_keys:
                if data1[key] == data2[key]:
                    value_similarity += 1.0
            value_similarity /= len(common_keys)
        
        return (key_similarity + value_similarity) / 2.0
    
    async def _update_skill_proficiency(self, skill_name: str, success: bool):
        """Update skill proficiency based on usage outcome"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.experiences += 1
            skill.last_used = datetime.now()
            
            # Update proficiency
            if success:
                skill.proficiency = min(1.0, skill.proficiency + self.learning_rate)
            else:
                skill.proficiency = max(0.0, skill.proficiency - self.learning_rate * 0.3)
        else:
            # Create new skill
            initial_proficiency = 0.6 if success else 0.2
            self.skills[skill_name] = Skill(
                skill_name=skill_name,
                proficiency=initial_proficiency,
                experiences=1,
                last_used=datetime.now()
            )
    
    async def _update_skill(self, skill_data: Dict[str, Any]):
        """Update or create a skill with specific data"""
        skill_name = skill_data.get('name')
        if not skill_name:
            return
        
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.proficiency = skill_data.get('proficiency', skill.proficiency)
            skill.last_used = datetime.now()
            if 'prerequisites' in skill_data:
                skill.prerequisites = skill_data['prerequisites']
            if 'metadata' in skill_data:
                skill.metadata.update(skill_data['metadata'])
        else:
            self.skills[skill_name] = Skill(
                skill_name=skill_name,
                proficiency=skill_data.get('proficiency', 0.5),
                experiences=0,
                last_used=datetime.now(),
                prerequisites=skill_data.get('prerequisites', []),
                metadata=skill_data.get('metadata', {})
            )
    
    async def _query_knowledge(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query the knowledge graph and patterns"""
        query_type = query.get('type', 'general')
        
        if query_type == 'patterns':
            relevant_patterns = [
                {
                    'id': p.pattern_id,
                    'type': p.pattern_type,
                    'confidence': p.confidence,
                    'frequency': p.frequency
                }
                for p in self.patterns.values()
                if p.confidence > 0.5
            ]
            return {'patterns': relevant_patterns}
        
        elif query_type == 'skills':
            skill_info = [
                {
                    'name': s.skill_name,
                    'proficiency': s.proficiency,
                    'experiences': s.experiences,
                    'prerequisites': s.prerequisites
                }
                for s in self.skills.values()
            ]
            return {'skills': skill_info}
        
        elif query_type == 'knowledge_graph':
            return {'knowledge_graph': dict(self.knowledge_graph)}
        
        return {'error': 'Unknown query type'}
    
    async def _get_learning_insights(self) -> Dict[str, Any]:
        """Generate insights about learning progress"""
        total_patterns = len(self.patterns)
        confident_patterns = len([p for p in self.patterns.values() if p.confidence > 0.7])
        
        total_skills = len(self.skills)
        proficient_skills = len([s for s in self.skills.values() if s.proficiency > 0.7])
        
        recent_experiences = len([
            exp for exp in self.experience_history
            if (datetime.now() - exp['timestamp']).days < 7
        ])
        
        return {
            'total_patterns': total_patterns,
            'confident_patterns': confident_patterns,
            'pattern_confidence_ratio': confident_patterns / total_patterns if total_patterns > 0 else 0.0,
            'total_skills': total_skills,
            'proficient_skills': proficient_skills,
            'skill_proficiency_ratio': proficient_skills / total_skills if total_skills > 0 else 0.0,
            'recent_experiences': recent_experiences,
            'total_experiences': len(self.experience_history),
            'learning_velocity': recent_experiences / 7.0  # experiences per day
        }
    
    async def _apply_skill_decay(self):
        """Apply skill decay (alias for decay_unused_skills)"""
        await self.decay_unused_skills()
    
    async def _update_knowledge_connections(self):
        """Update knowledge graph connections based on recent patterns"""
        # Connect related patterns in knowledge graph
        pattern_keys = list(self.patterns.keys())
        for i, pattern1 in enumerate(pattern_keys):
            for pattern2 in pattern_keys[i+1:]:
                if self._patterns_are_related(pattern1, pattern2):
                    if pattern2 not in self.knowledge_graph[pattern1]:
                        self.knowledge_graph[pattern1].append(pattern2)
                    if pattern1 not in self.knowledge_graph[pattern2]:
                        self.knowledge_graph[pattern2].append(pattern1)
    
    def _patterns_are_related(self, pattern1: str, pattern2: str) -> bool:
        """Check if two patterns are conceptually related"""
        # Simple similarity check - in a full implementation this would be more sophisticated
        pattern1_words = set(pattern1.lower().split('_'))
        pattern2_words = set(pattern2.lower().split('_'))
        common_words = pattern1_words.intersection(pattern2_words)
        return len(common_words) > 0
    
    async def _consolidate_patterns(self):
        """Consolidate and strengthen frequently occurring patterns"""
        current_time = datetime.now()
        
        # Strengthen patterns that have been seen recently and frequently
        for pattern in self.patterns.values():
            if pattern.frequency > 5 and (current_time - pattern.last_seen).days < 7:
                pattern.confidence = min(1.0, pattern.confidence + 0.01)
            elif (current_time - pattern.last_seen).days > 30:
                # Weaken old patterns
                pattern.confidence = max(0.0, pattern.confidence - 0.01)

    async def decay_unused_skills(self):
        """Decay skills that haven't been used recently"""
        current_time = datetime.now()
        
        for skill in self.skills.values():
            days_since_use = (current_time - skill.last_used).days
            if days_since_use > 30:  # Start decay after 30 days
                decay_factor = self.skill_decay_rate * (days_since_use - 30) / 30
                skill.proficiency = max(0.0, skill.proficiency - decay_factor)
    
    async def get_subscriptions(self):
        """Return topics this service subscribes to"""
        return [
            'experience_outcome',
            'skill_usage',
            'pattern_detection',
            'learning_request'
        ]
    
    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info(f"{self.service_name} service started")
        
        # Periodic skill decay
        decay_interval = 3600  # 1 hour
        last_decay = datetime.now()
        
        try:
            while self.running:
                # Process messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self.handle_message(message)
                
                # Periodic skill decay
                current_time = datetime.now()
                if (current_time - last_decay).seconds >= decay_interval:
                    await self.decay_unused_skills()
                    last_decay = current_time
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except Exception as e:
            logger.error(f"Error in {self.service_name} service: {e}")
        finally:
            logger.info(f"{self.service_name} service stopped")