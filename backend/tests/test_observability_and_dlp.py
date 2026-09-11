"""Unit tests for Observability (JSON Logging, Distributed Tracing, Intent vs Outcome) and Cloud DLP."""

import json
import logging
import pytest
from fastapi.testclient import TestClient
from opentelemetry import trace

from backend.app import app
from backend.protocols.a2ui import A2UIComponent, A2UIMessage
from backend.telemetry.logging import (
    StructuredJsonFormatter,
    setup_structured_logging,
    get_recent_structured_logs,
    clear_structured_logs,
    get_logger
)
from backend.telemetry.tracing import (
    get_tracer,
    get_current_trace_and_span_ids,
    get_collected_spans,
    clear_collected_spans
)
from backend.telemetry.intent_outcome import (
    IntentOutcomeTracker,
    INTENT_EXPECTED_OUTCOMES
)
from backend.security.dlp_service import (
    CloudDlpInspectionService,
    get_dlp_service
)
from backend.plugins.security_guardrails import InputSecurityGuardrailPlugin


@pytest.fixture(autouse=True)
def clean_telemetry_state():
    """Ensure clean logs and span buffers for each test."""
    clear_structured_logs()
    clear_collected_spans()
    yield
    clear_structured_logs()
    clear_collected_spans()


# --------------------------------------------------------------------------
# 1. Structured JSON Logging Tests
# --------------------------------------------------------------------------

def test_structured_json_formatter_fields():
    formatter = StructuredJsonFormatter(project_id="test-project")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/app/test.py",
        lineno=42,
        msg="Booking confirmed for %s",
        args=("Interstellar",),
        exc_info=None
    )
    record.session_id = "sess-abc-123"
    record.agent = "BookingAgent"
    record.intent = "BOOKING_CONFIRM"
    record.outcome = "SUCCESS"

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["severity"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Booking confirmed for Interstellar"
    assert parsed["session_id"] == "sess-abc-123"
    assert parsed["agent"] == "BookingAgent"
    assert parsed["intent"] == "BOOKING_CONFIRM"
    assert parsed["outcome"] == "SUCCESS"
    assert parsed["location"]["file"] == "/app/test.py"
    assert parsed["location"]["line"] == 42
    assert "timestamp" in parsed


def test_structured_json_correlation_with_opentelemetry_span():
    setup_structured_logging(project_id="gcp-cinema-test")
    tracer = get_tracer("test_tracer")
    test_logger = get_logger("correlated_test")

    with tracer.start_as_current_span("agent_execution_span") as span:
        ctx = span.get_span_context()
        expected_trace_id = format(ctx.trace_id, "032x")
        expected_span_id = format(ctx.span_id, "016x")

        test_logger.info("Executing subagent reasoning step", extra={"session_id": "trace-sess-1"})

    logs = get_recent_structured_logs()
    matching_logs = [l for l in logs if l.get("message") == "Executing subagent reasoning step"]
    assert len(matching_logs) >= 1
    log_entry = matching_logs[-1]

    assert log_entry["trace_id"] == expected_trace_id
    assert log_entry["span_id"] == expected_span_id
    assert log_entry["logging.googleapis.com/trace"].endswith(f"/traces/{expected_trace_id}")
    assert log_entry["logging.googleapis.com/spanId"] == expected_span_id


# --------------------------------------------------------------------------
# 2. OpenTelemetry Tracing Tests
# --------------------------------------------------------------------------

def test_distributed_tracing_spans_generation():
    tracer = get_tracer("outings_test")

    with tracer.start_as_current_span("coordinator_dispatch") as root_span:
        root_span.set_attribute("routing.intent", "BOOKING_SEATS")
        with tracer.start_as_current_span("booking_agent_action") as child_span:
            child_span.set_attribute("seat.hold_token", "HLD-999")

    spans = get_collected_spans()
    span_names = [s["name"] for s in spans]
    assert "coordinator_dispatch" in span_names
    assert "booking_agent_action" in span_names

    booking_span = next(s for s in spans if s["name"] == "booking_agent_action")
    coordinator_span = next(s for s in spans if s["name"] == "coordinator_dispatch")

    # Verify parent-child correlation
    assert booking_span["parent_span_id"] == coordinator_span["span_id"]
    assert booking_span["trace_id"] == coordinator_span["trace_id"]
    assert booking_span["attributes"]["seat.hold_token"] == "HLD-999"


# --------------------------------------------------------------------------
# 3. Intent vs Outcome Evaluation Tests
# --------------------------------------------------------------------------

def test_intent_vs_outcome_match():
    tracker = IntentOutcomeTracker()
    response = A2UIMessage(
        session_id="eval-sess-1",
        text="Here is the seating map for Metropolis Cinema.",
        components=[
            A2UIComponent(type="seat_map_selector", props={"showtime_id": "st-1", "available_seats": ["E5", "E6"]})
        ],
        agent="BookingAgent"
    )

    result = tracker.evaluate_and_log(
        session_id="eval-sess-1",
        intent="BOOKING_SEATS",
        model_tier="gemini-2.5-flash",
        response=response,
        latency_ms=145.2
    )

    assert result.intent_matched is True
    assert result.status == "SUCCESS"
    assert result.match_score == 1.0
    assert "seat_map_selector" in result.actual_components
    assert result.agent_dispatched == "BookingAgent"


def test_intent_vs_outcome_mismatch():
    tracker = IntentOutcomeTracker()
    # Response contains only a movie card instead of the expected seat_map_selector
    response = A2UIMessage(
        session_id="eval-sess-2",
        text="Check out this movie instead.",
        components=[
            A2UIComponent(type="movie_card", props={"title": "Inception"})
        ],
        agent="SearchRecoAgent"
    )

    result = tracker.evaluate_and_log(
        session_id="eval-sess-2",
        intent="BOOKING_SEATS",
        model_tier="gemini-2.5-flash",
        response=response,
        latency_ms=210.0
    )

    assert result.intent_matched is False
    assert result.status == "MISMATCH"
    assert result.match_score < 1.0


def test_intent_outcome_metrics_summary():
    tracker = IntentOutcomeTracker()

    good_resp = A2UIMessage(
        session_id="s1",
        text="Ticket confirmed",
        components=[A2UIComponent(type="ticket_pass", props={})],
        agent="BookingAgent"
    )
    bad_resp = A2UIMessage(
        session_id="s2",
        text="Error booking",
        components=[],
        agent="SearchRecoAgent"
    )

    tracker.evaluate_and_log("s1", "BOOKING_CONFIRM", "flash", good_resp, 100.0)
    tracker.evaluate_and_log("s2", "BOOKING_CONFIRM", "flash", bad_resp, 100.0)

    summary = tracker.get_metrics_summary()
    assert summary["total_evaluations"] == 2
    assert summary["matched_count"] == 1
    assert summary["mismatch_count"] == 1
    assert summary["intent_match_rate"] == 0.5
    assert "BOOKING_CONFIRM" in summary["per_intent_breakdown"]


# --------------------------------------------------------------------------
# 4. Cloud DLP and Sensitive Data Protection Tests
# --------------------------------------------------------------------------

def test_dlp_redacts_credit_card():
    dlp = CloudDlpInspectionService()
    result = dlp.inspect_and_redact("Please charge card 4532 8901 2345 6789 for 2 tickets.")
    assert "4532 8901 2345 6789" not in result.sanitized_text
    assert "[REDACTED_PAYMENT_CARD]" in result.sanitized_text
    assert result.is_sensitive is True
    assert result.findings_count >= 1


def test_dlp_redacts_email_and_phone():
    dlp = CloudDlpInspectionService()
    text = "Send the tickets to user.test@example.com or SMS +1 (555) 234-5678."
    result = dlp.inspect_and_redact(text)

    assert "user.test@example.com" not in result.sanitized_text
    assert "[REDACTED_EMAIL]" in result.sanitized_text
    assert "555) 234-5678" not in result.sanitized_text
    assert "[REDACTED_PHONE]" in result.sanitized_text
    assert result.is_sensitive is True


def test_dlp_redacts_ssn_and_tokens():
    dlp = CloudDlpInspectionService()
    text = "User SSN is 123-45-6789 and API token is AIzaSyD9876543210abcdefghij1234567890."
    result = dlp.inspect_and_redact(text)

    assert "123-45-6789" not in result.sanitized_text
    assert "[REDACTED_SSN]" in result.sanitized_text
    assert "AIzaSy" not in result.sanitized_text
    assert "[REDACTED_AUTH_TOKEN]" in result.sanitized_text


def test_input_guardrail_integration_with_dlp():
    guardrail = InputSecurityGuardrailPlugin()
    clean_text = guardrail.validate_and_sanitize(
        "Book Dune for john.doe@cinema.com with card 4111-2222-3333-4444"
    )

    assert "john.doe@cinema.com" not in clean_text
    assert "[REDACTED_EMAIL]" in clean_text
    assert "4111-2222-3333-4444" not in clean_text
    assert "[REDACTED_PAYMENT_CARD]" in clean_text

    stats = guardrail.get_dlp_summary()
    assert stats["total_inspections"] >= 1
    assert stats["sensitive_detections_count"] >= 2


# --------------------------------------------------------------------------
# 5. FastAPI Observability Endpoints Tests
# --------------------------------------------------------------------------

def test_api_health_observability_metadata():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert "observability" in data
    assert "structured_logging" in data["observability"]
    assert "distributed_tracing" in data["observability"]
    assert "dlp_inspection" in data["observability"]
    assert "OpenTelemetry W3C Tracing" in data["protocols"]
    assert any("IntentOutcomeEvaluationPlugin" in e for e in data["evaluations"])


def test_api_telemetry_and_traceparent_headers():
    client = TestClient(app)

    # 1. Trigger request and verify W3C traceparent response header
    res = client.get("/api/v1/telemetry")
    assert res.status_code == 200
    assert "traceparent" in res.headers
    assert "X-Trace-Id" in res.headers
    assert "X-Span-Id" in res.headers

    data = res.json()
    assert "intent_vs_outcome" in data
    assert "cloud_dlp" in data
    assert "open_telemetry" in data
    assert data["open_telemetry"]["service_name"] == "cinema-outings-agent"


def test_api_telemetry_traces_and_logs_endpoints():
    client = TestClient(app)

    # Make a chat request to generate logs and spans
    client.get("/api/v1/health")

    traces_res = client.get("/api/v1/telemetry/traces?limit=10")
    assert traces_res.status_code == 200
    traces_data = traces_res.json()
    assert "spans" in traces_data
    assert len(traces_data["spans"]) >= 1

    logs_res = client.get("/api/v1/telemetry/logs?limit=10")
    assert logs_res.status_code == 200
    logs_data = logs_res.json()
    assert "logs" in logs_data
    assert isinstance(logs_data["logs"], list)
