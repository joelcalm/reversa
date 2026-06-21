"""HTTP client for the BOE consolidated-legislation open-data API.

Features:
- httpx-based, JSON by default (the API also serves XML; we request JSON).
- tenacity retry/backoff on transient failures (timeouts, 5xx).
- polite delay between live requests.
- disk cache keyed by endpoint -> enables resume and avoids hammering the API.
- no API key required.

The BOE API wraps payloads as {"status": {...}, "data": ...}; we return the inner
`data` when present, otherwise the raw object.
"""
from __future__ import annotations

import time
from typing import Any, Iterator, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import (
    BOE_API_BASE,
    LIST_PAGE_SIZE,
    MAX_RETRIES,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
)
from app.utils.cache import read_cache, write_cache

_TRANSIENT = (httpx.TimeoutException, httpx.TransportError)


class BoeApiError(RuntimeError):
    """Raised when the BOE API returns a non-recoverable error."""


def _unwrap(payload: Any) -> Any:
    """Return the inner `data` field if the API wrapped the response."""
    if isinstance(payload, dict) and "data" in payload and "status" in payload:
        return payload["data"]
    return payload


def list_items(payload: Any) -> List[dict]:
    """Normalize a list-endpoint payload to a list of norm dicts."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "results"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        return [payload]
    return []


class BoeClient:
    def __init__(
        self,
        base_url: str = BOE_API_BASE,
        delay: float = REQUEST_DELAY_SECONDS,
        use_cache: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.use_cache = use_cache
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={
                "Accept": "application/json",
                "User-Agent": "boe-knowledge-graph/0.1 (technical-challenge)",
            },
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BoeClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type(_TRANSIENT),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(MAX_RETRIES),
        reraise=True,
    )
    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = self._client.get(url, params=params)
        if resp.status_code >= 500:
            raise httpx.TransportError(f"server error {resp.status_code} for {url}")
        if resp.status_code >= 400:
            raise BoeApiError(f"HTTP {resp.status_code} for {url}")
        time.sleep(self.delay)
        try:
            return resp.json()
        except ValueError as exc:  # not JSON
            raise BoeApiError(f"non-JSON response for {url}: {exc}") from exc

    def _cached_get(self, cache_key: str, path: str, params: Optional[dict] = None) -> Any:
        if self.use_cache:
            cached = read_cache(cache_key)
            if cached is not None:
                return _unwrap(cached)
        payload = self._get(path, params=params)
        if self.use_cache:
            write_cache(cache_key, payload)
        return _unwrap(payload)

    # --- Public endpoints -------------------------------------------------

    def list_norms(
        self,
        offset: int = 0,
        limit: int = 50,
        query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Any:
        """List one page of consolidated norms.

        Note: ``limit=-1`` is capped at 10_000 by the BOE API. Use ``iter_all_list_items()``
        to retrieve the full corpus (~12k+ norms).
        """
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if query:
            params["query"] = query
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to
        cache_key = f"list_off{offset}_lim{limit}_{query or ''}_{date_from or ''}_{date_to or ''}"
        return self._cached_get(cache_key, "", params=params)

    def iter_list_pages(
        self,
        page_size: int = LIST_PAGE_SIZE,
        query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Iterator[List[dict]]:
        """Yield successive pages until the API returns an empty or partial page."""
        offset = 0
        while True:
            batch = list_items(
                self.list_norms(
                    offset=offset,
                    limit=page_size,
                    query=query,
                    date_from=date_from,
                    date_to=date_to,
                )
            )
            if not batch:
                break
            yield batch
            if len(batch) < page_size:
                break
            offset += len(batch)

    def fetch_all_list_items(
        self,
        page_size: int = LIST_PAGE_SIZE,
        query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[dict]:
        """Fetch every norm from the list endpoint via pagination."""
        items: List[dict] = []
        for page in self.iter_list_pages(page_size, query, date_from, date_to):
            items.extend(page)
        return items

    def get_metadata(self, norm_id: str) -> Any:
        return self._cached_get(f"{norm_id}/metadatos", f"/id/{norm_id}/metadatos")

    def get_analysis(self, norm_id: str) -> Any:
        return self._cached_get(f"{norm_id}/analisis", f"/id/{norm_id}/analisis")

    def get_norm(self, norm_id: str) -> Any:
        return self._cached_get(f"{norm_id}/full", f"/id/{norm_id}")
