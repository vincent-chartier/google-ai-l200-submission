"""FastAPI Backend Gateway for AI Cinema Outings Application.

Serves A2UI protocol responses, processes interactive actions,
and connects the Flutter frontend to the Python Google ADK Multi-Agent system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from backend.protocols.a2ui import A2UIMessage
from backend.agents.coordinator_agent import OutingCoordinatorService
from backend.config import APP_HOST, APP_PORT

app = FastAPI(
    title="Cinema Outings Multi-Agent Backend",
    description="Powered by Google ADK, Gemini, MCP, and A2UI Protocol",
    version="1.0.0"
)

# Enable CORS for Flutter client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Coordinator Service
coordinator = OutingCoordinatorService()


class ChatRequest(BaseModel):
    session_id: str = "demo_session"
    message: str


class ActionRequest(BaseModel):
    session_id: str = "demo_session"
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class FavoriteRequest(BaseModel):
    session_id: str = "demo_session"
    movie_title: str
    genre: str = "Sci-Fi"
    rating: float = 5.0


class SeenRequest(BaseModel):
    session_id: str = "demo_session"
    movie_title: str
    cinema: str = "Metropolis Cinema IMAX"
    user_score: float = 5.0


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint with model routing and security guardrail status."""
    return {
        "status": "healthy",
        "service": "cinema-outings-agent-backend",
        "agents": [
            "OutingCoordinatorAgent",
            "SearchRecoAgent",
            "BookingAgent",
            "HousekeepingAgent"
        ],
        "protocols": ["A2UI v1.0", "MCP v1.0"],
        "model_routing": coordinator.routing_config,
        "security_guardrails": [
            "InputSecurityGuardrailPlugin (Injection & PII Defense)",
            "BookingSafetyGuardrailPlugin (Hold Validation & Rate-limiting)",
            "A2UIValidationGuardrailPlugin (Contract Verification)"
        ],
        "evaluations": [
            "RecommendationEvaluationPlugin (Negative Constraints / Zero Seen)",
            "ToolSequenceEvaluationPlugin (Transaction State Machine)",
            "LatencyAndCostTelemetryPlugin (Gemini Flash vs Pro vs Flash-Lite)"
        ]
    }


@app.get("/api/v1/telemetry")
async def get_telemetry():
    """Returns runtime latency and cost telemetry across model tiers."""
    return coordinator.telemetry.get_summary()


@app.post("/api/v1/agent/chat", response_model=A2UIMessage)
async def chat_with_agents(req: ChatRequest):
    """Conversational endpoint returning A2UI protocol messages."""
    try:
        response = await coordinator.handle_user_message(
            session_id=req.session_id,
            user_message=req.message
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/a2ui/action", response_model=A2UIMessage)
async def handle_a2ui_widget_action(req: ActionRequest):
    """Processes interactive widget actions from Flutter and returns new A2UI UI."""
    try:
        response = await coordinator.handle_a2ui_action(
            session_id=req.session_id,
            action=req.action,
            payload=req.payload
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/user/state/{session_id}")
async def get_session_state(session_id: str):
    """Fetches user session memory (favorite movies, seen movies, active booking)."""
    state = coordinator.get_or_create_session(session_id)
    return state


@app.post("/api/v1/user/favorites")
async def add_favorite_movie(req: FavoriteRequest):
    """Adds a favorite movie directly to session memory."""
    state = coordinator.get_or_create_session(req.session_id)
    entry = coordinator.housekeeping_service.add_favorite(
        movie_title=req.movie_title,
        genre=req.genre,
        session_state=state
    )
    return {"success": True, "entry": entry, "state": state}


@app.post("/api/v1/user/seen")
async def add_seen_movie(req: SeenRequest):
    """Adds a watched movie directly to session memory."""
    state = coordinator.get_or_create_session(req.session_id)
    entry = coordinator.housekeeping_service.record_watched_movie(
        movie_title=req.movie_title,
        session_state=state,
        user_score=req.user_score
    )
    return {"success": True, "entry": entry, "state": state}


# Mount Flutter Web app if built
from fastapi.staticfiles import StaticFiles
from pathlib import Path

web_dir = Path(__file__).resolve().parent.parent / "frontend" / "build" / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="flutter_web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=APP_HOST, port=APP_PORT, reload=True)
