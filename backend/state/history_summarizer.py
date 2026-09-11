"""History Summarization and Compaction Engine.

Provides dual-mode summarization:
1. LLM-driven summarization using Gemini via google-genai when GEMINI_API_KEY is active.
2. Semantic narrative synthesis when offline, in mock test environments, or on fallback.
Also performs profile entity extraction (favorites, watched movies, bookings).
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from google import genai

from backend.config import GEMINI_API_KEY, MODEL_ROUTING_CONFIG
from backend.mcp_servers.movie_search_server import MOVIES_DATABASE
from backend.state.memory_manager import (
    add_movie_to_favorites,
    add_movie_to_seen_history
)

logger = logging.getLogger(__name__)

SUMMARIZATION_SYSTEM_PROMPT = """You are an expert dialogue summarization agent for a cinema outing concierge.
Your task is to take recent conversation turns and any prior summary, and synthesize them into a dense, concise narrative memory (1 to 3 sentences).

Strict Guidelines:
1. Retain all user preferences, tastes, favorite movies, and watched films.
2. Retain all discussed screenings, showtimes, venues, held seats, and bookings.
3. Retain key user requests and agent recommendations.
4. Eliminate conversational pleasantries, greetings, and repetitive filler.
5. Return ONLY the concise narrative summary text, nothing else.
"""


class HistorySummarizer:
    """Performs intelligent conversation summarization and entity extraction."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or MODEL_ROUTING_CONFIG.get("housekeeping", "gemini-2.0-flash-lite")
        self.client: Optional[genai.Client] = None
        if GEMINI_API_KEY and GEMINI_API_KEY.strip() and not GEMINI_API_KEY.startswith("mock"):
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize google.genai Client: {e}")

    def extract_entities_from_turns(
        self,
        turns: List[Dict[str, Any]],
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """Extracts user preferences, watched movies, and cinema entities from dialogue turns."""
        extracted_favs: List[str] = []
        extracted_seen: List[str] = []

        for turn in turns:
            text = turn.get("text", "")
            # Split into clauses by punctuation and coordinating conjunctions
            clauses = re.split(r'[.;,]|(?:\band\b)|(?:\balso\b)', text.lower())
            for clause in clauses:
                clause = clause.strip()
                if not clause:
                    continue
                is_fav = any(fav_cue in clause for fav_cue in ["favorite", "love", "loved", "fan of"])
                is_seen = any(seen_cue in clause for seen_cue in ["watched", "already seen", "saw", "seen"])

                for m in MOVIES_DATABASE:
                    title = m["title"]
                    if title.lower() in clause:
                        if is_fav and not is_seen:
                            extracted_favs.append(title)
                            if session_state is not None:
                                add_movie_to_favorites(
                                    session_state,
                                    movie_title=title,
                                    genre=m.get("genres", ["Sci-Fi"])[0] if m.get("genres") else "Sci-Fi"
                                )
                        elif is_seen:
                            extracted_seen.append(title)
                            if session_state is not None:
                                add_movie_to_seen_history(
                                    session_state,
                                    movie_title=title
                                )

        return {
            "favorites": list(set(extracted_favs)),
            "seen": list(set(extracted_seen))
        }

    async def summarize_async(
        self,
        turns: List[Dict[str, Any]],
        existing_summary: str = "",
        session_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Asynchronously summarizes conversation turns using Gemini LLM or semantic fallback."""
        # 1. Extract entities into session state
        self.extract_entities_from_turns(turns, session_state=session_state)

        # 2. Attempt LLM-driven summarization if client is available
        if self.client:
            try:
                prompt = self._build_summarization_prompt(turns, existing_summary)
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                if response and response.text:
                    cleaned = response.text.strip()
                    if cleaned:
                        return cleaned
            except Exception as e:
                logger.warning(f"Async LLM summarization fallback triggered due to: {e}")

        # 3. Fallback to semantic narrative synthesis
        return self._synthesize_narrative_summary(turns, existing_summary)

    def summarize_sync(
        self,
        turns: List[Dict[str, Any]],
        existing_summary: str = "",
        session_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synchronously summarizes conversation turns using Gemini LLM or semantic fallback."""
        # 1. Extract entities into session state
        self.extract_entities_from_turns(turns, session_state=session_state)

        # 2. Attempt LLM-driven summarization if client is available
        if self.client:
            try:
                prompt = self._build_summarization_prompt(turns, existing_summary)
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                if response and response.text:
                    cleaned = response.text.strip()
                    if cleaned:
                        return cleaned
            except Exception as e:
                logger.warning(f"Sync LLM summarization fallback triggered due to: {e}")

        # 3. Fallback to semantic narrative synthesis
        return self._synthesize_narrative_summary(turns, existing_summary)

    def _build_summarization_prompt(
        self,
        turns: List[Dict[str, Any]],
        existing_summary: str = ""
    ) -> str:
        """Constructs prompt for Gemini dialogue summarization."""
        turns_repr = []
        for t in turns:
            sender = t.get("sender") or t.get("role", "user")
            text = t.get("text", "")
            ui = t.get("ui_summary")
            line = f"{sender}: {text}"
            if ui:
                line += f" {ui}"
            turns_repr.append(line)

        dialogue_block = "\n".join(turns_repr)
        summary_context = f"Prior summary: {existing_summary}\n" if existing_summary else ""

        return (
            f"{SUMMARIZATION_SYSTEM_PROMPT}\n\n"
            f"{summary_context}"
            f"Dialogue turns to compact:\n"
            f"{dialogue_block}\n\n"
            f"Condensed summary narrative:"
        )

    def _synthesize_narrative_summary(
        self,
        turns: List[Dict[str, Any]],
        existing_summary: str = ""
    ) -> str:
        """Synthesizes a cohesive semantic narrative when LLM is offline or unavailable."""
        user_inquiries: List[str] = []
        agent_actions: List[str] = []
        entities_noted: List[str] = []

        for turn in turns:
            role = turn.get("role", "user")
            sender = turn.get("sender") or role
            text = turn.get("text", "").strip()
            ui = turn.get("ui_summary")

            if role == "user":
                # Extract core inquiry gist
                clean = text
                for p in ["what movies are", "can you show me", "show me", "can i see", "i want to see", "please"]:
                    if clean.lower().startswith(p):
                        clean = clean[len(p):].strip()
                        break
                gist = clean.split(".")[0].split("?")[0].strip()
                if gist and len(gist) > 3:
                    # Take up to 5 words for narrative brevity
                    words = gist.split()
                    short_gist = " ".join(words[:5])
                    user_inquiries.append(short_gist)
            else:
                if ui:
                    agent_actions.append(ui)
                elif text:
                    # Capture agent response gist
                    words = text.split()
                    short_act = " ".join(words[:5])
                    agent_actions.append(f"{sender}: {short_act}")

        # Extract mentioned movies
        for turn in turns:
            text_lower = turn.get("text", "").lower()
            for m in MOVIES_DATABASE:
                if m["title"].lower() in text_lower and m["title"] not in entities_noted:
                    entities_noted.append(m["title"])

        narrative_parts: List[str] = []
        if user_inquiries:
            topics = ", ".join(user_inquiries[:2])
            narrative_parts.append(f"User inquired about {topics}")
        if agent_actions:
            acts = "; ".join(agent_actions[:2])
            narrative_parts.append(f"Agent provided {acts}")
        if entities_noted:
            films = ", ".join(entities_noted[:2])
            narrative_parts.append(f"Discussed {films}")

        delta = ". ".join(narrative_parts) + "." if narrative_parts else "Prior conversation turns completed."

        if existing_summary:
            # Bound summary within 80 words to ensure constant token savings
            combined = f"{existing_summary} Next: {delta}"
            words = combined.split()
            if len(words) > 70:
                combined = "Earlier context: " + " ".join(words[-60:])
            return combined
        else:
            return f"Earlier context: {delta}"
