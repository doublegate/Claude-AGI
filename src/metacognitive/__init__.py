"""
Metacognitive Module
====================

Provides meta-cognitive capabilities including self-model and introspection.
"""

from .self_model import SelfModel, Capability, Limitation, CapabilityLevel
from .metacognitive_service import MetaCognitiveService
from .enhanced_self_model import EnhancedSelfModel, CapabilityDomain, ProficiencyLevel

__all__ = [
    'SelfModel', 'Capability', 'Limitation', 'CapabilityLevel',
    'MetaCognitiveService',
    'EnhancedSelfModel', 'CapabilityDomain', 'ProficiencyLevel'
]
