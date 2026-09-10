"""Tests for MCP Movie Search server tools."""

import json
import pytest
from backend.mcp_servers.movie_search_server import (
    search_internet_movies,
    get_movie_details,
    get_theater_showtimes
)

def test_mcp_search_by_query():
    raw = search_internet_movies(query="Dune")
    results = json.loads(raw)
    assert len(results) >= 1
    assert "Dune" in results[0]["title"]


def test_mcp_search_by_genre():
    raw = search_internet_movies(genre="Sci-Fi")
    results = json.loads(raw)
    assert len(results) >= 1
    for r in results:
        assert any("Sci-Fi" in g for g in r["genres"])


def test_mcp_get_movie_details():
    raw = get_movie_details(title="Interstellar")
    details = json.loads(raw)
    assert details["title"] == "Interstellar"
    assert "director" in details
    assert details["director"] == "Christopher Nolan"


def test_mcp_get_showtimes():
    raw = get_theater_showtimes(movie_title="Dune: Part Two")
    data = json.loads(raw)
    assert "showtimes" in data
    assert len(data["showtimes"]) >= 1
    assert data["theater"] == "Metropolis Cinema IMAX"
