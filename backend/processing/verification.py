"""Event verification heuristics for Good Shepherd."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

TRUSTED_SOURCES: tuple[str, ...] = (
    "gdacs.org",
    "earthquake.usgs.gov",
    "gov.uk",
    "ec.europa.eu",
)

HIGH_RISK_CATEGORIES: tuple[str, ...] = (
    "attack",
    "terrorism",
    "conflict",
    "kidnapping",
)

MODERATE_RISK_CATEGORIES: tuple[str, ...] = (
    "protest",
    "riot",
    "disease",
    "weather",
)


@dataclass(slots=True)
class VerificationResult:
    """Structured verification output."""

    verification_status: str
    credibility_score: float
    threat_level: str | None


def evaluate_event(payload: Mapping[str, str]) -> VerificationResult:
    """Compute verification metadata for an event payload."""

    source_url = payload.get("source_url") or ""
    category = (payload.get("category") or "").lower()
    title = payload.get("title") or ""
    summary = payload.get("summary") or ""

    score = 0.25

    if _is_trusted_source(source_url):
        score += 0.35
    if category in HIGH_RISK_CATEGORIES:
        score += 0.2
    elif category in MODERATE_RISK_CATEGORIES:
        score += 0.1

    if any(keyword in (title + " " + summary).lower() for keyword in ("confirmed", "official", "gov")):
        score += 0.1

    score = min(score, 1.0)

    if score >= 0.7:
        status = "verified"
    elif score >= 0.45:
        status = "probable"
    else:
        status = "needs_review"

    if category in HIGH_RISK_CATEGORIES:
        threat = "high"
    elif category in MODERATE_RISK_CATEGORIES:
        threat = "medium"
    else:
        threat = "low" if score >= 0.5 else None

    return VerificationResult(
        verification_status=status,
        credibility_score=round(score, 2),
        threat_level=threat,
    )


def _is_trusted_source(url: str) -> bool:
    return any(domain in url for domain in TRUSTED_SOURCES)
