"""Unit tests for Evaluation Plugins and Telemetry."""

import pytest
from backend.plugins.evaluation_plugins import (
    RecommendationEvaluationPlugin,
    ToolSequenceEvaluationPlugin,
    LatencyAndCostTelemetryPlugin
)


def test_recommendation_eval_zero_duplicates():
    evaluator = RecommendationEvaluationPlugin()
    recommended = ["Dune: Part Two", "Interstellar"]
    seen = [{"title": "Blade Runner 2049"}, {"title": "Arrival"}]

    result = evaluator.evaluate_negative_constraints(recommended, seen)
    assert result["passed"] is True
    assert result["duplicate_count"] == 0
    assert result["clean_recommendation_rate"] == 1.0


def test_recommendation_eval_detects_duplicate():
    evaluator = RecommendationEvaluationPlugin()
    recommended = ["Dune: Part Two", "Arrival"]
    seen = [{"title": "Arrival"}]

    result = evaluator.evaluate_negative_constraints(recommended, seen)
    assert result["passed"] is False
    assert result["duplicate_count"] == 1
    assert "Arrival" in result["duplicates"]
    assert result["clean_recommendation_rate"] == 0.5


def test_recommendation_eval_taste_grounding():
    evaluator = RecommendationEvaluationPlugin()
    favorites = [{"title": "Interstellar", "genre": "Sci-Fi"}]

    grounded_result = evaluator.evaluate_taste_grounding(
        taste_match_reason="Matches your love for Interstellar and Christopher Nolan",
        favorite_movies=favorites
    )
    assert grounded_result["is_grounded"] is True
    assert "Interstellar" in grounded_result["matched_favorites"]


def test_tool_sequence_evaluator_valid_workflow():
    evaluator = ToolSequenceEvaluationPlugin()
    actions = ["check_availability", "hold_seats", "process_payment", "calendar_invite"]
    result = evaluator.evaluate_sequence(actions)
    assert result["is_valid_sequence"] is True
    assert len(result["violations"]) == 0


def test_tool_sequence_evaluator_detects_payment_without_hold():
    evaluator = ToolSequenceEvaluationPlugin()
    actions = ["check_availability", "process_payment"]
    result = evaluator.evaluate_sequence(actions)
    assert result["is_valid_sequence"] is False
    assert any("hold" in v.lower() for v in result["violations"])


def test_latency_and_cost_telemetry():
    telemetry = LatencyAndCostTelemetryPlugin()

    telemetry.record_call(
        agent_name="SearchRecoAgent",
        model_name="gemini-2.5-pro",
        duration_ms=450.0,
        prompt_tokens=1000,
        completion_tokens=500
    )
    telemetry.record_call(
        agent_name="BookingAgent",
        model_name="gemini-2.5-flash",
        duration_ms=120.0,
        prompt_tokens=400,
        completion_tokens=200
    )

    summary = telemetry.get_summary()
    assert summary["total_calls"] == 2
    assert summary["avg_duration_ms"] > 0
    assert summary["total_estimated_cost_usd"] > 0
    assert "gemini-2.5-pro" in summary["calls_per_model"]
    assert "gemini-2.5-flash" in summary["calls_per_model"]
