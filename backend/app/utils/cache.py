"""Tiny on-disk JSON cache for raw BOE API responses.

The cache key is derived from the endpoint path so ingestion can be stopped and
resumed without re-hitting the API. Files live under data/cache/boe/.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from app.core.config import CACHE_DIR

_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _key_to_filename(key: str) -> str:
    safe = _SAFE.sub("_", key.strip("/"))
    return f"{safe}.json"


def cache_path(key: str) -> Path:
    return CACHE_DIR / _key_to_filename(key)


def read_cache(key: str) -> Optional[Any]:
    path = cache_path(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(key: str, value: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = cache_path(key)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def has_cache(key: str) -> bool:
    return cache_path(key).exists()
