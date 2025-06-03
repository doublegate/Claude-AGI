"""
FastAPI server for Claude-AGI external interaction
=================================================

Provides REST API endpoints for interacting with the consciousness system.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..core.orchestrator import AGIOrchestrator, SystemState
from ..memory.manager import MemoryManager
from ..consciousness.stream import ConsciousnessStream
from ..core.ai_integration import ThoughtGenerator
from ..database.models import EmotionalState, MemoryType, StreamType
from ..database.connections import get_db_manager

import logging

logger = logging.getLogger(__name__)


# Request/Response models
class ThoughtRequest(BaseModel):
    """Request model for generating a thought"""
    stream_type: StreamType = StreamType.PRIMARY
    context: Dict[str, Any] = Field(default_factory=dict)
    emotional_state: Optional[EmotionalState] = None


class ThoughtResponse(BaseModel):
    """Response model for a generated thought"""
    thought_id: str
    content: str
    stream_type: StreamType
    timestamp: datetime
    emotional_state: Optional[EmotionalState] = None
    importance: float = Field(ge=0, le=1)


class MemoryQuery(BaseModel):
    """Request model for memory queries"""
    query: str
    memory_type: Optional[MemoryType] = None
    limit: int = Field(default=10, ge=1, le=100)


class ConversationRequest(BaseModel):
    """Request model for conversation"""
    message: str
    conversation_id: Optional[str] = None
    emotional_context: Optional[EmotionalState] = None


class ConversationResponse(BaseModel):
    """Response model for conversation"""
    response: str
    conversation_id: str
    emotional_state: EmotionalState
    thought_count: int


class SystemStatus(BaseModel):
    """System status information"""
    state: SystemState
    uptime_seconds: float
    total_thoughts: int
    active_streams: List[str]
    memory_count: int
    current_activity: str


# Global instances (will be initialized on startup)
orchestrator: Optional[AGIOrchestrator] = None
memory_manager: Optional[MemoryManager] = None
thought_generator: Optional[ThoughtGenerator] = None
startup_time: datetime = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global orchestrator, memory_manager, thought_generator
    
    logger.info("Starting Claude-AGI API server...")
    
    # Initialize components
    try:
        # Create orchestrator
        config = {
            'environment': os.getenv('CLAUDE_AGI_ENV', 'development'),
            'api_key': os.getenv('ANTHROPIC_API_KEY')
        }
        orchestrator = AGIOrchestrator(config=config)
        
        # Initialize memory manager
        memory_manager = await MemoryManager.create()
        await memory_manager.initialize(use_database=True)
        
        # Initialize thought generator
        thought_generator = ThoughtGenerator()
        
        # Start orchestrator in background
        asyncio.create_task(orchestrator.run())
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Claude-AGI API server...")
    if orchestrator:
        orchestrator.running = False
    if memory_manager:
        await memory_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Claude-AGI API",
    description="API for interacting with Claude's consciousness system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "components": {
            "orchestrator": orchestrator is not None and orchestrator.running,
            "memory": memory_manager is not None,
            "thought_generator": thought_generator is not None
        }
    }


# System status endpoint
@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get current system status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    # Get consciousness stream info
    consciousness_service = orchestrator.services.get('consciousness')
    if consciousness_service:
        total_thoughts = consciousness_service.total_thoughts
        active_streams = list(consciousness_service.streams.keys())
    else:
        total_thoughts = 0
        active_streams = []
    
    # Get memory count (simplified for now)
    memory_count = 0
    if memory_manager:
        recent_memories = await memory_manager.recall_recent(100)
        memory_count = len(recent_memories)
    
    return SystemStatus(
        state=orchestrator.state,
        uptime_seconds=uptime,
        total_thoughts=total_thoughts,
        active_streams=active_streams,
        memory_count=memory_count,
        current_activity=orchestrator.state.value
    )


# Thought generation endpoint
@app.post("/thoughts/generate", response_model=ThoughtResponse)
async def generate_thought(request: ThoughtRequest):
    """Generate a single thought"""
    if not thought_generator:
        raise HTTPException(status_code=503, detail="Thought generator not initialized")
    
    try:
        # Generate thought
        thought = await thought_generator.generate_thought(
            stream_type=request.stream_type,
            context=request.context,
            emotional_state=request.emotional_state
        )
        
        # Store in memory if available
        thought_id = "temp-" + str(thought['timestamp'].timestamp())
        if memory_manager:
            thought_id = await memory_manager.store_thought(thought)
        
        return ThoughtResponse(
            thought_id=thought_id,
            content=thought['content'],
            stream_type=request.stream_type,
            timestamp=thought['timestamp'],
            emotional_state=thought.get('emotional_state'),
            importance=thought.get('importance', 0.5)
        )
        
    except Exception as e:
        logger.error(f"Failed to generate thought: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Memory query endpoint
@app.post("/memory/query")
async def query_memory(query: MemoryQuery):
    """Query memories"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    
    try:
        # Search for similar memories
        memories = await memory_manager.recall_similar(query.query, k=query.limit)
        
        return {
            "query": query.query,
            "results": memories,
            "count": len(memories)
        }
        
    except Exception as e:
        logger.error(f"Memory query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Recent thoughts endpoint
@app.get("/thoughts/recent")
async def get_recent_thoughts(limit: int = 10, stream: Optional[str] = None):
    """Get recent thoughts"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    
    try:
        thoughts = await memory_manager.recall_recent(limit)
        
        # Filter by stream if specified
        if stream:
            thoughts = [t for t in thoughts if t.get('stream') == stream]
        
        return {
            "thoughts": thoughts,
            "count": len(thoughts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent thoughts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Conversation endpoint
@app.post("/conversation", response_model=ConversationResponse)
async def have_conversation(request: ConversationRequest):
    """Have a conversation with Claude"""
    if not thought_generator or not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv-{datetime.utcnow().timestamp()}"
        
        # Update orchestrator state
        orchestrator.state = SystemState.CONVERSING
        
        # Notify consciousness stream about user input
        consciousness_service = orchestrator.services.get('consciousness')
        if consciousness_service:
            await consciousness_service.handle_user_input({
                'message': request.message,
                'conversation_id': conversation_id
            })
        
        # Generate response
        response = await thought_generator.generate_response(
            user_input=request.message,
            emotional_state=request.emotional_context
        )
        
        # Get current emotional state
        emotional_state = request.emotional_context or EmotionalState()
        
        # Get thought count
        thought_count = consciousness_service.total_thoughts if consciousness_service else 0
        
        return ConversationResponse(
            response=response,
            conversation_id=conversation_id,
            emotional_state=emotional_state,
            thought_count=thought_count
        )
        
    except Exception as e:
        logger.error(f"Conversation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time consciousness stream
@app.websocket("/ws/consciousness")
async def websocket_consciousness(websocket: WebSocket):
    """WebSocket endpoint for streaming consciousness"""
    await websocket.accept()
    
    if not orchestrator:
        await websocket.close(code=1003, reason="System not initialized")
        return
    
    try:
        # Subscribe to consciousness stream
        consciousness_service = orchestrator.services.get('consciousness')
        if not consciousness_service:
            await websocket.close(code=1003, reason="Consciousness service not available")
            return
        
        # Stream thoughts as they are generated
        while True:
            # This is simplified - in reality, you'd subscribe to thought events
            await asyncio.sleep(2)  # Check every 2 seconds
            
            # Get latest thoughts
            for stream in consciousness_service.streams.values():
                recent = stream.get_recent(1)
                if recent:
                    thought = recent[0]
                    await websocket.send_json({
                        "type": "thought",
                        "stream": stream.stream_id,
                        "content": thought.get('content', ''),
                        "timestamp": thought.get('timestamp', 0),
                        "emotional_tone": thought.get('emotional_tone', 'neutral')
                    })
                    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


# Memory consolidation endpoint
@app.post("/memory/consolidate")
async def consolidate_memory():
    """Trigger memory consolidation"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    
    try:
        await memory_manager.consolidate_memories()
        return {"status": "success", "message": "Memory consolidation completed"}
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System control endpoints
@app.post("/system/pause")
async def pause_system():
    """Pause the consciousness system"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.state = SystemState.IDLE
    return {"status": "paused", "state": orchestrator.state.value}


@app.post("/system/resume")
async def resume_system():
    """Resume the consciousness system"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.state = SystemState.THINKING
    return {"status": "resumed", "state": orchestrator.state.value}


@app.post("/system/sleep")
async def sleep_system():
    """Put system into sleep mode for memory consolidation"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.state = SystemState.SLEEPING
    
    # Trigger memory consolidation
    if memory_manager:
        asyncio.create_task(memory_manager.consolidate_memories())
    
    return {"status": "sleeping", "state": orchestrator.state.value}


# Main entry point for running the server
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server"""
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=os.getenv("CLAUDE_AGI_ENV") == "development",
        log_level="info"
    )


if __name__ == "__main__":
    run_server()