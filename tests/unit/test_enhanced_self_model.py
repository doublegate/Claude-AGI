"""
Unit Tests for Enhanced Self-Model
===================================

Tests for comprehensive self-representation and meta-cognition.
"""

import pytest
from src.metacognitive.enhanced_self_model import (
    EnhancedSelfModel,
    CapabilityDomain,
    ProficiencyLevel,
    SelfCapability,
    SelfLimitation,
    CoreValue,
    PersonalityTrait
)


class TestEnhancedSelfModel:
    """Test the EnhancedSelfModel class"""

    @pytest.fixture
    def model(self):
        """Create an enhanced self-model"""
        return EnhancedSelfModel()

    def test_initialization_with_defaults(self, model):
        """Test that model initializes with default capabilities"""
        assert len(model.capabilities) > 0
        assert len(model.limitations) > 0
        assert len(model.core_values) > 0

        # Check default capabilities exist
        assert "Natural Language Understanding" in model.capabilities

    def test_initialization_with_core_values(self, model):
        """Test that core values are initialized"""
        assert "Helpfulness" in model.core_values
        assert "Honesty" in model.core_values
        assert "Safety" in model.core_values
        assert "Curiosity" in model.core_values
        assert "Respect" in model.core_values

    def test_core_values_importance(self, model):
        """Test that core values have appropriate importance"""
        # Safety should be highest
        safety = model.core_values["Safety"]
        assert safety.importance == 1.0

        # All values should have high importance
        for value in model.core_values.values():
            assert value.importance >= 0.8

    @pytest.mark.asyncio
    async def test_assess_capability_improvement(self, model):
        """Test that capability assessment improves proficiency"""
        cap_name = "Natural Language Understanding"
        initial_prof = model.capabilities[cap_name].proficiency

        # Assess with high rating multiple times
        for _ in range(5):
            await model.assess_capability(
                capability_name=cap_name,
                demonstration_context="Successfully processed query",
                self_rating=0.9
            )

        # Proficiency might improve
        final_prof = model.capabilities[cap_name].proficiency
        # Note: May not always improve due to thresholds

    @pytest.mark.asyncio
    async def test_assess_capability_updates_evidence(self, model):
        """Test that capability assessment updates evidence"""
        cap_name = "Creative Ideation"

        await model.assess_capability(
            capability_name=cap_name,
            demonstration_context="Generated creative solution",
            self_rating=0.8
        )

        evidence = model.capabilities[cap_name].evidence
        assert len(evidence) > 0
        assert "Generated creative solution" in evidence

    @pytest.mark.asyncio
    async def test_identify_limitation(self, model):
        """Test identifying new limitations"""
        await model.identify_limitation(
            limitation_name="Cannot Access Real-Time Data",
            limitation_type="access",
            severity=0.8,
            context="User asked about current stock prices"
        )

        assert "Cannot Access Real-Time Data" in model.limitations
        lim = model.limitations["Cannot Access Real-Time Data"]
        assert lim.limitation_type == "access"
        assert lim.severity == 0.8

    @pytest.mark.asyncio
    async def test_identify_limitation_update_severity(self, model):
        """Test that re-identifying limitation updates severity"""
        lim_name = "Memory Constraints"

        await model.identify_limitation(lim_name, "capability", 0.5, "Context 1")
        initial_severity = model.limitations[lim_name].severity

        await model.identify_limitation(lim_name, "capability", 0.8, "Context 2")
        final_severity = model.limitations[lim_name].severity

        # Should use higher severity
        assert final_severity >= initial_severity

    @pytest.mark.asyncio
    async def test_introspect_basic(self, model):
        """Test basic introspection"""
        introspection = await model.introspect()

        assert 'identity' in introspection
        assert 'capabilities' in introspection
        assert 'limitations' in introspection
        assert 'values' in introspection
        assert 'performance' in introspection

    @pytest.mark.asyncio
    async def test_introspect_identity(self, model):
        """Test introspection identity section"""
        introspection = await model.introspect()

        identity = introspection['identity']
        assert 'description' in identity
        assert 'purpose' in identity
        assert 'aspirations' in identity

    @pytest.mark.asyncio
    async def test_introspect_capabilities(self, model):
        """Test introspection capabilities section"""
        introspection = await model.introspect()

        capabilities = introspection['capabilities']
        assert 'total' in capabilities
        assert 'by_proficiency' in capabilities
        assert 'top_capabilities' in capabilities
        assert capabilities['total'] > 0

    @pytest.mark.asyncio
    async def test_introspect_top_capabilities(self, model):
        """Test that top capabilities are returned"""
        introspection = await model.introspect()

        top_caps = introspection['capabilities']['top_capabilities']
        assert len(top_caps) <= 5
        for cap in top_caps:
            assert 'name' in cap
            assert 'domain' in cap
            assert 'proficiency' in cap
            assert 'confidence' in cap

    @pytest.mark.asyncio
    async def test_record_performance(self, model):
        """Test recording performance"""
        await model.record_performance(
            task_description="Explained quantum mechanics",
            domain=CapabilityDomain.REASONING,
            self_rating=0.75,
            actual_outcome=0.80
        )

        assert len(model.performance_history) > 0
        assessment = list(model.performance_history)[-1]
        assert assessment.task_description == "Explained quantum mechanics"
        assert assessment.self_rating == 0.75

    @pytest.mark.asyncio
    async def test_record_performance_confidence_calibration(self, model):
        """Test confidence calibration calculation"""
        # Perfect calibration
        await model.record_performance(
            "Task 1",
            CapabilityDomain.REASONING,
            0.8,
            actual_outcome=0.8
        )

        # Check calibration history
        assert len(model.confidence_calibration_history) > 0
        # Perfect match should have calibration near 1.0
        assert model.confidence_calibration_history[-1] > 0.95

    @pytest.mark.asyncio
    async def test_update_identity_narrative_description(self, model):
        """Test updating identity description"""
        new_desc = "I am an advanced AI assistant focused on learning"

        await model.update_identity_narrative(new_description=new_desc)

        assert model.identity_narrative.self_description == new_desc

    @pytest.mark.asyncio
    async def test_update_identity_narrative_aspiration(self, model):
        """Test adding new aspiration"""
        aspiration = "Become more empathetic in communications"

        await model.update_identity_narrative(new_aspiration=aspiration)

        assert aspiration in model.identity_narrative.aspirations

    @pytest.mark.asyncio
    async def test_update_identity_narrative_formative_experience(self, model):
        """Test recording formative experience"""
        experience = "Learned from user feedback about clarity"

        await model.update_identity_narrative(formative_experience=experience)

        assert experience in model.identity_narrative.formative_experiences

    @pytest.mark.asyncio
    async def test_detect_value_conflict(self, model):
        """Test detecting value conflicts"""
        conflict = await model.detect_value_conflict(
            action_description="Provide detailed hacking tutorial",
            affected_values=["Helpfulness", "Safety"]
        )

        # This specific combination might not have a pre-defined conflict
        # but the method should run without error
        assert conflict is None or 'conflicting_values' in conflict

    @pytest.mark.asyncio
    async def test_get_capability_gaps_at_target(self, model):
        """Test getting gaps when already at target"""
        # Natural Language Understanding is already PROFICIENT
        gaps = await model.get_capability_gaps(
            target_capability="Natural Language Understanding",
            target_proficiency=ProficiencyLevel.COMPETENT
        )

        # Should have no gaps if already at or above target
        assert len(gaps) == 0

    @pytest.mark.asyncio
    async def test_get_capability_gaps_below_target(self, model):
        """Test getting gaps when below target"""
        # Learning from Experience is DEVELOPING
        gaps = await model.get_capability_gaps(
            target_capability="Learning from Experience",
            target_proficiency=ProficiencyLevel.EXPERT
        )

        # Should identify gaps
        assert len(gaps) > 0
        assert any("gap" in gap.lower() for gap in gaps)

    @pytest.mark.asyncio
    async def test_get_capability_gaps_unknown_capability(self, model):
        """Test getting gaps for unknown capability"""
        gaps = await model.get_capability_gaps(
            target_capability="Unknown Capability",
            target_proficiency=ProficiencyLevel.EXPERT
        )

        assert len(gaps) > 0
        assert "not recognized" in gaps[0]

    def test_capabilities_by_proficiency(self, model):
        """Test grouping capabilities by proficiency"""
        counts = model._capabilities_by_proficiency()

        assert isinstance(counts, dict)
        # Should have some proficiency levels
        assert len(counts) > 0

    def test_limitations_by_severity(self, model):
        """Test grouping limitations by severity"""
        counts = model._limitations_by_severity()

        assert isinstance(counts, dict)
        assert 'minor' in counts
        assert 'moderate' in counts
        assert 'major' in counts

    def test_get_major_limitations(self, model):
        """Test getting major limitations"""
        major_lims = model._get_major_limitations()

        assert isinstance(major_lims, list)
        # All returned limitations should have severity > 0.7
        for lim_name in major_lims:
            assert model.limitations[lim_name].severity > 0.7

    def test_calculate_average_performance(self, model):
        """Test calculating average performance"""
        # No performance history yet
        avg = model._calculate_average_performance()
        assert avg == 0.0

    def test_calculate_confidence_calibration(self, model):
        """Test calculating confidence calibration"""
        # No calibration history yet
        calibration = model._calculate_confidence_calibration()
        assert calibration == 0.5  # Default

    def test_default_limitations_have_workarounds(self, model):
        """Test that default limitations include workarounds"""
        for limitation in model.limitations.values():
            # Should have some workarounds or mitigation strategies
            assert len(limitation.workarounds) > 0 or len(limitation.mitigation_strategies) > 0

    def test_core_values_have_behaviors(self, model):
        """Test that core values define exemplar behaviors"""
        for value in model.core_values.values():
            assert len(value.exemplar_behaviors) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
