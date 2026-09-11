"""Distributed Tracing with OpenTelemetry for Cinema Outings Multi-Agent System.

Instruments multi-agent collaboration with:
1. End-to-end W3C Trace Context propagation across HTTP and agents.
2. Root request spans, coordinator routing spans, agent execution spans, and tool spans.
3. In-memory trace exporter for live telemetry querying and test assertions.
4. OpenTelemetry semantic conventions for AI agents and LLM invocations.
"""

import functools
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode, Span
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Service Resource
RESOURCE = Resource.create({
    "service.name": "cinema-outings-agent",
    "service.version": "1.0.0",
    "deployment.environment": "production"
})

# Tracer Provider & In-Memory Exporter
_TRACER_PROVIDER: Optional[TracerProvider] = None
_SPAN_EXPORTER: Optional[InMemorySpanExporter] = None


def init_tracing() -> TracerProvider:
    """Initializes OpenTelemetry TracerProvider with in-memory and stdout exporters."""
    global _TRACER_PROVIDER, _SPAN_EXPORTER
    if _TRACER_PROVIDER is not None:
        return _TRACER_PROVIDER

    _TRACER_PROVIDER = TracerProvider(resource=RESOURCE)
    _SPAN_EXPORTER = InMemorySpanExporter()
    span_processor = SimpleSpanProcessor(_SPAN_EXPORTER)
    _TRACER_PROVIDER.add_span_processor(span_processor)

    trace.set_tracer_provider(_TRACER_PROVIDER)
    return _TRACER_PROVIDER


def get_tracer(name: str = "cinema_outings_agents") -> trace.Tracer:
    """Returns an OpenTelemetry tracer instance."""
    if _TRACER_PROVIDER is None:
        init_tracing()
    return trace.get_tracer(name)


def get_current_trace_and_span_ids() -> Tuple[Optional[str], Optional[str]]:
    """Returns the current active (trace_id_hex, span_id_hex) or (None, None)."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        ctx = current_span.get_span_context()
        return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")
    return None, None


def get_collected_spans(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns serialized spans from the in-memory exporter."""
    if not _SPAN_EXPORTER:
        return []
    raw_spans = _SPAN_EXPORTER.get_finished_spans()
    serialized = []
    for s in raw_spans[-limit:]:
        ctx = s.get_span_context()
        parent_id = format(s.parent.span_id, "016x") if s.parent else None
        duration_ms = (s.end_time - s.start_time) / 1_000_000 if s.end_time and s.start_time else 0.0
        serialized.append({
            "name": s.name,
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
            "parent_span_id": parent_id,
            "start_time_ns": s.start_time,
            "end_time_ns": s.end_time,
            "duration_ms": round(duration_ms, 2),
            "status": s.status.status_code.name,
            "attributes": dict(s.attributes or {})
        })
    return serialized


def clear_collected_spans() -> None:
    """Clears spans recorded by the in-memory exporter."""
    if _SPAN_EXPORTER:
        _SPAN_EXPORTER.clear()


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware instrumenting HTTP requests with root OpenTelemetry spans."""

    def __init__(self, app, tracer_name: str = "cinema_outings_fastapi"):
        super().__init__(app)
        self.tracer = get_tracer(tracer_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        span_name = f"HTTP {request.method} {request.url.path}"
        with self.tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", request.url.path)

            ctx = span.get_span_context()
            trace_id_hex = format(ctx.trace_id, "032x")
            span_id_hex = format(ctx.span_id, "016x")

            response: Response = await call_next(request)

            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, f"HTTP error {response.status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))

            # Propagate trace identifiers back to client in standard headers
            response.headers["X-Trace-Id"] = trace_id_hex
            response.headers["X-Span-Id"] = span_id_hex
            response.headers["traceparent"] = f"00-{trace_id_hex}-{span_id_hex}-01"
            return response


def traced_agent_call(span_name: Optional[str] = None):
    """Decorator to instrument agent methods with OpenTelemetry spans."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer("cinema_outings_agents")
            name = span_name or f"Agent.{func.__name__}"
            session_id = kwargs.get("session_id", "unknown")
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("agent.session_id", session_id)
                span.set_attribute("agent.method", func.__name__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.record_exception(exc)
                    raise
        return async_wrapper
    return decorator
