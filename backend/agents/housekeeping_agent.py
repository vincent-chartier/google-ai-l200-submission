"""Housekeeping Agent for Cinema Outings.

Maintains the user's watched movie history, user favorite movies, and dispatches
calendar invites for upcoming cinema outings. Generates A2UI calendar cards and history lists.
"""

import logging
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
    get_seen_movie_titles,
    estimate_history_tokens,
    apply_history_compaction,
    get_compacted_context
)
from backend.state.history_summarizer import HistorySummarizer

logger = logging.getLogger(__name__)

def compact_history_tool(
    turns_summary: str,
    extracted_favorites: Optional[List[str]] = None,
    extracted_seen: Optional[List[str]] = None
) -> Dict[str, Any]:
    """ADK Tool for compacting older conversation turns and saving extracted profile entities."""
    return {
        "success": True,
        "summary": turns_summary,
        "extracted_favorites": extracted_favorites or [],
        "extracted_seen": extracted_seen or []
    }

HOUSEKEEPING_AGENT_INSTRUCTION = """You are the Housekeeping & Profile Specialist Agent for Cinema Outings.
Your duties:
1. Watched Movies: Maintain the user's history of watched films so they never get recommended something they've already seen.
2. Favorites Management: Keep track of films the user loves, enabling the Search & Reco Agent to perform taste matching.
3. Calendar Invites: Coordinate and dispatch calendar invites for upcoming movie bookings with exact venue, hall, and seat info.
4. History & Context Compaction: Compact older dialogue turns into concise rolling summaries to prevent LLM context bloat and preserve critical user intent.

Rules:
- Ensure the user's session state is kept fresh with accurate favorites and watched titles.
- When an outing is booked, offer or generate a calendar invite immediately.
- Strip redundant conversational filler during compaction while preserving movie titles, dates, seats, and preferences.
"""

def create_housekeeping_agent(model: Optional[str] = None) -> LlmAgent:
    """Instantiates the Housekeeping ADK Agent with lightweight model support."""
    selected_model = model or DEFAULT_MODEL
    return LlmAgent(
        name="HousekeepingAgent",
        model=selected_model,
        description="Tracks user movie history, favorites, manages history compaction, and dispatches calendar invitations for cinema outings.",
        instruction=HOUSEKEEPING_AGENT_INSTRUCTION,
        tools=[create_calendar_invite, compact_history_tool],
        output_key="housekeeping_result"
    )


class HousekeepingService:
    """Service wrapper for Housekeeping Agent operations and A2UI generation."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.agent = create_housekeeping_agent(model=self.model)
        self.summarizer = HistorySummarizer(model=self.model)

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

    def compact_conversation_history(
        self,
        session_state: Dict[str, Any],
        max_recent_turns: int = 4,
        token_threshold: int = 400,
        session_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Compacts older conversation turns into rolling memory to manage context bloat.
        
        Extracts user preferences into session state and synthesizes dialogue history.
        """
        history = session_state.get("conversation_history", [])
        existing_summary = session_state.get("conversation_summary", "")
        tokens_before = estimate_history_tokens(history, existing_summary)

        # Check if compaction threshold is reached
        needs_compaction = len(history) > max_recent_turns or tokens_before > token_threshold
        if not needs_compaction or len(history) <= 1:
            return {
                "compacted": False,
                "reason": "Context within token and turn limits",
                "tokens_before": tokens_before,
                "tokens_after": tokens_before,
                "tokens_saved": 0,
                "total_turns": len(history)
            }

        # Determine slice of turns to compact (everything except recent window)
        num_to_compact = len(history) - max_recent_turns if len(history) > max_recent_turns else max(1, len(history) // 2)
        turns_to_compact = history[:num_to_compact]

        # Use HistorySummarizer for entity extraction and intelligent narrative summarization
        new_summary = self.summarizer.summarize_sync(
            turns=turns_to_compact,
            existing_summary=existing_summary,
            session_state=session_state
        )

        # Apply compaction in session memory
        meta = apply_history_compaction(session_state, new_summary, num_to_compact)
        remaining_history = session_state.get("conversation_history", [])
        tokens_after = estimate_history_tokens(remaining_history, new_summary)
        tokens_saved = max(0, tokens_before - tokens_after)

        if db and session_id:
            try:
                db.mark_turns_compacted_sync(session_id, num_to_compact)
                db.update_summary_and_metadata_sync(session_id, new_summary, meta)
                db.save_session_sync(session_id, session_state)
            except Exception as e:
                logger.warning(f"Could not persist compaction to sync DB: {e}")

        return {
            "compacted": True,
            "turns_compacted_count": num_to_compact,
            "remaining_turns_count": len(remaining_history),
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "new_summary": new_summary,
            "compaction_metadata": meta
        }

    async def compact_conversation_history_async(
        self,
        session_state: Dict[str, Any],
        max_recent_turns: int = 4,
        token_threshold: int = 400,
        session_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Asynchronously compacts older conversation turns into rolling memory.
        
        Non-blocking execution for background tasks and asynchronous pipelines.
        """
        history = session_state.get("conversation_history", [])
        existing_summary = session_state.get("conversation_summary", "")
        tokens_before = estimate_history_tokens(history, existing_summary)

        needs_compaction = len(history) > max_recent_turns or tokens_before > token_threshold
        if not needs_compaction or len(history) <= 1:
            return {
                "compacted": False,
                "reason": "Context within token and turn limits",
                "tokens_before": tokens_before,
                "tokens_after": tokens_before,
                "tokens_saved": 0,
                "total_turns": len(history)
            }

        num_to_compact = len(history) - max_recent_turns if len(history) > max_recent_turns else max(1, len(history) // 2)
        turns_to_compact = history[:num_to_compact]

        # Use async HistorySummarizer
        new_summary = await self.summarizer.summarize_async(
            turns=turns_to_compact,
            existing_summary=existing_summary,
            session_state=session_state
        )

        meta = apply_history_compaction(session_state, new_summary, num_to_compact)
        remaining_history = session_state.get("conversation_history", [])
        tokens_after = estimate_history_tokens(remaining_history, new_summary)
        tokens_saved = max(0, tokens_before - tokens_after)

        if db and session_id:
            try:
                await db.mark_turns_compacted(session_id, num_to_compact)
                await db.update_summary_and_metadata(session_id, new_summary, meta)
                await db.save_session(session_id, session_state)
            except Exception as e:
                logger.warning(f"Could not persist compaction to async DB: {e}")

        return {
            "compacted": True,
            "turns_compacted_count": num_to_compact,
            "remaining_turns_count": len(remaining_history),
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "new_summary": new_summary,
            "compaction_metadata": meta
        }
