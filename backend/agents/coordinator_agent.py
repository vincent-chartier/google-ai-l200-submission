"""Outing Coordinator Agent (Supervisor / Host).

The top-level orchestrator in the 4-agent system.
Interprets user intent, coordinates state & memory passing across
SearchRecoAgent, BookingAgent, and HousekeepingAgent, and constructs
unified A2UI Protocol messages for the Flutter frontend.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from backend.config import DEFAULT_MODEL
from backend.protocols.a2ui import A2UIMessage, A2UIQuickReply, A2UIComponent
from backend.agents.search_reco_agent import SearchRecoService
from backend.agents.booking_agent import BookingService
from backend.agents.housekeeping_agent import HousekeepingService
from backend.state.memory_manager import (
    initialize_user_session_state,
    add_movie_to_seen_history,
    add_movie_to_favorites
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

def create_coordinator_agent() -> LlmAgent:
    """Instantiates the Outing Coordinator ADK Agent."""
    return LlmAgent(
        name="OutingCoordinatorAgent",
        model=DEFAULT_MODEL,
        description="Top-level supervisor routing requests across Search/Reco, Booking, and Housekeeping agents.",
        instruction=COORDINATOR_INSTRUCTION
    )


class OutingCoordinatorService:
    """Multi-agent coordinator implementing intent dispatch, memory passing, and A2UI assembly."""

    def __init__(self):
        self.coordinator_agent = create_coordinator_agent()
        self.search_reco_service = SearchRecoService()
        self.booking_service = BookingService()
        self.housekeeping_service = HousekeepingService()
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves or initializes session state for a user session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = initialize_user_session_state(user_id=session_id)
        return self.sessions[session_id]

    async def handle_user_message(
        self,
        session_id: str,
        user_message: str
    ) -> A2UIMessage:
        """Processes user input, orchestrates agents with memory passing, and returns A2UI response."""
        session_state = self.get_or_create_session(session_id)
        msg_lower = user_message.lower().strip()

        # Intent Detection
        # 1. Booking / Seat selection intent
        if any(w in msg_lower for w in ["seat", "seats", "book", "buy", "ticket", "tickets"]):
            if any(w in msg_lower for w in ["confirm", "pay", "charge"]):
                # Complete active booking
                active_res = session_state.get("active_reservation")
                token = active_res["token"] if active_res else "HLD-DEMO01"
                booking_result = self.booking_service.complete_booking(
                    reservation_token=token,
                    payment_method="Google Pay",
                    session_state=session_state
                )
                
                # Automatically trigger Housekeeping Agent to offer calendar invite
                quick_replies = [
                    A2UIQuickReply(label="Add to Calendar", action="SEND_CALENDAR_INVITE", payload={"booking": booking_result.get("booking", {})}),
                    A2UIQuickReply(label="View My History", action="VIEW_HISTORY", payload={})
                ]
                
                return A2UIMessage(
                    session_id=session_id,
                    agent="BookingAgent",
                    text=booking_result["text"],
                    components=booking_result["components"],
                    quick_replies=quick_replies,
                    state_updates={"active_booking": session_state.get("active_booking")}
                )
            else:
                # Default to showing interactive seat map
                seats_result = self.booking_service.show_seats_for_showtime(showtime_id="SH-DUNE-1930")
                quick_replies = [
                    A2UIQuickReply(label="Select VIP Seats (F4, F5)", action="SELECT_SEATS", payload={"seats": ["F4", "F5"], "showtime_id": "SH-DUNE-1930"}),
                    A2UIQuickReply(label="Back to Movies", action="RECOMMEND_MOVIES", payload={})
                ]
                return A2UIMessage(
                    session_id=session_id,
                    agent="BookingAgent",
                    text=seats_result["text"],
                    components=seats_result["components"],
                    quick_replies=quick_replies
                )

        # 2. Calendar invite intent
        elif any(w in msg_lower for w in ["calendar", "invite", "schedule", "remind"]):
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
            return A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=cal_result["text"],
                components=cal_result["components"],
                quick_replies=quick_replies
            )

        # 3. Housekeeping / Watched Movies / History intent
        elif any(w in msg_lower for w in ["history", "watched", "seen", "favorites", "profile"]):
            hist_result = self.housekeeping_service.get_profile_history_ui(session_state=session_state)
            quick_replies = [
                A2UIQuickReply(label="Recommend based on favorites", action="RECOMMEND_MOVIES", payload={}),
                A2UIQuickReply(label="Search New Movies", action="RECOMMEND_MOVIES", payload={"query": "sci-fi"})
            ]
            return A2UIMessage(
                session_id=session_id,
                agent="HousekeepingAgent",
                text=hist_result["text"],
                components=hist_result["components"],
                quick_replies=quick_replies
            )

        # 4. Search & Recommendations (Default conversational flow)
        else:
            # Passes favorite_movies and seen_movies from session_state to SearchRecoService
            reco_result = self.search_reco_service.search_and_recommend(
                query=user_message,
                session_state=session_state
            )
            quick_replies = [
                A2UIQuickReply(label="Book 19:30 IMAX for Dune: Part Two", action="SELECT_SHOWTIME", payload={"showtime_id": "SH-DUNE-1930"}),
                A2UIQuickReply(label="View My Watched Movies", action="VIEW_HISTORY", payload={}),
                A2UIQuickReply(label="Look for Action Movies", action="RECOMMEND_MOVIES", payload={"genre": "Action"})
            ]
            return A2UIMessage(
                session_id=session_id,
                agent="SearchRecoAgent",
                text=reco_result["text"],
                components=reco_result["components"],
                quick_replies=quick_replies
            )

    async def handle_a2ui_action(
        self,
        session_id: str,
        action: str,
        payload: Dict[str, Any]
    ) -> A2UIMessage:
        """Processes interactive actions emitted by Flutter A2UI widgets."""
        session_state = self.get_or_create_session(session_id)
        
        if action == "SELECT_SHOWTIME":
            showtime_id = payload.get("showtime_id", "SH-DUNE-1930")
            seats_result = self.booking_service.show_seats_for_showtime(showtime_id=showtime_id)
            return A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=seats_result["text"],
                components=seats_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Hold Seats F4, F5", action="HOLD_SEATS", payload={"seats": ["F4", "F5"], "showtime_id": showtime_id})
                ]
            )
            
        elif action == "HOLD_SEATS" or action == "SELECT_SEATS":
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
            return A2UIMessage(
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
            booking_result = self.booking_service.complete_booking(
                reservation_token=token,
                payment_method="Google Pay",
                session_state=session_state
            )
            return A2UIMessage(
                session_id=session_id,
                agent="BookingAgent",
                text=booking_result["text"],
                components=booking_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Add to Calendar", action="SEND_CALENDAR_INVITE", payload={"booking": booking_result.get("booking")})
                ],
                state_updates={"active_booking": session_state.get("active_booking")}
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
            return A2UIMessage(
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
            return A2UIMessage(
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
            return A2UIMessage(
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
            return A2UIMessage(
                session_id=session_id,
                agent="SearchRecoAgent",
                text=reco_result["text"],
                components=reco_result["components"],
                quick_replies=[
                    A2UIQuickReply(label="Select Showtime 19:30", action="SELECT_SHOWTIME", payload={"showtime_id": "SH-DUNE-1930"})
                ]
            )
