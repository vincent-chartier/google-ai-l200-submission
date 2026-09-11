"""Unit tests for SQLite Persistence, Real History Summarization, and Async Memory Operations.

Tests:
1. DatabaseManager: synchronous & asynchronous persistence of sessions, turns, favorites, and seen history.
2. Cross-instance recovery: session state survives across coordinator restarts via SQLite.
3. HistorySummarizer: entity extraction (favorites vs seen) and semantic narrative synthesis.
4. HousekeepingService: async compaction (compact_conversation_history_async) with DB updates.
5. CoordinatorAgent: async memory operations and persistence during multi-turn conversations.
6. FastAPI BackgroundTasks and async /api/v1/session/compact endpoint.
"""

import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app import app
from backend.state.database import DatabaseManager
from backend.state.history_summarizer import HistorySummarizer
from backend.agents.coordinator_agent import OutingCoordinatorService
from backend.agents.housekeeping_agent import HousekeepingService
from backend.state.memory_manager import (
    initialize_user_session_state,
    add_conversation_turn
)


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        path = tf.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_database_manager_async_crud(temp_db_path):
    """Verifies async CRUD operations on sessions, turns, favorites, and seen history."""
    db = DatabaseManager(temp_db_path)

    # 1. Save and load session
    state = initialize_user_session_state("user_test_async")
    state["conversation_summary"] = "Prior context: User discussed sci-fi films."
    state["compaction_metadata"] = {"compaction_count": 1, "tokens_saved": 40}
    state["favorite_movies"].append({"title": "Inception", "genre": "Sci-Fi", "rating": 5.0})
    state["seen_movies"].append({"title": "Arrival", "cinema": "IMAX", "user_score": 5.0, "watched_date": "2026-09-10"})

    await db.save_session("session_async_1", state)

    loaded = await db.load_session("session_async_1")
    assert loaded is not None
    assert loaded["user_id"] == "user_test_async"
    assert loaded["conversation_summary"] == "Prior context: User discussed sci-fi films."
    assert any(m["title"] == "Inception" for m in loaded["favorite_movies"])
    assert any(m["title"] == "Arrival" for m in loaded["seen_movies"])

    # 2. Append turns
    turn1 = {"role": "user", "sender": "user", "text": "What time is Dune playing?", "ui_summary": None, "timestamp": 1.0}
    turn2 = {"role": "agent", "sender": "SearchRecoAgent", "text": "Screening at 19:30", "ui_summary": "[UI: movie_card for 'Dune: Part Two']", "timestamp": 2.0}
    id1 = await db.append_turn("session_async_1", turn1)
    id2 = await db.append_turn("session_async_1", turn2)
    assert id1 > 0
    assert id2 > id1

    loaded_with_turns = await db.load_session("session_async_1")
    assert len(loaded_with_turns["conversation_history"]) == 2

    # 3. Mark turn compacted
    await db.mark_turns_compacted("session_async_1", 1)
    loaded_after_compaction = await db.load_session("session_async_1")
    assert len(loaded_after_after := loaded_after_compaction["conversation_history"]) == 1
    assert loaded_after_after[0]["text"] == "Screening at 19:30"


@pytest.mark.asyncio
async def test_session_persistence_across_coordinator_restarts(temp_db_path):
    """Verifies that a session state persists across different OutingCoordinatorService instances."""
    db = DatabaseManager(temp_db_path)
    session_id = "persistent_restart_session"

    # Instance 1: Handle user message and update state
    coordinator1 = OutingCoordinatorService(db=db)
    resp1 = await coordinator1.handle_user_message(session_id=session_id, user_message="I love Interstellar and saw Oppenheimer")
    assert resp1 is not None
    await coordinator1.drain_memory_tasks()

    # Instance 2: Brand new coordinator with empty in-memory cache, connected to same DB
    coordinator2 = OutingCoordinatorService(db=db)
    assert session_id not in coordinator2.sessions  # Not in in-memory cache

    # Load session state through coordinator2
    loaded_state = await coordinator2.get_or_create_session_async(session_id)
    assert loaded_state is not None
    assert session_id in coordinator2.sessions

    fav_titles = [m["title"] for m in loaded_state["favorite_movies"]]
    seen_titles = [m["title"] for m in loaded_state["seen_movies"]]
    assert "Interstellar" in fav_titles
    assert "Oppenheimer" in seen_titles
    assert len(loaded_state["conversation_history"]) >= 2


def test_history_summarizer_entity_extraction_and_narrative():
    """Verifies that HistorySummarizer correctly separates favorites and seen entities and synthesizes narrative."""
    summarizer = HistorySummarizer()

    turns = [
        {"role": "user", "sender": "user", "text": "Can you show me showtimes for Dune: Part Two?", "ui_summary": None},
        {"role": "agent", "sender": "SearchRecoAgent", "text": "Screenings are at Metropolis Cinema.", "ui_summary": "[UI: movie_card for 'Dune: Part Two']"},
        {"role": "user", "sender": "user", "text": "I love Interstellar and also watched Oppenheimer.", "ui_summary": None}
    ]

    state = initialize_user_session_state("summary_test_user")
    summary = summarizer.summarize_sync(turns, existing_summary="", session_state=state)

    # Check narrative synthesis
    assert "Dune: Part Two" in summary or "showtimes" in summary
    assert summary.startswith("Earlier context:")

    # Check entity extraction
    favs = [m["title"] for m in state["favorite_movies"]]
    seen = [m["title"] for m in state["seen_movies"]]
    assert "Interstellar" in favs
    assert "Oppenheimer" in seen


@pytest.mark.asyncio
async def test_housekeeping_async_compaction_with_db(temp_db_path):
    """Verifies that HousekeepingService.compact_conversation_history_async updates state and DB."""
    db = DatabaseManager(temp_db_path)
    housekeeping = HousekeepingService()
    session_id = "housekeeping_async_session"

    state = initialize_user_session_state(session_id)
    await db.save_session(session_id, state)

    # Add 6 dialogue turns
    for i in range(6):
        turn_u = add_conversation_turn(state, role="user", text=f"Query {i}: Where is screening {i}?")
        await db.append_turn(session_id, turn_u)
        turn_a = add_conversation_turn(state, role="agent", text=f"Screening {i} is at Metropolis Cinema.")
        await db.append_turn(session_id, turn_a)

    assert len(state["conversation_history"]) == 12

    # Run async compaction
    res = await housekeeping.compact_conversation_history_async(
        session_state=state,
        max_recent_turns=4,
        token_threshold=50,
        session_id=session_id,
        db=db
    )

    assert res["compacted"] is True
    assert res["turns_compacted_count"] == 8
    assert res["remaining_turns_count"] == 4
    assert res["tokens_saved"] > 0

    # Verify persistent DB was updated
    db_state = await db.load_session(session_id)
    assert len(db_state["conversation_history"]) == 4
    assert db_state["conversation_summary"] != ""
    assert db_state["compaction_metadata"]["compaction_count"] == 1


@pytest.mark.asyncio
async def test_coordinator_async_compaction_and_api(temp_db_path):
    """Verifies coordinator.compact_session_history_async and FastAPI POST /api/v1/session/compact."""
    coordinator = OutingCoordinatorService(db=DatabaseManager(temp_db_path))
    session_id = "coordinator_async_api_session"

    # Multi-turn interaction (2 user turns = 4 total turns, under auto-trigger threshold)
    await coordinator.handle_user_message(session_id=session_id, user_message="What movies are playing?")
    await coordinator.handle_user_message(session_id=session_id, user_message="Show me showtimes for Dune: Part Two")
    await coordinator.drain_memory_tasks()

    # Call async compaction directly
    result = await coordinator.compact_session_history_async(
        session_id=session_id,
        max_recent_turns=2,
        token_threshold=10
    )
    assert result["compacted"] is True

    # Add further turn to compact via API
    await coordinator.handle_user_message(session_id=session_id, user_message="I love Interstellar")
    await coordinator.drain_memory_tasks()

    # Call via FastAPI HTTP endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/session/compact",
            json={"session_id": session_id, "max_recent_turns": 2, "token_threshold": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "compacted" in data


def test_search_reco_utilizes_compacted_conversation_summary():
    """Verifies that SearchRecoService actively prioritizes movies based on conversation_summary."""
    from backend.agents.search_reco_agent import SearchRecoService

    service = SearchRecoService()
    session_state = {
        "user_id": "test_user_summary",
        "favorite_movies": [],
        "seen_movies": [],
        "conversation_summary": "Earlier context: User expressed strong interest in Denis Villeneuve, Dune, and epic sci-fi."
    }

    result = service.search_and_recommend(query="What should I watch?", session_state=session_state)
    assert len(result["components"]) >= 1
    assert "conversation" in result["text"].lower()

    # Verify top recommended movie matches the compacted context
    top_card = result["components"][0]
    reason = top_card.props.get("taste_match_reason", "").lower()
    assert "conversation" in reason or "sci-fi" in reason or "denis villeneuve" in reason


def test_booking_persistence_across_separate_db_instances(temp_db_path):
    """Verifies that reservations and bookings persist in SQLite across independent DB instances without in-memory dicts."""
    db1 = DatabaseManager(temp_db_path)
    showtime_id = "SH-DUNE-1930"

    # 1. Save a reservation directly in DB instance 1
    res_data = {
        "token": "HLD-TEST-RECOVERY-99",
        "showtime_id": showtime_id,
        "movie_title": "Dune: Part Two",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "IMAX Laser Hall",
        "date_time": "2026-09-12 19:30",
        "seats": ["E3", "E4"],
        "subtotal": 36.0,
        "booking_fee": 3.0,
        "total_amount": 39.0,
        "user_id": "user_recovery",
        "expires_at": 9999999999.0
    }
    db1.save_reservation_sync(res_data)

    # 2. Independent DB instance 2 loads reservation from SQLite
    db2 = DatabaseManager(temp_db_path)
    loaded_res = db2.get_reservation_sync("HLD-TEST-RECOVERY-99")
    assert loaded_res is not None
    assert loaded_res["token"] == "HLD-TEST-RECOVERY-99"
    assert loaded_res["seats"] == ["E3", "E4"]

    # 3. Save booking and occupied seats in DB instance 2
    booking_data = {
        "booking_id": "BK-TEST-RECOVERY-01",
        "showtime_id": showtime_id,
        "movie_title": "Dune: Part Two",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "IMAX Laser Hall",
        "date_time": "2026-09-12 19:30",
        "seats": ["E3", "E4"],
        "number_of_tickets": 2,
        "total_amount": 39.0,
        "payment_method": "Google Pay",
        "user_name": "Test Guest",
        "qr_code_token": "PASS://TEST",
        "transaction_timestamp": "2026-09-11T12:00:00Z",
        "status": "CONFIRMED"
    }
    db2.save_booking_sync(booking_data)
    db2.add_occupied_seats_sync(showtime_id, ["E3", "E4"], "BK-TEST-RECOVERY-01")

    # 4. Third independent DB instance retrieves the booking and occupied seats
    db3 = DatabaseManager(temp_db_path)
    loaded_booking = db3.get_booking_sync("BK-TEST-RECOVERY-01")
    assert loaded_booking is not None
    assert loaded_booking["movie_title"] == "Dune: Part Two"
    assert loaded_booking["seats"] == ["E3", "E4"]

    occupied = db3.get_occupied_seats_sync(showtime_id)
    assert "E3" in occupied
    assert "E4" in occupied


@pytest.mark.asyncio
async def test_non_blocking_async_memory_execution(temp_db_path):
    """Verifies that handle_user_message returns immediately and background tasks flush turns to DB."""
    import time
    db = DatabaseManager(temp_db_path)
    coordinator = OutingCoordinatorService(db=db)
    session_id = "async_non_blocking_sess"

    t0 = time.time()
    resp = await coordinator.handle_user_message(session_id=session_id, user_message="Find me top movies")
    duration = time.time() - t0

    # User receives response promptly (sub-second)
    assert resp is not None
    assert duration < 1.0

    # Background task set exists or has tasks running/queued
    await coordinator.drain_memory_tasks()

    # Now verify persistent SQLite DB has the turns
    loaded = await db.load_session(session_id)
    assert loaded is not None
    assert len(loaded["conversation_history"]) >= 2
