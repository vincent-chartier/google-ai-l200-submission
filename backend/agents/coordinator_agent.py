"""Outing Coordinator Agent (Supervisor / Host).

The top-level orchestrator in the 4-agent system.
Interprets user intent, coordinates state & memory passing across
SearchRecoAgent, BookingAgent, and HousekeepingAgent, and constructs
unified A2UI Protocol messages for the Flutter frontend.

Enhanced with:
- Strategic Semantic Router (Intent & Gemini Model Tier Selection)
- Security Guardrails (Input Injection Defense, Booking Safety, A2UI Contracts)
- Evaluation & Telemetry Plugins (Duplicate Avoidance, Latency & Cost Tracking)
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent

from backend.config import DEFAULT_MODEL, MODEL_ROUTING_CONFIG
from backend.protocols.a2ui import A2UIMessage, A2UIQuickReply, A2UIComponent
from backend.agents.search_reco_agent import SearchRecoService
from backend.agents.booking_agent import BookingService
from backend.agents.housekeeping_agent import HousekeepingService
from backend.state.database import DatabaseManager
from backend.state.memory_manager import (
    initialize_user_session_state,
    add_movie_to_seen_history,
    add_movie_to_favorites,
    add_conversation_turn,
    get_compacted_context,
    summarize_a2ui_components
)

logger = logging.getLogger(__name__)
from backend.routers.semantic_router import (
    SemanticRouter,
    RouteIntent,
    ModelTier,
    RoutingDecision
)
from backend.plugins.security_guardrails import (
    InputSecurityGuardrailPlugin,
    BookingSafetyGuardrailPlugin,
    A2UIValidationGuardrailPlugin,
    SecurityViolationError
)
from backend.plugins.evaluation_plugins import (
    RecommendationEvaluationPlugin,
    ToolSequenceEvaluationPlugin,
    LatencyAndCostTelemetryPlugin
)

COORDINATOR_INSTRUCTION = """You are the Outing Coordinator Agent, the primary host of the Cinema Outings assistant.
You work alongside 3 specialized agents to deliver a seamless cinema experience:
1. Search & Recommendation Agent: Discovers movies, current screenings, and delivers taste-matched picks using MCP web tools and favorites memory.
2. Booking Agent: Handles auditorium seat layouts, holding tickets, and executing payment transactions.
3. Housekeeping Agent: Manages user watched history, maintains favorite movies, and dispatches calendar invitations.

Your job:
- Understand user goals and route appropriately.
- Ensure the user's favorites from Housekeeping are always shared with Search & Reco.
- Ensure confirmed bookings trigger calendar invites via Housekeeping.
- Keep responses friendly, helpful, and concise.
"""

def create_coordinator_agent(model: Optional[str] = None) -> LlmAgent:
    """Instantiates the Outing Coordinator ADK Agent with tiered model support."""
    selected_model = model or MODEL_ROUTING_CONFIG.get("coordinator", DEFAULT_MODEL)
    return LlmAgent(
        name="OutingCoordinatorAgent",
        model=selected_model,
        description="Top-level supervisor routing requests across Search/Reco, Booking, and Housekeeping agents.",
        instruction=COORDINATOR_INSTRUCTION
    )


class OutingCoordinatorService:
    """Multi-agent coordinator implementing intent dispatch, memory passing, and A2UI assembly."""

    def __init__(
        self,
        routing_config: Optional[Dict[str, str]] = None,
        db: Optional[DatabaseManager] = None
    ):
        self.routing_config = routing_config or MODEL_ROUTING_CONFIG
        self.coordinator_agent = create_coordinator_agent(model=self.routing_config.get("coordinator"))
        self.search_reco_service = SearchRecoService(model=self.routing_config.get("search_reco_fast"))
        self.search_reco_deep_service = SearchRecoService(model=self.routing_config.get("search_reco_deep"))
        self.booking_service = BookingService(model=self.routing_config.get("booking"))
        self.housekeeping_service = HousekeepingService(model=self.routing_config.get("housekeeping"))

        # Semantic Router
        self.router = SemanticRouter(routing_config=self.routing_config)

        # Security Guardrails
        self.input_guardrail = InputSecurityGuardrailPlugin()
        self.booking_guardrail = BookingSafetyGuardrailPlugin()
        self.a2ui_guardrail = A2UIValidationGuardrailPlugin()

        # Evaluation & Telemetry Plugins
        self.reco_evaluator = RecommendationEvaluationPlugin()
        self.tool_evaluator = ToolSequenceEvaluationPlugin()
        self.telemetry = LatencyAndCostTelemetryPlugin()

        # Persistent SQLite Database & In-Memory Session Cache
        self.db = db or DatabaseManager()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._background_tasks: set = set()

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves or initializes session state from memory cache or persistent SQLite database."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        loaded = self.db.load_session_sync(session_id)
        if loaded:
            self.sessions[session_id] = loaded
            return loaded

        state = initialize_user_session_state(user_id=session_id)
        self.db.save_session_sync(session_id, state)
        self.sessions[session_id] = state
        return state

    async def get_or_create_session_async(self, session_id: str) -> Dict[str, Any]:
        """Asynchronously retrieves or initializes session state from persistent SQLite database."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        loaded = await self.db.load_session(session_id)
        if loaded:
            self.sessions[session_id] = loaded
            return loaded

        state = initialize_user_session_state(user_id=session_id)
        await self.db.save_session(session_id, state)
        self.sessions[session_id] = state
        return state

    async def _record_turn_and_compact_task(
        self,
        session_id: str,
        role: str,
        text: str,
        sender: Optional[str] = None,
        a2ui_components: Optional[List[Any]] = None
    ) -> None:
        """Asynchronous background worker that persists turns and triggers compaction non-blockingly."""
        try:
            turn_data = {
                "role": role,
                "sender": sender or role or "user",
                "text": text,
                "ui_summary": summarize_a2ui_components(a2ui_components) if a2ui_components else None,
                "timestamp": time.time()
            }
            await self.db.append_turn(session_id, turn_data)

            session_state = self.get_or_create_session(session_id)
            await self.housekeeping_service.compact_conversation_history_async(
                session_state=session_state,
                session_id=session_id,
                db=self.db
            )
        except Exception as e:
            logger.warning(f"Background memory operation failed for {session_id}: {e}")

    def _enqueue_memory_task(
        self,
        session_id: str,
        role: str,
        text: str,
        sender: Optional[str] = None,
        a2ui_components: Optional[List[Any]] = None
    ) -> None:
        """Dispatches an asynchronous background task for turn persistence and compaction."""
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(
                self._record_turn_and_compact_task(
                    session_id=session_id,
                    role=role,
                    text=text,
                    sender=sender,
                    a2ui_components=a2ui_components
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        except RuntimeError:
            # Fallback if invoked outside active asyncio event loop
            pass

    def _enqueue_state_save(self, session_id: str, session_state: Dict[str, Any]) -> None:
        """Enqueues async session state persistence."""
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self.db.save_session(session_id, session_state))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        except RuntimeError:
            self.db.save_session_sync(session_id, session_state)

    async def drain_memory_tasks(self) -> None:
        """Awaits all pending background persistence and compaction tasks."""
        if self._background_tasks:
            await asyncio.gather(*list(self._background_tasks), return_exceptions=True)

    async def handle_user_message(
        self,
        session_id: str,
        user_message: str
    ) -> A2UIMessage:
        """Processes user input, runs security guardrails, routes to optimal model tier, and returns A2UI response."""
        t0 = time.time()
        session_state = self.get_or_create_session(session_id)

        # 1. Input Security Guardrail Check (Prompt Injection, PII scrubbing)
        try:
            sanitized_message = self.input_guardrail.validate_and_sanitize(user_message)
        except SecurityViolationError as sve:
            return A2UIMessage(
                session_id=session_id,
                agent="OutingCoordinatorAgent",
                text=f"⚠️ Request Blocked: {sve.message}",
                components=[],
                quick_replies=[
                    A2UIQuickReply(label="Browse Movies Safely", action="RECOMMEND_MOVIES", payload={})
                ]
            )

        # 2. Add incoming user turn to memory & execute async persistence and compaction
        add_conversation_turn(session_state, role="user", text=sanitized_message, sender="user")
        await self._record_turn_and_compact_task(
            session_id=session_id,
            role="user",
            text=sanitized_message,
            sender="user"
        )

        # 3. Semantic Intent & Model Tier Routing
        route = self.router.route(sanitized_message, session_state=session_state)

        # 3. Intent Dispatch with Memory Passing
        if route.intent == RouteIntent.BOOKING_CONFIRM:
            active_res = session_state.get("active_reservation")
            token = active_res["token"] if active_res else "HLD-DEMO01"

            # Validate booking payment transaction
            self.booking_guardrail.validate_payment_transaction(token, session_state)

            booking_result = self.booking_service.complete_booking(
                reservation_token=token,
                payment_method="Google Pay",
                session_state=session_state
            )

            quick_replies = [
                A2UIQuickReply(label="Add to Calendar", action="SEND_CALENDAR_INVITE", payload={"booking": booking_result.get("booking", {})}),
                A2UIQuickReply(label="View My History", action="VIEW_HISTORY", payload={})
            ]

            response = A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=booking_result["text"],
                components=booking_result["components"],
                quick_replies=quick_replies,
                state_updates={"active_booking": session_state.get("active_booking")}
            )

        elif route.intent == RouteIntent.BOOKING_SEATS:
            showtime = route.extracted_params.get("showtime", "19:30")
            showtime_id = f"SH-DUNE-{showtime.replace(':', '')}" if ":" in showtime else "SH-DUNE-1930"
            seats_result = self.booking_service.show_seats_for_showtime(showtime_id=showtime_id)
            quick_replies = [
                A2UIQuickReply(label=f"Select VIP Seats (F4, F5) ({showtime})", action="SELECT_SEATS", payload={"seats": ["F4", "F5"], "showtime_id": showtime_id}),
                A2UIQuickReply(label="Back to Movies", action="RECOMMEND_MOVIES", payload={})
            ]
            response = A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=seats_result["text"],
                components=seats_result["components"],
                quick_replies=quick_replies
            )

        elif route.intent == RouteIntent.HOUSEKEEPING_CALENDAR:
            booking = session_state.get("active_booking") or {
                "movie_title": "Dune: Part Two",
                "cinema": "Metropolis Cinema IMAX",
                "date_time": "2026-09-12 19:30",
                "seats": ["F7", "F8"]
            }
            cal_result = self.housekeeping_service.send_calendar_invite_for_booking(
                movie_title=booking.get("movie_title", "Dune: Part Two"),
                cinema=booking.get("cinema", "Metropolis Cinema IMAX"),
                date_time=booking.get("date_time", "2026-09-12 19:30"),
                seats=booking.get("seats", ["F7", "F8"]),
                session_state=session_state
            )
            quick_replies = [
                A2UIQuickReply(label="View Watched List", action="VIEW_HISTORY", payload={}),
                A2UIQuickReply(label="Find Another Movie", action="RECOMMEND_MOVIES", payload={})
            ]
            response = A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=cal_result["text"],
                components=cal_result["components"],
                quick_replies=quick_replies
            )

        elif route.intent in (RouteIntent.HOUSEKEEPING_HISTORY, RouteIntent.HOUSEKEEPING_FAVORITE):
            hist_result = self.housekeeping_service.get_profile_history_ui(session_state=session_state)
            quick_replies = [
                A2UIQuickReply(label="Recommend based on favorites", action="RECOMMEND_MOVIES", payload={}),
                A2UIQuickReply(label="Search New Movies", action="RECOMMEND_MOVIES", payload={"query": "sci-fi"})
            ]
            response = A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=hist_result["text"],
                components=hist_result["components"],
                quick_replies=quick_replies
            )

        else:
            # Search & Recommendation (Tiered: Deep Reasoning Pro vs Fast Flash)
            service = self.search_reco_deep_service if route.model_tier == ModelTier.DEEP_REASONING else self.search_reco_service
            reco_result = service.search_and_recommend(
                query=sanitized_message,
                session_state=session_state
            )

            # Run Recommendation Evaluation Plugin (evaluating zero duplicates and negative constraints)
            recommended_titles = []
            for comp in reco_result.get("components", []):
                props = getattr(comp, "props", {}) if hasattr(comp, "props") else comp.get("props", {})
                if "title" in props:
                    recommended_titles.append(props["title"])

            self.reco_evaluator.evaluate_negative_constraints(
                recommended_titles=recommended_titles,
                seen_movies=session_state.get("seen_movies", [])
            )

            quick_replies = [
                A2UIQuickReply(label="Book 19:30 IMAX for Dune: Part Two", action="SELECT_SHOWTIME", payload={"showtime_id": "SH-DUNE-1930"}),
                A2UIQuickReply(label="View My Watched Movies", action="VIEW_HISTORY", payload={}),
                A2UIQuickReply(label="Look for Action Movies", action="RECOMMEND_MOVIES", payload={"genre": "Action"})
            ]
            response = A2UIMessage(
                session_id=session_id,
                agent="SearchRecoAgent",
                text=reco_result["text"],
                components=reco_result["components"],
                quick_replies=quick_replies
            )

        # 4. Outgoing A2UI Validation Guardrail
        for comp in response.components:
            self.a2ui_guardrail.validate_component(comp)

        # 5. Record agent response in memory and execute async persistence & compaction
        add_conversation_turn(
            session_state,
            role="agent",
            text=response.text,
            sender=response.agent,
            a2ui_components=response.components
        )
        await self._record_turn_and_compact_task(
            session_id=session_id,
            role="agent",
            text=response.text,
            sender=response.agent,
            a2ui_components=response.components
        )
        await self.db.save_session(session_id, session_state)

        # 6. Telemetry & Cost Recording
        duration_ms = (time.time() - t0) * 1000
        self.telemetry.record_call(
            agent_name=response.agent,
            model_name=route.selected_model,
            duration_ms=duration_ms
        )

        return response

    async def handle_a2ui_action(
        self,
        session_id: str,
        action: str,
        payload: Dict[str, Any]
    ) -> A2UIMessage:
        """Processes interactive actions emitted by Flutter A2UI widgets."""
        t0 = time.time()
        session_state = self.get_or_create_session(session_id)

        # Record action in conversation history & execute async persistence & compaction
        action_repr = f"User Action: {action} ({payload})" if payload else f"User Action: {action}"
        add_conversation_turn(session_state, role="user", text=action_repr, sender="user")
        await self._record_turn_and_compact_task(
            session_id=session_id,
            role="user",
            text=action_repr,
            sender="user"
        )

        if action == "SELECT_SHOWTIME":
            showtime_id = payload.get("showtime_id", "SH-DUNE-1930")
            seats_result = self.booking_service.show_seats_for_showtime(showtime_id=showtime_id)
            response = A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=seats_result["text"],
                components=seats_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Hold Seats F4, F5", action="HOLD_SEATS", payload={"seats": ["F4", "F5"], "showtime_id": showtime_id})
                ]
            )

        elif action == "HOLD_SEATS" or action == "SELECT_SEATS":
            # Guardrail: Check rate limit for seat holds
            self.booking_guardrail.check_rate_limit(session_id)

            seats = payload.get("seats", ["F4", "F5"])
            showtime_id = payload.get("showtime_id", "SH-DUNE-1930")
            hold_result = self.booking_service.hold_and_confirm_seats(
                showtime_id=showtime_id,
                seats=seats,
                user_id=session_id
            )
            session_state["active_reservation"] = hold_result.get("reservation")
            reservation = hold_result.get("reservation") or {}
            res_token = reservation.get("reservation_token", "")
            response = A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=hold_result["text"],
                components=[],
                quick_replies=[
                    A2UIQuickReply(label="Confirm & Pay with Google Pay", action="CONFIRM_PAYMENT", payload={"reservation_token": res_token}),
                    A2UIQuickReply(label="Cancel", action="RECOMMEND_MOVIES", payload={})
                ]
            )

        elif action == "CONFIRM_PAYMENT":
            active_res = session_state.get("active_reservation") or {}
            token = payload.get("reservation_token") or active_res.get("reservation_token") or "HLD-DEMO"

            # Guardrail: Validate booking payment transaction
            self.booking_guardrail.validate_payment_transaction(token, session_state)

            booking_result = self.booking_service.complete_booking(
                reservation_token=token,
                payment_method="Google Pay",
                session_state=session_state
            )
            # A film is considered watched when a ticket has been purchased for it
            if booking_result.get("booking") and booking_result["booking"].get("movie_title"):
                movie_title = booking_result["booking"]["movie_title"]
                cinema_name = booking_result["booking"].get("cinema", "Metropolis Cinema IMAX")
                add_movie_to_seen_history(session_state, movie_title=movie_title, cinema=cinema_name)

            response = A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=booking_result["text"],
                components=booking_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Add to Calendar", action="SEND_CALENDAR_INVITE", payload={"booking": booking_result.get("booking")}),
                    A2UIQuickReply(label="My Cinema", action="VIEW_HISTORY", payload={})
                ],
                state_updates={
                    "active_booking": session_state.get("active_booking"),
                    "seen_movies": session_state.get("seen_movies", [])
                }
            )

        elif action == "SEND_CALENDAR_INVITE":
            booking = payload.get("booking") or session_state.get("active_booking") or {}
            cal_result = self.housekeeping_service.send_calendar_invite_for_booking(
                movie_title=booking.get("movie_title", "Dune: Part Two"),
                cinema=booking.get("cinema", "Metropolis Cinema IMAX"),
                date_time=booking.get("date_time", "2026-09-12 19:30"),
                seats=booking.get("seats", ["F7", "F8"]),
                session_state=session_state
            )
            response = A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=cal_result["text"],
                components=cal_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="View My Profile & Seen History", action="VIEW_HISTORY", payload={})
                ]
            )

        elif action == "ADD_FAVORITE":
            title = payload.get("movie_title", "Dune: Part Two")
            genre = payload.get("genre", "Sci-Fi")
            fav_result = self.housekeeping_service.add_favorite(
                movie_title=title,
                genre=genre,
                session_state=session_state
            )
            response = A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=fav_result["text"],
                components=[],
                quick_replies=[
                    A2UIQuickReply(label="Find recommendations with new favorites", action="RECOMMEND_MOVIES", payload={})
                ],
                state_updates={"favorite_movies": session_state.get("favorite_movies")}
            )

        elif action == "VIEW_HISTORY":
            hist_result = self.housekeeping_service.get_profile_history_ui(session_state=session_state)
            response = A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=hist_result["text"],
                components=hist_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Recommend Movies", action="RECOMMEND_MOVIES", payload={})
                ]
            )

        else: # Default fallback to recommendations
            reco_result = self.search_reco_service.search_and_recommend(
                query=payload.get("genre", "sci-fi"),
                session_state=session_state
            )
            response = A2UIMessage(
                session_id=session_id,
                agent="SearchRecoAgent",
                text=reco_result["text"],
                components=reco_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Select Showtime 19:30", action="SELECT_SHOWTIME", payload={"showtime_id": "SH-DUNE-1930"})
                ]
            )

        # Validate Outgoing A2UI Components
        for comp in response.components:
            self.a2ui_guardrail.validate_component(comp)

        # Record agent action response in history & execute async persistence & compaction
        add_conversation_turn(
            session_state,
            role="agent",
            text=response.text,
            sender=response.agent,
            a2ui_components=response.components
        )
        await self._record_turn_and_compact_task(
            session_id=session_id,
            role="agent",
            text=response.text,
            sender=response.agent,
            a2ui_components=response.components
        )
        await self.db.save_session(session_id, session_state)

        # Record Telemetry
        duration_ms = (time.time() - t0) * 1000
        self.telemetry.record_call(
            agent_name=response.agent,
            model_name=self.routing_config.get("coordinator", DEFAULT_MODEL),
            duration_ms=duration_ms
        )

        return response

    async def compact_session_history_async(
        self,
        session_id: str,
        max_recent_turns: int = 4,
        token_threshold: int = 400
    ) -> Dict[str, Any]:
        """Asynchronously triggers conversation history compaction for a user session."""
        session_state = self.get_or_create_session(session_id)
        return await self.housekeeping_service.compact_conversation_history_async(
            session_state=session_state,
            max_recent_turns=max_recent_turns,
            token_threshold=token_threshold,
            session_id=session_id,
            db=self.db
        )

    def compact_session_history(
        self,
        session_id: str,
        max_recent_turns: int = 4,
        token_threshold: int = 400
    ) -> Dict[str, Any]:
        """Triggers conversation history compaction for a user session."""
        session_state = self.get_or_create_session(session_id)
        return self.housekeeping_service.compact_conversation_history(
            session_state=session_state,
            max_recent_turns=max_recent_turns,
            token_threshold=token_threshold,
            session_id=session_id,
            db=self.db
        )
