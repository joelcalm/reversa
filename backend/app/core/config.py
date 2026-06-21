"""Central configuration and filesystem paths.

All tunables live here so ingestion, the API and tests share one source of truth.
No secrets are required: the BOE open-data API needs no API key.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repository layout: this file is backend/app/core/config.py
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

DATA_DIR = REPO_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache" / "boe"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"
FIXTURES_DIR = BACKEND_DIR / "tests" / "fixtures"

# SQLite database location (override with BOE_DB_PATH, e.g. for tests).
DEFAULT_DB_PATH = PROCESSED_DIR / "boe_graph.db"


def get_db_path() -> Path:
    env = os.environ.get("BOE_DB_PATH")
    return Path(env) if env else DEFAULT_DB_PATH


def get_database_url() -> str:
    return f"sqlite:///{get_db_path()}"


# BOE open-data API
BOE_API_BASE = os.environ.get(
    "BOE_API_BASE", "https://boe.es/datosabiertos/api/legislacion-consolidada"
)
BOE_HTML_BASE = "https://www.boe.es/buscar/act.php?id="

# Client politeness / robustness
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("BOE_TIMEOUT", "30"))
REQUEST_DELAY_SECONDS = float(os.environ.get("BOE_DELAY", "0.4"))
MAX_RETRIES = int(os.environ.get("BOE_MAX_RETRIES", "4"))

# Scope handling
DEFAULT_SCOPE = "state"  # maps to ambito "Estatal"
STATE_SCOPE_LABEL = "Estatal"

# Key norm for briefing 4
LEY_30_1992_ID = "BOE-A-1992-26318"

# Sample ingestion: norms always attempted plus N recent from the list endpoint.
SAMPLE_SEED_IDS = [
    LEY_30_1992_ID,
    "BOE-A-2015-10565",  # Ley 39/2015
    "BOE-A-2015-10566",  # Ley 40/2015
]
SAMPLE_RECENT_COUNT = int(os.environ.get("BOE_SAMPLE_RECENT", "40"))


def ensure_directories() -> None:
    for d in (CACHE_DIR, PROCESSED_DIR, SAMPLES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def boe_html_url(norm_id: str) -> str:
    return f"{BOE_HTML_BASE}{norm_id}"
