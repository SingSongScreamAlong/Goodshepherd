"""Meilisearch client wrapper with graceful fallbacks."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from backend.database.models import EventRecord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchSettings:
    """Configuration for connecting to Meilisearch."""

    url: str
    index_uid: str
    api_key: str | None
    timeout: float
    enabled: bool

    @classmethod
    def from_env(cls) -> "SearchSettings":
        url = os.getenv("MEILI_HTTP_ADDR", "http://localhost:7700").rstrip("/")
        index_uid = os.getenv("MEILI_INDEX", "events")
        api_key = os.getenv("MEILI_API_KEY") or os.getenv("MEILI_MASTER_KEY")
        timeout = float(os.getenv("MEILI_TIMEOUT", "10"))
        enabled = os.getenv("MEILI_INDEXING_DISABLED", "false").lower() not in {"1", "true", "yes"}
        return cls(url=url, index_uid=index_uid, api_key=api_key, timeout=timeout, enabled=enabled)


class SearchClientError(RuntimeError):
    """Raised when search indexing fails."""


class SearchClient:
    """Thin async wrapper over the Meilisearch HTTP API."""

    def __init__(self, settings: SearchSettings) -> None:
        self.settings = settings
        if not settings.enabled:
            self._client: httpx.AsyncClient | None = None
        else:
            headers = {"Content-Type": "application/json"}
            if settings.api_key:
                headers["X-Meili-API-Key"] = settings.api_key

            self._client = httpx.AsyncClient(
                base_url=settings.url,
                headers=headers,
                timeout=settings.timeout,
            )
        self._index_checked = False
        self._index_lock = asyncio.Lock()

    async def ensure_index(self) -> None:
        """Ensure the target index exists before indexing documents."""

        if not self.settings.enabled or self._client is None or self._index_checked:
            return

        async with self._index_lock:
            if self._index_checked:
                return

            try:
                response = await self._client.get(f"/indexes/{self.settings.index_uid}")
                if response.status_code == httpx.codes.NOT_FOUND:
                    create_resp = await self._client.post(
                        "/indexes",
                        json={"uid": self.settings.index_uid, "primaryKey": "id"},
                    )
                    create_resp.raise_for_status()
                else:
                    response.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover - network dependent
                raise SearchClientError(f"Failed to ensure Meilisearch index: {exc}") from exc

            self._index_checked = True

    async def index_event(self, record: EventRecord) -> None:
        """Index an event document in Meilisearch."""

        if not self.settings.enabled or self._client is None:
            logger.debug("Search indexing disabled; skipping event %s", record.id)
            return

        await self.ensure_index()

        document = self._serialize_record(record)
        try:
            response = await self._client.post(
                f"/indexes/{self.settings.index_uid}/documents",
                json=[document],
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - external dependency
            raise SearchClientError(f"Failed to index event {record.id}: {exc}") from exc

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        if self._client is not None:
            await self._client.aclose()

    @staticmethod
    def _serialize_record(record: EventRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "title": record.title,
            "summary": record.summary,
            "category": record.category,
            "region": record.region,
            "link": record.link,
            "source_url": record.source_url,
            "confidence": record.confidence,
            "geocode": record.geocode,
            "published_at": record.published_at.isoformat() if record.published_at else None,
            "fetched_at": record.fetched_at.isoformat() if record.fetched_at else None,
        }


_search_client: SearchClient | None = None


async def get_search_client() -> SearchClient:
    """Return a singleton search client instance."""

    global _search_client
    if _search_client is None:
        settings = SearchSettings.from_env()
        _search_client = SearchClient(settings)
        await _search_client.ensure_index()
    return _search_client
