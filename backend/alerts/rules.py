"""Alert rules, evaluation logic, and data structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Protocol

from backend.database.models import EventRecord


class AlertPriority(str, Enum):
    """Notification priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(slots=True)
class AlertRule:
    """Configuration describing when to trigger an alert."""

    name: str
    description: str
    regions: set[str] | None = None
    categories: set[str] | None = None
    minimum_threat: str = "medium"
    minimum_credibility: float = 0.6
    lookback_minutes: int = 60
    priority: AlertPriority = AlertPriority.HIGH
    auto_ack: bool = False


@dataclass(slots=True)
class AlertCandidate:
    """Event selected by the rules engine for alerting."""

    event: EventRecord
    rule: AlertRule


class AlertSink(Protocol):
    """Protocol for alert delivery targets (Matrix/SMTP/etc.)."""

    async def send(self, candidate: AlertCandidate) -> None:  # pragma: no cover - template only
        ...


class RuleEvaluator:
    """Evaluate events against configured alert rules."""

    def __init__(self, rules: Iterable[AlertRule]) -> None:
        self.rules = list(rules)

    def evaluate(self, events: Iterable[EventRecord], now: datetime | None = None) -> list[AlertCandidate]:
        """Return alert candidates for the provided events."""

        now = now or datetime.utcnow()
        candidates: list[AlertCandidate] = []
        for event in events:
            for rule in self.rules:
                if self._matches(event, rule, now):
                    candidates.append(AlertCandidate(event=event, rule=rule))
        return candidates

    def _matches(self, event: EventRecord, rule: AlertRule, now: datetime) -> bool:
        if rule.regions and (event.region or "").lower() not in {r.lower() for r in rule.regions}:
            return False

        if rule.categories and (event.category or "").lower() not in {c.lower() for c in rule.categories}:
            return False

        threat = (event.threat_level or "").lower()
        if threat not in _THREAT_ORDER:
            return False
        if _THREAT_ORDER[threat] < _THREAT_ORDER[rule.minimum_threat.lower()] :
            return False

        if event.credibility_score < rule.minimum_credibility:
            return False

        cutoff = now - timedelta(minutes=rule.lookback_minutes)
        if event.fetched_at < cutoff:
            return False

        if event.verification_status not in {"verified", "primary", "probable"}:
            return False

        return True


_THREAT_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}
