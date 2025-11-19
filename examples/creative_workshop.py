#!/usr/bin/env python3
"""
Creative Workshop - Interactive Demo Application
=================================================

Demonstrates Claude-AGI's creative synthesis capabilities through
an interactive web application.

Features:
- Conceptual blending across domains
- Cross-domain analogies
- Constraint-based creativity
- Pattern abstraction
- Creative idea generation

Usage:
    python examples/creative_workshop.py
    # Then visit: http://localhost:5000
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, send_from_directory
from src.creative.creative_synthesis import (
    CreativeSynthesisEngine,
    SynthesisStrategy,
    NoveltyLevel
)

app = Flask(__name__, template_folder='templates')
engine = CreativeSynthesisEngine()


# Initialize with sample concepts
async def initialize_concepts():
    """Load sample concepts from different domains"""

    # Science concepts
    await engine.add_concept(
        "quantum",
        "Quantum Mechanics",
        "physics",
        attributes={
            "behavior": "probabilistic",
            "scale": "atomic",
            "properties": "wave-particle duality",
            "measurement": "observer-dependent"
        }
    )

    await engine.add_concept(
        "evolution",
        "Evolution",
        "biology",
        attributes={
            "mechanism": "natural selection",
            "scale": "species",
            "properties": "adaptation",
            "timeframe": "generations"
        }
    )

    await engine.add_concept(
        "neural_network",
        "Neural Network",
        "AI",
        attributes={
            "structure": "layered",
            "learning": "gradient descent",
            "properties": "distributed processing",
            "function": "pattern recognition"
        }
    )

    # Art concepts
    await engine.add_concept(
        "jazz",
        "Jazz Music",
        "music",
        attributes={
            "style": "improvisational",
            "structure": "loose",
            "properties": "syncopation",
            "expression": "emotional"
        }
    )

    await engine.add_concept(
        "cubism",
        "Cubism",
        "art",
        attributes={
            "style": "geometric",
            "perspective": "multiple viewpoints",
            "properties": "fragmentation",
            "representation": "abstract"
        }
    )

    # Philosophy concepts
    await engine.add_concept(
        "consciousness",
        "Consciousness",
        "philosophy",
        attributes={
            "nature": "subjective",
            "properties": "qualia",
            "emergence": "complex systems",
            "understanding": "first-person"
        }
    )

    await engine.add_concept(
        "emergence",
        "Emergence",
        "philosophy",
        attributes={
            "nature": "systemic",
            "properties": "unpredictable",
            "scale": "macro from micro",
            "causation": "bottom-up"
        }
    )

    # Technology concepts
    await engine.add_concept(
        "blockchain",
        "Blockchain",
        "technology",
        attributes={
            "structure": "distributed ledger",
            "properties": "immutable",
            "consensus": "decentralized",
            "trust": "cryptographic"
        }
    )

    await engine.add_concept(
        "swarm",
        "Swarm Intelligence",
        "technology",
        attributes={
            "structure": "distributed agents",
            "properties": "emergent behavior",
            "coordination": "local rules",
            "intelligence": "collective"
        }
    )

    # Economics concepts
    await engine.add_concept(
        "market",
        "Free Market",
        "economics",
        attributes={
            "mechanism": "supply and demand",
            "properties": "self-regulating",
            "participants": "autonomous agents",
            "optimization": "distributed"
        }
    )

    print(f"Initialized {len(engine.concepts)} concepts across {len(engine.domains)} domains")


# Flask Routes

@app.route("/")
def index():
    """Home page"""
    return render_template("creative_workshop.html")


@app.route("/api/concepts", methods=["GET"])
def get_concepts():
    """Get all available concepts"""
    concepts = [
        {
            "id": c.concept_id,
            "name": c.name,
            "domain": c.domain,
            "attributes": c.attributes
        }
        for c in engine.concepts.values()
    ]
    return jsonify({"concepts": concepts})


@app.route("/api/blend", methods=["POST"])
def blend_concepts():
    """Blend two concepts"""
    data = request.json
    concept1_id = data.get("concept1")
    concept2_id = data.get("concept2")
    blend_ratio = data.get("ratio", 0.5)

    if not concept1_id or not concept2_id:
        return jsonify({"error": "Missing concept IDs"}), 400

    # Run async synthesis
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    synthesis = loop.run_until_complete(
        engine.blend_concepts(concept1_id, concept2_id, blend_ratio)
    )

    if not synthesis:
        return jsonify({"error": "Blending failed"}), 400

    return jsonify({
        "synthesis": {
            "id": synthesis.synthesis_id,
            "name": synthesis.synthesized_concept,
            "description": synthesis.description,
            "strategy": synthesis.strategy.value,
            "novelty": synthesis.novelty_level.value,
            "confidence": synthesis.confidence,
            "properties": synthesis.properties
        }
    })


@app.route("/api/analogy", methods=["POST"])
def find_analogy():
    """Find cross-domain analogies"""
    data = request.json
    source_id = data.get("source")
    target_domain = data.get("target_domain")

    if not source_id or not target_domain:
        return jsonify({"error": "Missing parameters"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    analogy = loop.run_until_complete(
        engine.find_analogy(source_id, target_domain, min_similarity=0.2)
    )

    if not analogy:
        return jsonify({"error": "No analogy found"}), 404

    return jsonify({
        "analogy": {
            "id": analogy.analogy_id,
            "source_domain": analogy.source_domain,
            "target_domain": analogy.target_domain,
            "source_concept": analogy.source_concept,
            "target_concept": analogy.target_concept,
            "mapping": analogy.mapping,
            "strength": analogy.strength,
            "explanation": analogy.explanation
        }
    })


@app.route("/api/transform", methods=["POST"])
def transform_concept():
    """Transform concept with constraints"""
    data = request.json
    concept_id = data.get("concept")
    constraints = data.get("constraints", {})

    if not concept_id:
        return jsonify({"error": "Missing concept ID"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    synthesis = loop.run_until_complete(
        engine.generate_by_constraint(concept_id, constraints)
    )

    if not synthesis:
        return jsonify({"error": "Transformation failed"}), 400

    return jsonify({
        "synthesis": {
            "id": synthesis.synthesis_id,
            "name": synthesis.synthesized_concept,
            "description": synthesis.description,
            "novelty": synthesis.novelty_level.value,
            "confidence": synthesis.confidence,
            "properties": synthesis.properties
        }
    })


@app.route("/api/abstract", methods=["POST"])
def abstract_pattern():
    """Abstract pattern from multiple concepts"""
    data = request.json
    concept_ids = data.get("concepts", [])

    if len(concept_ids) < 2:
        return jsonify({"error": "Need at least 2 concepts"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    synthesis = loop.run_until_complete(
        engine.abstract_pattern(concept_ids)
    )

    if not synthesis:
        return jsonify({"error": "Pattern abstraction failed"}), 400

    return jsonify({
        "synthesis": {
            "id": synthesis.synthesis_id,
            "name": synthesis.synthesized_concept,
            "description": synthesis.description,
            "novelty": synthesis.novelty_level.value,
            "confidence": synthesis.confidence,
            "properties": synthesis.properties
        }
    })


@app.route("/api/generate", methods=["POST"])
def generate_ideas():
    """Generate creative ideas around a theme"""
    data = request.json
    theme = data.get("theme", "innovation")
    num_ideas = min(data.get("num_ideas", 5), 10)  # Max 10
    strategies = data.get("strategies")

    if strategies:
        strategies = [SynthesisStrategy(s) for s in strategies]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ideas = loop.run_until_complete(
        engine.generate_creative_ideas(theme, num_ideas, strategies)
    )

    return jsonify({
        "theme": theme,
        "ideas": [
            {
                "id": idea.synthesis_id,
                "name": idea.synthesized_concept,
                "description": idea.description,
                "strategy": idea.strategy.value,
                "novelty": idea.novelty_level.value,
                "confidence": idea.confidence
            }
            for idea in ideas
        ]
    })


@app.route("/api/recombine", methods=["POST"])
def recombine_elements():
    """Recombine concept elements"""
    data = request.json
    concept_ids = data.get("concepts", [])
    num_combinations = min(data.get("num_combinations", 3), 5)

    if len(concept_ids) < 2:
        return jsonify({"error": "Need at least 2 concepts"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    combinations = loop.run_until_complete(
        engine.recombine_elements(concept_ids, num_combinations)
    )

    return jsonify({
        "combinations": [
            {
                "id": combo.synthesis_id,
                "name": combo.synthesized_concept,
                "description": combo.description,
                "novelty": combo.novelty_level.value,
                "confidence": combo.confidence,
                "properties": combo.properties
            }
            for combo in combinations
        ]
    })


@app.route("/api/stats", methods=["GET"])
def get_statistics():
    """Get synthesis statistics"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stats = loop.run_until_complete(engine.get_statistics())
    return jsonify(stats)


if __name__ == "__main__":
    print("=" * 60)
    print("Creative Workshop - Claude-AGI Demo")
    print("=" * 60)
    print()
    print("Initializing creative synthesis engine...")

    # Initialize concepts
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize_concepts())

    print()
    print("Starting web server...")
    print("Visit: http://localhost:5000")
    print()
    print("Try these features:")
    print("  • Blend concepts from different domains")
    print("  • Find cross-domain analogies")
    print("  • Transform concepts with constraints")
    print("  • Abstract patterns from multiple concepts")
    print("  • Generate creative ideas around themes")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    app.run(debug=True, host="0.0.0.0", port=5000)
