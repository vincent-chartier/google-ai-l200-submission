"""Explicit Intent vs Outcome Logging and Evaluation for Cinema Outings Multi-Agent System.

Provides:
1. Formal mapping between detected user/routing intent and expected system outcomes.
2. Real-time evaluation comparing routed intent to actual agent response (A2UI components, status, state changes).
3. Structured JSON logging of every intent-to-outcome transition.
4. Aggregated metrics on intent accuracy, outcome fulfillment, and failure diagnostics.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.protocols.a2ui import A2UIMessage
from backend.telemetry.logging import get_logger
from backend.telemetry.tracing import get_current_trace_and_span_ids

logger = get_logger("intent_outcome")

# Intent definitions and their expected UI component contracts
INTENT_EXPECTED_OUTCOMES: Dict[str, Dict[str, Any]] = {
    "BOOKING_SEATS": {
        "expected_agent": "BookingAgent",
        "expected_components": ["seat_map_selector"],
        "expected_actions": ["SELECT_SEATS", "HOLD_SEATS"],
        "description": "User requested seating chart; expected seat map selector widget."
    },
    "BOOKING_CONFIRM": {
        "expected_agent": "BookingAgent",
        "expected_components": ["ticket_pass"],
        "expected_actions": ["SEND_CALENDAR_INVITE", "VIEW_HISTORY"],
        "description": "User confirmed payment; expected digital ticket pass widget."
    },
    "SEARCH_RECO": {
        "expected_agent": "SearchRecoAgent",
        "expected_components": ["movie_card"],
        "expected_actions": ["SELECT_SHOWTIME", "ADD_FAVORITE"],
        "description": "User requested discovery/recommendations; expected movie cards."
    },
    "HOUSEKEEPING_CALENDAR": {
        "expected_agent": "HousekeepingAgent",
        "expected_components": ["calendar_invite_card"],
        "expected_actions": ["VIEW_HISTORY", "RECOMMEND_MOVIES"],
        "description": "User requested calendar invite; expected calendar widget."
    },
    "HOUSEKEEPING_HISTORY": {
        "expected_agent": "HousekeepingAgent",
        "expected_components": ["seen_history_viewer"],
        "expected_actions": ["RECOMMEND_MOVIES"],
        "description": "User requested watched history or profile; expected seen history viewer."
    },
    "HOUSEKEEPING_FAVORITE": {
        "expected_agent": "HousekeepingAgent",
        "expected_components": [],
        "expected_actions": ["RECOMMEND_MOVIES"],
        "description": "User saved a movie to favorites; expected state confirmation."
    },
    "UNKNOWN": {
        "expected_agent": "SearchRecoAgent",
        "expected_components": [],
        "expected_actions": [],
        "description": "Fallback or general conversational intent."
    }
}


@dataclass
class IntentOutcomeResult:
    timestamp: float
    session_id: str
    intent: str
    model_tier: str
    agent_dispatched: str
    expected_components: List[str]
    actual_components: List[str]
    intent_matched: bool
    status: str
    match_score: float
    latency_ms: float
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "intent": self.intent,
            "model_tier": self.model_tier,
            "agent_dispatched": self.agent_dispatched,
            "expected_components": self.expected_components,
            "actual_components": self.actual_components,
            "intent_matched": self.intent_matched,
            "status": self.status,
            "match_score": self.match_score,
            "latency_ms": self.latency_ms,
            "details": self.details
        }


class IntentOutcomeTracker:
    """Evaluates and logs intent vs outcome correlation for multi-agent workflows."""

    def __init__(self):
        self.history: List[IntentOutcomeResult] = []

    def evaluate_and_log(
        self,
        session_id: str,
        intent: str,
        model_tier: str,
        response: A2UIMessage,
        latency_ms: float,
        error: Optional[str] = None
    ) -> IntentOutcomeResult:
        """Compares detected intent against the actual generated A2UIMessage response."""
        now = time.time()
        trace_id, span_id = get_current_trace_and_span_ids()

        contract = INTENT_EXPECTED_OUTCOMES.get(intent, INTENT_EXPECTED_OUTCOMES["UNKNOWN"])
        expected_comps = contract.get("expected_components", [])

        # Extract actual component types
        actual_comps = [
            c.type if hasattr(c, "type") else c.get("type", "")
            for c in (response.components or [])
        ]

        # Check intent match:
        # 1. Did response come from expected agent?
        expected_agent = contract.get("expected_agent")
        agent_match = (expected_agent is None) or (response.agent == expected_agent)

        # 2. Were required A2UI components generated?
        if expected_comps:
            comp_match = any(ec in actual_comps for ec in expected_comps)
        else:
            comp_match = True

        status = "SUCCESS" if (not error and comp_match and agent_match) else "MISMATCH" if not comp_match else "ERROR"
        intent_matched = (status == "SUCCESS")

        score = 1.0 if intent_matched else (0.5 if (agent_match or comp_match) else 0.0)

        result = IntentOutcomeResult(
            timestamp=now,
            session_id=session_id,
            intent=intent,
            model_tier=model_tier,
            agent_dispatched=response.agent,
            expected_components=expected_comps,
            actual_components=actual_comps,
            intent_matched=intent_matched,
            status=status,
            match_score=score,
            latency_ms=round(latency_ms, 2),
            trace_id=trace_id,
            span_id=span_id,
            details={
                "description": contract.get("description", ""),
                "error": error,
                "text_summary": response.text[:120] if response.text else ""
            }
        )

        self.history.append(result)

        # Structured JSON Log with explicit intent vs outcome fields
        log_level = logger.info if intent_matched else logger.warning
        log_level(
            f"Intent vs Outcome evaluation: intent={intent} status={status} matched={intent_matched}",
            extra={
                "event": "INTENT_VS_OUTCOME",
                "session_id": session_id,
                "intent": intent,
                "outcome": status,
                "expected_outcome": {"components": expected_comps, "agent": expected_agent},
                "actual_outcome": {"components": actual_comps, "agent": response.agent, "status": status},
                "intent_matched": intent_matched,
                "match_score": score,
                "latency_ms": round(latency_ms, 2)
            }
        )

        return result

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Calculates aggregate intent vs outcome performance metrics."""
        total = len(self.history)
        if total == 0:
            return {
                "total_evaluations": 0,
                "matched_count": 0,
                "mismatch_count": 0,
                "intent_match_rate": 1.0,
                "avg_match_score": 1.0,
                "per_intent_breakdown": {}
            }

        matched = sum(1 for r in self.history if r.intent_matched)
        avg_score = sum(r.match_score for r in self.history) / total

        breakdown: Dict[str, Dict[str, Any]] = {}
        for r in self.history:
            if r.intent not in breakdown:
                breakdown[r.intent] = {"total": 0, "matched": 0, "mismatched": 0}
            breakdown[r.intent]["total"] += 1
            if r.intent_matched:
                breakdown[r.intent]["matched"] += 1
            else:
                breakdown[r.intent]["mismatched"] += 1

        for intent_data in breakdown.values():
            t = intent_data["total"]
            m = intent_data["matched"]
            intent_data["rate"] = round(m / t, 3) if t > 0 else 1.0

        return {
            "total_evaluations": total,
            "matched_count": matched,
            "mismatch_count": total - matched,
            "intent_match_rate": round(matched / total, 3),
            "avg_match_score": round(avg_score, 3),
            "per_intent_breakdown": breakdown
        }

    def clear(self) -> None:
        """Clears evaluation history."""
        self.history.clear()


# Global Singleton Tracker
_INTENT_TRACKER = IntentOutcomeTracker()


def get_intent_outcome_tracker() -> IntentOutcomeTracker:
    """Returns global IntentOutcomeTracker singleton."""
    return _INTENT_TRACKER
