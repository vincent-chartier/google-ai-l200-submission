"""State & Memory Passing management for Google ADK Agents.

Manages persistent user preferences, favorite movies, watched history,
and active cinema booking sessions passed across agents.
"""

from typing import Dict, Any, List

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
        "user_location": "Downtown"
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
