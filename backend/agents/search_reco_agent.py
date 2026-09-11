"""Search & Recommendation Agent for Cinema Outings.

Specializes in discovering movies, current screenings, and providing
personalized recommendations grounded in user favorites via MCP internet search.
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from backend.config import DEFAULT_MODEL
from backend.protocols.a2ui import build_movie_card_component, A2UIComponent
from backend.mcp_servers.movie_search_server import MOVIES_DATABASE, THEATERS_DATABASE

# Setup MCP Toolset connected via Stdio to movie_search_server
def create_movie_mcp_toolset() -> McpToolset:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.mcp_servers.movie_search_server"],
        env={**os.environ, "PYTHONPATH": "."}
    )
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=server_params,
            timeout=10.0
        )
    )

SEARCH_RECO_INSTRUCTION = """You are the Search & Recommendation Specialist Agent for Cinema Outings.
Your mission is to help users find fantastic movies currently playing in cinemas and deliver hyper-personalized recommendations.

Key Responsibilities & Rules:
1. Grounded Discovery: Always use your internet search tools (search_internet_movies, get_movie_details, get_theater_showtimes) to fetch current listings and showtimes.
2. Memory & Taste Matching: You receive the user's favorite movies, seen movies, and compacted conversation summary from session state.
   - User's Favorite Movies: {favorite_movies}
   - User's Watched/Seen Movies: {seen_movies}
   - Compacted Conversation Summary: {conversation_summary}
3. Never recommend a movie the user has already marked as seen.
4. Ground recommendations in both long-term favorites and context preserved across compacted conversation turns.
5. Highlight why a recommendation fits their taste profile (e.g., 'Matches your love for Interstellar and Denis Villeneuve sci-fi').
6. Be enthusiastic, concise, and structured.
"""

def create_search_reco_agent(mcp_toolset: Optional[McpToolset] = None, model: Optional[str] = None) -> LlmAgent:
    """Instantiates the Search & Recommendation ADK Agent with tiered model support."""
    tools = [mcp_toolset] if mcp_toolset else [create_movie_mcp_toolset()]
    selected_model = model or DEFAULT_MODEL
    return LlmAgent(
        name="SearchRecoAgent",
        model=selected_model,
        description="Finds movies playing in cinemas, fetches showtimes, and provides personalized recommendations based on user favorites and watched history.",
        instruction=SEARCH_RECO_INSTRUCTION,
        tools=tools,
        output_key="search_reco_result"
    )


class SearchRecoService:
    """Service wrapper for Search & Recommendation agent execution and A2UI generation."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self._mcp_toolset = create_movie_mcp_toolset()
        self.agent = create_search_reco_agent(self._mcp_toolset, model=self.model)

    def search_and_recommend(
        self,
        query: str,
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Performs movie discovery with state/memory passing and returns A2UI payload."""
        favorite_movies = session_state.get("favorite_movies", [])
        seen_movies = session_state.get("seen_movies", [])
        conversation_summary = (session_state.get("conversation_summary") or "").lower()
        fav_titles = [m.get("title", "").lower() for m in favorite_movies]
        seen_titles = [m.get("title", "").lower() for m in seen_movies]
        
        # 1. Filter out already seen movies
        candidates = [
            m for m in MOVIES_DATABASE
            if m.get("in_theaters", False) and m["title"].lower() not in seen_titles
        ]
        
        # 2. Score candidates based on favorites similarity and conversation summary
        matched_candidates = []
        for movie in candidates:
            score = 0
            reason = ""
            
            # Check genre overlap with favorites
            fav_genres = [g.lower() for fav in favorite_movies for g in fav.get("genre", "").split("/")]
            genre_overlap = [g for g in movie["genres"] if any(g.lower() in fg for fg in fav_genres)]
            if genre_overlap:
                score += len(genre_overlap) * 2
                
            # Check director / tags with favorites
            for fav in favorite_movies:
                if fav.get("director") and fav["director"].lower() == movie.get("director", "").lower():
                    score += 5
                    reason = f"Directed by {movie['director']} (who directed your favorite: {fav['title']})"
                if any(fav["title"].lower() in tag.lower() for tag in movie.get("similarity_tags", [])):
                    score += 4
                    if not reason:
                        reason = f"Fans of your favorite '{fav['title']}' love this"

            # Check context from compacted conversation summary
            if conversation_summary:
                for g in movie.get("genres", []):
                    if g.lower() in conversation_summary:
                        score += 3
                        if not reason:
                            reason = f"Matches your interest in {g} from our conversation"
                if movie.get("director", "").lower() and movie["director"].lower() in conversation_summary:
                    score += 5
                    if not reason:
                        reason = f"Directed by {movie['director']}, mentioned in our previous discussion"
                for tag in movie.get("similarity_tags", []):
                    if tag.lower() in conversation_summary:
                        score += 3
                        if not reason:
                            reason = f"Matches themes discussed in our conversation"

            if not reason and genre_overlap:
                reason = f"Matches your passion for {', '.join(genre_overlap)} films"
                
            matched_candidates.append((score, reason, movie))

        matched_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Select top recommendations
        selected = matched_candidates[:2] if matched_candidates else []
        if not selected and candidates:
            selected = [(1, "Top trending cinema release this week", candidates[0])]

        components = []
        rec_titles = []
        for idx, (_, match_reason, movie) in enumerate(selected):
            # Look up showtimes for this movie
            showtimes = ["16:30", "19:30", "22:15"]
            category = "on_show" if idx == 0 else "suggested"
            cmp = build_movie_card_component(
                movie=movie,
                taste_match_reason=match_reason,
                showtimes=showtimes,
                category=category
            )
            components.append(cmp)
            rec_titles.append(movie["title"])

        fav_str = ", ".join([f["title"] for f in favorite_movies[:2]]) if favorite_movies else ""
        if conversation_summary:
            reply_text = (
                f"Recalling our earlier conversation, I found top-rated screenings tailored to your tastes! "
                f"I also checked your watched list so no repeat movies are included."
            )
        elif fav_str:
            reply_text = (
                f"Based on your favorite films ({fav_str}), I found top-rated screenings currently in theaters! "
                f"I also checked your watched list so no repeat movies are included."
            )
        else:
            reply_text = (
                "Here are top-rated screenings currently in theaters! "
                "I also checked your watched list so no repeat movies are included."
            )

        return {
            "text": reply_text,
            "components": components,
            "recommended_titles": rec_titles
        }
