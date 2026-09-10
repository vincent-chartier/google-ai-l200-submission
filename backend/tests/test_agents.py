"""Integration and Unit tests for the 4-Agent Cinema Outings System."""

import pytest
import asyncio
from backend.agents.coordinator_agent import OutingCoordinatorService
from backend.state.memory_manager import (
    initialize_user_session_state,
    add_movie_to_seen_history,
    add_movie_to_favorites
)
from backend.tools.booking_transactions import (
    get_seat_availability,
    hold_seats_reservation,
    process_ticket_payment
)
from backend.tools.calendar_tools import create_calendar_invite


@pytest.mark.asyncio
async def test_coordinator_search_flow_with_state_passing():
    coordinator = OutingCoordinatorService()
    session_id = "test_sess_01"
    
    # Pre-populate state with favorites and seen movies
    state = coordinator.get_or_create_session(session_id)
    add_movie_to_seen_history(state, "Oppenheimer")
    
    # 1. Ask for recommendation
    resp = await coordinator.handle_user_message(session_id, "Recommend a great sci-fi movie for Friday")
    assert resp.agent == "SearchRecoAgent"
    assert len(resp.components) >= 1
    assert resp.components[0].type == "movie_card"
    
    # Verify Oppenheimer is NOT recommended because it's in seen_movies
    for comp in resp.components:
        assert "Oppenheimer" not in comp.props.get("title", "")


@pytest.mark.asyncio
async def test_coordinator_seat_and_booking_flow():
    coordinator = OutingCoordinatorService()
    session_id = "test_sess_02"
    
    # 1. Ask for seats
    seat_resp = await coordinator.handle_user_message(session_id, "Show me seats for Dune")
    assert seat_resp.agent == "BookingAgent"
    assert len(seat_resp.components) >= 1
    assert seat_resp.components[0].type == "seat_map_selector"
    
    # 2. Hold seats via A2UI Action
    hold_resp = await coordinator.handle_a2ui_action(
        session_id=session_id,
        action="HOLD_SEATS",
        payload={"showtime_id": "SH-DUNE-1930", "seats": ["F7", "F8"]}
    )
    assert hold_resp.agent == "BookingAgent"
    assert "Locked in seats" in hold_resp.text
    
    # 3. Confirm Payment via A2UI Action
    pay_resp = await coordinator.handle_a2ui_action(
        session_id=session_id,
        action="CONFIRM_PAYMENT",
        payload={}
    )
    assert pay_resp.agent == "BookingAgent"
    assert len(pay_resp.components) >= 1
    assert pay_resp.components[0].type == "ticket_pass"
    assert "BK-" in pay_resp.components[0].props["booking_id"]


@pytest.mark.asyncio
async def test_housekeeping_calendar_invite():
    coordinator = OutingCoordinatorService()
    session_id = "test_sess_03"
    
    # Ask for calendar invite
    cal_resp = await coordinator.handle_user_message(session_id, "Send calendar invite for my movie outing")
    assert cal_resp.agent == "HousekeepingAgent"
    assert len(cal_resp.components) >= 1
    assert cal_resp.components[0].type == "calendar_invite_card"
    assert "BEGIN:VCALENDAR" in cal_resp.components[0].props["ics_content"]


@pytest.mark.asyncio
async def test_profile_favorites_sync():
    coordinator = OutingCoordinatorService()
    session_id = "test_sess_04"
    
    # Add favorite via A2UI action
    fav_resp = await coordinator.handle_a2ui_action(
        session_id=session_id,
        action="ADD_FAVORITE",
        payload={"movie_title": "Blade Runner 2049", "genre": "Sci-Fi"}
    )
    assert fav_resp.agent == "HousekeepingAgent"
    
    state = coordinator.get_or_create_session(session_id)
    fav_titles = [m["title"] for m in state["favorite_movies"]]
    assert "Blade Runner 2049" in fav_titles
