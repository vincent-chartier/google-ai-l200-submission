"""Configuration for Cinema Outing Agent backend."""

import os
from pathlib import Path

# Load Gemini API Key from environment or home key file
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    home_key_path = Path.home() / "gemini_key.txt"
    if home_key_path.exists():
        GEMINI_API_KEY = home_key_path.read_text().strip()
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

PROJECT_ID = os.environ.get("PROJECT_ID", "vchartier-project")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gemini-2.5-flash")

# Tiered model routing configuration based on reasoning complexity and cost
MODEL_ROUTING_CONFIG = {
    "coordinator": os.environ.get("MODEL_COORDINATOR", "gemini-2.5-flash"),
    "search_reco_deep": os.environ.get("MODEL_SEARCH_RECO_DEEP", "gemini-2.5-pro"),
    "search_reco_fast": os.environ.get("MODEL_SEARCH_RECO_FAST", "gemini-2.5-flash"),
    "booking": os.environ.get("MODEL_BOOKING", "gemini-2.5-flash"),
    "housekeeping": os.environ.get("MODEL_HOUSEKEEPING", "gemini-2.0-flash-lite"),
}

APP_PORT = int(os.environ.get("PORT", "8080"))
APP_HOST = os.environ.get("HOST", "0.0.0.0")
