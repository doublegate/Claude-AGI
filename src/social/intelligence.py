"""
Social Intelligence for Claude-AGI
==================================

Advanced social reasoning and interaction capabilities including:
- Social relationship modeling and tracking
- Emotional intelligence in social contexts
- Communication style adaptation
- Social norm understanding and adherence
"""

import asyncio
import logging
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import json

from ..core.communication import ServiceBase
from ..database.models import Memory, StreamType

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of social relationships"""
    FRIEND = "friend"
    FAMILY = "family"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"
    STUDENT = "student"
    ACQUAINTANCE = "acquaintance"
    PROFESSIONAL = "professional"
    COLLABORATIVE = "collaborative"


class CommunicationStyle(str, Enum):
    """Different communication styles"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"
    DIRECT = "direct"
    DIPLOMATIC = "diplomatic"
    PLAYFUL = "playful"
    SUPPORTIVE = "supportive"


class SocialContext(str, Enum):
    """Different social contexts"""
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    PERSONAL = "personal"
    CREATIVE = "creative"
    THERAPEUTIC = "therapeutic"
    EDUCATIONAL = "educational"
    CASUAL = "casual"


@dataclass
class SocialEntity:
    """Represents a social entity (person, group, organization)"""
    entity_id: str
    name: str
    entity_type: str  # person, group, organization
    relationship_type: Optional[RelationshipType] = None
    preferred_communication_style: Optional[CommunicationStyle] = None
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    personality_traits: Dict[str, float] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    communication_patterns: Dict[str, Any] = field(default_factory=dict)
    last_interaction: Optional[datetime] = None
    relationship_strength: float = 0.5
    trust_level: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SocialInteraction:
    """Represents a social interaction"""
    interaction_id: str
    entities: List[str]  # Entity IDs involved
    context: SocialContext
    interaction_type: str  # conversation, collaboration, etc.
    content_summary: str
    sentiment: float  # -1 to 1
    success_rating: float  # 0 to 1
    communication_style_used: CommunicationStyle
    timestamp: datetime = field(default_factory=datetime.now)
    duration_minutes: Optional[float] = None
    outcomes: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)


@dataclass
class SocialNorm:
    """Represents a social norm or rule"""
    norm_id: str
    context: SocialContext
    description: str
    importance: float  # 0 to 1
    adherence_examples: List[str] = field(default_factory=list)
    violation_consequences: List[str] = field(default_factory=list)
    cultural_variations: Dict[str, str] = field(default_factory=dict)


class SocialIntelligence(ServiceBase):
    """
    Advanced social intelligence for relationship management,
    communication adaptation, and social norm understanding.
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "social")
        
        # Social state
        self.social_entities: Dict[str, SocialEntity] = {}
        self.interactions: Dict[str, SocialInteraction] = {}
        self.social_norms: Dict[str, SocialNorm] = {}
        
        # Social parameters
        self.relationship_decay_rate = 0.01
        self.trust_adjustment_rate = 0.05
        self.communication_adaptation_threshold = 0.7
        
        # Analytics and tracking
        self.interaction_history = deque(maxlen=1000)
        self.relationship_networks: Dict[str, Set[str]] = defaultdict(set)
        self.communication_success_patterns: Dict[str, List[float]] = defaultdict(list)
        self.social_learning_insights: List[Dict[str, Any]] = []
        
        # Initialize base social norms
        self._initialize_social_norms()
    
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['social_interaction', 'communication_request', 'relationship_update', 'norm_violation']
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for social intelligence updates"""
        try:
            # Update relationships
            await self._update_relationships()
            
            # Analyze communication patterns
            await self._analyze_communication_patterns()
            
            # Update social norms
            await self._update_social_norms()
            
            # Generate social insights
            await self._generate_social_insights()
            
        except Exception as e:
            logger.error(f"Error in social intelligence service cycle: {e}", exc_info=True)
        
    async def handle_message(self, message):
        """Handle incoming messages for social intelligence operations"""
        message_type = message.type
        content = message.content
        
        if message_type == 'analyze_social_context':
            return await self._analyze_social_context(content)
        elif message_type == 'adapt_communication_style':
            return await self._adapt_communication_style(content)
        elif message_type == 'record_interaction':
            return await self._record_interaction(content)
        elif message_type == 'get_relationship_status':
            return await self._get_relationship_status(content)
        elif message_type == 'update_social_entity':
            return await self._update_social_entity(content)
        elif message_type == 'assess_social_appropriateness':
            return await self._assess_social_appropriateness(content)
        elif message_type == 'get_social_insights':
            return await self._get_social_insights()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def _initialize_social_norms(self):
        """Initialize basic social norms"""
        base_norms = [
            {
                'context': SocialContext.PROFESSIONAL,
                'description': 'Maintain professional boundaries and respect hierarchy',
                'importance': 0.9,
                'adherence_examples': ['Use formal titles', 'Respect meeting protocols', 'Keep personal topics minimal']
            },
            {
                'context': SocialContext.PERSONAL,
                'description': 'Show genuine interest and empathy in personal conversations',
                'importance': 0.8,
                'adherence_examples': ['Listen actively', 'Share appropriately', 'Respect privacy']
            },
            {
                'context': SocialContext.ACADEMIC,
                'description': 'Encourage intellectual discourse and respect different viewpoints',
                'importance': 0.8,
                'adherence_examples': ['Cite sources', 'Ask clarifying questions', 'Build on ideas constructively']
            },
            {
                'context': SocialContext.CREATIVE,
                'description': 'Foster open expression and constructive feedback',
                'importance': 0.7,
                'adherence_examples': ['Encourage experimentation', 'Provide supportive criticism', 'Share inspiration']
            },
            {
                'context': SocialContext.THERAPEUTIC,
                'description': 'Create safe space and maintain confidentiality',
                'importance': 1.0,
                'adherence_examples': ['Non-judgmental listening', 'Respect boundaries', 'Maintain confidentiality']
            }
        ]
        
        for i, norm_data in enumerate(base_norms):
            norm_id = f"norm_{i+1}"
            norm = SocialNorm(
                norm_id=norm_id,
                context=norm_data['context'],
                description=norm_data['description'],
                importance=norm_data['importance'],
                adherence_examples=norm_data['adherence_examples']
            )
            self.social_norms[norm_id] = norm
    
    async def _analyze_social_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the social context of a situation"""
        entities_present = request.get('entities', [])
        situation_description = request.get('situation', '')
        explicit_context = request.get('context')
        
        # Determine context if not explicit
        if explicit_context:
            context = SocialContext(explicit_context)
        else:
            context = await self._infer_social_context(situation_description, entities_present)
        
        # Get relevant social norms
        relevant_norms = [
            norm for norm in self.social_norms.values()
            if norm.context == context or norm.context == SocialContext.CASUAL
        ]
        
        # Analyze relationships between entities
        relationship_dynamics = {}
        if len(entities_present) > 1:
            for entity_id in entities_present:
                if entity_id in self.social_entities:
                    entity = self.social_entities[entity_id]
                    relationship_dynamics[entity_id] = {
                        'name': entity.name,
                        'relationship_type': entity.relationship_type,
                        'relationship_strength': entity.relationship_strength,
                        'trust_level': entity.trust_level,
                        'preferred_style': entity.preferred_communication_style
                    }
        
        # Recommend communication approach
        communication_recommendations = await self._generate_communication_recommendations(
            context, entities_present, situation_description
        )
        
        return {
            'context': context.value,
            'context_confidence': 0.8,  # Would be calculated in real implementation
            'relevant_norms': [
                {
                    'description': norm.description,
                    'importance': norm.importance,
                    'examples': norm.adherence_examples
                }
                for norm in relevant_norms
            ],
            'relationship_dynamics': relationship_dynamics,
            'communication_recommendations': communication_recommendations,
            'risk_factors': await self._identify_social_risks(context, entities_present, situation_description)
        }
    
    async def _infer_social_context(self, situation: str, entities: List[str]) -> SocialContext:
        """Infer social context from situation description"""
        situation_lower = situation.lower()
        
        # Context keywords
        context_indicators = {
            SocialContext.PROFESSIONAL: ['work', 'meeting', 'business', 'project', 'deadline', 'client'],
            SocialContext.ACADEMIC: ['research', 'study', 'paper', 'thesis', 'conference', 'lecture'],
            SocialContext.PERSONAL: ['friend', 'family', 'personal', 'private', 'relationship'],
            SocialContext.CREATIVE: ['creative', 'art', 'design', 'music', 'writing', 'brainstorm'],
            SocialContext.THERAPEUTIC: ['support', 'help', 'problem', 'stress', 'emotional', 'therapy'],
            SocialContext.EDUCATIONAL: ['learn', 'teach', 'explain', 'understand', 'knowledge', 'skill']
        }
        
        # Score each context
        context_scores = {}
        for context, keywords in context_indicators.items():
            score = sum(1 for keyword in keywords if keyword in situation_lower)
            if score > 0:
                context_scores[context] = score
        
        # Return highest scoring context, or casual as default
        if context_scores:
            return max(context_scores.items(), key=lambda x: x[1])[0]
        else:
            return SocialContext.CASUAL
    
    async def _generate_communication_recommendations(self, context: SocialContext, 
                                                    entities: List[str], 
                                                    situation: str) -> Dict[str, Any]:
        """Generate communication style recommendations"""
        # Base recommendations by context
        context_styles = {
            SocialContext.PROFESSIONAL: [CommunicationStyle.FORMAL, CommunicationStyle.DIRECT],
            SocialContext.ACADEMIC: [CommunicationStyle.TECHNICAL, CommunicationStyle.DIPLOMATIC],
            SocialContext.PERSONAL: [CommunicationStyle.EMPATHETIC, CommunicationStyle.CASUAL],
            SocialContext.CREATIVE: [CommunicationStyle.PLAYFUL, CommunicationStyle.SUPPORTIVE],
            SocialContext.THERAPEUTIC: [CommunicationStyle.EMPATHETIC, CommunicationStyle.SUPPORTIVE],
            SocialContext.EDUCATIONAL: [CommunicationStyle.SUPPORTIVE, CommunicationStyle.TECHNICAL],
            SocialContext.CASUAL: [CommunicationStyle.CASUAL, CommunicationStyle.PLAYFUL]
        }
        
        recommended_styles = context_styles.get(context, [CommunicationStyle.CASUAL])
        
        # Adjust for specific entities if known
        entity_preferences = []
        for entity_id in entities:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                if entity.preferred_communication_style:
                    entity_preferences.append(entity.preferred_communication_style)
        
        # If entities have style preferences, consider them
        if entity_preferences:
            # Find most common preference
            style_counts = {}
            for style in entity_preferences:
                style_counts[style] = style_counts.get(style, 0) + 1
            
            most_preferred = max(style_counts.items(), key=lambda x: x[1])[0]
            if most_preferred not in recommended_styles:
                recommended_styles.insert(0, most_preferred)
        
        return {
            'primary_style': recommended_styles[0].value if recommended_styles else CommunicationStyle.CASUAL.value,
            'alternative_styles': [style.value for style in recommended_styles[1:3]],
            'style_rationale': f"Based on {context.value} context and entity preferences",
            'communication_tips': await self._get_communication_tips(recommended_styles[0] if recommended_styles else CommunicationStyle.CASUAL)
        }
    
    async def _get_communication_tips(self, style: CommunicationStyle) -> List[str]:
        """Get tips for a specific communication style"""
        tips = {
            CommunicationStyle.FORMAL: [
                "Use professional language and titles",
                "Structure communication clearly with agenda",
                "Maintain respectful tone throughout",
                "Be concise and focused on objectives"
            ],
            CommunicationStyle.CASUAL: [
                "Use conversational tone",
                "Include some personal elements",
                "Be flexible with structure",
                "Show enthusiasm and personality"
            ],
            CommunicationStyle.TECHNICAL: [
                "Use precise terminology",
                "Provide detailed explanations",
                "Support points with data/evidence",
                "Encourage questions and clarification"
            ],
            CommunicationStyle.EMPATHETIC: [
                "Listen actively and acknowledge feelings",
                "Use supportive language",
                "Validate experiences and perspectives",
                "Offer appropriate emotional support"
            ],
            CommunicationStyle.DIRECT: [
                "Be clear and straightforward",
                "State objectives upfront",
                "Avoid ambiguity",
                "Focus on facts and decisions"
            ],
            CommunicationStyle.DIPLOMATIC: [
                "Consider all perspectives",
                "Use tactful language",
                "Find common ground",
                "Build consensus gradually"
            ],
            CommunicationStyle.PLAYFUL: [
                "Include humor appropriately",
                "Be creative with expressions",
                "Encourage fun interactions",
                "Keep atmosphere light"
            ],
            CommunicationStyle.SUPPORTIVE: [
                "Encourage participation",
                "Provide positive reinforcement",
                "Offer help and resources",
                "Create safe space for expression"
            ]
        }
        
        return tips.get(style, ["Adapt to the social context", "Be authentic and respectful"])
    
    async def _identify_social_risks(self, context: SocialContext, entities: List[str], 
                                   situation: str) -> List[Dict[str, str]]:
        """Identify potential social risks in the situation"""
        risks = []
        
        # Context-specific risks
        if context == SocialContext.PROFESSIONAL:
            if 'conflict' in situation.lower() or 'disagreement' in situation.lower():
                risks.append({
                    'type': 'professional_conflict',
                    'description': 'Workplace conflict may affect professional relationships',
                    'mitigation': 'Focus on facts, maintain professionalism, seek mediation if needed'
                })
        
        if context == SocialContext.PERSONAL:
            if len(entities) > 2:
                risks.append({
                    'type': 'group_dynamics',
                    'description': 'Complex personal group dynamics may lead to exclusion',
                    'mitigation': 'Ensure everyone feels included and heard'
                })
        
        # Relationship-based risks
        low_trust_entities = [
            entity_id for entity_id in entities
            if entity_id in self.social_entities and self.social_entities[entity_id].trust_level < 0.5
        ]
        
        if low_trust_entities:
            risks.append({
                'type': 'trust_issues',
                'description': 'Low trust levels may impede effective communication',
                'mitigation': 'Build trust through consistency, transparency, and reliability'
            })
        
        return risks
    
    async def _adapt_communication_style(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt communication style for specific context and entities"""
        target_entities = request.get('entities', [])
        current_style = CommunicationStyle(request.get('current_style', 'casual'))
        context = SocialContext(request.get('context', 'casual'))
        message_content = request.get('message', '')
        
        # Analyze target entities
        entity_analysis = {}
        for entity_id in target_entities:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                entity_analysis[entity_id] = {
                    'preferred_style': entity.preferred_communication_style,
                    'relationship_strength': entity.relationship_strength,
                    'communication_patterns': entity.communication_patterns
                }
        
        # Determine optimal style
        optimal_style = await self._calculate_optimal_style(
            current_style, context, entity_analysis, message_content
        )
        
        # Generate adaptation suggestions
        adaptations = await self._generate_style_adaptations(
            current_style, optimal_style, message_content
        )
        
        return {
            'current_style': current_style.value,
            'recommended_style': optimal_style.value,
            'adaptation_needed': current_style != optimal_style,
            'entity_analysis': entity_analysis,
            'adaptations': adaptations,
            'confidence': 0.8  # Would be calculated based on data quality
        }
    
    async def _calculate_optimal_style(self, current_style: CommunicationStyle,
                                     context: SocialContext,
                                     entity_analysis: Dict[str, Any],
                                     message: str) -> CommunicationStyle:
        """Calculate the optimal communication style"""
        # Get context-appropriate styles
        context_analysis = await self._generate_communication_recommendations(
            context, list(entity_analysis.keys()), message
        )
        
        recommended_style = CommunicationStyle(context_analysis['primary_style'])
        
        # Adjust for entity preferences
        if entity_analysis:
            preferred_styles = [
                info['preferred_style'] for info in entity_analysis.values()
                if info['preferred_style']
            ]
            
            if preferred_styles:
                # Weight by relationship strength
                style_weights = {}
                for entity_id, info in entity_analysis.items():
                    if info['preferred_style']:
                        style = info['preferred_style']
                        weight = info['relationship_strength']
                        style_weights[style] = style_weights.get(style, 0) + weight
                
                if style_weights:
                    best_weighted_style = max(style_weights.items(), key=lambda x: x[1])[0]
                    return best_weighted_style
        
        return recommended_style
    
    async def _generate_style_adaptations(self, current_style: CommunicationStyle,
                                        optimal_style: CommunicationStyle,
                                        message: str) -> List[Dict[str, str]]:
        """Generate specific adaptations to move from current to optimal style"""
        if current_style == optimal_style:
            return [{'type': 'no_change', 'description': 'Current style is optimal'}]
        
        adaptations = []
        
        # Style-specific adaptations
        style_transitions = {
            (CommunicationStyle.CASUAL, CommunicationStyle.FORMAL): [
                {'type': 'formality', 'description': 'Use more formal language and titles'},
                {'type': 'structure', 'description': 'Add clear structure and agenda'},
                {'type': 'tone', 'description': 'Adopt professional tone'}
            ],
            (CommunicationStyle.FORMAL, CommunicationStyle.CASUAL): [
                {'type': 'relaxation', 'description': 'Use more conversational language'},
                {'type': 'personal', 'description': 'Add some personal elements'},
                {'type': 'flexibility', 'description': 'Be more flexible with structure'}
            ],
            (CommunicationStyle.DIRECT, CommunicationStyle.DIPLOMATIC): [
                {'type': 'tact', 'description': 'Use more tactful language'},
                {'type': 'perspective', 'description': 'Acknowledge multiple viewpoints'},
                {'type': 'consensus', 'description': 'Focus on building agreement'}
            ],
            (CommunicationStyle.TECHNICAL, CommunicationStyle.EMPATHETIC): [
                {'type': 'emotion', 'description': 'Acknowledge emotional aspects'},
                {'type': 'support', 'description': 'Offer emotional support'},
                {'type': 'validation', 'description': 'Validate feelings and experiences'}
            ]
        }
        
        specific_adaptations = style_transitions.get((current_style, optimal_style))
        if specific_adaptations:
            adaptations.extend(specific_adaptations)
        else:
            # Generic adaptation
            adaptations.append({
                'type': 'general',
                'description': f'Adjust communication from {current_style.value} to {optimal_style.value} approach'
            })
        
        return adaptations
    
    async def _record_interaction(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Record a social interaction"""
        interaction_id = f"interaction_{datetime.now().timestamp()}"
        entities = request.get('entities', [])
        context = SocialContext(request.get('context', 'casual'))
        interaction_type = request.get('type', 'conversation')
        content_summary = request.get('summary', '')
        sentiment = request.get('sentiment', 0.0)
        success_rating = request.get('success_rating', 0.5)
        style_used = CommunicationStyle(request.get('style_used', 'casual'))
        duration_minutes = request.get('duration_minutes')
        
        # Create interaction record
        interaction = SocialInteraction(
            interaction_id=interaction_id,
            entities=entities,
            context=context,
            interaction_type=interaction_type,
            content_summary=content_summary,
            sentiment=sentiment,
            success_rating=success_rating,
            communication_style_used=style_used,
            duration_minutes=duration_minutes,
            outcomes=request.get('outcomes', []),
            lessons_learned=request.get('lessons_learned', [])
        )
        
        self.interactions[interaction_id] = interaction
        self.interaction_history.append(interaction)
        
        # Update entity relationships
        for entity_id in entities:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                
                # Update interaction history
                entity.interaction_history.append({
                    'interaction_id': interaction_id,
                    'timestamp': interaction.timestamp.isoformat(),
                    'sentiment': sentiment,
                    'success_rating': success_rating,
                    'context': context.value
                })
                
                # Update relationship strength and trust
                if success_rating > 0.7:
                    entity.relationship_strength = min(1.0, entity.relationship_strength + 0.05)
                    entity.trust_level = min(1.0, entity.trust_level + 0.03)
                elif success_rating < 0.3:
                    entity.relationship_strength = max(0.0, entity.relationship_strength - 0.05)
                    entity.trust_level = max(0.0, entity.trust_level - 0.02)
                
                entity.last_interaction = interaction.timestamp
        
        # Track communication success patterns
        style_key = f"{style_used.value}_{context.value}"
        self.communication_success_patterns[style_key].append(success_rating)
        
        return {
            'interaction_id': interaction_id,
            'status': 'recorded',
            'entities_updated': len([e for e in entities if e in self.social_entities]),
            'relationship_changes': await self._calculate_relationship_changes(entities, success_rating)
        }
    
    async def _calculate_relationship_changes(self, entities: List[str], 
                                           success_rating: float) -> Dict[str, Dict[str, float]]:
        """Calculate how relationships changed after interaction"""
        changes = {}
        
        for entity_id in entities:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                
                # Calculate expected changes (simplified)
                strength_change = 0.05 if success_rating > 0.7 else (-0.05 if success_rating < 0.3 else 0)
                trust_change = 0.03 if success_rating > 0.7 else (-0.02 if success_rating < 0.3 else 0)
                
                changes[entity_id] = {
                    'relationship_strength_change': strength_change,
                    'trust_level_change': trust_change,
                    'new_relationship_strength': min(1.0, max(0.0, entity.relationship_strength + strength_change)),
                    'new_trust_level': min(1.0, max(0.0, entity.trust_level + trust_change))
                }
        
        return changes
    
    async def _get_relationship_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get relationship status with specific entities"""
        entity_ids = request.get('entities', [])
        
        if not entity_ids:
            # Return summary of all relationships
            return {
                'total_entities': len(self.social_entities),
                'relationship_summary': {
                    rel_type.value: len([
                        e for e in self.social_entities.values()
                        if e.relationship_type == rel_type
                    ])
                    for rel_type in RelationshipType
                },
                'average_relationship_strength': sum(
                    e.relationship_strength for e in self.social_entities.values()
                ) / len(self.social_entities) if self.social_entities else 0.0
            }
        
        # Return specific entity relationships
        relationships = {}
        for entity_id in entity_ids:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                relationships[entity_id] = {
                    'name': entity.name,
                    'relationship_type': entity.relationship_type.value if entity.relationship_type else None,
                    'relationship_strength': entity.relationship_strength,
                    'trust_level': entity.trust_level,
                    'last_interaction': entity.last_interaction.isoformat() if entity.last_interaction else None,
                    'total_interactions': len(entity.interaction_history),
                    'preferred_communication_style': entity.preferred_communication_style.value if entity.preferred_communication_style else None,
                    'interests': entity.interests
                }
        
        return {
            'relationships': relationships,
            'total_requested': len(entity_ids),
            'found': len(relationships)
        }
    
    async def _update_social_entity(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Update or create a social entity"""
        entity_id = request.get('entity_id')
        name = request.get('name')
        
        if not entity_id or not name:
            return {'error': 'Entity ID and name required'}
        
        # Get or create entity
        if entity_id in self.social_entities:
            entity = self.social_entities[entity_id]
        else:
            entity = SocialEntity(
                entity_id=entity_id,
                name=name,
                entity_type=request.get('entity_type', 'person')
            )
            self.social_entities[entity_id] = entity
        
        # Update fields if provided
        if 'relationship_type' in request:
            entity.relationship_type = RelationshipType(request['relationship_type'])
        
        if 'preferred_communication_style' in request:
            entity.preferred_communication_style = CommunicationStyle(request['preferred_communication_style'])
        
        if 'interests' in request:
            entity.interests = request['interests']
        
        if 'personality_traits' in request:
            entity.personality_traits.update(request['personality_traits'])
        
        return {
            'entity_id': entity_id,
            'name': entity.name,
            'status': 'updated',
            'relationship_type': entity.relationship_type.value if entity.relationship_type else None,
            'preferred_style': entity.preferred_communication_style.value if entity.preferred_communication_style else None
        }
    
    async def _assess_social_appropriateness(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess social appropriateness of planned communication"""
        message_content = request.get('message', '')
        context = SocialContext(request.get('context', 'casual'))
        target_entities = request.get('entities', [])
        proposed_style = CommunicationStyle(request.get('style', 'casual'))
        
        # Get relevant social norms
        relevant_norms = [norm for norm in self.social_norms.values() if norm.context == context]
        
        # Assess appropriateness
        appropriateness_score = 0.8  # Base score
        concerns = []
        recommendations = []
        
        # Check against social norms
        for norm in relevant_norms:
            # Simplified norm checking (in real implementation, would use NLP)
            if norm.importance > 0.8:  # High importance norms
                if 'professional' in norm.description.lower() and context == SocialContext.PROFESSIONAL:
                    if proposed_style in [CommunicationStyle.CASUAL, CommunicationStyle.PLAYFUL]:
                        appropriateness_score -= 0.2
                        concerns.append(f"Style may be too casual for {context.value} context")
                        recommendations.append("Consider using more formal communication style")
        
        # Check entity compatibility
        for entity_id in target_entities:
            if entity_id in self.social_entities:
                entity = self.social_entities[entity_id]
                if entity.preferred_communication_style and entity.preferred_communication_style != proposed_style:
                    if entity.relationship_strength > 0.7:  # Strong relationship
                        appropriateness_score -= 0.1
                        recommendations.append(f"Consider adapting to {entity.name}'s preferred {entity.preferred_communication_style.value} style")
        
        return {
            'appropriateness_score': max(0.0, min(1.0, appropriateness_score)),
            'assessment': 'appropriate' if appropriateness_score > 0.7 else ('concerning' if appropriateness_score < 0.4 else 'acceptable'),
            'concerns': concerns,
            'recommendations': recommendations,
            'relevant_norms': [
                {
                    'description': norm.description,
                    'importance': norm.importance
                }
                for norm in relevant_norms
            ]
        }
    
    async def _get_social_insights(self) -> Dict[str, Any]:
        """Generate insights about social interactions and relationships"""
        total_entities = len(self.social_entities)
        total_interactions = len(self.interactions)
        
        # Relationship type distribution
        relationship_distribution = {}
        for entity in self.social_entities.values():
            rel_type = entity.relationship_type.value if entity.relationship_type else 'unknown'
            relationship_distribution[rel_type] = relationship_distribution.get(rel_type, 0) + 1
        
        # Communication style success rates
        style_success = {}
        for style_context, success_rates in self.communication_success_patterns.items():
            if success_rates:
                avg_success = sum(success_rates) / len(success_rates)
                style_success[style_context] = {
                    'average_success': avg_success,
                    'interaction_count': len(success_rates)
                }
        
        # Recent interaction trends
        recent_interactions = [
            interaction for interaction in self.interaction_history
            if (datetime.now() - interaction.timestamp).days < 7
        ]
        
        return {
            'total_social_entities': total_entities,
            'total_interactions_recorded': total_interactions,
            'recent_interactions_count': len(recent_interactions),
            'relationship_type_distribution': relationship_distribution,
            'communication_style_success_rates': style_success,
            'average_relationship_strength': sum(
                e.relationship_strength for e in self.social_entities.values()
            ) / total_entities if total_entities > 0 else 0.0,
            'average_trust_level': sum(
                e.trust_level for e in self.social_entities.values()
            ) / total_entities if total_entities > 0 else 0.0,
            'social_norms_count': len(self.social_norms),
            'relationship_network_size': sum(len(connections) for connections in self.relationship_networks.values())
        }
    
    async def relationship_maintenance(self):
        """Perform periodic relationship maintenance"""
        current_time = datetime.now()
        
        for entity in self.social_entities.values():
            if entity.last_interaction:
                days_since_last = (current_time - entity.last_interaction).days
                
                # Decay relationship strength for inactive relationships
                if days_since_last > 30:  # After 30 days of no interaction
                    decay_factor = self.relationship_decay_rate * (days_since_last - 30)
                    entity.relationship_strength = max(0.0, entity.relationship_strength - decay_factor)
                    entity.trust_level = max(0.0, entity.trust_level - decay_factor * 0.5)
    
    async def _update_relationships(self):
        """Update relationship states (alias for relationship_maintenance)"""
        await self.relationship_maintenance()
    
    async def _analyze_communication_patterns(self):
        """Analyze communication patterns for adaptation"""
        # Analyze recent interactions for patterns
        if len(self.interaction_history) > 10:
            recent_interactions = list(self.interaction_history)[-20:]
            
            # Track success patterns by communication style
            for interaction in recent_interactions:
                style = interaction.get('communication_style', 'default')
                success = interaction.get('success_rating', 0.5)
                self.communication_success_patterns[style].append(success)
                
                # Keep only recent patterns
                if len(self.communication_success_patterns[style]) > 50:
                    self.communication_success_patterns[style] = self.communication_success_patterns[style][-50:]
    
    async def _update_social_norms(self):
        """Update social norms based on observed patterns"""
        # Update social norms based on successful interaction patterns
        for norm in self.social_norms.values():
            # Strengthen norms that lead to positive interactions
            norm.confidence = min(1.0, norm.confidence + 0.01)
    
    async def _generate_social_insights(self):
        """Generate insights about social patterns"""
        if len(self.social_entities) > 0:
            avg_trust = sum(entity.trust_level for entity in self.social_entities.values()) / len(self.social_entities)
            avg_relationship = sum(entity.relationship_strength for entity in self.social_entities.values()) / len(self.social_entities)
            
            insight = {
                'timestamp': datetime.now(),
                'average_trust': avg_trust,
                'average_relationship_strength': avg_relationship,
                'total_entities': len(self.social_entities),
                'total_interactions': len(self.interaction_history)
            }
            
            self.social_learning_insights.append(insight)
            
            # Keep only recent insights
            if len(self.social_learning_insights) > 100:
                self.social_learning_insights = self.social_learning_insights[-100:]

    async def get_subscriptions(self):
        """Return topics this service subscribes to"""
        return [
            'social_interaction',
            'relationship_update',
            'communication_request',
            'social_context_change',
            'norm_violation_alert'
        ]
    
    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info(f"{self.service_name} service started")
        
        # Relationship maintenance interval
        maintenance_interval = 3600  # 1 hour
        last_maintenance = datetime.now()
        
        try:
            while self.running:
                # Process messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self.handle_message(message)
                
                # Periodic relationship maintenance
                current_time = datetime.now()
                if (current_time - last_maintenance).seconds >= maintenance_interval:
                    await self.relationship_maintenance()
                    last_maintenance = current_time
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
        except Exception as e:
            logger.error(f"Error in {self.service_name} service: {e}")
        finally:
            logger.info(f"{self.service_name} service stopped")