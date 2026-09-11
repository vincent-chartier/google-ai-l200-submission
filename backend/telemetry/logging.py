"""Structured JSON Logging for Cinema Outings Multi-Agent System.

Provides machine-readable JSON logging with:
1. ISO-8601 UTC timestamps
2. OpenTelemetry trace_id and span_id correlation
3. Google Cloud Logging semantic compatibility (severity, logging.googleapis.com/trace)
4. Contextual fields (session_id, agent, intent, outcome)
5. In-memory log capture buffer for evaluation and debugging
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class StructuredJsonFormatter(logging.Formatter):
    """Formats standard Python logging records into structured JSON lines."""

    def __init__(self, project_id: Optional[str] = None):
        super().__init__()
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("PROJECT_ID", "vchartier-project"))

    def format(self, record: logging.LogRecord) -> str:
        # 1. Base log record payload
        created_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload: Dict[str, Any] = {
            "timestamp": created_dt.isoformat(),
            "level": record.levelname,
            "severity": record.levelname,  # GCP Logging severity
            "logger": record.name,
            "message": record.getMessage(),
            "location": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
        }

        # 2. Extract OpenTelemetry tracing context if active
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                ctx = current_span.get_span_context()
                trace_id_hex = format(ctx.trace_id, "032x")
                span_id_hex = format(ctx.span_id, "016x")
                payload["trace_id"] = trace_id_hex
                payload["span_id"] = span_id_hex
                # Google Cloud Logging trace format
                payload["logging.googleapis.com/trace"] = f"projects/{self.project_id}/traces/{trace_id_hex}"
                payload["logging.googleapis.com/spanId"] = span_id_hex
        except ImportError:
            pass

        # 3. Extract contextual agent/session fields if passed via extra
        context_fields = [
            "session_id", "agent", "intent", "outcome", "expected_outcome",
            "latency_ms", "model_tier", "selected_model", "event", "user_id"
        ]
        for field in context_fields:
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        # 4. Include custom extra data dictionary if provided
        if hasattr(record, "metadata") and isinstance(record.metadata, dict):
            payload["metadata"] = record.metadata

        # 5. Include exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


# Global in-memory log buffer for testing and verification
_LOG_BUFFER: List[Dict[str, Any]] = []
_MAX_BUFFER_SIZE = 500


class InMemoryLogHandler(logging.Handler):
    """Stores structured JSON logs in an in-memory deque for programmatic querying."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.formatter:
                formatted = self.formatter.format(record)
                parsed = json.loads(formatted)
                _LOG_BUFFER.append(parsed)
                if len(_LOG_BUFFER) > _MAX_BUFFER_SIZE:
                    _LOG_BUFFER.pop(0)
        except Exception:
            self.handleError(record)


def get_recent_structured_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the most recent structured JSON logs collected in memory."""
    return list(_LOG_BUFFER[-limit:])


def clear_structured_logs() -> None:
    """Clears the in-memory structured log buffer."""
    _LOG_BUFFER.clear()


_IS_CONFIGURED = False


def setup_structured_logging(level: int = logging.INFO, project_id: Optional[str] = None) -> None:
    """Configures root application loggers to output structured JSON."""
    global _IS_CONFIGURED
    if _IS_CONFIGURED:
        return

    formatter = StructuredJsonFormatter(project_id=project_id)

    # Console / stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    # In-memory evaluation handler
    mem_handler = InMemoryLogHandler()
    mem_handler.setFormatter(formatter)
    mem_handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing default stream handlers to avoid double printing
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(mem_handler)

    _IS_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger configured for structured logging."""
    if not _IS_CONFIGURED:
        setup_structured_logging()
    return logging.getLogger(name)
