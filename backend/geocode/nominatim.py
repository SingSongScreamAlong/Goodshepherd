"""Async Nominatim geocoding client."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeocodeSettings:
    """Configuration for the geocode client."""

    base_url: str
    user_agent: str
    timeout: float
    enabled: bool
    rate_limit_seconds: float

    @classmethod
    def from_env(cls) -> "GeocodeSettings":
        base_url = os.getenv("GEOCODE_BASE_URL", "https://nominatim.openstreetmap.org").rstrip("/")
        user_agent = os.getenv("GEOCODE_USER_AGENT", "GoodShepherd/0.1 (+https://example.org)")
        timeout = float(os.getenv("GEOCODE_TIMEOUT", "10"))
        enabled = os.getenv("GEOCODE_DISABLED", "false").lower() not in {"1", "true", "yes"}
        rate_limit_seconds = float(os.getenv("GEOCODE_RATE_LIMIT_SECONDS", "1.0"))
        return cls(
            base_url=base_url,
            user_agent=user_agent,
            timeout=timeout,
            enabled=enabled,
            rate_limit_seconds=rate_limit_seconds,
        )


class GeocodeError(RuntimeError):
    """Raised when the geocode service is unavailable or returns errors."""


class NominatimClient:
    """Minimal async client for the Nominatim API."""

    def __init__(self, settings: GeocodeSettings | None = None) -> None:
        self.settings = settings or GeocodeSettings.from_env()
        if not self.settings.enabled:
            self._client: httpx.AsyncClient | None = None
        else:
            self._client = httpx.AsyncClient(
                base_url=self.settings.base_url,
                headers={
                    "User-Agent": self.settings.user_agent,
                    "Accept": "application/json",
                },
                timeout=self.settings.timeout,
            )
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def forward_geocode(self, query: str) -> dict[str, Any] | None:
        """Perform forward geocoding for the supplied query."""

        if not query:
            return None

        if not self.settings.enabled or self._client is None:
            logger.debug("Geocoding disabled; skipping query %s", query)
            return None

        async with self._lock:
            await asyncio.sleep(self.settings.rate_limit_seconds)
            try:
                response = await self._client.get(
                    "/search",
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "limit": 1,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover - external dependency
                raise GeocodeError(f"Failed to geocode '{query}': {exc}") from exc

        payload: list[dict[str, Any]] = response.json()
        if not payload:
            return None
        return payload[0]


_geocode_client: NominatimClient | None = None


async def get_geocode_client() -> NominatimClient:
    """Return a singleton geocode client."""

    global _geocode_client
    if _geocode_client is None:
        _geocode_client = NominatimClient()
    return _geocode_client
