"""A2UI (Agent-to-UI) Protocol specification and builders.

Defines the declarative JSON schema sent to Flutter to dynamically
render native interactive UI elements.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

class A2UIAction(BaseModel):
    label: str = ""
    action: str
    icon: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

class A2UIComponent(BaseModel):
    id: str = Field(default_factory=lambda: f"cmp_{uuid.uuid4().hex[:8]}")
    type: str # 'movie_card', 'movie_carousel', 'seat_map_selector', 'ticket_pass', 'calendar_invite_card', 'seen_history_list'
    props: Dict[str, Any] = Field(default_factory=dict)
    actions: List[A2UIAction] = Field(default_factory=list)

class A2UIQuickReply(BaseModel):
    label: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class A2UIMessage(BaseModel):
    protocol_version: str = "1.0"
    session_id: str
    agent: str
    text: str
    components: List[A2UIComponent] = Field(default_factory=list)
    quick_replies: List[A2UIQuickReply] = Field(default_factory=list)
    state_updates: Dict[str, Any] = Field(default_factory=dict)


# --- Helper Component Builders ---

def build_movie_card_component(
    movie: Dict[str, Any],
    taste_match_reason: str = "",
    showtimes: List[str] = None,
    category: str = "on_show"
) -> A2UIComponent:
    """Builds an A2UI movie card component."""
    theater_name = movie.get("theater", "Metropolis Cinema IMAX")
    theater_loc = movie.get("location", "450 7th Ave, Downtown")
    full_location = f"{theater_name} • {theater_loc}" if theater_name not in theater_loc else theater_loc

    props = {
        "movie_id": movie.get("id", movie.get("title", "")),
        "title": movie.get("title", "Unknown Title"),
        "theater": theater_name,
        "location": full_location,
        "theater_location": full_location,
        "category": category,
        "group": "On Show" if category == "on_show" else "Suggested",
        "genres": movie.get("genres", []),
        "year": movie.get("year", 2024),
        "runtime": movie.get("runtime", "120 min"),
        "director": movie.get("director", ""),
        "cast": movie.get("cast", []),
        "imdb_rating": movie.get("imdb_rating", 8.0),
        "rotten_tomatoes": movie.get("rotten_tomatoes", "90%"),
        "synopsis": movie.get("synopsis", ""),
        "poster_url": movie.get("poster_url", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500"),
        "taste_match_reason": taste_match_reason,
        "showtimes": showtimes or ["16:30", "19:30", "22:15"]
    }
    actions = [
        A2UIAction(
            label="View Seats (19:30)",
            action="SELECT_SHOWTIME",
            icon="event_seat",
            payload={"movie_title": props["title"], "showtime_id": "SH-DUNE-1930", "time": "19:30"}
        ),
        A2UIAction(
            label="Save to Favorites",
            action="ADD_FAVORITE",
            icon="favorite",
            payload={"movie_title": props["title"], "genre": props["genres"][0] if props["genres"] else "Sci-Fi"}
        )
    ]
    return A2UIComponent(type="movie_card", props=props, actions=actions)


def build_seat_map_component(seat_availability: Dict[str, Any]) -> A2UIComponent:
    """Builds an A2UI interactive seat map component."""
    return A2UIComponent(
        type="seat_map_selector",
        props=seat_availability,
        actions=[
            A2UIAction(
                label="Confirm & Hold Seats",
                action="HOLD_SEATS",
                icon="lock",
                payload={"showtime_id": seat_availability.get("showtime_id", "SH-DUNE-1930")}
            )
        ]
    )


def build_ticket_pass_component(booking: Dict[str, Any]) -> A2UIComponent:
    """Builds an A2UI confirmed ticket pass component."""
    return A2UIComponent(
        type="ticket_pass",
        props=booking,
        actions=[
            A2UIAction(
                label="Add to Calendar",
                action="SEND_CALENDAR_INVITE",
                icon="calendar_today",
                payload={
                    "movie_title": booking.get("movie_title"),
                    "cinema": booking.get("cinema"),
                    "date_time": booking.get("date_time"),
                    "seats": booking.get("seats")
                }
            )
        ]
    )


def build_calendar_invite_component(calendar_data: Dict[str, Any]) -> A2UIComponent:
    """Builds an A2UI calendar invite confirmation card."""
    return A2UIComponent(
        type="calendar_invite_card",
        props=calendar_data,
        actions=[
            A2UIAction(
                label="Open in Google Calendar",
                action="OPEN_EXTERNAL_URL",
                icon="open_in_new",
                payload={"url": calendar_data.get("google_calendar_url", "")}
            ),
            A2UIAction(
                label="Export .ICS File",
                action="DOWNLOAD_ICS",
                icon="download",
                payload={"ics_content": calendar_data.get("ics_content", "")}
            )
        ]
    )


def build_seen_history_component(seen_movies: List[Dict[str, Any]], favorite_movies: List[Dict[str, Any]]) -> A2UIComponent:
    """Builds an A2UI profile movies history and favorites component."""
    return A2UIComponent(
        type="seen_history_list",
        props={
            "seen_movies": seen_movies,
            "favorite_movies": favorite_movies
        },
        actions=[
            A2UIAction(
                label="Find Movie Similar to Favorites",
                action="FIND_SIMILAR_MOVIES",
                icon="auto_awesome",
                payload={}
            )
        ]
    )
