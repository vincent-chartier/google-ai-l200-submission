"""Unit tests for Strategic Model Routing and Intent Classification."""

import pytest
from backend.routers.semantic_router import SemanticRouter, RouteIntent, ModelTier


@pytest.fixture
def router():
    return SemanticRouter()


def test_routing_booking_confirm(router):
    decision = router.route("I want to confirm and pay for my seats with Google Pay")
    assert decision.intent == RouteIntent.BOOKING_CONFIRM
    assert decision.target_agent == "BookingAgent"
    assert decision.model_tier == ModelTier.DETERMINISTIC


def test_routing_booking_seats_with_time_extraction(router):
    decision = router.route("Show me the seat map for 21:15 showtime")
    assert decision.intent == RouteIntent.BOOKING_SEATS
    assert decision.target_agent == "BookingAgent"
    assert decision.extracted_params.get("showtime") == "21:15"


def test_routing_housekeeping_history(router):
    decision = router.route("Show my watched movie history")
    assert decision.intent == RouteIntent.HOUSEKEEPING_HISTORY
    assert decision.target_agent == "HousekeepingAgent"
    assert decision.model_tier == ModelTier.LITE


def test_routing_housekeeping_calendar(router):
    decision = router.route("Export my cinema booking to google calendar ics")
    assert decision.intent == RouteIntent.HOUSEKEEPING_CALENDAR
    assert decision.target_agent == "HousekeepingAgent"
    assert decision.model_tier == ModelTier.LITE


def test_routing_search_reco_fast_tier(router):
    decision = router.route("What movies are playing today?")
    assert decision.intent == RouteIntent.SEARCH_RECO
    assert decision.target_agent == "SearchRecoAgent"
    assert decision.model_tier == ModelTier.FAST


def test_routing_search_reco_deep_reasoning_tier(router):
    # Triggers deep reasoning due to taste comparison / explanation
    decision = router.route("Explain why I would enjoy Dune Part Two and compare its cinematography to Interstellar")
    assert decision.intent == RouteIntent.SEARCH_RECO
    assert decision.target_agent == "SearchRecoAgent"
    assert decision.model_tier == ModelTier.DEEP_REASONING
    assert "compare" in decision.complexity_factors or "cinematography" in decision.complexity_factors
