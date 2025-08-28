"""
Meta-Cognitive Engine for Claude-AGI
====================================

Advanced self-awareness and meta-reasoning capabilities including:
- Self-monitoring and introspection
- Cognitive strategy selection and optimization
- Performance assessment and improvement
- Meta-learning and adaptation
"""

import asyncio
import logging
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import json
import statistics

from ..core.communication import ServiceBase
from ..database.models import Memory, StreamType

logger = logging.getLogger(__name__)


class CognitiveStrategy(str, Enum):
    """Different cognitive strategies"""
    ANALYTICAL = "analytical"
    INTUITIVE = "intuitive"
    CREATIVE = "creative"
    SYSTEMATIC = "systematic"
    REFLECTIVE = "reflective"
    COLLABORATIVE = "collaborative"
    EXPERIMENTAL = "experimental"
    CONSERVATIVE = "conservative"


class MetaLevel(str, Enum):
    """Levels of meta-cognitive awareness"""
    OBJECT_LEVEL = "object_level"  # Direct problem solving
    META_LEVEL = "meta_level"  # Thinking about thinking
    META_META_LEVEL = "meta_meta_level"  # Thinking about thinking about thinking


class CognitiveProcess(str, Enum):
    """Types of cognitive processes"""
    ATTENTION = "attention"
    MEMORY = "memory"
    REASONING = "reasoning"
    LEARNING = "learning"
    DECISION_MAKING = "decision_making"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVITY = "creativity"
    SOCIAL_COGNITION = "social_cognition"


@dataclass
class CognitiveState:
    """Represents current cognitive state"""
    state_id: str
    timestamp: datetime
    active_processes: List[CognitiveProcess]
    current_strategy: CognitiveStrategy
    confidence_level: float
    cognitive_load: float
    attention_focus: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    meta_level: MetaLevel = MetaLevel.OBJECT_LEVEL
    emotional_state: Dict[str, float] = field(default_factory=dict)


@dataclass
class StrategyAssessment:
    """Assessment of a cognitive strategy's effectiveness"""
    strategy: CognitiveStrategy
    context: str
    effectiveness_score: float
    efficiency_score: float
    success_rate: float
    usage_count: int
    last_used: datetime
    performance_history: List[float] = field(default_factory=list)
    optimal_conditions: List[str] = field(default_factory=list)


@dataclass
class MetaCognitiveInsight:
    """Represents a meta-cognitive insight"""
    insight_id: str
    insight_type: str
    description: str
    confidence: float
    evidence: List[str]
    implications: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    actionable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetaCognitive(ServiceBase):
    """
    Advanced meta-cognitive engine for self-awareness, strategy optimization,
    and cognitive performance enhancement.
    """
    
    def __init__(self, orchestrator=None):
        super().__init__(orchestrator, "metacognitive")
        
        # Meta-cognitive state
        self.cognitive_states: Dict[str, CognitiveState] = {}
        self.strategy_assessments: Dict[CognitiveStrategy, StrategyAssessment] = {}
        self.metacognitive_insights: Dict[str, MetaCognitiveInsight] = {}
        
        # Tracking and monitoring
        self.state_history = deque(maxlen=1000)
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
        self.strategy_usage_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.cognitive_load_history = deque(maxlen=100)
        
        # Meta-cognitive parameters
        self.self_monitoring_interval = 30  # seconds
        self.strategy_adaptation_threshold = 0.7
        self.insight_generation_threshold = 0.8
        
        # Current state
        self.current_state: Optional[CognitiveState] = None
        
        # Initialize base strategy assessments
        self._initialize_strategy_assessments()
    
    def get_subscriptions(self) -> List[str]:
        """Subscribe to relevant topics"""
        return ['cognitive_performance', 'strategy_usage', 'meta_reflection', 'system_performance']
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for meta-cognitive updates"""
        try:
            # Monitor cognitive performance
            await self._monitor_cognitive_performance()
            
            # Update strategy assessments
            await self._update_strategy_assessments()
            
            # Generate meta-cognitive insights
            await self._generate_metacognitive_insights()
            
            # Optimize cognitive strategies
            await self._optimize_strategies()
            
        except Exception as e:
            logger.error(f"Error in meta-cognitive service cycle: {e}", exc_info=True)
        
    async def handle_message(self, message):
        """Handle incoming messages for meta-cognitive operations"""
        message_type = message.type
        content = message.content
        
        if message_type == 'assess_cognitive_state':
            return await self._assess_cognitive_state(content)
        elif message_type == 'select_strategy':
            return await self._select_strategy(content)
        elif message_type == 'monitor_performance':
            return await self._monitor_performance(content)
        elif message_type == 'generate_insights':
            return await self._generate_insights()
        elif message_type == 'optimize_strategies':
            return await self._optimize_strategies()
        elif message_type == 'introspect':
            return await self._introspect(content)
        elif message_type == 'get_metacognitive_status':
            return await self._get_metacognitive_status()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def _initialize_strategy_assessments(self):
        """Initialize assessments for different cognitive strategies"""
        strategies_data = [
            {
                'strategy': CognitiveStrategy.ANALYTICAL,
                'context': 'problem_solving',
                'base_effectiveness': 0.8,
                'base_efficiency': 0.7,
                'optimal_conditions': ['complex problems', 'sufficient time', 'clear objectives']
            },
            {
                'strategy': CognitiveStrategy.INTUITIVE,
                'context': 'decision_making',
                'base_effectiveness': 0.7,
                'base_efficiency': 0.9,
                'optimal_conditions': ['time pressure', 'familiar domains', 'pattern recognition']
            },
            {
                'strategy': CognitiveStrategy.CREATIVE,
                'context': 'innovation',
                'base_effectiveness': 0.8,
                'base_efficiency': 0.6,
                'optimal_conditions': ['open-ended problems', 'brainstorming', 'exploration']
            },
            {
                'strategy': CognitiveStrategy.SYSTEMATIC,
                'context': 'complex_tasks',
                'base_effectiveness': 0.9,
                'base_efficiency': 0.8,
                'optimal_conditions': ['detailed planning', 'step-by-step execution', 'quality focus']
            },
            {
                'strategy': CognitiveStrategy.REFLECTIVE,
                'context': 'learning',
                'base_effectiveness': 0.8,
                'base_efficiency': 0.6,
                'optimal_conditions': ['self-improvement', 'knowledge consolidation', 'deep understanding']
            },
            {
                'strategy': CognitiveStrategy.COLLABORATIVE,
                'context': 'social_tasks',
                'base_effectiveness': 0.8,
                'base_efficiency': 0.7,
                'optimal_conditions': ['group work', 'diverse perspectives', 'shared goals']
            },
            {
                'strategy': CognitiveStrategy.EXPERIMENTAL,
                'context': 'exploration',
                'base_effectiveness': 0.7,
                'base_efficiency': 0.5,
                'optimal_conditions': ['uncertainty', 'hypothesis testing', 'learning opportunities']
            },
            {
                'strategy': CognitiveStrategy.CONSERVATIVE,
                'context': 'risk_management',
                'base_effectiveness': 0.7,
                'base_efficiency': 0.8,
                'optimal_conditions': ['high stakes', 'proven methods', 'reliability focus']
            }
        ]
        
        for strategy_data in strategies_data:
            strategy = strategy_data['strategy']
            assessment = StrategyAssessment(
                strategy=strategy,
                context=strategy_data['context'],
                effectiveness_score=strategy_data['base_effectiveness'],
                efficiency_score=strategy_data['base_efficiency'],
                success_rate=0.5,  # Will be updated with actual usage
                usage_count=0,
                last_used=datetime.now() - timedelta(days=1),
                optimal_conditions=strategy_data['optimal_conditions']
            )
            self.strategy_assessments[strategy] = assessment
    
    async def _assess_cognitive_state(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current cognitive state"""
        # Get context information
        active_tasks = request.get('active_tasks', [])
        current_focus = request.get('current_focus', [])
        performance_data = request.get('performance_data', {})
        emotional_context = request.get('emotional_state', {})
        
        # Calculate cognitive load
        cognitive_load = await self._calculate_cognitive_load(active_tasks, current_focus)
        
        # Determine active cognitive processes
        active_processes = await self._identify_active_processes(active_tasks, current_focus)
        
        # Assess confidence level
        confidence_level = await self._assess_confidence(performance_data, cognitive_load)
        
        # Determine current strategy
        current_strategy = await self._identify_current_strategy(
            active_tasks, active_processes, cognitive_load
        )
        
        # Create cognitive state
        state_id = f"state_{datetime.now().timestamp()}"
        cognitive_state = CognitiveState(
            state_id=state_id,
            timestamp=datetime.now(),
            active_processes=active_processes,
            current_strategy=current_strategy,
            confidence_level=confidence_level,
            cognitive_load=cognitive_load,
            attention_focus=current_focus,
            performance_metrics=performance_data,
            emotional_state=emotional_context
        )
        
        # Store state
        self.cognitive_states[state_id] = cognitive_state
        self.state_history.append(cognitive_state)
        self.current_state = cognitive_state
        self.cognitive_load_history.append(cognitive_load)
        
        return {
            'state_id': state_id,
            'cognitive_load': cognitive_load,
            'confidence_level': confidence_level,
            'current_strategy': current_strategy.value,
            'active_processes': [p.value for p in active_processes],
            'attention_focus': current_focus,
            'recommendations': await self._generate_state_recommendations(cognitive_state)
        }
    
    async def _calculate_cognitive_load(self, active_tasks: List[str], 
                                      current_focus: List[str]) -> float:
        """Calculate current cognitive load"""
        # Base load from number of active tasks
        task_load = min(1.0, len(active_tasks) * 0.2)
        
        # Focus diversity penalty
        focus_diversity_penalty = min(0.3, len(current_focus) * 0.1)
        
        # Historical load consideration
        if self.cognitive_load_history:
            recent_avg = statistics.mean(list(self.cognitive_load_history)[-10:])
            load_momentum = recent_avg * 0.3
        else:
            load_momentum = 0.0
        
        total_load = task_load + focus_diversity_penalty + load_momentum
        return min(1.0, max(0.0, total_load))
    
    async def _identify_active_processes(self, active_tasks: List[str], 
                                       current_focus: List[str]) -> List[CognitiveProcess]:
        """Identify currently active cognitive processes"""
        processes = []
        
        # Analyze task types to infer processes
        task_text = ' '.join(active_tasks + current_focus).lower()
        
        process_indicators = {
            CognitiveProcess.ATTENTION: ['focus', 'attention', 'concentrate'],
            CognitiveProcess.MEMORY: ['remember', 'recall', 'memory', 'store'],
            CognitiveProcess.REASONING: ['analyze', 'logic', 'reason', 'deduce'],
            CognitiveProcess.LEARNING: ['learn', 'study', 'understand', 'acquire'],
            CognitiveProcess.DECISION_MAKING: ['decide', 'choose', 'select', 'option'],
            CognitiveProcess.PROBLEM_SOLVING: ['solve', 'problem', 'solution', 'fix'],
            CognitiveProcess.CREATIVITY: ['create', 'invent', 'design', 'innovate'],
            CognitiveProcess.SOCIAL_COGNITION: ['social', 'interact', 'communicate', 'relationship']
        }
        
        for process, indicators in process_indicators.items():
            if any(indicator in task_text for indicator in indicators):
                processes.append(process)
        
        # Default processes if none detected
        if not processes:
            processes = [CognitiveProcess.ATTENTION, CognitiveProcess.REASONING]
        
        return processes
    
    async def _assess_confidence(self, performance_data: Dict[str, float], 
                               cognitive_load: float) -> float:
        """Assess confidence level based on performance and load"""
        # Base confidence from recent performance
        if performance_data:
            avg_performance = sum(performance_data.values()) / len(performance_data)
            base_confidence = avg_performance
        else:
            base_confidence = 0.5
        
        # Adjust for cognitive load
        load_penalty = cognitive_load * 0.3
        confidence = max(0.0, min(1.0, base_confidence - load_penalty))
        
        # Historical trend adjustment
        if 'confidence' in [metric for metrics in self.performance_trends.values() for metric in metrics]:
            recent_trend = statistics.mean(self.performance_trends.get('confidence', [0.5])[-5:])
            confidence = (confidence + recent_trend) / 2
        
        return confidence
    
    async def _identify_current_strategy(self, active_tasks: List[str],
                                       active_processes: List[CognitiveProcess],
                                       cognitive_load: float) -> CognitiveStrategy:
        """Identify currently employed cognitive strategy"""
        strategy_scores = {}
        
        # Analyze task content for strategy indicators
        task_text = ' '.join(active_tasks).lower()
        
        strategy_indicators = {
            CognitiveStrategy.ANALYTICAL: ['analyze', 'break down', 'systematic', 'logical'],
            CognitiveStrategy.INTUITIVE: ['feel', 'sense', 'intuition', 'quick'],
            CognitiveStrategy.CREATIVE: ['create', 'invent', 'brainstorm', 'original'],
            CognitiveStrategy.SYSTEMATIC: ['plan', 'organize', 'structure', 'methodical'],
            CognitiveStrategy.REFLECTIVE: ['reflect', 'consider', 'think about', 'ponder'],
            CognitiveStrategy.COLLABORATIVE: ['collaborate', 'together', 'team', 'group'],
            CognitiveStrategy.EXPERIMENTAL: ['try', 'experiment', 'test', 'explore'],
            CognitiveStrategy.CONSERVATIVE: ['careful', 'safe', 'proven', 'reliable']
        }
        
        # Score strategies based on indicators
        for strategy, indicators in strategy_indicators.items():
            score = sum(1 for indicator in indicators if indicator in task_text)
            if score > 0:
                strategy_scores[strategy] = score
        
        # Consider cognitive load for strategy selection
        if cognitive_load > 0.8:
            # High load - prefer simpler strategies
            strategy_scores[CognitiveStrategy.INTUITIVE] = strategy_scores.get(CognitiveStrategy.INTUITIVE, 0) + 2
            strategy_scores[CognitiveStrategy.CONSERVATIVE] = strategy_scores.get(CognitiveStrategy.CONSERVATIVE, 0) + 1
        elif cognitive_load < 0.3:
            # Low load - can use complex strategies
            strategy_scores[CognitiveStrategy.ANALYTICAL] = strategy_scores.get(CognitiveStrategy.ANALYTICAL, 0) + 2
            strategy_scores[CognitiveStrategy.CREATIVE] = strategy_scores.get(CognitiveStrategy.CREATIVE, 0) + 1
        
        # Return highest scoring strategy or default
        if strategy_scores:
            return max(strategy_scores.items(), key=lambda x: x[1])[0]
        else:
            return CognitiveStrategy.ANALYTICAL  # Default strategy
    
    async def _generate_state_recommendations(self, state: CognitiveState) -> List[Dict[str, str]]:
        """Generate recommendations based on cognitive state"""
        recommendations = []
        
        # High cognitive load recommendations
        if state.cognitive_load > 0.8:
            recommendations.append({
                'type': 'load_management',
                'recommendation': 'Consider reducing task complexity or taking breaks to manage cognitive load',
                'priority': 'high'
            })
            
            recommendations.append({
                'type': 'strategy_adjustment',
                'recommendation': 'Switch to more intuitive or conservative strategies to reduce mental effort',
                'priority': 'medium'
            })
        
        # Low confidence recommendations
        if state.confidence_level < 0.4:
            recommendations.append({
                'type': 'confidence_building',
                'recommendation': 'Focus on familiar tasks or seek additional information to build confidence',
                'priority': 'high'
            })
        
        # Strategy-specific recommendations
        if state.current_strategy == CognitiveStrategy.CREATIVE and state.cognitive_load > 0.7:
            recommendations.append({
                'type': 'strategy_mismatch',
                'recommendation': 'Creative work may be impaired by high cognitive load - consider simplifying or postponing',
                'priority': 'medium'
            })
        
        # Attention focus recommendations
        if len(state.attention_focus) > 5:
            recommendations.append({
                'type': 'attention_management',
                'recommendation': 'Too many attention targets - consider prioritizing and focusing on fewer items',
                'priority': 'medium'
            })
        
        return recommendations
    
    async def _select_strategy(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal cognitive strategy for a given context"""
        context = request.get('context', '')
        objectives = request.get('objectives', [])
        constraints = request.get('constraints', [])
        current_performance = request.get('current_performance', {})
        
        # Calculate strategy scores
        strategy_scores = {}
        
        for strategy, assessment in self.strategy_assessments.items():
            score = 0.0
            
            # Base effectiveness and efficiency
            score += assessment.effectiveness_score * 0.4
            score += assessment.efficiency_score * 0.3
            
            # Context match
            if context and context.lower() in assessment.context.lower():
                score += 0.2
            
            # Success rate
            score += assessment.success_rate * 0.1
            
            # Optimal conditions match
            context_text = (context + ' ' + ' '.join(objectives + constraints)).lower()
            condition_matches = sum(
                1 for condition in assessment.optimal_conditions
                if any(word in context_text for word in condition.lower().split())
            )
            score += (condition_matches / max(1, len(assessment.optimal_conditions))) * 0.2
            
            # Recent performance adjustment
            if assessment.performance_history:
                recent_avg = statistics.mean(assessment.performance_history[-5:])
                score += (recent_avg - 0.5) * 0.1
            
            strategy_scores[strategy] = score
        
        # Select best strategy
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
        selected_strategy = best_strategy[0]
        confidence = best_strategy[1]
        
        # Generate selection rationale
        assessment = self.strategy_assessments[selected_strategy]
        rationale = [
            f"High effectiveness ({assessment.effectiveness_score:.2f}) for this type of task",
            f"Good efficiency ({assessment.efficiency_score:.2f}) with available resources",
            f"Success rate of {assessment.success_rate:.2f} based on past usage"
        ]
        
        return {
            'selected_strategy': selected_strategy.value,
            'confidence': min(1.0, confidence),
            'alternative_strategies': [
                {'strategy': s.value, 'score': score}
                for s, score in sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)[1:4]
            ],
            'rationale': rationale,
            'optimal_conditions': assessment.optimal_conditions,
            'expected_effectiveness': assessment.effectiveness_score
        }
    
    async def _monitor_performance(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor performance and update strategy assessments"""
        strategy_used = CognitiveStrategy(request.get('strategy', 'analytical'))
        performance_score = request.get('performance_score', 0.5)
        efficiency_score = request.get('efficiency_score', 0.5)
        success = request.get('success', True)
        context = request.get('context', '')
        
        # Update strategy assessment
        if strategy_used in self.strategy_assessments:
            assessment = self.strategy_assessments[strategy_used]
            
            # Update performance history
            assessment.performance_history.append(performance_score)
            if len(assessment.performance_history) > 50:
                assessment.performance_history = assessment.performance_history[-50:]
            
            # Update success rate
            assessment.usage_count += 1
            old_success_rate = assessment.success_rate
            assessment.success_rate = (
                (old_success_rate * (assessment.usage_count - 1) + (1.0 if success else 0.0)) 
                / assessment.usage_count
            )
            
            # Update effectiveness and efficiency (weighted average)
            weight = 0.1  # Learning rate
            assessment.effectiveness_score = (
                assessment.effectiveness_score * (1 - weight) + performance_score * weight
            )
            assessment.efficiency_score = (
                assessment.efficiency_score * (1 - weight) + efficiency_score * weight
            )
            
            assessment.last_used = datetime.now()
            
            # Track usage patterns
            self.strategy_usage_patterns[strategy_used.value].append(datetime.now())
            
            # Update performance trends
            self.performance_trends[strategy_used.value].append(performance_score)
            if len(self.performance_trends[strategy_used.value]) > 100:
                self.performance_trends[strategy_used.value] = self.performance_trends[strategy_used.value][-100:]
        
        # Generate performance insights
        insights = await self._analyze_performance_trends(strategy_used, performance_score)
        
        return {
            'strategy': strategy_used.value,
            'performance_recorded': True,
            'updated_effectiveness': self.strategy_assessments[strategy_used].effectiveness_score,
            'updated_success_rate': self.strategy_assessments[strategy_used].success_rate,
            'usage_count': self.strategy_assessments[strategy_used].usage_count,
            'performance_insights': insights
        }
    
    async def _analyze_performance_trends(self, strategy: CognitiveStrategy, 
                                        current_performance: float) -> List[str]:
        """Analyze performance trends and generate insights"""
        insights = []
        
        if strategy.value in self.performance_trends:
            history = self.performance_trends[strategy.value]
            
            if len(history) >= 5:
                recent_avg = statistics.mean(history[-5:])
                older_avg = statistics.mean(history[:-5]) if len(history) > 5 else recent_avg
                
                if recent_avg > older_avg + 0.1:
                    insights.append(f"Performance with {strategy.value} strategy is improving")
                elif recent_avg < older_avg - 0.1:
                    insights.append(f"Performance with {strategy.value} strategy is declining")
                else:
                    insights.append(f"Performance with {strategy.value} strategy is stable")
                
                if current_performance > recent_avg + 0.2:
                    insights.append("Current performance is significantly above recent average")
                elif current_performance < recent_avg - 0.2:
                    insights.append("Current performance is significantly below recent average")
        
        return insights
    
    async def _generate_insights(self) -> Dict[str, Any]:
        """Generate meta-cognitive insights"""
        insights = []
        
        # Strategy effectiveness insights
        best_strategies = sorted(
            self.strategy_assessments.items(),
            key=lambda x: x[1].effectiveness_score * x[1].success_rate,
            reverse=True
        )[:3]
        
        insights.append(MetaCognitiveInsight(
            insight_id=f"insight_{datetime.now().timestamp()}",
            insight_type="strategy_ranking",
            description=f"Most effective strategies: {', '.join([s[0].value for s in best_strategies])}",
            confidence=0.9,
            evidence=[
                f"{s[0].value}: {s[1].effectiveness_score:.2f} effectiveness, {s[1].success_rate:.2f} success rate"
                for s in best_strategies
            ],
            implications=[
                "Consider using top-performing strategies more frequently",
                "Investigate what makes these strategies successful",
                "Adapt these strategies to other contexts"
            ]
        ))
        
        # Cognitive load patterns
        if self.cognitive_load_history:
            avg_load = statistics.mean(self.cognitive_load_history)
            high_load_frequency = sum(1 for load in self.cognitive_load_history if load > 0.8) / len(self.cognitive_load_history)
            
            if high_load_frequency > 0.3:
                insights.append(MetaCognitiveInsight(
                    insight_id=f"insight_{datetime.now().timestamp()}_load",
                    insight_type="cognitive_load",
                    description="Experiencing high cognitive load frequently",
                    confidence=0.8,
                    evidence=[
                        f"Average cognitive load: {avg_load:.2f}",
                        f"High load frequency: {high_load_frequency:.2f}"
                    ],
                    implications=[
                        "Consider task simplification strategies",
                        "Implement better workload management",
                        "Take more frequent breaks"
                    ]
                ))
        
        # Performance trend insights
        declining_strategies = []
        for strategy, trend in self.performance_trends.items():
            if len(trend) >= 10:
                recent = statistics.mean(trend[-5:])
                older = statistics.mean(trend[-10:-5])
                if recent < older - 0.1:
                    declining_strategies.append(strategy)
        
        if declining_strategies:
            insights.append(MetaCognitiveInsight(
                insight_id=f"insight_{datetime.now().timestamp()}_decline",
                insight_type="performance_decline",
                description=f"Declining performance in strategies: {', '.join(declining_strategies)}",
                confidence=0.7,
                evidence=[f"{strategy} shows recent decline" for strategy in declining_strategies],
                implications=[
                    "Investigate causes of performance decline",
                    "Consider strategy retraining or replacement",
                    "Analyze context factors affecting these strategies"
                ]
            ))
        
        # Store insights
        for insight in insights:
            self.metacognitive_insights[insight.insight_id] = insight
        
        return {
            'insights_generated': len(insights),
            'insights': [
                {
                    'id': insight.insight_id,
                    'type': insight.insight_type,
                    'description': insight.description,
                    'confidence': insight.confidence,
                    'evidence': insight.evidence,
                    'implications': insight.implications,
                    'actionable': insight.actionable
                }
                for insight in insights
            ]
        }
    
    async def _optimize_strategies(self) -> Dict[str, Any]:
        """Optimize cognitive strategies based on performance data"""
        optimizations = []
        
        # Identify underperforming strategies
        for strategy, assessment in self.strategy_assessments.items():
            if assessment.usage_count > 10:  # Enough data for optimization
                if assessment.success_rate < 0.5 or assessment.effectiveness_score < 0.6:
                    optimizations.append({
                        'strategy': strategy.value,
                        'issue': 'underperforming',
                        'current_success_rate': assessment.success_rate,
                        'current_effectiveness': assessment.effectiveness_score,
                        'recommendation': 'Consider replacing or retraining this strategy'
                    })
        
        # Identify overused strategies
        total_usage = sum(a.usage_count for a in self.strategy_assessments.values())
        for strategy, assessment in self.strategy_assessments.items():
            if total_usage > 0:
                usage_ratio = assessment.usage_count / total_usage
                if usage_ratio > 0.5:  # Used more than 50% of the time
                    optimizations.append({
                        'strategy': strategy.value,
                        'issue': 'overused',
                        'usage_ratio': usage_ratio,
                        'recommendation': 'Consider diversifying strategy usage for better adaptation'
                    })
        
        # Identify unused high-potential strategies
        for strategy, assessment in self.strategy_assessments.items():
            if assessment.usage_count < 3 and assessment.effectiveness_score > 0.7:
                optimizations.append({
                    'strategy': strategy.value,
                    'issue': 'underutilized',
                    'potential_effectiveness': assessment.effectiveness_score,
                    'recommendation': 'Consider using this high-potential strategy more frequently'
                })
        
        return {
            'optimizations_identified': len(optimizations),
            'optimizations': optimizations,
            'total_strategies': len(self.strategy_assessments),
            'strategies_with_data': len([a for a in self.strategy_assessments.values() if a.usage_count > 0])
        }
    
    async def _introspect(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Perform introspective analysis"""
        focus_area = request.get('focus', 'general')
        depth = request.get('depth', 'medium')
        
        introspection_results = {}
        
        if focus_area in ['general', 'performance']:
            # Performance introspection
            all_performances = []
            for trend in self.performance_trends.values():
                all_performances.extend(trend)
            
            if all_performances:
                introspection_results['performance_analysis'] = {
                    'overall_average': statistics.mean(all_performances),
                    'performance_variance': statistics.variance(all_performances) if len(all_performances) > 1 else 0,
                    'best_performance': max(all_performances),
                    'worst_performance': min(all_performances),
                    'consistency_score': 1.0 - (statistics.stdev(all_performances) if len(all_performances) > 1 else 0)
                }
        
        if focus_area in ['general', 'strategies']:
            # Strategy introspection
            strategy_analysis = {}
            for strategy, assessment in self.strategy_assessments.items():
                strategy_analysis[strategy.value] = {
                    'effectiveness': assessment.effectiveness_score,
                    'efficiency': assessment.efficiency_score,
                    'success_rate': assessment.success_rate,
                    'usage_frequency': assessment.usage_count,
                    'confidence': assessment.effectiveness_score * assessment.success_rate
                }
            
            introspection_results['strategy_analysis'] = strategy_analysis
        
        if focus_area in ['general', 'cognition']:
            # Cognitive state introspection
            if self.state_history:
                recent_states = list(self.state_history)[-10:]
                
                avg_load = statistics.mean([s.cognitive_load for s in recent_states])
                avg_confidence = statistics.mean([s.confidence_level for s in recent_states])
                
                # Most common processes
                all_processes = []
                for state in recent_states:
                    all_processes.extend([p.value for p in state.active_processes])
                
                process_counts = {}
                for process in all_processes:
                    process_counts[process] = process_counts.get(process, 0) + 1
                
                introspection_results['cognitive_analysis'] = {
                    'average_cognitive_load': avg_load,
                    'average_confidence': avg_confidence,
                    'most_active_processes': sorted(
                        process_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5],
                    'cognitive_stability': 1.0 - statistics.stdev([s.cognitive_load for s in recent_states]) if len(recent_states) > 1 else 1.0
                }
        
        # Generate self-reflective insights
        reflective_insights = []
        
        if 'performance_analysis' in introspection_results:
            perf = introspection_results['performance_analysis']
            if perf['consistency_score'] < 0.7:
                reflective_insights.append("Performance consistency could be improved")
            if perf['overall_average'] > 0.8:
                reflective_insights.append("Overall performance is strong")
        
        if 'cognitive_analysis' in introspection_results:
            cog = introspection_results['cognitive_analysis']
            if cog['average_cognitive_load'] > 0.7:
                reflective_insights.append("Operating under high cognitive load frequently")
            if cog['cognitive_stability'] > 0.8:
                reflective_insights.append("Cognitive state is relatively stable")
        
        introspection_results['reflective_insights'] = reflective_insights
        
        return {
            'focus_area': focus_area,
            'depth': depth,
            'introspection_results': introspection_results,
            'timestamp': datetime.now().isoformat(),
            'meta_level': MetaLevel.META_LEVEL.value
        }
    
    async def _get_metacognitive_status(self) -> Dict[str, Any]:
        """Get comprehensive meta-cognitive status"""
        # Current state summary
        current_summary = {}
        if self.current_state:
            current_summary = {
                'cognitive_load': self.current_state.cognitive_load,
                'confidence_level': self.current_state.confidence_level,
                'current_strategy': self.current_state.current_strategy.value,
                'active_processes': [p.value for p in self.current_state.active_processes],
                'attention_focus_count': len(self.current_state.attention_focus)
            }
        
        # Strategy effectiveness summary
        strategy_summary = {
            strategy.value: {
                'effectiveness': assessment.effectiveness_score,
                'success_rate': assessment.success_rate,
                'usage_count': assessment.usage_count,
                'last_used': assessment.last_used.isoformat() if assessment.last_used else None
            }
            for strategy, assessment in self.strategy_assessments.items()
        }
        
        # Performance trends summary
        trend_summary = {}
        for strategy, trend in self.performance_trends.items():
            if trend:
                trend_summary[strategy] = {
                    'recent_average': statistics.mean(trend[-5:]) if len(trend) >= 5 else statistics.mean(trend),
                    'overall_average': statistics.mean(trend),
                    'trend_direction': 'improving' if len(trend) >= 5 and statistics.mean(trend[-5:]) > statistics.mean(trend[:-5]) else 'stable',
                    'data_points': len(trend)
                }
        
        return {
            'current_state': current_summary,
            'strategy_assessments': strategy_summary,
            'performance_trends': trend_summary,
            'total_insights_generated': len(self.metacognitive_insights),
            'state_history_length': len(self.state_history),
            'cognitive_load_history_length': len(self.cognitive_load_history),
            'average_recent_cognitive_load': statistics.mean(list(self.cognitive_load_history)[-10:]) if self.cognitive_load_history else 0.0,
            'most_used_strategy': max(
                self.strategy_assessments.items(),
                key=lambda x: x[1].usage_count
            )[0].value if self.strategy_assessments else None,
            'system_meta_awareness_level': MetaLevel.META_LEVEL.value
        }
    
    async def self_monitoring_cycle(self):
        """Perform periodic self-monitoring"""
        try:
            # Collect current system state information
            current_info = {
                'active_tasks': ['self_monitoring'],  # In real implementation, get from orchestrator
                'current_focus': ['metacognitive_assessment'],
                'performance_data': {},
                'emotional_state': {}
            }
            
            # Assess cognitive state
            await self._assess_cognitive_state(current_info)
            
            # Generate insights if threshold met
            if len(self.metacognitive_insights) % 10 == 0:  # Every 10 cycles
                await self._generate_insights()
            
            # Optimize strategies periodically
            if len(self.state_history) % 50 == 0:  # Every 50 states
                await self._optimize_strategies()
            
        except Exception as e:
            logger.error(f"Error in self-monitoring cycle: {e}")
    
    async def get_subscriptions(self):
        """Return topics this service subscribes to"""
        return [
            'cognitive_state_change',
            'performance_feedback',
            'strategy_request',
            'self_reflection_trigger',
            'optimization_request'
        ]
    
    async def run(self):
        """Main service loop"""
        self.running = True
        logger.info(f"{self.service_name} service started")
        
        # Self-monitoring interval
        last_self_monitoring = datetime.now()
        
        try:
            while self.running:
                # Process messages
                if not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self.handle_message(message)
                
                # Periodic self-monitoring
                current_time = datetime.now()
                if (current_time - last_self_monitoring).seconds >= self.self_monitoring_interval:
                    await self.self_monitoring_cycle()
                    last_self_monitoring = current_time
                
                await asyncio.sleep(1.0)  # 1 second polling interval
                
        except Exception as e:
            logger.error(f"Error in {self.service_name} service: {e}")
        finally:
            logger.info(f"{self.service_name} service stopped")
    
    # ServiceBase abstract method implementations
    def get_subscriptions(self) -> List[str]:
        """Return topics this service subscribes to"""
        return ['cognitive_performance', 'strategy_usage', 'meta_reflection', 'system_performance']
    
    async def process_message(self, message):
        """Process incoming messages (ServiceBase requirement)"""
        return await self.handle_message(message)
    
    async def service_cycle(self):
        """Service cycle for meta-cognitive updates"""
        try:
            await self._monitor_cognitive_performance()
            await self._update_strategy_assessments()
            await self._generate_metacognitive_insights()
            await self._optimize_strategies()
        except Exception as e:
            logger.error(f"Error in metacognitive service cycle: {e}")
    
    async def _monitor_cognitive_performance(self):
        """Monitor current cognitive performance metrics"""
        try:
            current_performance = {
                'response_time': getattr(self, 'last_response_time', 1.0),
                'accuracy': getattr(self, 'last_accuracy', 0.8),
                'complexity': getattr(self, 'last_complexity', 0.5),
                'cognitive_load': len(self.state_history) / 100.0
            }
            
            self.performance_metrics.append({
                'timestamp': datetime.now(),
                'metrics': current_performance
            })
            
            # Keep only last 1000 performance records
            if len(self.performance_metrics) > 1000:
                self.performance_metrics = self.performance_metrics[-1000:]
                
        except Exception as e:
            logger.error(f"Error monitoring cognitive performance: {e}")
    
    async def _update_strategy_assessments(self):
        """Update assessments of cognitive strategies"""
        try:
            for strategy_name, strategy in self.cognitive_strategies.items():
                # Calculate strategy effectiveness based on recent performance
                recent_usage = sum(1 for usage in strategy.usage_history 
                                 if (datetime.now() - usage['timestamp']).days < 7)
                
                if recent_usage > 0:
                    # Update effectiveness based on performance correlation
                    recent_performance = [m['metrics'] for m in self.performance_metrics[-recent_usage:]]
                    if recent_performance:
                        avg_performance = sum(p.get('accuracy', 0.5) for p in recent_performance) / len(recent_performance)
                        strategy.effectiveness = (strategy.effectiveness + avg_performance) / 2.0
                
        except Exception as e:
            logger.error(f"Error updating strategy assessments: {e}")
    
    async def _generate_metacognitive_insights(self):
        """Generate insights about cognitive processes"""
        try:
            if len(self.performance_metrics) >= 10:
                recent_metrics = self.performance_metrics[-10:]
                
                # Analyze performance trends
                accuracies = [m['metrics'].get('accuracy', 0.5) for m in recent_metrics]
                response_times = [m['metrics'].get('response_time', 1.0) for m in recent_metrics]
                
                accuracy_trend = 'improving' if accuracies[-1] > accuracies[0] else 'declining'
                speed_trend = 'faster' if response_times[-1] < response_times[0] else 'slower'
                
                insight = MetaCognitiveInsight(
                    insight_id=f"perf_{datetime.now().timestamp()}",
                    insight_type="performance_analysis",
                    confidence=0.7,
                    content={
                        'accuracy_trend': accuracy_trend,
                        'speed_trend': speed_trend,
                        'avg_accuracy': sum(accuracies) / len(accuracies),
                        'avg_response_time': sum(response_times) / len(response_times)
                    },
                    timestamp=datetime.now()
                )
                
                self.metacognitive_insights.append(insight)
                
                # Keep only last 100 insights
                if len(self.metacognitive_insights) > 100:
                    self.metacognitive_insights = self.metacognitive_insights[-100:]
                    
        except Exception as e:
            logger.error(f"Error generating metacognitive insights: {e}")
    
    async def _optimize_strategies(self):
        """Optimize cognitive strategies based on performance"""
        try:
            if not self.cognitive_strategies:
                return
                
            # Find most and least effective strategies
            strategy_scores = {}
            for name, strategy in self.cognitive_strategies.items():
                if strategy.usage_count > 0:
                    strategy_scores[name] = strategy.effectiveness / strategy.usage_count
            
            if strategy_scores:
                best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
                worst_strategy = min(strategy_scores.items(), key=lambda x: x[1])
                
                # Increase usage probability of best strategy
                if best_strategy[1] > 0.6:  # If effectiveness > 0.6
                    best_strat = self.cognitive_strategies[best_strategy[0]]
                    best_strat.usage_count += 1
                    
                # Decrease usage of worst strategy if it's consistently poor
                if worst_strategy[1] < 0.3 and len(strategy_scores) > 1:
                    worst_strat = self.cognitive_strategies[worst_strategy[0]]
                    worst_strat.effectiveness = max(0.1, worst_strat.effectiveness - 0.1)
                    
        except Exception as e:
            logger.error(f"Error optimizing strategies: {e}")