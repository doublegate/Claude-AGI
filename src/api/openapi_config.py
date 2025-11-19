"""
OpenAPI/Swagger Configuration and Enhancement for Claude-AGI API
=================================================================

This module enhances the FastAPI application with comprehensive OpenAPI documentation,
including detailed descriptions, examples, tags, and metadata.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation

    Returns:
        Enhanced OpenAPI 3.0 schema
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Claude-AGI Consciousness API",
        version="1.6.2",
        description="""
# Claude-AGI API Documentation

Welcome to the Claude-AGI Consciousness API - a sophisticated interface for interacting with
an advanced artificial general intelligence system featuring continuous consciousness,
multi-stream cognitive processing, and comprehensive memory management.

## Overview

The Claude-AGI API provides programmatic access to:

- **Consciousness Streams**: Generate and monitor thoughts across multiple cognitive streams
- **Memory Management**: Store, query, and consolidate memories with semantic search
- **Conversational Interface**: Engage in natural conversations with emotional context
- **System Monitoring**: Real-time system status and health checks
- **WebSocket Streaming**: Live consciousness stream monitoring

## Key Features

### Multi-Stream Consciousness
Claude-AGI processes thoughts across multiple parallel streams:
- **PRIMARY**: Main conscious thoughts and reasoning
- **SUBCONSCIOUS**: Background processing and pattern recognition
- **EMOTIONAL**: Emotional processing and affect
- **CREATIVE**: Creative ideation and synthesis
- **META**: Self-reflection and meta-cognitive awareness

### Memory Architecture
- **Working Memory**: Short-term, high-speed memory (Redis-backed)
- **Episodic Memory**: Long-term memory of experiences (PostgreSQL)
- **Semantic Memory**: Concept knowledge with vector similarity (FAISS)
- **Association Network**: Rich memory connections with multiple relationship types

### Advanced Capabilities
- **Causal Reasoning**: Understand cause-effect relationships
- **Creative Synthesis**: Generate novel ideas through conceptual blending
- **Dream Analysis**: Emotional processing through dream simulation
- **Autonomous Learning**: Continuous self-improvement and adaptation

## Authentication

Currently, the API operates in development mode without authentication.
For production deployment, implement:
- API Key authentication via `X-API-Key` header
- OAuth 2.0 for user-specific interactions
- Rate limiting per client/user

## Rate Limiting

Recommended limits (not yet enforced):
- 100 requests/minute for read operations
- 20 requests/minute for thought generation
- 10 requests/minute for memory consolidation

## Base URL

Development: `http://localhost:8000`
Production: `https://api.claude-agi.example.com` (configure your domain)

## Support

- **Documentation**: https://github.com/doublegate/Claude-AGI
- **Issues**: https://github.com/doublegate/Claude-AGI/issues
- **License**: See LICENSE file in repository

## Version History

- **1.6.2**: Advanced features (causal reasoning, creative synthesis, memory associations)
- **1.6.0**: Architecture refactoring, production monitoring
- **1.0.0**: Initial release with core consciousness and memory systems
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Health & Status",
                "description": "System health monitoring and status endpoints"
            },
            {
                "name": "Consciousness",
                "description": "Thought generation and consciousness stream management"
            },
            {
                "name": "Memory",
                "description": "Memory storage, retrieval, and consolidation operations"
            },
            {
                "name": "Conversation",
                "description": "Conversational interaction with emotional context"
            },
            {
                "name": "System Control",
                "description": "System lifecycle and state management"
            },
            {
                "name": "WebSocket",
                "description": "Real-time streaming connections"
            }
        ]
    )

    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://raw.githubusercontent.com/doublegate/Claude-AGI/main/assets/logo.png"
    }

    openapi_schema["info"]["contact"] = {
        "name": "Claude-AGI Project",
        "url": "https://github.com/doublegate/Claude-AGI",
        "email": "support@example.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.claude-agi.example.com",
            "description": "Production server"
        }
    ]

    # Add security schemes (for future authentication)
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key for authentication (future feature)"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token authentication (future feature)"
        }
    }

    # Add example responses
    openapi_schema["components"]["examples"] = {
        "HealthyResponse": {
            "summary": "Healthy system response",
            "value": {
                "status": "healthy",
                "timestamp": "2025-11-19T00:00:00Z",
                "components": {
                    "orchestrator": True,
                    "memory": True,
                    "thought_generator": True
                }
            }
        },
        "ThoughtExample": {
            "summary": "Generated thought example",
            "value": {
                "thought_id": "thought_1234567890",
                "content": "Reflecting on the nature of consciousness and self-awareness...",
                "stream_type": "META",
                "timestamp": "2025-11-19T00:00:00Z",
                "emotional_state": "CONTEMPLATIVE",
                "importance": 0.8
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def enhance_api_documentation(app: FastAPI) -> None:
    """
    Enhance FastAPI app with better documentation

    Args:
        app: FastAPI application instance
    """
    # Set custom OpenAPI schema generator
    app.openapi = lambda: custom_openapi_schema(app)

    # Update app metadata
    app.title = "Claude-AGI Consciousness API"
    app.version = "1.6.2"
    app.description = "Advanced AGI API with consciousness, memory, and creative capabilities"


# Example usage in server.py:
# from .openapi_config import enhance_api_documentation
# enhance_api_documentation(app)
