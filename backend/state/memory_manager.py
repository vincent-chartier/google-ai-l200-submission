"""State & Memory Passing management for Google ADK Agents.

Manages persistent user preferences, favorite movies, watched history,
and active cinema booking sessions passed across agents.
"""

import time
from typing import Dict, Any, List, Optional

DEFAULT_FAVORITE_MOVIES = [
    {"title": "Interstellar", "genre": "Sci-Fi", "rating": 5, "director": "Christopher Nolan"},
    {"title": "Arrival", "genre": "Sci-Fi", "rating": 4.5, "director": "Denis Villeneuve"},
    {"title": "Blade Runner 2049", "genre": "Sci-Fi", "rating": 4.8, "director": "Denis Villeneuve"}
]

DEFAULT_SEEN_MOVIES = [
    {"title": "Oppenheimer", "watched_date": "2025-08-12", "user_score": 5, "cinema": "Metropolis Cinema IMAX"},
    {"title": "The Matrix", "watched_date": "2024-03-10", "user_score": 4.5, "cinema": "Regal Downtown"}
]


def initialize_user_session_state(user_id: str = "user_default") -> Dict[str, Any]:
    """Generates the initial session state for a user session."""
    return {
        "user_id": user_id,
        "user_name": "Alex Morgan",
        "favorite_movies": [dict(m) for m in DEFAULT_FAVORITE_MOVIES],
        "seen_movies": [dict(m) for m in DEFAULT_SEEN_MOVIES],
        "active_booking": None,
        "active_reservation": None,
        "last_recommended_movies": [],
        "user_location": "Downtown",
        "conversation_history": [],
        "conversation_summary": "",
        "compaction_metadata": {
            "total_turns_compacted": 0,
            "last_compaction_timestamp": None,
            "compaction_count": 0
        }
    }


def add_movie_to_seen_history(
    state: Dict[str, Any],
    movie_title: str,
    cinema: str = "Metropolis Cinema IMAX",
    user_score: float = 5.0
) -> Dict[str, Any]:
    """Appends a movie to the user's watched history in session state."""
    seen_list = state.setdefault("seen_movies", [])
    entry = {
        "title": movie_title,
        "watched_date": "2026-09-10",
        "user_score": user_score,
        "cinema": cinema
    }
    # Avoid duplicate exact titles
    if not any(item["title"].lower() == movie_title.lower() for item in seen_list):
        seen_list.append(entry)
    return entry


def add_movie_to_favorites(
    state: Dict[str, Any],
    movie_title: str,
    genre: str = "Sci-Fi",
    rating: float = 5.0
) -> Dict[str, Any]:
    """Appends a movie to the user's favorites in session state."""
    favs = state.setdefault("favorite_movies", [])
    entry = {
        "title": movie_title,
        "genre": genre,
        "rating": rating
    }
    if not any(item["title"].lower() == movie_title.lower() for item in favs):
        favs.append(entry)
    return entry


def get_favorite_movie_titles(state: Dict[str, Any]) -> List[str]:
    """Extracts a list of favorite movie titles from session state."""
    favs = state.get("favorite_movies", [])
    return [m["title"] for m in favs if "title" in m]


def get_seen_movie_titles(state: Dict[str, Any]) -> List[str]:
    """Extracts a list of watched movie titles from session state."""
    seen = state.get("seen_movies", [])
    return [m["title"] for m in seen if "title" in m]


def summarize_a2ui_components(components: Optional[List[Any]]) -> Optional[str]:
    """Extracts a lightweight semantic summary of A2UI components to prevent token bloat."""
    if not components:
        return None
    summaries = []
    for c in components:
        c_type = getattr(c, "type", None) or (c.get("type") if isinstance(c, dict) else "")
        props = getattr(c, "props", None) or (c.get("props") if isinstance(c, dict) else {})
        if c_type == "movie_card":
            summaries.append(f"[UI: movie_card for '{props.get('title', 'Unknown')}']")
        elif c_type == "seat_map":
            movie = props.get("movie_title", "")
            showtime = props.get("showtime_id", "")
            summaries.append(f"[UI: seat_map for '{movie}' ({showtime})]")
        elif c_type == "ticket_pass":
            movie = props.get("movie_title", "")
            seats = ", ".join(props.get("seats", []))
            summaries.append(f"[UI: ticket_pass for '{movie}' seats ({seats})]")
        elif c_type == "calendar_invite_card":
            movie = props.get("movie_title", "")
            summaries.append(f"[UI: calendar_invite for '{movie}']")
        elif c_type:
            summaries.append(f"[UI: {c_type}]")
    return "; ".join(summaries) if summaries else None


def add_conversation_turn(
    state: Dict[str, Any],
    role: str,
    text: str,
    sender: Optional[str] = None,
    a2ui_components: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """Appends a sanitized conversational turn to session state."""
    history = state.setdefault("conversation_history", [])
    ui_summary = summarize_a2ui_components(a2ui_components)
    entry = {
        "role": role,
        "sender": sender or role or "user",
        "text": text,
        "timestamp": time.time(),
        "ui_summary": ui_summary
    }
    history.append(entry)
    return entry


def estimate_history_tokens(history: List[Dict[str, Any]], summary: str = "") -> int:
    """Estimates the token count of conversation history and rolling summary."""
    tokens = 0
    if summary:
        tokens += int(len(summary.split()) * 1.3) + 10
    for turn in history:
        text = turn.get("text", "")
        ui_summary = turn.get("ui_summary") or ""
        turn_words = len(text.split()) + len(ui_summary.split())
        tokens += int(turn_words * 1.3) + 4
    return tokens


def get_compacted_context(state: Dict[str, Any], max_recent_turns: int = 4) -> Dict[str, Any]:
    """Builds a compacted context payload combining rolling summary and recent turns."""
    history = state.get("conversation_history", [])
    summary = state.get("conversation_summary", "")
    recent_turns = history[-max_recent_turns:] if len(history) > max_recent_turns else list(history)
    return {
        "conversation_summary": summary,
        "recent_turns": recent_turns,
        "total_turns": len(history),
        "estimated_tokens": estimate_history_tokens(recent_turns, summary),
        "compaction_metadata": state.get("compaction_metadata", {})
    }


def apply_history_compaction(
    state: Dict[str, Any],
    new_summary: str,
    num_compacted_turns: int
) -> Dict[str, Any]:
    """Applies compaction result: stores new rolling summary and trims historical turns."""
    history = state.get("conversation_history", [])
    if num_compacted_turns >= len(history):
        state["conversation_history"] = []
    else:
        state["conversation_history"] = history[num_compacted_turns:]

    state["conversation_summary"] = new_summary
    meta = state.setdefault("compaction_metadata", {})
    meta["total_turns_compacted"] = meta.get("total_turns_compacted", 0) + num_compacted_turns
    meta["compaction_count"] = meta.get("compaction_count", 0) + 1
    meta["last_compaction_timestamp"] = time.time()
    return meta
