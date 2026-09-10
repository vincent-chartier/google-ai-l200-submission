"""Housekeeping Agent for Cinema Outings.

Maintains the user's watched movie history, user favorite movies, and dispatches
calendar invites for upcoming cinema outings. Generates A2UI calendar cards and history lists.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from backend.config import DEFAULT_MODEL
from backend.tools.calendar_tools import create_calendar_invite
from backend.protocols.a2ui import (
    build_calendar_invite_component,
    build_seen_history_component,
    A2UIComponent
)
from backend.state.memory_manager import (
    add_movie_to_seen_history,
    add_movie_to_favorites,
    get_favorite_movie_titles,
    get_seen_movie_titles
)

HOUSEKEEPING_AGENT_INSTRUCTION = """You are the Housekeeping & Profile Specialist Agent for Cinema Outings.
Your duties:
1. Watched Movies: Maintain the user's history of watched films so they never get recommended something they've already seen.
2. Favorites Management: Keep track of films the user loves, enabling the Search & Reco Agent to perform taste matching.
3. Calendar Invites: Coordinate and dispatch calendar invites for upcoming movie bookings with exact venue, hall, and seat info.

Rules:
- Ensure the user's session state is kept fresh with accurate favorites and watched titles.
- When an outing is booked, offer or generate a calendar invite immediately.
"""

def create_housekeeping_agent(model: Optional[str] = None) -> LlmAgent:
    """Instantiates the Housekeeping ADK Agent with lightweight model support."""
    selected_model = model or DEFAULT_MODEL
    return LlmAgent(
        name="HousekeepingAgent",
        model=selected_model,
        description="Tracks user movie history, favorites, and dispatches calendar invitations for cinema outings.",
        instruction=HOUSEKEEPING_AGENT_INSTRUCTION,
        tools=[create_calendar_invite],
        output_key="housekeeping_result"
    )


class HousekeepingService:
    """Service wrapper for Housekeeping Agent operations and A2UI generation."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.agent = create_housekeeping_agent(model=self.model)

    def send_calendar_invite_for_booking(
        self,
        movie_title: str,
        cinema: str,
        date_time: str,
        seats: List[str],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Dispatches a calendar invite for a booked outing and generates A2UI calendar card."""
        invite_data = create_calendar_invite(
            movie_title=movie_title,
            cinema=cinema,
            date_time_str=date_time,
            seats=seats
        )
        
        # Also record this outing in seen/upcoming history
        if session_state is not None:
            add_movie_to_seen_history(session_state, movie_title, cinema=cinema)

        component = build_calendar_invite_component(invite_data)
        seats_str = ", ".join(seats) if seats else "General"
        text = (
            f"📅 Calendar invite created for '{movie_title}' at {cinema} on {date_time} ({seats_str})! "
            f"Tap below to add it directly to your Google or Apple Calendar."
        )
        
        return {
            "text": text,
            "components": [component],
            "calendar_data": invite_data
        }

    def record_watched_movie(
        self,
        movie_title: str,
        session_state: Dict[str, Any],
        user_score: float = 5.0
    ) -> Dict[str, Any]:
        """Adds a movie to the user's watched history and informs user."""
        entry = add_movie_to_seen_history(
            session_state,
            movie_title=movie_title,
            user_score=user_score
        )
        return {
            "text": f"Got it! Added '{movie_title}' to your watched history. The Search & Reco Agent won't recommend this again.",
            "entry": entry
        }

    def add_favorite(
        self,
        movie_title: str,
        genre: str,
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Saves a favorite movie and triggers updated taste memory."""
        entry = add_movie_to_favorites(
            session_state,
            movie_title=movie_title,
            genre=genre
        )
        return {
            "text": f"Added '{movie_title}' to your favorites! The Search & Reco Agent will use this to fine-tune your recommendations.",
            "entry": entry
        }

    def get_profile_history_ui(
        self,
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Builds an A2UI component displaying user's seen history and favorites."""
        seen = session_state.get("seen_movies", [])
        favs = session_state.get("favorite_movies", [])
        comp = build_seen_history_component(seen, favs)
        
        text = (
            f"Here is your cinema history: you've watched {len(seen)} movies and saved "
            f"{len(favs)} favorites. These are actively passed to the Search & Reco Agent to shape your recommendations."
        )
        return {
            "text": text,
            "components": [comp]
        }
