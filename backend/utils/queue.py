"""Redis stream helpers for Good Shepherd services."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping

try:
    from redis.asyncio import Redis  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback typing when redis not installed yet
    Redis = Any  # type: ignore


DEFAULT_STREAM = "events.raw"
DEFAULT_CONSUMER_GROUP = "event_processor"
DEFAULT_CONSUMER_NAME = "processor-1"


@dataclass
class QueueConfig:
    """Runtime settings for Redis connectivity."""

    url: str
    stream: str = DEFAULT_STREAM
    consumer_group: str = DEFAULT_CONSUMER_GROUP
    consumer_name: str = DEFAULT_CONSUMER_NAME

    @classmethod
    def from_env(cls) -> "QueueConfig":
        """Load configuration from environment variables."""

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        stream = os.getenv("REDIS_STREAM", DEFAULT_STREAM)
        consumer_group = os.getenv("REDIS_CONSUMER_GROUP", DEFAULT_CONSUMER_GROUP)
        consumer_name = os.getenv("REDIS_CONSUMER_NAME", DEFAULT_CONSUMER_NAME)
        return cls(url=url, stream=stream, consumer_group=consumer_group, consumer_name=consumer_name)


async def create_redis_connection(config: QueueConfig) -> Redis:
    """Create an asynchronous Redis client bound to the configured URL."""

    redis: Redis = Redis.from_url(config.url, decode_responses=True)
    return redis


async def ensure_consumer_group(redis: Redis, stream: str, group: str) -> None:
    """Create the consumer group on the stream if it does not already exist."""

    try:
        await redis.xgroup_create(stream, group, id="0-0", mkstream=True)  # type: ignore[call-arg]
    except Exception as exc:  # pragma: no cover - redis raises generic errors
        # Group already exists. Swallow the error and continue.
        if "BUSYGROUP" not in str(exc):
            raise


async def enqueue_event(redis: Redis, stream: str, payload: Mapping[str, Any]) -> str:
    """Push an event payload to the configured Redis stream."""

    serialized: Dict[str, str] = {key: str(value) for key, value in payload.items()}
    message_id = await redis.xadd(stream, serialized)
    return message_id


async def read_events(
    redis: Redis,
    stream: str,
    group: str,
    consumer: str,
    count: int = 10,
    block_ms: int = 1000,
) -> Iterable[tuple[str, Dict[str, str]]]:
    """Read a batch of events from the Redis stream for the consumer group."""

    response = await redis.xreadgroup(group, consumer, {stream: ">"}, count=count, block=block_ms)
    if not response:
        return []

    # redis returns [(stream, [(id, data), ...])]
    _, entries = response[0]
    return entries


async def acknowledge(redis: Redis, stream: str, group: str, message_ids: Iterable[str]) -> None:
    """Acknowledge processed messages so they are not re-delivered."""

    message_ids = list(message_ids)
    if not message_ids:
        return
    await redis.xack(stream, group, *message_ids)


async def main_example() -> None:  # pragma: no cover - illustrative usage
    """Example event loop for local testing."""

    config = QueueConfig.from_env()
    redis = await create_redis_connection(config)
    await ensure_consumer_group(redis, config.stream, config.consumer_group)
    await enqueue_event(redis, config.stream, {"example": "event"})
    entries = await read_events(redis, config.stream, config.consumer_group, config.consumer_name)
    print(entries)
    await acknowledge(redis, config.stream, config.consumer_group, (entry_id for entry_id, _ in entries))


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main_example())
