"""
Creative Work Indexing System for Claude-AGI
=============================================

Indexes and organizes creative works including:
- Work categorization and tagging
- Style and theme extraction
- Cross-referencing and relationships
- Portfolio management and curation
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WorkType(Enum):
    """Types of creative works"""
    STORY = "story"
    POEM = "poem"
    CODE = "code"
    DESIGN = "design"
    ESSAY = "essay"
    CONCEPT = "concept"
    SOLUTION = "solution"


@dataclass
class CreativeWork:
    """A creative work with metadata"""
    work_id: str
    title: str
    work_type: WorkType
    content: str
    tags: Set[str] = field(default_factory=set)
    themes: List[str] = field(default_factory=list)
    style_markers: Dict[str, float] = field(default_factory=dict)
    related_works: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.5
    originality_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


class CreativeWorkIndexer:
    """Indexes and organizes creative works"""

    def __init__(self):
        self.works: Dict[str, CreativeWork] = {}
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.theme_index: Dict[str, List[str]] = defaultdict(list)
        self.type_index: Dict[WorkType, List[str]] = defaultdict(list)

    async def add_work(
        self,
        work_id: str,
        title: str,
        work_type: WorkType,
        content: str,
        tags: Optional[Set[str]] = None,
        themes: Optional[List[str]] = None
    ) -> CreativeWork:
        """Add a creative work to the index"""
        work = CreativeWork(
            work_id=work_id,
            title=title,
            work_type=work_type,
            content=content,
            tags=tags or set(),
            themes=themes or []
        )

        self.works[work_id] = work

        # Update indexes
        for tag in work.tags:
            self.tag_index[tag].append(work_id)

        for theme in work.themes:
            self.theme_index[theme].append(work_id)

        self.type_index[work_type].append(work_id)

        logger.info(f"Indexed work: {title} ({work_type.value})")
        return work

    async def find_by_tag(self, tag: str) -> List[CreativeWork]:
        """Find works by tag"""
        work_ids = self.tag_index.get(tag, [])
        return [self.works[wid] for wid in work_ids]

    async def find_by_theme(self, theme: str) -> List[CreativeWork]:
        """Find works by theme"""
        work_ids = self.theme_index.get(theme, [])
        return [self.works[wid] for wid in work_ids]

    async def find_by_type(self, work_type: WorkType) -> List[CreativeWork]:
        """Find works by type"""
        work_ids = self.type_index.get(work_type, [])
        return [self.works[wid] for wid in work_ids]

    async def find_related_works(self, work_id: str, limit: int = 5) -> List[CreativeWork]:
        """Find works related to given work"""
        if work_id not in self.works:
            return []

        work = self.works[work_id]
        related = []

        # Find works with overlapping tags
        for other_id, other_work in self.works.items():
            if other_id == work_id:
                continue

            # Calculate similarity based on tags
            tag_overlap = len(work.tags & other_work.tags)
            if tag_overlap > 0:
                related.append((tag_overlap, other_work))

        # Sort by overlap and return top matches
        related.sort(key=lambda x: x[0], reverse=True)
        return [work for _, work in related[:limit]]

    async def get_portfolio_stats(self) -> Dict[str, Any]:
        """Get portfolio statistics"""
        if not self.works:
            return {'message': 'No works yet'}

        type_distribution = {
            work_type.value: len(work_ids)
            for work_type, work_ids in self.type_index.items()
        }

        avg_quality = sum(w.quality_score for w in self.works.values()) / len(self.works)
        avg_originality = sum(w.originality_score for w in self.works.values()) / len(self.works)

        return {
            'total_works': len(self.works),
            'type_distribution': type_distribution,
            'total_tags': len(self.tag_index),
            'total_themes': len(self.theme_index),
            'avg_quality_score': round(avg_quality, 2),
            'avg_originality_score': round(avg_originality, 2)
        }
