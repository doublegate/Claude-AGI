"""
Unit tests for causal reasoning capabilities
"""

import pytest
from datetime import datetime
from src.reasoning.causal_reasoning import (
    CausalReasoner,
    CausalRelationType,
    Variable,
    CausalRelation,
    Observation
)


@pytest.fixture
async def reasoner():
    """Create a causal reasoner instance"""
    return CausalReasoner()


@pytest.mark.asyncio
class TestVariableManagement:
    """Test variable tracking and management"""

    async def test_add_variable(self, reasoner):
        """Test adding variables to track"""
        var = await reasoner.add_variable(
            var_id="temp",
            name="Temperature",
            var_type="continuous"
        )

        assert var.var_id == "temp"
        assert var.name == "Temperature"
        assert var.var_type == "continuous"
        assert "temp" in reasoner.variables

    async def test_add_multiple_variables(self, reasoner):
        """Test adding multiple variables"""
        await reasoner.add_variable("temp", "Temperature", "continuous")
        await reasoner.add_variable("humidity", "Humidity", "continuous")
        await reasoner.add_variable("rain", "Is Raining", "binary")

        assert len(reasoner.variables) == 3
        assert reasoner.variables["rain"].var_type == "binary"

    async def test_variable_observed_values_empty(self, reasoner):
        """Test that new variables have no observations"""
        var = await reasoner.add_variable("test", "Test Variable")
        assert len(var.observed_values) == 0


@pytest.mark.asyncio
class TestObservations:
    """Test observation recording"""

    async def test_record_observation(self, reasoner):
        """Test recording observations"""
        await reasoner.add_variable("temp", "Temperature")
        await reasoner.add_variable("ice_cream_sales", "Ice Cream Sales")

        obs = await reasoner.record_observation(
            observation_id="obs1",
            variables={"temp": 30, "ice_cream_sales": 150}
        )

        assert obs.observation_id == "obs1"
        assert obs.variables["temp"] == 30
        assert len(reasoner.observations) == 1

    async def test_observation_updates_variable_values(self, reasoner):
        """Test that observations update variable values"""
        await reasoner.add_variable("temp", "Temperature")

        await reasoner.record_observation("obs1", {"temp": 25})
        await reasoner.record_observation("obs2", {"temp": 30})
        await reasoner.record_observation("obs3", {"temp": 28})

        assert len(reasoner.variables["temp"].observed_values) == 3
        assert reasoner.variables["temp"].observed_values == [25, 30, 28]

    async def test_observation_with_context(self, reasoner):
        """Test recording observations with context"""
        await reasoner.add_variable("temp", "Temperature")

        obs = await reasoner.record_observation(
            observation_id="obs1",
            variables={"temp": 25},
            context={"location": "New York", "time_of_day": "noon"}
        )

        assert obs.context["location"] == "New York"
        assert obs.context["time_of_day"] == "noon"

    async def test_observations_max_length(self, reasoner):
        """Test that observations are limited to 1000"""
        await reasoner.add_variable("x", "Variable X")

        # Add 1200 observations
        for i in range(1200):
            await reasoner.record_observation(f"obs{i}", {"x": i})

        # Should only keep most recent 1000
        assert len(reasoner.observations) == 1000


@pytest.mark.asyncio
class TestCorrelationDetection:
    """Test correlation detection between variables"""

    async def test_perfect_positive_correlation(self, reasoner):
        """Test detecting perfect positive correlation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Record perfectly correlated observations
        for i in range(10):
            await reasoner.record_observation(
                f"obs{i}",
                {"x": i, "y": i * 2}  # Perfect linear relationship
            )

        correlation = await reasoner.detect_correlation("x", "y")
        assert correlation > 0.95  # Should be very close to 1.0

    async def test_perfect_negative_correlation(self, reasoner):
        """Test detecting perfect negative correlation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Record negatively correlated observations
        for i in range(10):
            await reasoner.record_observation(
                f"obs{i}",
                {"x": i, "y": -i}
            )

        correlation = await reasoner.detect_correlation("x", "y")
        assert correlation < -0.95  # Should be very close to -1.0

    async def test_no_correlation(self, reasoner):
        """Test detecting no correlation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Record uncorrelated observations
        x_values = [1, 2, 3, 4, 5]
        y_values = [5, 2, 4, 1, 3]  # No pattern
        for i in range(5):
            await reasoner.record_observation(
                f"obs{i}",
                {"x": x_values[i], "y": y_values[i]}
            )

        correlation = await reasoner.detect_correlation("x", "y")
        # Should be close to 0 (allowing for small random variation)
        assert abs(correlation) < 0.5

    async def test_correlation_insufficient_data(self, reasoner):
        """Test correlation with insufficient data"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Only one observation
        await reasoner.record_observation("obs1", {"x": 1, "y": 2})

        correlation = await reasoner.detect_correlation("x", "y")
        assert correlation == 0.0  # Not enough data

    async def test_correlation_missing_variable(self, reasoner):
        """Test correlation with missing variable"""
        await reasoner.add_variable("x", "X")

        correlation = await reasoner.detect_correlation("x", "nonexistent")
        assert correlation == 0.0

    async def test_correlation_caching(self, reasoner):
        """Test that correlation results are cached"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        # First calculation
        correlation1 = await reasoner.detect_correlation("x", "y")

        # Should be cached
        cache_key = tuple(sorted(["x", "y"]))
        assert cache_key in reasoner.correlations
        assert reasoner.correlations[cache_key] == correlation1

        # Second call should return cached value
        correlation2 = await reasoner.detect_correlation("x", "y")
        assert correlation1 == correlation2


@pytest.mark.asyncio
class TestCausationInference:
    """Test causal relationship inference"""

    async def test_infer_causation_strong_correlation(self, reasoner):
        """Test inferring causation from strong correlation"""
        await reasoner.add_variable("temp", "Temperature")
        await reasoner.add_variable("ice_cream", "Ice Cream Sales")

        # Create strong correlation
        for i in range(20):
            temp = 20 + i
            sales = 50 + i * 5
            await reasoner.record_observation(
                f"obs{i}",
                {"temp": temp, "ice_cream": sales}
            )

        relation = await reasoner.infer_causation("temp", "ice_cream")

        assert relation is not None
        assert relation.cause_var == "temp"
        assert relation.effect_var == "ice_cream"
        assert relation.strength > 0.3
        assert relation.confidence > 0

    async def test_infer_causation_with_temporal_evidence(self, reasoner):
        """Test causation inference with temporal evidence"""
        await reasoner.add_variable("cause", "Cause")
        await reasoner.add_variable("effect", "Effect")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"cause": i, "effect": i * 2})

        relation = await reasoner.infer_causation(
            "cause",
            "effect",
            temporal_evidence=True
        )

        assert relation.relation_type == CausalRelationType.DIRECT_CAUSE
        assert relation.confidence == 0.7

    async def test_infer_causation_without_temporal_evidence(self, reasoner):
        """Test causation inference without temporal evidence"""
        await reasoner.add_variable("var1", "Variable 1")
        await reasoner.add_variable("var2", "Variable 2")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"var1": i, "var2": i})

        relation = await reasoner.infer_causation("var1", "var2", temporal_evidence=False)

        assert relation.relation_type == CausalRelationType.CONTRIBUTING_FACTOR
        assert relation.confidence == 0.5

    async def test_infer_causation_weak_correlation(self, reasoner):
        """Test that weak correlation doesn't infer causation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Create truly weak correlation (< 0.3) with alternating pattern
        x_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_values = [5, 2, 6, 3, 4, 7, 2, 8, 3, 5]  # No clear pattern
        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": x_values[i], "y": y_values[i]})

        relation = await reasoner.infer_causation("x", "y")

        # Should return None for weak correlation (< 0.3)
        # If correlation happens to be >= 0.3, accept the relation
        if relation is not None:
            # Verify it's due to strong enough correlation
            correlation = await reasoner.detect_correlation("x", "y")
            assert abs(correlation) >= 0.3

    async def test_causal_relations_indexed(self, reasoner):
        """Test that causal relations are properly indexed"""
        await reasoner.add_variable("a", "A")
        await reasoner.add_variable("b", "B")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"a": i, "b": i * 2})

        relation = await reasoner.infer_causation("a", "b")

        assert len(reasoner.relation_index["a"]) == 1
        assert reasoner.relation_index["a"][0] == relation


@pytest.mark.asyncio
class TestPredictions:
    """Test predictive capabilities"""

    async def test_make_prediction(self, reasoner):
        """Test making predictions"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Establish relationship
        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i * 2})

        await reasoner.infer_causation("x", "y")

        # Make prediction
        prediction = await reasoner.make_prediction("x", 15, "y")

        assert prediction is not None
        # Prediction should be recorded
        assert len(reasoner.predictions) == 1
        assert reasoner.predictions[0]["cause_value"] == 15

    async def test_make_prediction_no_relation(self, reasoner):
        """Test prediction with no causal relation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # No relationship established
        prediction = await reasoner.make_prediction("x", 5, "y")

        assert prediction is None

    async def test_test_prediction_accuracy(self, reasoner):
        """Test testing prediction accuracy"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Establish relationship
        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i * 2})

        await reasoner.infer_causation("x", "y")

        # Make prediction
        predicted = await reasoner.make_prediction("x", 10, "y")

        # Test prediction
        accuracy = await reasoner.test_prediction(0, 20)  # Actual value

        assert accuracy > 0
        assert accuracy <= 1.0
        assert "accuracy" in reasoner.predictions[0]

    async def test_prediction_uses_strongest_relation(self, reasoner):
        """Test that prediction uses strongest causal relation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        # Create two potential relationships (simplified scenario)
        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i * 2})

        relation1 = await reasoner.infer_causation("x", "y", temporal_evidence=True)

        # Make prediction - should use the relation we created
        prediction = await reasoner.make_prediction("x", 10, "y")

        assert prediction is not None
        assert reasoner.predictions[0]["relation_id"] == relation1.relation_id


@pytest.mark.asyncio
class TestCausalModelUpdating:
    """Test updating causal models based on evidence"""

    async def test_update_causal_strength(self, reasoner):
        """Test updating causal strength"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        relation = await reasoner.infer_causation("x", "y")
        original_strength = relation.strength

        # Update strength
        await reasoner.update_causal_model(
            relation.relation_id,
            new_strength=0.9
        )

        assert relation.strength == 0.9
        assert relation.strength != original_strength

    async def test_update_causal_confidence(self, reasoner):
        """Test updating causal confidence"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        relation = await reasoner.infer_causation("x", "y")

        # Update confidence
        await reasoner.update_causal_model(
            relation.relation_id,
            new_confidence=0.95
        )

        assert relation.confidence == 0.95

    async def test_add_evidence_to_relation(self, reasoner):
        """Test adding evidence to causal relation"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        relation = await reasoner.infer_causation("x", "y")
        original_evidence_count = len(relation.evidence)

        # Add evidence
        await reasoner.update_causal_model(
            relation.relation_id,
            additional_evidence="Experimental confirmation"
        )

        assert len(relation.evidence) == original_evidence_count + 1
        assert "Experimental confirmation" in relation.evidence

    async def test_update_nonexistent_relation(self, reasoner):
        """Test updating nonexistent relation"""
        # Should handle gracefully
        await reasoner.update_causal_model(
            "nonexistent_id",
            new_strength=0.5
        )
        # No error should be raised

    async def test_strength_clamping(self, reasoner):
        """Test that strength is clamped to [0, 1]"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        relation = await reasoner.infer_causation("x", "y")

        # Try to set invalid values
        await reasoner.update_causal_model(relation.relation_id, new_strength=1.5)
        assert relation.strength == 1.0

        await reasoner.update_causal_model(relation.relation_id, new_strength=-0.5)
        assert relation.strength == 0.0


@pytest.mark.asyncio
class TestCausalQueries:
    """Test querying causal relationships"""

    async def test_get_causes(self, reasoner):
        """Test getting causes of an effect"""
        await reasoner.add_variable("temp", "Temperature")
        await reasoner.add_variable("exercise", "Exercise")
        await reasoner.add_variable("heart_rate", "Heart Rate")

        # Create multiple causes
        for i in range(10):
            await reasoner.record_observation(
                f"obs{i}",
                {"temp": 20 + i, "exercise": i, "heart_rate": 60 + i * 2}
            )

        await reasoner.infer_causation("temp", "heart_rate")
        await reasoner.infer_causation("exercise", "heart_rate")

        causes = await reasoner.get_causes("heart_rate")

        assert len(causes) == 2
        assert all(c.effect_var == "heart_rate" for c in causes)

    async def test_get_effects(self, reasoner):
        """Test getting effects of a cause"""
        await reasoner.add_variable("exercise", "Exercise")
        await reasoner.add_variable("heart_rate", "Heart Rate")
        await reasoner.add_variable("calories", "Calories Burned")

        # Create multiple effects
        for i in range(10):
            await reasoner.record_observation(
                f"obs{i}",
                {"exercise": i, "heart_rate": 60 + i, "calories": i * 10}
            )

        await reasoner.infer_causation("exercise", "heart_rate")
        await reasoner.infer_causation("exercise", "calories")

        effects = await reasoner.get_effects("exercise")

        assert len(effects) == 2
        assert all(e.cause_var == "exercise" for e in effects)

    async def test_causes_sorted_by_strength(self, reasoner):
        """Test that causes are sorted by strength"""
        await reasoner.add_variable("a", "A")
        await reasoner.add_variable("b", "B")
        await reasoner.add_variable("c", "C")

        # Create different strength relationships
        for i in range(10):
            await reasoner.record_observation(
                f"obs{i}",
                {"a": i, "b": i * 0.5, "c": i * 2}
            )

        await reasoner.infer_causation("a", "c")  # Strong
        await reasoner.infer_causation("b", "c")  # Weaker

        causes = await reasoner.get_causes("c")

        # Should be sorted by strength * confidence (strongest first)
        for i in range(len(causes) - 1):
            score1 = causes[i].strength * causes[i].confidence
            score2 = causes[i + 1].strength * causes[i + 1].confidence
            assert score1 >= score2


@pytest.mark.asyncio
class TestStatistics:
    """Test causal reasoning statistics"""

    async def test_statistics_no_data(self, reasoner):
        """Test statistics with no causal relations"""
        stats = await reasoner.get_statistics()

        assert "message" in stats
        assert stats["message"] == "No causal relations yet"

    async def test_statistics_with_data(self, reasoner):
        """Test statistics with causal data"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i})

        await reasoner.infer_causation("x", "y")

        stats = await reasoner.get_statistics()

        assert stats["total_variables"] == 2
        assert stats["total_observations"] == 10
        assert stats["total_causal_relations"] == 1
        assert "avg_causal_strength" in stats
        assert "avg_confidence" in stats

    async def test_statistics_with_predictions(self, reasoner):
        """Test statistics with predictions"""
        await reasoner.add_variable("x", "X")
        await reasoner.add_variable("y", "Y")

        for i in range(10):
            await reasoner.record_observation(f"obs{i}", {"x": i, "y": i * 2})

        await reasoner.infer_causation("x", "y")
        await reasoner.make_prediction("x", 10, "y")
        await reasoner.test_prediction(0, 20)

        stats = await reasoner.get_statistics()

        assert stats["total_predictions"] == 1
        assert stats["tested_predictions"] == 1
        assert "avg_prediction_accuracy" in stats
        assert stats["avg_prediction_accuracy"] > 0


@pytest.mark.asyncio
class TestAdvancedReasoningScenarios:
    """Test complex real-world reasoning scenarios"""

    async def test_multi_causal_chain(self, reasoner):
        """Test reasoning about causal chains (A -> B -> C)"""
        await reasoner.add_variable("rain", "Rainfall")
        await reasoner.add_variable("humidity", "Humidity")
        await reasoner.add_variable("mold", "Mold Growth")

        # Rain causes humidity causes mold
        for i in range(20):
            rain = i
            humidity = 50 + i * 2  # Rain increases humidity
            mold = humidity * 0.5  # Humidity causes mold
            await reasoner.record_observation(
                f"obs{i}",
                {"rain": rain, "humidity": humidity, "mold": mold}
            )

        # Infer causal chain
        rain_humidity = await reasoner.infer_causation("rain", "humidity")
        humidity_mold = await reasoner.infer_causation("humidity", "mold")

        assert rain_humidity is not None
        assert humidity_mold is not None

        # Check that we can trace causes
        mold_causes = await reasoner.get_causes("mold")
        assert len(mold_causes) >= 1

    async def test_common_cause_scenario(self, reasoner):
        """Test common cause scenario (A causes both B and C)"""
        await reasoner.add_variable("season", "Season Temperature")
        await reasoner.add_variable("ice_cream", "Ice Cream Sales")
        await reasoner.add_variable("sunburn", "Sunburn Cases")

        # Hot season causes both ice cream sales and sunburn
        for i in range(15):
            temp = i
            ice_cream = temp * 10
            sunburn = temp * 5
            await reasoner.record_observation(
                f"obs{i}",
                {"season": temp, "ice_cream": ice_cream, "sunburn": sunburn}
            )

        season_ice = await reasoner.infer_causation("season", "ice_cream")
        season_sun = await reasoner.infer_causation("season", "sunburn")

        assert season_ice is not None
        assert season_sun is not None

        # Both should be effects of season
        effects = await reasoner.get_effects("season")
        assert len(effects) == 2

    async def test_confounding_variable(self, reasoner):
        """Test handling confounding variables"""
        await reasoner.add_variable("coffee", "Coffee Consumption")
        await reasoner.add_variable("productivity", "Productivity")
        await reasoner.add_variable("sleep", "Sleep Quality")

        # Coffee and productivity both affected by sleep
        for i in range(15):
            sleep = 10 - i  # Decreasing sleep
            coffee = 10 - sleep  # More coffee with less sleep
            productivity = sleep * 5  # Productivity depends on sleep
            await reasoner.record_observation(
                f"obs{i}",
                {"coffee": coffee, "productivity": productivity, "sleep": sleep}
            )

        # Might see correlation between coffee and productivity
        correlation = await reasoner.detect_correlation("coffee", "productivity")

        # But real cause is sleep
        sleep_coffee = await reasoner.infer_causation("sleep", "coffee")
        sleep_prod = await reasoner.infer_causation("sleep", "productivity")

        assert abs(correlation) > 0.3  # Correlation exists
        assert sleep_coffee is not None  # Sleep causes coffee
        assert sleep_prod is not None  # Sleep causes productivity
