"""Unit tests for A2UI Protocol models, serialization, and builders."""

import pytest
from backend.protocols.a2ui import (
    A2UIMessage,
    A2UIComponent,
    A2UIAction,
    A2UIQuickReply,
    build_movie_card_component,
    build_seat_map_component,
    build_ticket_pass_component,
    build_calendar_invite_component
)

def test_a2ui_message_serialization():
    comp = A2UIComponent(
        type="test_card",
        props={"title": "Test Movie", "rating": 8.5},
        actions=[A2UIAction(label="Click Me", action="TEST_ACTION", payload={"id": 1})]
    )
    msg = A2UIMessage(
        session_id="s123",
        agent="SearchRecoAgent",
        text="Check this out:",
        components=[comp],
        quick_replies=[A2UIQuickReply(label="Reply 1", action="ACTION_1")]
    )
    
    data = msg.model_dump()
    assert data["protocol_version"] == "1.0"
    assert data["session_id"] == "s123"
    assert data["agent"] == "SearchRecoAgent"
    assert len(data["components"]) == 1
    assert data["components"][0]["type"] == "test_card"
    assert len(data["quick_replies"]) == 1


def test_build_movie_card():
    movie = {
        "id": "dune-2",
        "title": "Dune: Part Two",
        "genres": ["Sci-Fi"],
        "imdb_rating": 8.6,
        "runtime": "166 min"
    }
    cmp = build_movie_card_component(movie, taste_match_reason="Matches Interstellar")
    assert cmp.type == "movie_card"
    assert cmp.props["title"] == "Dune: Part Two"
    assert cmp.props["taste_match_reason"] == "Matches Interstellar"
    assert len(cmp.actions) >= 1


def test_build_seat_map():
    seat_data = {
        "showtime_id": "SH-1",
        "movie_title": "Interstellar",
        "hall": "IMAX",
        "seat_grid": []
    }
    cmp = build_seat_map_component(seat_data)
    assert cmp.type == "seat_map_selector"
    assert cmp.props["movie_title"] == "Interstellar"


def test_build_ticket_pass():
    booking = {
        "booking_id": "BK-1234",
        "movie_title": "Dune: Part Two",
        "seats": ["F7", "F8"],
        "total_amount": 39.0
    }
    cmp = build_ticket_pass_component(booking)
    assert cmp.type == "ticket_pass"
    assert cmp.props["booking_id"] == "BK-1234"
