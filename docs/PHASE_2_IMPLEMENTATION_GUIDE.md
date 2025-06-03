# Phase 2: Cognitive Enhancement Implementation Guide

Detailed implementation guide for Phase 2 (Months 4-6) focusing on learning systems, web exploration, and advanced NLP integration.

## Prerequisites

Before starting Phase 2, ensure ALL Phase 1 completion criteria are met:
- ✅ Test suite >95% pass rate
- ✅ Zero P0 security vulnerabilities
- ✅ TUI fully functional
- ✅ Architecture refactored (no god objects)
- ✅ Memory system synchronized
- ✅ Monitoring operational

## Phase 2 Overview

### Core Objectives
1. **Learning Systems**: Goal-directed behavior and self-improvement
2. **Web Exploration**: Safe, curiosity-driven knowledge acquisition
3. **Advanced NLP**: Beyond basic Claude API integration

### Timeline
- Month 4: Learning system foundation
- Month 5: Web exploration engine
- Month 6: Advanced NLP and integration

## Module 1: Learning Systems

### Architecture
```
┌─────────────────────────────────────────────────────┐
│                Learning Coordinator                  │
├──────────────┬────────────────┬────────────────────┤
│Goal Manager  │Knowledge Graph │Skill Tracker       │
├──────────────┼────────────────┼────────────────────┤
│Goal Queue    │Neo4j/NetworkX  │Progress Monitor    │
└──────────────┴────────────────┴────────────────────┘
```

### Implementation Steps

#### 1.1 Goal-Directed Behavior
```python
# src/learning/goal_manager.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import asyncio

class GoalPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class GoalStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

@dataclass
class LearningGoal:
    id: str
    description: str
    success_criteria: List[str]
    priority: GoalPriority
    status: GoalStatus
    progress: float = 0.0
    parent_goal: Optional[str] = None
    sub_goals: List[str] = None
    created_at: datetime
    deadline: Optional[datetime] = None
    
class GoalManager:
    """Manages learning goals and tracks progress"""
    
    def __init__(self, memory_manager, orchestrator):
        self.memory_manager = memory_manager
        self.orchestrator = orchestrator
        self.active_goals = {}
        self.goal_queue = asyncio.PriorityQueue()
        
    async def create_goal(self, description: str, 
                         criteria: List[str],
                         priority: GoalPriority) -> LearningGoal:
        """Create a new learning goal"""
        goal = LearningGoal(
            id=str(uuid.uuid4()),
            description=description,
            success_criteria=criteria,
            priority=priority,
            status=GoalStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Decompose into sub-goals if complex
        if self._is_complex_goal(goal):
            sub_goals = await self._decompose_goal(goal)
            goal.sub_goals = [sg.id for sg in sub_goals]
            
        # Add to queue
        await self.goal_queue.put((priority.value, goal))
        
        # Store in memory
        await self.memory_manager.store_memory(
            content=f"Created learning goal: {description}",
            memory_type="goal",
            metadata={"goal_id": goal.id}
        )
        
        return goal
        
    async def _decompose_goal(self, goal: LearningGoal) -> List[LearningGoal]:
        """Use AI to decompose complex goals into sub-goals"""
        prompt = f"""
        Decompose this learning goal into smaller, actionable sub-goals:
        Goal: {goal.description}
        Success Criteria: {', '.join(goal.success_criteria)}
        
        Provide 3-5 specific sub-goals that lead to achieving the main goal.
        """
        
        response = await self.orchestrator.ai_integration.generate_completion(prompt)
        # Parse response and create sub-goals
        sub_goals = self._parse_subgoals(response)
        
        return [
            await self.create_goal(
                description=sg_desc,
                criteria=[f"Complete: {sg_desc}"],
                priority=goal.priority
            )
            for sg_desc in sub_goals
        ]
```

#### 1.2 Knowledge Graph Implementation
```python
# src/learning/knowledge_graph.py
import networkx as nx
from typing import Dict, List, Tuple
import numpy as np

class KnowledgeNode:
    def __init__(self, concept: str, embedding: np.ndarray):
        self.id = str(uuid.uuid4())
        self.concept = concept
        self.embedding = embedding
        self.confidence = 0.5  # Initial confidence
        self.last_accessed = datetime.utcnow()
        self.access_count = 0

class KnowledgeGraph:
    """Graph-based knowledge representation"""
    
    def __init__(self, embedding_model):
        self.graph = nx.DiGraph()
        self.embedding_model = embedding_model
        self.node_index = {}  # concept -> node_id mapping
        
    async def add_concept(self, concept: str, 
                         related_concepts: List[str] = None) -> KnowledgeNode:
        """Add a new concept to the knowledge graph"""
        # Generate embedding
        embedding = await self.embedding_model.encode(concept)
        
        # Create node
        node = KnowledgeNode(concept, embedding)
        self.graph.add_node(node.id, data=node)
        self.node_index[concept] = node.id
        
        # Add relationships
        if related_concepts:
            for related in related_concepts:
                if related in self.node_index:
                    # Calculate relationship strength
                    related_node = self.get_node(related)
                    similarity = self._cosine_similarity(
                        embedding, related_node.embedding
                    )
                    self.graph.add_edge(
                        node.id, 
                        self.node_index[related],
                        weight=similarity,
                        relationship_type="related_to"
                    )
                    
        return node
        
    async def find_learning_paths(self, 
                                 from_concept: str, 
                                 to_concept: str) -> List[List[str]]:
        """Find optimal learning paths between concepts"""
        if from_concept not in self.node_index or to_concept not in self.node_index:
            return []
            
        from_id = self.node_index[from_concept]
        to_id = self.node_index[to_concept]
        
        # Find all paths up to length 5
        paths = list(nx.all_simple_paths(
            self.graph, from_id, to_id, cutoff=5
        ))
        
        # Sort by total confidence and path length
        scored_paths = []
        for path in paths:
            confidence = self._calculate_path_confidence(path)
            length = len(path)
            score = confidence / length  # Prefer shorter, high-confidence paths
            scored_paths.append((score, path))
            
        scored_paths.sort(reverse=True)
        
        # Convert back to concepts
        return [
            [self.graph.nodes[node_id]['data'].concept for node_id in path]
            for score, path in scored_paths[:5]  # Top 5 paths
        ]
```

#### 1.3 Skill Tracking System
```python
# src/learning/skill_tracker.py
@dataclass
class Skill:
    name: str
    category: str
    level: float  # 0.0 to 1.0
    experience_points: int
    last_practiced: datetime
    practice_count: int
    
class SkillTracker:
    """Tracks skill development and suggests practice"""
    
    def __init__(self):
        self.skills = {}
        self.skill_graph = nx.Graph()  # Skills that complement each other
        
    async def update_skill(self, skill_name: str, 
                          performance_score: float) -> Skill:
        """Update skill based on practice performance"""
        if skill_name not in self.skills:
            self.skills[skill_name] = Skill(
                name=skill_name,
                category=self._categorize_skill(skill_name),
                level=0.1,
                experience_points=0,
                last_practiced=datetime.utcnow(),
                practice_count=0
            )
            
        skill = self.skills[skill_name]
        
        # Update skill level using learning curve
        improvement = self._calculate_improvement(
            current_level=skill.level,
            performance=performance_score,
            practice_count=skill.practice_count
        )
        
        skill.level = min(1.0, skill.level + improvement)
        skill.experience_points += int(performance_score * 100)
        skill.practice_count += 1
        skill.last_practiced = datetime.utcnow()
        
        # Update related skills
        await self._update_related_skills(skill_name, improvement * 0.3)
        
        return skill
        
    def _calculate_improvement(self, current_level: float, 
                              performance: float, 
                              practice_count: int) -> float:
        """Calculate skill improvement using logarithmic learning curve"""
        # Diminishing returns as skill increases
        learning_rate = 0.1 * (1 - current_level)
        
        # Performance factor
        performance_factor = performance - 0.5  # -0.5 to 0.5
        
        # Practice bonus (encourages consistency)
        practice_bonus = min(0.1, practice_count * 0.001)
        
        improvement = learning_rate * performance_factor + practice_bonus
        return max(0, improvement)  # No negative improvement
```

## Module 2: Web Exploration Engine

### Safety-First Design
```python
# src/exploration/web_explorer.py
class SafeWebExplorer:
    """Web exploration with comprehensive safety measures"""
    
    def __init__(self, safety_framework, rate_limiter):
        self.safety = safety_framework
        self.rate_limiter = rate_limiter
        self.sandbox = self._create_sandbox()
        self.blocked_domains = self._load_blocked_domains()
        self.content_filter = ContentFilter()
        
    async def explore_topic(self, topic: str, 
                           max_pages: int = 10) -> List[WebContent]:
        """Safely explore a topic on the web"""
        # Validate topic
        if not await self.safety.validate_search_query(topic):
            raise UnsafeQueryError(f"Topic '{topic}' failed safety check")
            
        # Rate limit check
        if not await self.rate_limiter.check_limit("web_search"):
            raise RateLimitError("Web search rate limit exceeded")
            
        # Search with safe search enabled
        search_results = await self._safe_search(topic, max_results=max_pages)
        
        # Process results in sandbox
        contents = []
        for result in search_results:
            try:
                content = await self._fetch_in_sandbox(result.url)
                if await self._validate_content(content):
                    contents.append(content)
            except Exception as e:
                logger.warning(f"Failed to fetch {result.url}: {e}")
                
        return contents
        
    async def _fetch_in_sandbox(self, url: str) -> WebContent:
        """Fetch content in isolated sandbox environment"""
        # Use Docker container or VM for isolation
        async with self.sandbox.create_session() as session:
            # Set resource limits
            session.set_limits(
                cpu_percent=10,
                memory_mb=512,
                timeout_seconds=30,
                network_bandwidth_kb=1024
            )
            
            # Fetch with safety headers
            headers = {
                'User-Agent': 'Claude-AGI-Explorer/1.0 (Educational)',
                'DNT': '1',
                'X-Robots-Tag': 'noarchive'
            }
            
            response = await session.get(url, headers=headers)
            
            # Extract and sanitize content
            content = await self._extract_content(response)
            sanitized = await self.content_filter.sanitize(content)
            
            return WebContent(
                url=url,
                title=sanitized.title,
                text=sanitized.text,
                metadata=sanitized.metadata,
                fetched_at=datetime.utcnow()
            )
```

### Curiosity-Driven Exploration
```python
# src/exploration/curiosity_engine.py
class CuriosityEngine:
    """Drives autonomous exploration based on curiosity"""
    
    def __init__(self, knowledge_graph, interest_tracker):
        self.knowledge_graph = knowledge_graph
        self.interests = interest_tracker
        self.exploration_history = []
        
    async def suggest_exploration(self) -> List[ExplorationTarget]:
        """Suggest topics to explore based on curiosity metrics"""
        suggestions = []
        
        # 1. Knowledge gaps (unknown connections)
        gaps = await self._find_knowledge_gaps()
        for gap in gaps[:3]:
            suggestions.append(ExplorationTarget(
                topic=gap,
                reason="knowledge_gap",
                curiosity_score=0.8
            ))
            
        # 2. Trending interests (reinforcement)
        trending = await self.interests.get_trending()
        for interest in trending[:2]:
            suggestions.append(ExplorationTarget(
                topic=interest.topic,
                reason="trending_interest",
                curiosity_score=interest.score * 0.7
            ))
            
        # 3. Random exploration (serendipity)
        random_topics = await self._generate_random_topics()
        for topic in random_topics[:2]:
            suggestions.append(ExplorationTarget(
                topic=topic,
                reason="serendipity",
                curiosity_score=0.5
            ))
            
        # Sort by curiosity score
        suggestions.sort(key=lambda x: x.curiosity_score, reverse=True)
        
        return suggestions
        
    async def _find_knowledge_gaps(self) -> List[str]:
        """Identify gaps in knowledge graph"""
        # Find weakly connected components
        weak_components = list(nx.weakly_connected_components(
            self.knowledge_graph.graph
        ))
        
        # Find potential bridge concepts
        gaps = []
        for comp1, comp2 in itertools.combinations(weak_components, 2):
            if len(comp1) > 5 and len(comp2) > 5:  # Significant components
                # Get representative concepts
                concept1 = self._get_central_concept(comp1)
                concept2 = self._get_central_concept(comp2)
                
                # Generate bridge topic
                bridge = await self._generate_bridge_topic(concept1, concept2)
                gaps.append(bridge)
                
        return gaps
```

## Module 3: Advanced NLP Integration

### Multi-Model Architecture
```python
# src/nlp/multi_model_manager.py
class ModelConfig:
    def __init__(self, name: str, api_endpoint: str, 
                 capabilities: List[str], cost_per_token: float):
        self.name = name
        self.api_endpoint = api_endpoint
        self.capabilities = capabilities
        self.cost_per_token = cost_per_token
        self.performance_history = []

class MultiModelManager:
    """Manages multiple NLP models with fallback and optimization"""
    
    def __init__(self):
        self.models = {
            'claude-3': ModelConfig(
                name='Claude 3 Opus',
                api_endpoint='anthropic',
                capabilities=['reasoning', 'creativity', 'coding'],
                cost_per_token=0.00003
            ),
            'gpt-4': ModelConfig(
                name='GPT-4',
                api_endpoint='openai',
                capabilities=['general', 'translation'],
                cost_per_token=0.00002
            ),
            'llama-3': ModelConfig(
                name='Llama 3',
                api_endpoint='local',
                capabilities=['fast_inference'],
                cost_per_token=0.0
            )
        }
        
    async def generate(self, prompt: str, 
                      required_capabilities: List[str] = None,
                      budget_limit: float = None) -> str:
        """Generate response using optimal model selection"""
        # Select best model based on requirements
        selected_model = self._select_model(
            required_capabilities, budget_limit
        )
        
        try:
            response = await self._call_model(selected_model, prompt)
            
            # Track performance
            self._update_performance(selected_model, success=True)
            
            return response
            
        except Exception as e:
            logger.error(f"Model {selected_model.name} failed: {e}")
            
            # Fallback to next best model
            fallback = self._get_fallback_model(selected_model)
            if fallback:
                return await self._call_model(fallback, prompt)
            else:
                raise NoAvailableModelError()
```

### Domain-Specific Fine-Tuning
```python
# src/nlp/domain_adapter.py
class DomainAdapter:
    """Adapts models for specific domains"""
    
    def __init__(self, base_model):
        self.base_model = base_model
        self.domain_prompts = {}
        self.few_shot_examples = {}
        
    async def adapt_for_domain(self, domain: str, 
                              examples: List[Tuple[str, str]]):
        """Create domain-specific adaptation"""
        # Store few-shot examples
        self.few_shot_examples[domain] = examples
        
        # Generate domain prompt template
        self.domain_prompts[domain] = await self._generate_domain_prompt(
            domain, examples
        )
        
    async def generate_domain_specific(self, domain: str, 
                                     query: str) -> str:
        """Generate response with domain adaptation"""
        if domain not in self.domain_prompts:
            raise ValueError(f"Domain {domain} not adapted")
            
        # Build prompt with few-shot examples
        prompt = self.domain_prompts[domain]
        for input_ex, output_ex in self.few_shot_examples[domain][:3]:
            prompt += f"\nInput: {input_ex}\nOutput: {output_ex}\n"
            
        prompt += f"\nInput: {query}\nOutput:"
        
        # Generate with domain context
        response = await self.base_model.generate(
            prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        return response
```

## Integration Plan

### Month 4: Foundation
1. **Week 1-2**: Implement goal manager and basic learning loop
2. **Week 3-4**: Build knowledge graph with Neo4j/NetworkX

### Month 5: Expansion
1. **Week 1-2**: Implement safe web explorer with sandboxing
2. **Week 3-4**: Build curiosity engine and interest tracking

### Month 6: Advanced Features
1. **Week 1-2**: Multi-model NLP integration
2. **Week 3-4**: Domain adaptation and fine-tuning

## Testing Strategy

### Unit Tests
```python
# tests/test_learning_system.py
async def test_goal_decomposition():
    """Test complex goal decomposition"""
    goal_manager = GoalManager(mock_memory, mock_orchestrator)
    
    complex_goal = await goal_manager.create_goal(
        description="Learn quantum computing",
        criteria=["Understand superposition", "Implement Shor's algorithm"],
        priority=GoalPriority.HIGH
    )
    
    assert len(complex_goal.sub_goals) > 0
    assert all(sg.parent_goal == complex_goal.id for sg in sub_goals)
```

### Integration Tests
```python
async def test_learning_web_integration():
    """Test learning system with web exploration"""
    # Create learning goal
    goal = await goal_manager.create_goal(
        "Learn about transformers in NLP"
    )
    
    # Explore web for resources
    resources = await web_explorer.explore_topic(
        "transformer architecture NLP"
    )
    
    # Update knowledge graph
    for resource in resources:
        await knowledge_graph.add_concepts_from_text(
            resource.text
        )
    
    # Verify learning progress
    progress = await goal_manager.check_progress(goal.id)
    assert progress > 0.0
```

## Performance Targets

| Component | Metric | Target |
|-----------|--------|--------|
| Goal Processing | Goals/hour | >10 |
| Web Exploration | Pages/minute | 5-10 |
| Knowledge Graph | Queries/sec | >100 |
| NLP Generation | Tokens/sec | >50 |

## Success Criteria

Phase 2 is complete when:
- [ ] Learning system achieves goals autonomously
- [ ] Web exploration runs safely 24/7
- [ ] Knowledge graph contains >10,000 concepts
- [ ] Multi-model NLP reduces costs by 30%
- [ ] All integration tests passing
- [ ] Performance targets met