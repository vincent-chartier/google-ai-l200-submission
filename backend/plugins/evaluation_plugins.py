"""Evaluation Plugins for Cinema Outings Multi-Agent System.

Provides automated evaluation and telemetry for:
1. Recommendation Quality: Duplicate avoidance (zero seen movies) and taste grounding.
2. Tool Sequence Accuracy: Ensuring valid state transitions across multi-agent workflows.
3. Latency & Cost Telemetry: Benchmarking performance across Gemini Flash, Pro, and Flash-Lite.
"""

import time
from typing import Dict, Any, List, Optional
from google.adk.plugins import BasePlugin


class RecommendationEvaluationPlugin(BasePlugin):
    """Evaluates recommendation relevance, duplicate exclusion, and taste alignment."""

    def __init__(self):
        super().__init__(name="recommendation_evaluation_plugin")

    def evaluate_negative_constraints(
        self,
        recommended_titles: List[str],
        seen_movies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluates whether any recommended movies violate the seen-movies exclusion rule."""
        seen_titles_lower = {
            m.get("title", "").strip().lower() for m in seen_movies if isinstance(m, dict)
        }
        duplicates = [
            title for title in recommended_titles
            if title.strip().lower() in seen_titles_lower
        ]

        total = len(recommended_titles)
        clean_count = total - len(duplicates)
        clean_rate = (clean_count / total) if total > 0 else 1.0

        return {
            "total_recommended": total,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "clean_recommendation_rate": clean_rate,
            "passed": len(duplicates) == 0
        }

    def evaluate_taste_grounding(
        self,
        taste_match_reason: str,
        favorite_movies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verifies that the taste explanation grounds itself in the user's actual favorites."""
        fav_titles = [f.get("title", "") for f in favorite_movies if isinstance(f, dict)]
        matched_favorites = [
            title for title in fav_titles
            if title and title.lower() in taste_match_reason.lower()
        ]

        is_grounded = len(matched_favorites) > 0 or len(fav_titles) == 0

        return {
            "is_grounded": is_grounded,
            "matched_favorites": matched_favorites,
            "taste_match_reason": taste_match_reason,
            "available_favorites_count": len(fav_titles)
        }


class ToolSequenceEvaluationPlugin(BasePlugin):
    """Evaluates tool invocation sequence correctness in transactional outing workflows."""

    EXPECTED_BOOKING_SEQUENCE = ["check_availability", "hold_seats", "process_payment", "calendar_invite"]

    def __init__(self):
        super().__init__(name="tool_sequence_evaluation_plugin")

    def evaluate_sequence(self, actions_taken: List[str]) -> Dict[str, Any]:
        """Evaluates whether the user's booking workflow adhered to the safe transition path."""
        violations = []

        # Payment without hold check
        if "process_payment" in actions_taken:
            if "hold_seats" not in actions_taken:
                violations.append("Payment executed without prior seat reservation hold.")

        # Calendar before payment check
        if "calendar_invite" in actions_taken:
            if "process_payment" not in actions_taken:
                violations.append("Calendar invite dispatched prior to payment confirmation.")

        return {
            "actions_count": len(actions_taken),
            "actions_sequence": actions_taken,
            "violations": violations,
            "is_valid_sequence": len(violations) == 0
        }


class LatencyAndCostTelemetryPlugin(BasePlugin):
    """Tracks latency, token throughput, and estimated API cost per model tier."""

    # Estimated pricing per 1M tokens (USD)
    ESTIMATED_RATES = {
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.0-flash-lite": {"input": 0.0375, "output": 0.15},
    }

    def __init__(self):
        super().__init__(name="latency_and_cost_telemetry_plugin")
        self.records: List[Dict[str, Any]] = []

    def record_call(
        self,
        agent_name: str,
        model_name: str,
        duration_ms: float,
        prompt_tokens: int = 250,
        completion_tokens: int = 150
    ) -> Dict[str, Any]:
        """Logs an LLM invocation with latency and estimated cost."""
        rates = self.ESTIMATED_RATES.get(model_name, {"input": 0.10, "output": 0.40})
        cost = (
            (prompt_tokens / 1_000_000) * rates["input"] +
            (completion_tokens / 1_000_000) * rates["output"]
        )

        record = {
            "timestamp": time.time(),
            "agent": agent_name,
            "model": model_name,
            "duration_ms": round(duration_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": round(cost, 6)
        }
        self.records.append(record)
        return record

    def get_summary(self) -> Dict[str, Any]:
        """Aggregates telemetry records across all invocations."""
        total_calls = len(self.records)
        total_duration = sum(r["duration_ms"] for r in self.records)
        total_cost = sum(r["estimated_cost_usd"] for r in self.records)

        per_model = {}
        for r in self.records:
            m = r["model"]
            per_model[m] = per_model.get(m, 0) + 1

        return {
            "total_calls": total_calls,
            "avg_duration_ms": round(total_duration / total_calls, 2) if total_calls else 0.0,
            "total_estimated_cost_usd": round(total_cost, 6),
            "calls_per_model": per_model
        }


class ContextCompactionEvaluationPlugin(BasePlugin):
    """Evaluates context compaction efficiency, token reduction ratio, and state preservation."""

    def __init__(self):
        super().__init__(name="context_compaction_evaluation_plugin")

    def evaluate_compaction(
        self,
        tokens_before: int,
        tokens_after: int,
        turns_compacted: int,
        remaining_turns: int
    ) -> Dict[str, Any]:
        """Evaluates token reduction efficiency and verifies context bounds."""
        tokens_saved = max(0, tokens_before - tokens_after)
        reduction_rate = (tokens_saved / tokens_before) if tokens_before > 0 else 0.0

        return {
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "tokens_saved": tokens_saved,
            "reduction_rate": round(reduction_rate, 4),
            "turns_compacted": turns_compacted,
            "remaining_turns": remaining_turns,
            "passed": tokens_after <= tokens_before and turns_compacted > 0
        }

    def evaluate_entity_preservation(
        self,
        expected_entities: List[str],
        actual_entities: List[str]
    ) -> Dict[str, Any]:
        """Verifies that key user entities/preferences were preserved after dialogue compaction."""
        actual_lower = {e.strip().lower() for e in actual_entities}
        preserved = [e for e in expected_entities if e.strip().lower() in actual_lower]
        missing = [e for e in expected_entities if e.strip().lower() not in actual_lower]

        return {
            "expected_count": len(expected_entities),
            "preserved_count": len(preserved),
            "missing": missing,
            "preservation_rate": (len(preserved) / len(expected_entities)) if expected_entities else 1.0,
            "passed": len(missing) == 0
        }


class IntentOutcomeEvaluationPlugin(BasePlugin):
    """Evaluates the alignment between detected user intent and actual agent outcomes."""

    def __init__(self):
        super().__init__(name="intent_outcome_evaluation_plugin")
        from backend.telemetry.intent_outcome import get_intent_outcome_tracker
        self.tracker = get_intent_outcome_tracker()

    def evaluate_intent_outcome(
        self,
        session_id: str,
        intent: str,
        model_tier: str,
        response: Any,
        latency_ms: float,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs explicit intent vs outcome evaluation and records structured metrics."""
        result = self.tracker.evaluate_and_log(
            session_id=session_id,
            intent=intent,
            model_tier=model_tier,
            response=response,
            latency_ms=latency_ms,
            error=error
        )
        return result.to_dict()

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate intent vs outcome performance statistics."""
        return self.tracker.get_metrics_summary()
