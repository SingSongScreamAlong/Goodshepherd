"""RSS and advisory ingestion service."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Sequence

import feedparser

from backend.utils.queue import (
    QueueConfig,
    create_redis_connection,
    enqueue_event,
    ensure_consumer_group,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@dataclass(slots=True)
class FeedConfig:
    """Configuration for a single RSS/Atom feed."""

    url: str
    category: str
    region: str | None = None
    enabled: bool = True


@dataclass
class IngestionSettings:
    """Runtime settings for the ingestion loop."""

    feeds: Sequence[FeedConfig]
    poll_interval: int = 300  # seconds
    queue: QueueConfig = field(default_factory=QueueConfig.from_env)

    @staticmethod
    def _default_feeds() -> list[FeedConfig]:
        return [
            FeedConfig(url="https://www.gdacs.org/rss.xml", category="disaster"),
            FeedConfig(url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom", category="earthquake"),
            FeedConfig(url="https://www.gov.uk/foreign-travel-advice.rss", category="advisory"),
        ]

    @classmethod
    def from_env(cls) -> "IngestionSettings":
        """Create settings from environment variables."""

        poll_interval = int(os.getenv("INGESTION_POLL_INTERVAL", "300"))
        raw_feeds = os.getenv("INGESTION_FEEDS")
        feeds: list[FeedConfig]

        if raw_feeds:
            try:
                parsed = json.loads(raw_feeds)
                feeds = []
                for item in parsed:
                    url = item.get("url")
                    if not url:
                        continue
                    feeds.append(
                        FeedConfig(
                            url=url,
                            category=item.get("category", "general"),
                            region=item.get("region"),
                            enabled=item.get("enabled", True),
                        )
                    )
            except json.JSONDecodeError:
                logger.warning("Failed to parse INGESTION_FEEDS JSON; using defaults")
                feeds = cls._default_feeds()
        else:
            feeds = cls._default_feeds()

        if not feeds:
            logger.warning("No feeds configured; ingestion will idle")

        return cls(feeds=feeds, poll_interval=poll_interval)


class IngestionService:
    """Service responsible for polling feeds and enqueueing new events."""

    def __init__(self, settings: IngestionSettings) -> None:
        self.settings = settings
        self._stop = asyncio.Event()
        self._redis = None

    async def start(self) -> None:
        """Start the ingestion loop and block until stopped."""

        logger.info("Starting ingestion service with %d feeds", len(self.settings.feeds))
        self._redis = await create_redis_connection(self.settings.queue)
        await ensure_consumer_group(self._redis, self.settings.queue.stream, self.settings.queue.consumer_group)

        try:
            while not self._stop.is_set():
                await self.poll_feeds()
                try:
                    await asyncio.wait_for(
                        self._stop.wait(),
                        timeout=self.settings.poll_interval,
                    )
                except asyncio.TimeoutError:
                    continue
        except Exception:  # pragma: no cover - surfaces in logs for manual review
            logger.exception("Ingestion loop crashed")
            raise

    async def stop(self) -> None:
        """Signal the ingestion loop to halt."""

        self._stop.set()
        if self._redis:
            await self._redis.close()

    async def poll_feeds(self) -> None:
        """Poll all configured feeds once."""

        assert self._redis is not None, "Redis connection must be established before polling"

        for feed in self.settings.feeds:
            if not feed.enabled:
                continue

            try:
                logger.debug("Fetching feed %s", feed.url)
                entries = await self.fetch_feed(feed)
                for entry in entries:
                    payload = self._build_event_payload(feed, entry)
                    await enqueue_event(self._redis, self.settings.queue.stream, payload)
            except Exception:  # pragma: no cover - surfaces in logs for manual review
                logger.exception("Failed to process feed %s", feed.url)

    async def fetch_feed(self, feed: FeedConfig) -> Iterable[dict[str, str]]:
        """Fetch and parse the remote feed using `feedparser`."""

        parsed = await asyncio.to_thread(feedparser.parse, feed.url)

        status = getattr(parsed, "status", 200)
        if status >= 400:
            raise RuntimeError(f"Feed {feed.url} responded with status {status}")

        if getattr(parsed, "bozo", False):  # malformed feed but still parsed
            logger.warning("Feed %s returned bozo=%s (%s)", feed.url, parsed.bozo, parsed.bozo_exception)

        items: list[dict[str, str]] = []
        for entry in parsed.entries:
            summary = entry.get("summary") or entry.get("description") or ""
            published = entry.get("published") or entry.get("updated") or ""

            items.append(
                {
                    "id": entry.get("id") or entry.get("guid") or entry.get("link") or "",
                    "title": entry.get("title", ""),
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "published": published,
                    "source": entry.get("source", {}).get("title", ""),
                }
            )

        return items

    def _build_event_payload(self, feed: FeedConfig, entry: dict[str, str]) -> dict[str, str]:
        """Normalize feed entry metadata into the canonical queue payload."""

        now = datetime.utcnow().isoformat()
        payload = {
            "source_url": feed.url,
            "category": feed.category,
            "region": feed.region or "global",
            "fetched_at": now,
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "link": entry.get("link", ""),
            "published_at": entry.get("published", now),
            "source_name": entry.get("source", ""),
            "source_entry_id": entry.get("id", ""),
        }
        return payload


async def run_default_service() -> None:  # pragma: no cover - helper for local testing
    settings = IngestionSettings.from_env()
    service = IngestionService(settings)
    await service.start()


if __name__ == "__main__":  # pragma: no cover
    try:
        asyncio.run(run_default_service())
    except KeyboardInterrupt:
        logger.info("Ingestion service interrupted by user")
