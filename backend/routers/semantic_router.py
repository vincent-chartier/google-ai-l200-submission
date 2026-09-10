"""Semantic Router for Cinema Outings Multi-Agent System.

Analyzes user requests, classifies multi-agent intent, evaluates reasoning
complexity, and selects the optimal Gemini model tier (Flash vs Pro vs Flash-Lite).
"""

import re
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field

from backend.config import MODEL_ROUTING_CONFIG, DEFAULT_MODEL


class RouteIntent(str, Enum):
    SEARCH_RECO = "SEARCH_RECO"
    BOOKING_SEATS = "BOOKING_SEATS"
    BOOKING_CONFIRM = "BOOKING_CONFIRM"
    HOUSEKEEPING_HISTORY = "HOUSEKEEPING_HISTORY"
    HOUSEKEEPING_FAVORITE = "HOUSEKEEPING_FAVORITE"
    HOUSEKEEPING_CALENDAR = "HOUSEKEEPING_CALENDAR"
    GENERAL_CHAT = "GENERAL_CHAT"


class ModelTier(str, Enum):
    FAST = "FAST"                     # Low-latency, cost-efficient (Gemini 2.5 Flash)
    DEEP_REASONING = "DEEP_REASONING" # High reasoning, nuanced synthesis (Gemini 2.5 Pro)
    DETERMINISTIC = "DETERMINISTIC"   # Tool & transaction execution (Gemini 2.5 Flash)
    LITE = "LITE"                     # Ultra-lightweight housekeeping (Gemini 2.0 Flash-Lite)


class RoutingDecision(BaseModel):
    """Encapsulates the routing decision for an incoming query."""
    intent: RouteIntent
    target_agent: str
    selected_model: str
    model_tier: ModelTier
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    complexity_factors: List[str] = Field(default_factory=list)
    extracted_params: Dict[str, Any] = Field(default_factory=dict)


class SemanticRouter:
    """Classifies user intent and assigns optimal agent and Gemini model tier."""

    # Keywords indicating nuanced taste/style comparison requiring deep reasoning
    DEEP_REASONING_TRIGGERS = [
        "why", "compare", "recommend based on", "similar to", "explain why",
        "director", "cinematography", "taste", "style", "philosophical",
        "nuance", "plot twist", "masterpiece", "critics", "difference between"
    ]

    def __init__(self, routing_config: Optional[Dict[str, str]] = None):
        self.config = routing_config or MODEL_ROUTING_CONFIG

    def route(self, user_message: str, session_state: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """Evaluates intent and selects the optimal agent and model tier."""
        text = user_message.lower().strip()
        session_state = session_state or {}

        # 1. Booking Confirmation Intent (High priority transaction)
        if any(w in text for w in ["confirm", "pay", "charge", "checkout", "purchase"]):
            if any(w in text for w in ["seat", "seats", "ticket", "tickets", "booking", "hold"]) or session_state.get("active_reservation"):
                return RoutingDecision(
                    intent=RouteIntent.BOOKING_CONFIRM,
                    target_agent="BookingAgent",
                    selected_model=self.config.get("booking", DEFAULT_MODEL),
                    model_tier=ModelTier.DETERMINISTIC,
                    confidence=0.95,
                    complexity_factors=["financial_transaction", "hold_verification"],
                    extracted_params={"action": "PROCESS_PAYMENT"}
                )

        # 2. Housekeeping: Calendar Invitations
        if any(w in text for w in ["calendar", "schedule", "ics", "google cal", "invite"]):
            return RoutingDecision(
                intent=RouteIntent.HOUSEKEEPING_CALENDAR,
                target_agent="HousekeepingAgent",
                selected_model=self.config.get("housekeeping", DEFAULT_MODEL),
                model_tier=ModelTier.LITE,
                confidence=0.92,
                complexity_factors=["calendar_generation"],
                extracted_params={}
            )

        # 3. Housekeeping: Watched History
        if any(w in text for w in ["watched", "seen", "history", "archive", "profile"]):
            return RoutingDecision(
                intent=RouteIntent.HOUSEKEEPING_HISTORY,
                target_agent="HousekeepingAgent",
                selected_model=self.config.get("housekeeping", DEFAULT_MODEL),
                model_tier=ModelTier.LITE,
                confidence=0.90,
                complexity_factors=["history_retrieval"],
                extracted_params={}
            )

        # 4. Seat Selection / Reservation Intent
        if any(w in text for w in ["seat", "seats", "book", "reserve", "seating", "hall", "auditorium"]):
            showtime_match = re.search(r"(\b\d{1,2}:\d{2}\b)", text)
            showtime = showtime_match.group(1) if showtime_match else "19:30"
            return RoutingDecision(
                intent=RouteIntent.BOOKING_SEATS,
                target_agent="BookingAgent",
                selected_model=self.config.get("booking", DEFAULT_MODEL),
                model_tier=ModelTier.DETERMINISTIC,
                confidence=0.92,
                complexity_factors=["interactive_grid", "availability_check"],
                extracted_params={"showtime": showtime}
            )

        # 5. Housekeeping: Add Favorite
        if any(w in text for w in ["favorite", "favourite", "bookmark", "love"]):
            if any(w in text for w in ["add", "save", "mark", "new"]):
                return RoutingDecision(
                    intent=RouteIntent.HOUSEKEEPING_FAVORITE,
                    target_agent="HousekeepingAgent",
                    selected_model=self.config.get("housekeeping", DEFAULT_MODEL),
                    model_tier=ModelTier.LITE,
                    confidence=0.88,
                    complexity_factors=["memory_update"],
                    extracted_params={}
                )

        # 6. Search & Recommendations (Evaluating Deep Reasoning vs Fast Flash)
        complexity_factors = []
        for trigger in self.DEEP_REASONING_TRIGGERS:
            if trigger in text:
                complexity_factors.append(trigger)

        # Check for multiple favorites or detailed taste reasoning
        user_favorites = session_state.get("favorite_movies", [])
        has_rich_favorites = len(user_favorites) >= 2

        if complexity_factors or (has_rich_favorites and any(w in text for w in ["recommend", "suggest", "pick", "why"])):
            # Route to Deep Reasoning Tier (Gemini Pro)
            return RoutingDecision(
                intent=RouteIntent.SEARCH_RECO,
                target_agent="SearchRecoAgent",
                selected_model=self.config.get("search_reco_deep", "gemini-2.5-pro"),
                model_tier=ModelTier.DEEP_REASONING,
                confidence=0.93,
                complexity_factors=complexity_factors or ["taste_synthesis"],
                extracted_params={"strategy": "deep_taste_matching"}
            )
        else:
            # Route to Fast Flash Tier (Gemini Flash)
            return RoutingDecision(
                intent=RouteIntent.SEARCH_RECO,
                target_agent="SearchRecoAgent",
                selected_model=self.config.get("search_reco_fast", "gemini-2.5-flash"),
                model_tier=ModelTier.FAST,
                confidence=0.89,
                complexity_factors=[],
                extracted_params={"strategy": "fast_catalog_search"}
            )
