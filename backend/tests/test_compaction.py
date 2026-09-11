"""Unit tests for History Compaction and Context Bloat Management.

Tests:
1. Conversation turn tracking and A2UI lightweight semantic summarization.
2. Turn-count and token-threshold compaction via HousekeepingService.
3. User profile entity preservation (favorites and watched list) during compaction.
4. OutingCoordinator automatic multi-turn compaction lifecycle.
5. ContextCompactionEvaluationPlugin evaluation metrics.
6. FastAPI /api/v1/session/compact and health endpoint checks.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app
from backend.state.memory_manager import (
    initialize_user_session_state,
    add_conversation_turn,
    estimate_history_tokens,
    get_compacted_context,
    apply_history_compaction,
    summarize_a2ui_components
)
from backend.agents.coordinator_agent import OutingCoordinatorService
from backend.agents.housekeeping_agent import HousekeepingService
from backend.plugins.evaluation_plugins import ContextCompactionEvaluationPlugin
from backend.protocols.a2ui import A2UIComponent


def test_turn_recording_and_a2ui_summarization():
    """Verifies that conversation turns are recorded with lightweight UI summaries."""
    state = initialize_user_session_state(user_id="test_user")
    assert state["conversation_history"] == []
    assert state["conversation_summary"] == ""

    # Add user turn
    turn1 = add_conversation_turn(state, role="user", text="What movies are playing today?", sender="user")
    assert len(state["conversation_history"]) == 1
    assert turn1["role"] == "user"
    assert turn1["ui_summary"] is None

    # Add agent turn with heavy A2UI components
    heavy_components = [
        A2UIComponent(
            id="movie_1",
            type="movie_card",
            props={"title": "Dune: Part Two", "showtimes": ["19:30"]},
            actions=[]
        ),
        A2UIComponent(
            id="seats_1",
            type="seat_map",
            props={"movie_title": "Dune: Part Two", "showtime_id": "SH-DUNE-1930", "grid": [["A1", "A2"], ["B1", "B2"]]},
            actions=[]
        )
    ]
    turn2 = add_conversation_turn(
        state,
        role="agent",
        text="Here are the screenings and seat options.",
        sender="SearchRecoAgent",
        a2ui_components=heavy_components
    )
    assert len(state["conversation_history"]) == 2
    assert "[UI: movie_card for 'Dune: Part Two']" in turn2["ui_summary"]
    assert "[UI: seat_map for 'Dune: Part Two' (SH-DUNE-1930)]" in turn2["ui_summary"]


def test_token_estimation_and_compaction():
    """Tests token count estimation and history compaction trimming."""
    state = initialize_user_session_state(user_id="test_user")
    housekeeping = HousekeepingService()

    # Add 6 conversation turns
    for i in range(6):
        add_conversation_turn(state, role="user", text=f"Query number {i}: Can you show me screening {i}?")
        add_conversation_turn(state, role="agent", text=f"Screening {i} is available at Metropolis Cinema.")

    assert len(state["conversation_history"]) == 12
    tokens_before = estimate_history_tokens(state["conversation_history"])
    assert tokens_before > 100

    # Compact down to 4 recent turns
    result = housekeeping.compact_conversation_history(
        session_state=state,
        max_recent_turns=4,
        token_threshold=50
    )

    assert result["compacted"] is True
    assert result["turns_compacted_count"] == 8
    assert result["remaining_turns_count"] == 4
    assert len(state["conversation_history"]) == 4
    assert result["tokens_after"] < result["tokens_before"]
    assert result["tokens_saved"] > 0
    assert state["conversation_summary"] != ""
    assert state["compaction_metadata"]["compaction_count"] == 1


def test_entity_extraction_during_compaction():
    """Tests that user likes/seen films in compacted turns are saved into session state."""
    state = initialize_user_session_state(user_id="test_user")
    housekeeping = HousekeepingService()

    # User expresses preferences inside dialogue
    add_conversation_turn(state, role="user", text="I love Interstellar and Sci-Fi movies so much!")
    add_conversation_turn(state, role="agent", text="Interstellar is a modern sci-fi masterpiece.")
    add_conversation_turn(state, role="user", text="Also I already watched Oppenheimer last summer.")
    add_conversation_turn(state, role="agent", text="Noted, Oppenheimer is logged in your seen history.")

    # Additional filler turns to push older turns into compaction window
    for i in range(5):
        add_conversation_turn(state, role="user", text=f"What about screening option {i}?")
        add_conversation_turn(state, role="agent", text=f"Option {i} has plenty of seats.")

    # Compact history
    res = housekeeping.compact_conversation_history(state, max_recent_turns=4)
    assert res["compacted"] is True

    # Verify entities are in session state
    fav_titles = [m["title"] for m in state["favorite_movies"]]
    seen_titles = [m["title"] for m in state["seen_movies"]]
    assert "Interstellar" in fav_titles
    assert "Oppenheimer" in seen_titles


@pytest.mark.asyncio
async def test_coordinator_automatic_compaction_flow():
    """Tests that OutingCoordinator automatically tracks turns and compacts history."""
    coordinator = OutingCoordinatorService()
    session_id = "compaction_flow_session"

    # Send multiple messages to cross the threshold
    prompts = [
        "What movies are currently showing?",
        "Show me showtimes for Dune: Part Two",
        "Can I see seats for 19:30?",
        "What is in my watched list?",
        "Recommend another sci-fi movie please"
    ]

    for p in prompts:
        resp = await coordinator.handle_user_message(session_id=session_id, user_message=p)
        assert resp is not None

    session_state = coordinator.get_or_create_session(session_id)
    compaction_meta = session_state.get("compaction_metadata", {})
    assert compaction_meta.get("compaction_count", 0) >= 1
    assert session_state.get("conversation_summary") != ""


def test_context_compaction_evaluation_plugin():
    """Verifies that the ContextCompactionEvaluationPlugin correctly scores compression and entity preservation."""
    plugin = ContextCompactionEvaluationPlugin()

    eval_result = plugin.evaluate_compaction(
        tokens_before=1200,
        tokens_after=350,
        turns_compacted=8,
        remaining_turns=4
    )
    assert eval_result["passed"] is True
    assert eval_result["tokens_saved"] == 850
    assert eval_result["reduction_rate"] > 0.70

    # Entity preservation check
    pres_result = plugin.evaluate_entity_preservation(
        expected_entities=["Interstellar", "Oppenheimer"],
        actual_entities=["Interstellar", "Oppenheimer", "Arrival"]
    )
    assert pres_result["passed"] is True
    assert pres_result["preservation_rate"] == 1.0


@pytest.mark.asyncio
async def test_api_session_compact_endpoint():
    """Tests POST /api/v1/session/compact and GET /api/v1/health endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check includes ContextCompactionEvaluationPlugin
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        evaluations = health_resp.json().get("evaluations", [])
        assert any("ContextCompactionEvaluationPlugin" in e for e in evaluations)

        # 2. Chat to create session turns
        chat_resp = await client.post(
            "/api/v1/agent/chat",
            json={"session_id": "api_test_session", "message": "Hello, show me sci-fi movies"}
        )
        assert chat_resp.status_code == 200

        # 3. Trigger manual compaction endpoint
        compact_resp = await client.post(
            "/api/v1/session/compact",
            json={"session_id": "api_test_session", "max_recent_turns": 1, "token_threshold": 10}
        )
        assert compact_resp.status_code == 200
        data = compact_resp.json()
        assert "compacted" in data
