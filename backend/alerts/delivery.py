"""Alert delivery sinks (Matrix, SMTP, logging placeholders)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .rules import AlertCandidate, AlertSink

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LoggingSink(AlertSink):
    """Simple sink that logs alerts for debugging environments."""

    channel: str = "alerts"

    async def send(self, candidate: AlertCandidate) -> None:
        logger.warning(
            "[ALERT][%s] %s :: %s",
            self.channel,
            candidate.rule.name,
            candidate.event.title,
        )


@dataclass(slots=True)
class MatrixSink(AlertSink):  # pragma: no cover - external dependency placeholder
    """Placeholder Matrix sink; implement client wiring in Phase 2."""

    homeserver: str
    room_id: str
    access_token: str

    async def send(self, candidate: AlertCandidate) -> None:
        logger.info(
            "Matrix alert (%s) to %s: %s", candidate.rule.name, self.room_id, candidate.event.title
        )


@dataclass(slots=True)
class SmtpSink(AlertSink):  # pragma: no cover - external dependency placeholder
    """Placeholder SMTP sink; implement actual email delivery in Phase 2."""

    smtp_host: str
    from_address: str
    to_addresses: tuple[str, ...]

    async def send(self, candidate: AlertCandidate) -> None:
        logger.info(
            "SMTP alert (%s) to %s: %s",
            candidate.rule.name,
            ", ".join(self.to_addresses),
            candidate.event.title,
        )
