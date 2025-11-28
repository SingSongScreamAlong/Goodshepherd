"""Event processing pipeline for Good Shepherd."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
import json
from datetime import datetime
from typing import Mapping

from backend.database.repository import (
    EventCreate,
    VerificationUpdate,
    create_event,
    find_duplicate_candidate,
    update_event_verification,
)
from backend.database.session import init_database, session_scope
from backend.database.models import EventRecord
from backend.geocode.nominatim import GeocodeError, get_geocode_client
from backend.search.client import SearchClientError, get_search_client
from backend.processing.verification import evaluate_event
from backend.ml.model_service import ModelService, get_model_service

from backend.utils.queue import (
    QueueConfig,
    acknowledge,
    create_redis_connection,
    ensure_consumer_group,
    read_events,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessorSettings:
    """Runtime configuration for the event processor."""

    queue: QueueConfig = field(default_factory=QueueConfig.from_env)
    batch_size: int = 20
    block_ms: int = 1_000


class EventProcessor:
    """Consumes queued events, enriches them, and stores results."""

    def __init__(self, settings: ProcessorSettings) -> None:
        self.settings = settings
        self._stop = asyncio.Event()
        self._redis = None
        self._search_client = None
        self._geocode_client = None
        self._ml_service: ModelService | None = None

    async def start(self) -> None:
        """Start consuming events until stopped."""

        logger.info("Starting event processor")
        await init_database()
        self._redis = await create_redis_connection(self.settings.queue)
        self._search_client = await get_search_client()
        self._geocode_client = await get_geocode_client()
        self._ml_service = get_model_service()
        await self._ml_service.initialize()
        await ensure_consumer_group(
            self._redis,
            self.settings.queue.stream,
            self.settings.queue.consumer_group,
        )

        try:
            while not self._stop.is_set():
                entries = await read_events(
                    self._redis,
                    self.settings.queue.stream,
                    self.settings.queue.consumer_group,
                    self.settings.queue.consumer_name,
                    count=self.settings.batch_size,
                    block_ms=self.settings.block_ms,
                )

                if not entries:
                    continue

                message_ids = []
                for message_id, payload in entries:
                    try:
                        event = await self._enrich_event(payload)
                        await self._persist_event(message_id, event, payload)
                        message_ids.append(message_id)
                    except Exception:  # pragma: no cover - logged for manual investigation
                        logger.exception("Failed to process message %s", message_id)

                await acknowledge(
                    self._redis,
                    self.settings.queue.stream,
                    self.settings.queue.consumer_group,
                    message_ids,
                )
        except Exception:  # pragma: no cover - fatal error bubble up
            logger.exception("Event processor halted unexpectedly")
            raise
        finally:
            if self._redis:
                await self._redis.close()
            if self._search_client:
                await self._search_client.close()
            if self._geocode_client:
                await self._geocode_client.close()
            if self._ml_service:
                await self._ml_service.close()

    async def stop(self) -> None:
        """Signal the processor to shut down."""

        self._stop.set()

    async def _enrich_event(self, payload: Mapping[str, str]) -> EventCreate:
        """Apply geoparsing, scoring, and normalization."""

        def parse_datetime(value: str | None) -> datetime | None:
            if not value:
                return None
            cleaned = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(cleaned)
            except ValueError:
                logger.debug("Unable to parse datetime value: %s", value)
                return None

        confidence_raw = payload.get("confidence")
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else 0.5
        except ValueError:
            confidence = 0.5

        verification = evaluate_event(payload)

        # ML-based analysis (translation, threat classification, disinfo detection)
        ml_analysis = None
        if self._ml_service:
            try:
                text = payload.get("summary") or payload.get("title") or ""
                ml_analysis = await self._ml_service.analyze_event(
                    text=text,
                    title=payload.get("title"),
                    source_url=payload.get("source_url"),
                    source_name=payload.get("source"),
                    source_credibility=verification.credibility_score or 0.7,
                    translate=True,
                )
                logger.debug(
                    "ML analysis: threat=%s, disinfo=%s, lang=%s",
                    ml_analysis.threat.threat_level.value,
                    ml_analysis.disinfo.risk_level.value,
                    ml_analysis.source_language,
                )
            except Exception:
                logger.exception("ML analysis failed for event")

        geocode_data = None
        if self._geocode_client:
            query = ", ".join(
                part
                for part in [payload.get("region"), payload.get("title"), payload.get("summary")]
                if part
            )
            if query:
                try:
                    geocode_data = await self._geocode_client.forward_geocode(query)
                except GeocodeError:
                    logger.exception("Failed to geocode payload %s", payload)

        # Determine threat level from ML or verification
        threat_level = verification.threat_level
        if ml_analysis and ml_analysis.threat.threat_score > 0.3:
            threat_level = ml_analysis.threat.threat_level.value

        # Adjust credibility based on disinfo detection
        credibility = verification.credibility_score or confidence
        if ml_analysis and ml_analysis.disinfo.risk_score > 0.5:
            credibility = max(0.1, credibility - 0.2)  # Reduce credibility for potential disinfo

        # Build ML metadata
        ml_metadata = None
        if ml_analysis:
            ml_metadata = {
                "source_language": ml_analysis.source_language,
                "translated": ml_analysis.source_language != "en",
                "threat": ml_analysis.threat.to_dict(),
                "disinfo": ml_analysis.disinfo.to_dict(),
            }

        enriched = EventCreate(
            source_url=payload.get("source_url"),
            category=ml_analysis.threat.category.value if ml_analysis else payload.get("category"),
            region=payload.get("region"),
            title=payload.get("title"),
            summary=ml_analysis.translated_text if ml_analysis and ml_analysis.source_language != "en" else payload.get("summary"),
            link=payload.get("link"),
            published_at=parse_datetime(payload.get("published_at")),
            fetched_at=parse_datetime(payload.get("fetched_at")) or datetime.utcnow(),
            geocode=geocode_data,
            confidence=credibility,
            verification_status=verification.verification_status,
            credibility_score=credibility,
            threat_level=threat_level,
            raw=json.dumps({**payload, "ml_analysis": ml_metadata}),
        )
        return enriched

    async def _persist_event(
        self,
        message_id: str,
        event: EventCreate,
        payload: Mapping[str, str],
    ) -> None:
        """Persist the enriched event and dispatch to search index."""

        logger.debug("Persisting event %s -> %s", message_id, event.title)
        async with session_scope() as session:
            duplicate = await find_duplicate_candidate(
                session,
                link=payload.get("link"),
                title=payload.get("title"),
            )

            event_payload = event
            if duplicate:
                event_payload = event.model_copy(
                    update={"duplicate_of": duplicate.id, "verification_status": "duplicate"}
                )

            record = await create_event(session, event_payload)

            if duplicate:
                await update_event_verification(
                    session,
                    duplicate.id,
                    VerificationUpdate(
                        verification_status="primary",
                        credibility_score=max(duplicate.credibility_score, event_payload.credibility_score),
                        threat_level=duplicate.threat_level or event_payload.threat_level,
                        duplicate_of=None,
                    ),
                )
        await self._index_event(record)

    async def _index_event(self, record: EventRecord) -> None:
        """Index the record in the search engine if enabled."""

        if not self._search_client:
            logger.debug("Search client unavailable; skipping event %s", record.id)
            return

        try:
            await self._search_client.index_event(record)
        except SearchClientError:
            logger.exception("Failed to index event %s", record.id)


async def run_default_processor() -> None:  # pragma: no cover - helper for manual testing
    processor = EventProcessor(ProcessorSettings())
    await processor.start()


if __name__ == "__main__":  # pragma: no cover
    try:
        asyncio.run(run_default_processor())
    except KeyboardInterrupt:
        logger.info("Event processor interrupted by user")
