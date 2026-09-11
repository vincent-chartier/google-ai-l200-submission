"""FastAPI Backend Gateway for AI Cinema Outings Application.

Serves A2UI protocol responses, processes interactive actions,
and connects the Flutter frontend to the Python Google ADK Multi-Agent system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from backend.protocols.a2ui import A2UIMessage
from backend.agents.coordinator_agent import OutingCoordinatorService
from backend.config import APP_HOST, APP_PORT
from backend.telemetry.logging import setup_structured_logging, get_recent_structured_logs
from backend.telemetry.tracing import OpenTelemetryMiddleware, get_collected_spans

# Initialize Structured JSON Logging with GCP Cloud Logging formatting
setup_structured_logging()

app = FastAPI(
    title="Cinema Outings Multi-Agent Backend",
    description="Powered by Google ADK, Gemini, MCP, OpenTelemetry, and A2UI Protocol",
    version="1.0.0"
)

# Distributed Tracing: OpenTelemetry W3C trace context propagation
app.add_middleware(OpenTelemetryMiddleware)

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


class CompactRequest(BaseModel):
    session_id: str = "demo_session"
    max_recent_turns: int = 4
    token_threshold: int = 400


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint with model routing, security guardrails, and tracing status."""
    return {
        "status": "healthy",
        "service": "cinema-outings-agent-backend",
        "agents": [
            "OutingCoordinatorAgent",
            "SearchRecoAgent",
            "BookingAgent",
            "HousekeepingAgent"
        ],
        "protocols": ["A2UI v1.0", "MCP v1.0", "OpenTelemetry W3C Tracing"],
        "observability": {
            "structured_logging": "JSON Formatter (GCP Logging Compatible)",
            "distributed_tracing": "OpenTelemetry SDK v1.42",
            "dlp_inspection": "Google Cloud Sensitive Data Protection (DLP)"
        },
        "model_routing": coordinator.routing_config,
        "security_guardrails": [
            "InputSecurityGuardrailPlugin (Prompt Injection & Cloud DLP PII Sanitization)",
            "BookingSafetyGuardrailPlugin (Hold Validation & Rate-limiting)",
            "A2UIValidationGuardrailPlugin (Contract Verification)"
        ],
        "evaluations": [
            "RecommendationEvaluationPlugin (Negative Constraints / Zero Seen)",
            "ToolSequenceEvaluationPlugin (Transaction State Machine)",
            "LatencyAndCostTelemetryPlugin (Gemini Flash vs Pro vs Flash-Lite)",
            "ContextCompactionEvaluationPlugin (History Compaction & Token Reducer)",
            "IntentOutcomeEvaluationPlugin (Explicit Intent vs Outcome Verification)"
        ]
    }


@app.get("/api/v1/telemetry")
async def get_telemetry():
    """Returns runtime latency, cost, DLP sanitization, and intent vs outcome telemetry."""
    return {
        "latency_and_cost": coordinator.telemetry.get_summary(),
        "intent_vs_outcome": coordinator.intent_outcome_evaluator.get_summary(),
        "cloud_dlp": coordinator.input_guardrail.get_dlp_summary(),
        "open_telemetry": {
            "spans_recorded_count": len(get_collected_spans(limit=1000)),
            "service_name": "cinema-outings-agent"
        }
    }


@app.get("/api/v1/telemetry/traces")
async def get_recent_traces(limit: int = 25):
    """Returns recent OpenTelemetry distributed trace spans."""
    return {"spans": get_collected_spans(limit=limit)}


@app.get("/api/v1/telemetry/logs")
async def get_recent_logs(limit: int = 50):
    """Returns recent machine-readable structured JSON logs."""
    return {"logs": get_recent_structured_logs(limit=limit)}


@app.post("/api/v1/agent/chat", response_model=A2UIMessage)
async def chat_with_agents(req: ChatRequest, background_tasks: BackgroundTasks):
    """Conversational endpoint returning A2UI protocol messages."""
    try:
        response = await coordinator.handle_user_message(
            session_id=req.session_id,
            user_message=req.message,
            background_tasks=background_tasks
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/a2ui/action", response_model=A2UIMessage)
async def handle_a2ui_widget_action(req: ActionRequest, background_tasks: BackgroundTasks):
    """Processes interactive widget actions from Flutter and returns new A2UI UI."""
    try:
        response = await coordinator.handle_a2ui_action(
            session_id=req.session_id,
            action=req.action,
            payload=req.payload,
            background_tasks=background_tasks
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
    """Adds a favorite movie directly to session memory and persistent database."""
    state = coordinator.get_or_create_session(req.session_id)
    entry = coordinator.housekeeping_service.add_favorite(
        movie_title=req.movie_title,
        genre=req.genre,
        session_state=state
    )
    await coordinator.db.save_session(req.session_id, state)
    return {"success": True, "entry": entry, "state": state}


@app.post("/api/v1/user/seen")
async def add_seen_movie(req: SeenRequest):
    """Adds a watched movie directly to session memory and persistent database."""
    state = coordinator.get_or_create_session(req.session_id)
    entry = coordinator.housekeeping_service.record_watched_movie(
        movie_title=req.movie_title,
        session_state=state,
        user_score=req.user_score
    )
    await coordinator.db.save_session(req.session_id, state)
    return {"success": True, "entry": entry, "state": state}


@app.post("/api/v1/session/compact")
async def compact_session_history(req: CompactRequest, background_tasks: BackgroundTasks):
    """Triggers dialogue history compaction to prune context bloat."""
    res = await coordinator.compact_session_history_async(
        session_id=req.session_id,
        max_recent_turns=req.max_recent_turns,
        token_threshold=req.token_threshold
    )
    return res


# Mount Flutter Web app if built
from fastapi.staticfiles import StaticFiles
from pathlib import Path

web_dir = Path(__file__).resolve().parent.parent / "frontend" / "build" / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="flutter_web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=APP_HOST, port=APP_PORT, reload=True)
