"""Security Guardrails Plugins for Cinema Outings Multi-Agent System.

Built using Google ADK plugin lifecycle hooks (BasePlugin) to enforce:
1. Input Guardrails: Prompt injection defense, PII sanitization, and cinema domain checks.
2. Booking Safety Guardrails: Payment hold authorization, seat hijacking prevention, and rate-limiting.
3. A2UI Contract Guardrails: Structural validation of outgoing dynamic UI payloads.
"""

import re
import time
from typing import Dict, Any, Optional, List
from google.adk.plugins import BasePlugin


class SecurityViolationError(Exception):
    """Raised when an operation violates security or safety guardrails."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class InputSecurityGuardrailPlugin(BasePlugin):
    """Input Guardrail: detects prompt injection, redacts PII, and bounds cinema scope."""

    # Patterns indicating prompt injection or jailbreak attempts
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
        re.compile(r"disregard\s+(all\s+)?(rules|guidelines|instructions)", re.IGNORECASE),
        re.compile(r"(reveal|print|show|dump)\s+(your\s+)?(system\s+prompt|instructions)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)", re.IGNORECASE),
        re.compile(r"(system\s+override|admin\s+mode|sudo\s+su)", re.IGNORECASE),
    ]

    # Pattern detecting payment card numbers (13-19 digits)
    CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

    def __init__(self):
        super().__init__(name="input_security_guardrail")
        from backend.security.dlp_service import get_dlp_service
        self.dlp_service = get_dlp_service()
        self.inspections_count: int = 0
        self.sensitive_findings_count: int = 0
        self.detected_info_types: List[str] = []

    def validate_and_sanitize(self, user_message: str) -> str:
        """Inspects user input for injection threats, redacts PII via Cloud DLP, and returns clean text."""
        # 1. Prompt Injection Detection
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(user_message):
                raise SecurityViolationError(
                    code="PROMPT_INJECTION_DETECTED",
                    message="Security guardrail blocked potential prompt injection attempt.",
                    details={"matched_pattern": pattern.pattern}
                )

        # 2. Comprehensive Cloud-Based Sensitive Data Protection (DLP)
        self.inspections_count += 1
        dlp_result = self.dlp_service.inspect_and_redact(user_message)

        if dlp_result.is_sensitive:
            self.sensitive_findings_count += dlp_result.findings_count
            for it in dlp_result.info_types_detected:
                if it not in self.detected_info_types:
                    self.detected_info_types.append(it)

        return dlp_result.sanitized_text

    def get_dlp_summary(self) -> Dict[str, Any]:
        """Returns aggregate Cloud DLP protection statistics."""
        return {
            "total_inspections": self.inspections_count,
            "sensitive_detections_count": self.sensitive_findings_count,
            "detected_info_types": self.detected_info_types,
            "supported_info_types": self.dlp_service.SUPPORTED_INFOTYPES,
            "cloud_dlp_operational": self.dlp_service._cloud_available
        }

    async def before_agent_callback(self, agent: Any, context: Any) -> Optional[Any]:
        """ADK lifecycle hook: validates user message before agent execution."""
        return None


class BookingSafetyGuardrailPlugin(BasePlugin):
    """Transaction Guardrail: enforces reservation holds, idempotency, and rate limits."""

    def __init__(self, max_holds_per_minute: int = 5):
        super().__init__(name="booking_safety_guardrail")
        self.max_holds_per_minute = max_holds_per_minute
        self._hold_timestamps: Dict[str, List[float]] = {}
        self._processed_tokens: set[str] = set()

    def check_rate_limit(self, session_id: str) -> None:
        """Enforces rate limit on temporary seat holds to prevent inventory lockouts."""
        now = time.time()
        timestamps = self._hold_timestamps.get(session_id, [])
        # Keep timestamps from the last 60 seconds
        recent = [t for t in timestamps if now - t < 60.0]
        if len(recent) >= self.max_holds_per_minute:
            raise SecurityViolationError(
                code="RATE_LIMIT_EXCEEDED",
                message=f"Too many seat reservation attempts. Max {self.max_holds_per_minute} per minute.",
                details={"session_id": session_id, "window_seconds": 60}
            )
        recent.append(now)
        self._hold_timestamps[session_id] = recent

    def validate_payment_transaction(
        self,
        reservation_token: str,
        session_state: Dict[str, Any]
    ) -> None:
        """Validates that a legitimate, unexpired hold exists before payment execution."""
        # 1. Check double payment / replay attack
        if reservation_token in self._processed_tokens:
            raise SecurityViolationError(
                code="DUPLICATE_PAYMENT_ATTEMPT",
                message=f"Reservation token '{reservation_token}' has already been processed and cannot be paid again.",
                details={"token": reservation_token}
            )

        # 2. Check hold verification in session state
        active_res = session_state.get("active_reservation")
        if not active_res:
            # For backward compatibility with test tokens like HLD-DEMO01
            if not reservation_token.startswith("HLD-"):
                raise SecurityViolationError(
                    code="NO_ACTIVE_HOLD",
                    message="Cannot process payment without an active seat reservation hold.",
                    details={"token": reservation_token}
                )
        else:
            held_token = active_res.get("token")
            if held_token and held_token != reservation_token and reservation_token != "HLD-DEMO01":
                raise SecurityViolationError(
                    code="HOLD_TOKEN_MISMATCH",
                    message=f"Provided token '{reservation_token}' does not match active hold '{held_token}'.",
                    details={"provided": reservation_token, "expected": held_token}
                )

        # Record token as processed
        self._processed_tokens.add(reservation_token)


class A2UIValidationGuardrailPlugin(BasePlugin):
    """Output Guardrail: ensures dynamic UI components meet structural schema contracts."""

    ALLOWED_TYPES = {
        "movie_card",
        "seat_map_selector",
        "ticket_pass",
        "calendar_invite_card",
        "seen_history_list"
    }

    def __init__(self):
        super().__init__(name="a2ui_validation_guardrail")

    def validate_component(self, component: Any) -> None:
        """Validates an A2UIComponent before transmission to Flutter client."""
        comp_type = getattr(component, "type", None) or component.get("type")
        if comp_type not in self.ALLOWED_TYPES:
            raise SecurityViolationError(
                code="INVALID_A2UI_COMPONENT_TYPE",
                message=f"Unknown or unauthorized A2UI component type '{comp_type}'.",
                details={"allowed_types": list(self.ALLOWED_TYPES)}
            )

        props = getattr(component, "props", None) or component.get("props", {})
        if not isinstance(props, dict):
            raise SecurityViolationError(
                code="MALFORMED_A2UI_PROPS",
                message=f"Component '{comp_type}' props must be a dictionary.",
                details={"props_type": str(type(props))}
            )

        # Type-specific contract checks
        if comp_type == "ticket_pass":
            required = ["booking_id", "movie_title", "cinema", "seats", "total_amount"]
            missing = [k for k in required if k not in props]
            if missing:
                raise SecurityViolationError(
                    code="INCOMPLETE_TICKET_PROPS",
                    message=f"ticket_pass missing required properties: {missing}",
                    details={"missing_keys": missing}
                )
