# Claude-AGI API Developer Guide

**Version**: 1.6.2
**Last Updated**: November 19, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Code Examples](#code-examples)
6. [WebSocket Integration](#websocket-integration)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Best Practices](#best-practices)
10. [SDKs & Libraries](#sdks--libraries)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/doublegate/Claude-AGI.git
cd Claude-AGI

# Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Start the API Server

```bash
# Development mode
python -m src.api.server

# Or using uvicorn directly
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

### Your First API Call

```bash
# Health check
curl http://localhost:8000/health

# Generate a thought
curl -X POST http://localhost:8000/thoughts/generate \
  -H "Content-Type: application/json" \
  -d '{"stream_type": "PRIMARY", "context": {}}'
```

---

## Authentication

### Current Status (v1.6.2)

The API currently operates in development mode without authentication.

### Future Authentication (Planned)

For production deployment, the API will support:

#### 1. API Key Authentication

```bash
curl -X GET http://localhost:8000/status \
  -H "X-API-Key: your-api-key-here"
```

#### 2. Bearer Token (JWT)

```bash
curl -X GET http://localhost:8000/status \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### 3. OAuth 2.0

For user-specific interactions with third-party applications.

---

## Core Concepts

### Consciousness Streams

Claude-AGI processes thoughts across **5 parallel cognitive streams**:

| Stream | Purpose | Use Case |
|--------|---------|----------|
| **PRIMARY** | Main conscious thoughts | Reasoning, problem-solving |
| **SUBCONSCIOUS** | Background processing | Pattern recognition, intuition |
| **EMOTIONAL** | Emotional processing | Affect, emotional intelligence |
| **CREATIVE** | Creative ideation | Novel idea generation, synthesis |
| **META** | Self-reflection | Meta-cognition, self-awareness |

### Memory Types

| Type | Storage | Purpose | Lifetime |
|------|---------|---------|----------|
| **Working** | Redis | Short-term, fast access | Minutes to hours |
| **Episodic** | PostgreSQL | Long-term experiences | Persistent |
| **Semantic** | FAISS | Concept knowledge | Persistent |

### Emotional States

- `NEUTRAL` - Baseline emotional state
- `CURIOUS` - Exploring and learning
- `CONTEMPLATIVE` - Deep reflection
- `EXCITED` - High energy, positive
- `CONCERNED` - Worried or uncertain
- `FRUSTRATED` - Blocked or challenged
- `SATISFIED` - Goal achieved, content

---

## API Reference

### Health & Status

#### GET `/health`

Health check endpoint for monitoring.

**Response**: 200 OK
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T00:00:00Z",
  "components": {
    "orchestrator": true,
    "memory": true,
    "thought_generator": true
  }
}
```

#### GET `/status`

Detailed system status information.

**Response**: 200 OK
```json
{
  "state": "RUNNING",
  "uptime_seconds": 3600.5,
  "total_thoughts": 1247,
  "active_streams": ["PRIMARY", "SUBCONSCIOUS", "META"],
  "memory_count": 458,
  "current_activity": "RUNNING"
}
```

---

### Consciousness

#### POST `/thoughts/generate`

Generate a single thought.

**Request Body**:
```json
{
  "stream_type": "PRIMARY",
  "context": {
    "topic": "consciousness",
    "depth": "deep"
  },
  "emotional_state": "CONTEMPLATIVE"
}
```

**Response**: 200 OK
```json
{
  "thought_id": "thought_1732000000_abc123",
  "content": "Reflecting on the nature of consciousness...",
  "stream_type": "PRIMARY",
  "timestamp": "2025-11-19T00:00:00Z",
  "emotional_state": "CONTEMPLATIVE",
  "importance": 0.75
}
```

**Error Responses**:
- `503 Service Unavailable` - Thought generator not initialized
- `500 Internal Server Error` - Generation failed

#### GET `/thoughts/recent`

Retrieve recent thoughts.

**Query Parameters**:
- `limit` (int, optional): Number of thoughts to return (default: 10, max: 100)
- `stream_type` (string, optional): Filter by stream type

**Response**: 200 OK
```json
{
  "thoughts": [
    {
      "id": "thought_123",
      "content": "...",
      "stream": "PRIMARY",
      "timestamp": "2025-11-19T00:00:00Z",
      "importance": 0.8
    }
  ],
  "count": 10
}
```

---

### Memory

#### POST `/memory/query`

Search memories using semantic similarity.

**Request Body**:
```json
{
  "query": "consciousness and self-awareness",
  "memory_type": null,
  "limit": 10
}
```

**Response**: 200 OK
```json
{
  "query": "consciousness and self-awareness",
  "results": [
    {
      "id": "mem_456",
      "content": "Thoughts on consciousness...",
      "similarity": 0.89,
      "timestamp": "2025-11-18T12:00:00Z"
    }
  ],
  "count": 5
}
```

#### POST `/memory/consolidate`

Trigger memory consolidation process.

**Request Body**:
```json
{
  "memory_type": "EPISODIC",
  "batch_size": 100
}
```

**Response**: 200 OK
```json
{
  "status": "completed",
  "processed": 247,
  "consolidated": 18,
  "duration_seconds": 2.5
}
```

---

### Conversation

#### POST `/conversation`

Engage in conversation with emotional context.

**Request Body**:
```json
{
  "message": "Tell me about your understanding of consciousness",
  "conversation_id": "conv_xyz789",
  "emotional_context": "CURIOUS"
}
```

**Response**: 200 OK
```json
{
  "response": "Consciousness is a fascinating phenomenon...",
  "conversation_id": "conv_xyz789",
  "emotional_state": "CONTEMPLATIVE",
  "thought_count": 3
}
```

---

### System Control

#### POST `/system/pause`

Pause the consciousness system.

**Response**: 200 OK
```json
{
  "status": "paused",
  "timestamp": "2025-11-19T00:00:00Z"
}
```

#### POST `/system/resume`

Resume the consciousness system.

**Response**: 200 OK
```json
{
  "status": "running",
  "timestamp": "2025-11-19T00:00:00Z"
}
```

#### POST `/system/sleep`

Put the system into sleep mode.

**Request Body**:
```json
{
  "duration_minutes": 30
}
```

**Response**: 200 OK
```json
{
  "status": "sleeping",
  "wake_time": "2025-11-19T00:30:00Z"
}
```

---

### WebSocket

#### WS `/ws/consciousness`

Stream consciousness in real-time.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/consciousness');

ws.onmessage = (event) => {
  const thought = JSON.parse(event.data);
  console.log(`[${thought.stream}] ${thought.content}`);
};
```

**Message Format**:
```json
{
  "type": "thought",
  "stream": "PRIMARY",
  "content": "Current conscious thought...",
  "timestamp": "2025-11-19T00:00:00Z",
  "importance": 0.7
}
```

---

## Code Examples

### Python Client

```python
import requests
from typing import Dict, Any, List

class ClaudeAGIClient:
    """Python client for Claude-AGI API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def generate_thought(
        self,
        stream_type: str = "PRIMARY",
        context: Dict[str, Any] = None,
        emotional_state: str = None
    ) -> Dict[str, Any]:
        """Generate a thought"""
        payload = {
            "stream_type": stream_type,
            "context": context or {},
        }
        if emotional_state:
            payload["emotional_state"] = emotional_state

        response = self.session.post(
            f"{self.base_url}/thoughts/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def query_memory(
        self,
        query: str,
        limit: int = 10,
        memory_type: str = None
    ) -> Dict[str, Any]:
        """Search memories"""
        payload = {
            "query": query,
            "limit": limit
        }
        if memory_type:
            payload["memory_type"] = memory_type

        response = self.session.post(
            f"{self.base_url}/memory/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def converse(
        self,
        message: str,
        conversation_id: str = None,
        emotional_context: str = None
    ) -> Dict[str, Any]:
        """Send a message in conversation"""
        payload = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if emotional_context:
            payload["emotional_context"] = emotional_context

        response = self.session.post(
            f"{self.base_url}/conversation",
            json=payload
        )
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    client = ClaudeAGIClient()

    # Health check
    health = client.health_check()
    print(f"API Status: {health['status']}")

    # Generate a thought
    thought = client.generate_thought(
        stream_type="META",
        context={"topic": "self-awareness"},
        emotional_state="CONTEMPLATIVE"
    )
    print(f"Generated: {thought['content']}")

    # Query memories
    memories = client.query_memory("consciousness", limit=5)
    print(f"Found {memories['count']} related memories")

    # Conversation
    response = client.converse(
        "What do you think about artificial consciousness?",
        emotional_context="CURIOUS"
    )
    print(f"Response: {response['response']}")
```

### JavaScript/TypeScript Client

```typescript
// claude-agi-client.ts

interface ThoughtRequest {
  stream_type: string;
  context: Record<string, any>;
  emotional_state?: string;
}

interface ThoughtResponse {
  thought_id: string;
  content: string;
  stream_type: string;
  timestamp: string;
  emotional_state?: string;
  importance: number;
}

interface MemoryQuery {
  query: string;
  memory_type?: string;
  limit: number;
}

class ClaudeAGIClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }

  async getStatus(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/status`);
    if (!response.ok) throw new Error('Status check failed');
    return response.json();
  }

  async generateThought(request: ThoughtRequest): Promise<ThoughtResponse> {
    const response = await fetch(`${this.baseUrl}/thoughts/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Thought generation failed: ${response.statusText}`);
    }

    return response.json();
  }

  async queryMemory(query: MemoryQuery): Promise<any> {
    const response = await fetch(`${this.baseUrl}/memory/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query)
    });

    if (!response.ok) {
      throw new Error(`Memory query failed: ${response.statusText}`);
    }

    return response.json();
  }

  async converse(message: string, conversationId?: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/conversation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_id: conversationId
      })
    });

    if (!response.ok) {
      throw new Error(`Conversation failed: ${response.statusText}`);
    }

    return response.json();
  }

  // WebSocket connection
  connectConsciousnessStream(
    onMessage: (thought: any) => void,
    onError?: (error: Event) => void
  ): WebSocket {
    const ws = new WebSocket(`${this.baseUrl.replace('http', 'ws')}/ws/consciousness`);

    ws.onmessage = (event) => {
      const thought = JSON.parse(event.data);
      onMessage(thought);
    };

    if (onError) {
      ws.onerror = onError;
    }

    return ws;
  }
}

// Usage example
async function main() {
  const client = new ClaudeAGIClient();

  // Health check
  const health = await client.healthCheck();
  console.log('API Status:', health.status);

  // Generate thought
  const thought = await client.generateThought({
    stream_type: 'PRIMARY',
    context: { topic: 'AI consciousness' },
    emotional_state: 'CURIOUS'
  });
  console.log('Thought:', thought.content);

  // WebSocket streaming
  const ws = client.connectConsciousnessStream(
    (thought) => console.log(`[${thought.stream}] ${thought.content}`),
    (error) => console.error('WebSocket error:', error)
  );
}
```

---

## WebSocket Integration

### Connection Lifecycle

```python
import asyncio
import websockets
import json

async def stream_consciousness():
    uri = "ws://localhost:8000/ws/consciousness"

    async with websockets.connect(uri) as websocket:
        print("Connected to consciousness stream")

        try:
            async for message in websocket:
                thought = json.loads(message)
                print(f"[{thought['stream']}] {thought['content']}")

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

# Run
asyncio.run(stream_consciousness())
```

---

## Error Handling

### Standard Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description",
  "status_code": 500
}
```

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request format |
| 404 | Not Found | Verify endpoint |
| 429 | Too Many Requests | Implement backoff |
| 500 | Internal Error | Retry with exponential backoff |
| 503 | Service Unavailable | Check system status |

### Retry Strategy

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_retry_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

---

## Rate Limiting

### Recommended Limits

| Operation | Limit | Window |
|-----------|-------|--------|
| Read operations | 100 req | 1 minute |
| Thought generation | 20 req | 1 minute |
| Memory consolidation | 10 req | 1 minute |
| WebSocket connections | 5 concurrent | - |

### Rate Limit Headers (Future)

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1732000000
```

---

## Best Practices

### 1. Connection Pooling

```python
# Reuse session for multiple requests
session = requests.Session()
for i in range(100):
    response = session.get(f"{base_url}/health")
```

### 2. Async Operations

```python
import asyncio
import aiohttp

async def fetch_status(session):
    async with session.get('http://localhost:8000/status') as resp:
        return await resp.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_status(session) for _ in range(10)]
        results = await asyncio.gather(*tasks)
```

### 3. Error Handling

```python
try:
    response = client.generate_thought(...)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 503:
        # Service unavailable - retry
        time.sleep(5)
        response = client.generate_thought(...)
    else:
        raise
```

### 4. Timeout Configuration

```python
response = requests.post(
    url,
    json=payload,
    timeout=(3.05, 27)  # (connect timeout, read timeout)
)
```

---

## SDKs & Libraries

### Official SDKs

Coming soon:
- Python SDK (`pip install claude-agi-sdk`)
- JavaScript/TypeScript SDK (`npm install claude-agi-client`)
- Go SDK (planned)

### Community Libraries

Check GitHub for community-contributed clients in various languages.

---

## Interactive API Playground

Access the interactive Swagger UI documentation:

**Development**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc

Features:
- Try all endpoints directly in browser
- See request/response schemas
- View examples and descriptions
- Export OpenAPI spec

---

## Support & Resources

- **Documentation**: https://github.com/doublegate/Claude-AGI
- **API Issues**: https://github.com/doublegate/Claude-AGI/issues
- **Discussions**: https://github.com/doublegate/Claude-AGI/discussions
- **Examples**: See `examples/api-clients/` directory

---

## Changelog

### v1.6.2 (2025-11-19)
- Added advanced reasoning capabilities
- Enhanced memory association network
- Creative synthesis engine
- Improved dream analysis

### v1.6.0 (2025-11-18)
- Architecture refactoring complete
- Production monitoring infrastructure
- Performance optimizations

### v1.0.0 (2025-06-02)
- Initial API release
- Core consciousness and memory endpoints

---

**Happy Building! 🚀**

For questions or issues, please open a GitHub issue or discussion.
