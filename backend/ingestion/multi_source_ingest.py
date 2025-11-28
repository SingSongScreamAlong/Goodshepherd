"""Multi-source ingestion service that aggregates from all data sources."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backend.utils.queue import (
    QueueConfig,
    create_redis_connection,
    enqueue_event,
    ensure_consumer_group,
)
from .sources.gdacs import GDACSSource, GDACSConfig
from .sources.reliefweb import ReliefWebSource, ReliefWebConfig
from .sources.who_outbreaks import WHOOutbreakSource, WHOConfig
from .sources.social_media import SocialMediaAggregator, TwitterConfig
from .sources.acled import ACLEDSource, ACLEDConfig

logger = logging.getLogger(__name__)


@dataclass
class MultiSourceConfig:
    """Configuration for multi-source ingestion."""

    # Poll intervals (seconds)
    gdacs_interval: int = 300  # 5 minutes
    reliefweb_interval: int = 900  # 15 minutes
    who_interval: int = 3600  # 1 hour
    social_interval: int = 600  # 10 minutes
    acled_interval: int = 3600  # 1 hour

    # Enable/disable sources
    gdacs_enabled: bool = True
    reliefweb_enabled: bool = True
    who_enabled: bool = True
    social_enabled: bool = True
    acled_enabled: bool = True

    # Queue config
    queue: QueueConfig = field(default_factory=QueueConfig.from_env)

    @classmethod
    def from_env(cls) -> "MultiSourceConfig":
        """Load configuration from environment."""
        return cls(
            gdacs_interval=int(os.getenv("GDACS_POLL_INTERVAL", "300")),
            reliefweb_interval=int(os.getenv("RELIEFWEB_POLL_INTERVAL", "900")),
            who_interval=int(os.getenv("WHO_POLL_INTERVAL", "3600")),
            social_interval=int(os.getenv("SOCIAL_POLL_INTERVAL", "600")),
            acled_interval=int(os.getenv("ACLED_POLL_INTERVAL", "3600")),
            gdacs_enabled=os.getenv("GDACS_ENABLED", "true").lower() == "true",
            reliefweb_enabled=os.getenv("RELIEFWEB_ENABLED", "true").lower() == "true",
            who_enabled=os.getenv("WHO_ENABLED", "true").lower() == "true",
            social_enabled=os.getenv("SOCIAL_ENABLED", "true").lower() == "true",
            acled_enabled=os.getenv("ACLED_ENABLED", "true").lower() == "true",
        )


@dataclass
class IngestionStats:
    """Statistics from ingestion run."""
    source: str
    events_fetched: int
    events_queued: int
    errors: int
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MultiSourceIngestionService:
    """
    Service that ingests events from multiple data sources.
    
    Sources:
    - GDACS: Global disaster alerts (earthquakes, floods, cyclones, etc.)
    - ReliefWeb: Humanitarian crisis reports
    - WHO: Disease outbreak news
    - Social Media: Twitter/Telegram crisis monitoring
    - ACLED: Armed conflict data
    """

    def __init__(self, config: Optional[MultiSourceConfig] = None):
        self.config = config or MultiSourceConfig.from_env()
        self._stop = asyncio.Event()
        self._redis = None
        
        # Initialize sources
        self._gdacs = GDACSSource() if self.config.gdacs_enabled else None
        self._reliefweb = ReliefWebSource() if self.config.reliefweb_enabled else None
        self._who = WHOOutbreakSource() if self.config.who_enabled else None
        self._social = SocialMediaAggregator() if self.config.social_enabled else None
        self._acled = None  # Requires API key
        
        if self.config.acled_enabled and os.getenv("ACLED_API_KEY"):
            self._acled = ACLEDSource()

        # Track last fetch times
        self._last_fetch = {
            "gdacs": datetime.min,
            "reliefweb": datetime.min,
            "who": datetime.min,
            "social": datetime.min,
            "acled": datetime.min,
        }

    async def start(self) -> None:
        """Start the multi-source ingestion service."""
        logger.info("Starting multi-source ingestion service")
        
        # Connect to Redis
        self._redis = await create_redis_connection(self.config.queue)
        await ensure_consumer_group(
            self._redis,
            self.config.queue.stream,
            self.config.queue.consumer_group,
        )

        # Log enabled sources
        sources = []
        if self._gdacs:
            sources.append("GDACS")
        if self._reliefweb:
            sources.append("ReliefWeb")
        if self._who:
            sources.append("WHO")
        if self._social:
            sources.append("Social Media")
        if self._acled:
            sources.append("ACLED")
        
        logger.info(f"Enabled sources: {', '.join(sources)}")

        try:
            while not self._stop.is_set():
                await self._poll_all_sources()
                
                # Wait for minimum interval or stop signal
                try:
                    await asyncio.wait_for(
                        self._stop.wait(),
                        timeout=60,  # Check every minute
                    )
                except asyncio.TimeoutError:
                    continue
        except Exception:
            logger.exception("Multi-source ingestion crashed")
            raise
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop the ingestion service."""
        self._stop.set()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._redis:
            await self._redis.close()
        if self._gdacs:
            await self._gdacs.close()
        if self._reliefweb:
            await self._reliefweb.close()
        if self._who:
            await self._who.close()
        if self._social:
            await self._social.close()

    async def _poll_all_sources(self) -> None:
        """Poll all sources that are due for refresh."""
        now = datetime.utcnow()
        tasks = []

        # Check each source
        if self._gdacs and self._should_poll("gdacs", self.config.gdacs_interval, now):
            tasks.append(self._poll_gdacs())

        if self._reliefweb and self._should_poll("reliefweb", self.config.reliefweb_interval, now):
            tasks.append(self._poll_reliefweb())

        if self._who and self._should_poll("who", self.config.who_interval, now):
            tasks.append(self._poll_who())

        if self._social and self._should_poll("social", self.config.social_interval, now):
            tasks.append(self._poll_social())

        if self._acled and self._should_poll("acled", self.config.acled_interval, now):
            tasks.append(self._poll_acled())

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Source polling failed: {result}")
                elif isinstance(result, IngestionStats):
                    logger.info(
                        f"[{result.source}] Fetched {result.events_fetched} events, "
                        f"queued {result.events_queued} in {result.duration_ms:.0f}ms"
                    )

    def _should_poll(self, source: str, interval: int, now: datetime) -> bool:
        """Check if a source should be polled."""
        last = self._last_fetch.get(source, datetime.min)
        elapsed = (now - last).total_seconds()
        return elapsed >= interval

    async def _poll_gdacs(self) -> IngestionStats:
        """Poll GDACS for disaster alerts."""
        start = datetime.utcnow()
        stats = IngestionStats(source="GDACS", events_fetched=0, events_queued=0, errors=0, duration_ms=0)

        try:
            events = await self._gdacs.get_events_as_dicts()
            stats.events_fetched = len(events)

            for event in events:
                try:
                    await self._enqueue_event(event, "gdacs")
                    stats.events_queued += 1
                except Exception as e:
                    logger.warning(f"Failed to queue GDACS event: {e}")
                    stats.errors += 1

            self._last_fetch["gdacs"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"GDACS polling failed: {e}")
            stats.errors += 1

        stats.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        return stats

    async def _poll_reliefweb(self) -> IngestionStats:
        """Poll ReliefWeb for humanitarian reports."""
        start = datetime.utcnow()
        stats = IngestionStats(source="ReliefWeb", events_fetched=0, events_queued=0, errors=0, duration_ms=0)

        try:
            events = await self._reliefweb.get_reports_as_dicts()
            stats.events_fetched = len(events)

            for event in events:
                try:
                    await self._enqueue_event(event, "reliefweb")
                    stats.events_queued += 1
                except Exception as e:
                    logger.warning(f"Failed to queue ReliefWeb event: {e}")
                    stats.errors += 1

            self._last_fetch["reliefweb"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"ReliefWeb polling failed: {e}")
            stats.errors += 1

        stats.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        return stats

    async def _poll_who(self) -> IngestionStats:
        """Poll WHO for disease outbreak news."""
        start = datetime.utcnow()
        stats = IngestionStats(source="WHO", events_fetched=0, events_queued=0, errors=0, duration_ms=0)

        try:
            events = await self._who.get_outbreaks_as_dicts()
            stats.events_fetched = len(events)

            for event in events:
                try:
                    await self._enqueue_event(event, "who")
                    stats.events_queued += 1
                except Exception as e:
                    logger.warning(f"Failed to queue WHO event: {e}")
                    stats.errors += 1

            self._last_fetch["who"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"WHO polling failed: {e}")
            stats.errors += 1

        stats.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        return stats

    async def _poll_social(self) -> IngestionStats:
        """Poll social media for crisis-related posts."""
        start = datetime.utcnow()
        stats = IngestionStats(source="Social", events_fetched=0, events_queued=0, errors=0, duration_ms=0)

        try:
            events = await self._social.fetch_all_posts()
            stats.events_fetched = len(events)

            for event in events:
                try:
                    await self._enqueue_event(event, "social")
                    stats.events_queued += 1
                except Exception as e:
                    logger.warning(f"Failed to queue social event: {e}")
                    stats.errors += 1

            self._last_fetch["social"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Social media polling failed: {e}")
            stats.errors += 1

        stats.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        return stats

    async def _poll_acled(self) -> IngestionStats:
        """Poll ACLED for conflict data."""
        start = datetime.utcnow()
        stats = IngestionStats(source="ACLED", events_fetched=0, events_queued=0, errors=0, duration_ms=0)

        try:
            events = await self._acled.get_events_as_dicts()
            stats.events_fetched = len(events)

            for event in events:
                try:
                    await self._enqueue_event(event, "acled")
                    stats.events_queued += 1
                except Exception as e:
                    logger.warning(f"Failed to queue ACLED event: {e}")
                    stats.errors += 1

            self._last_fetch["acled"] = datetime.utcnow()

        except Exception as e:
            logger.error(f"ACLED polling failed: {e}")
            stats.errors += 1

        stats.duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        return stats

    async def _enqueue_event(self, event: dict, source: str) -> None:
        """Enqueue an event to Redis."""
        # Add metadata
        event["source_type"] = source
        event["fetched_at"] = datetime.utcnow().isoformat()
        
        await enqueue_event(self._redis, self.config.queue.stream, event)


async def run_multi_source_service() -> None:
    """Run the multi-source ingestion service."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    
    config = MultiSourceConfig.from_env()
    service = MultiSourceIngestionService(config)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(run_multi_source_service())
