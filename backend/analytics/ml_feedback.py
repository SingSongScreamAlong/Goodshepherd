"""ML Feedback service for model improvement.

Collects analyst corrections and feedback to improve ML models over time.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EventRecord
from backend.database.session import session_scope

logger = logging.getLogger(__name__)


@dataclass
class MLFeedback:
    """ML feedback record."""
    event_id: str
    analyst_id: Optional[str]
    timestamp: datetime
    corrected_category: Optional[str] = None
    corrected_threat_level: Optional[str] = None
    is_disinformation: bool = False
    analyst_notes: Optional[str] = None
    original_category: Optional[str] = None
    original_threat_level: Optional[str] = None
    original_disinfo_score: Optional[float] = None


@dataclass
class FeedbackStats:
    """Statistics about collected feedback."""
    total_feedback: int
    category_corrections: int
    threat_corrections: int
    disinfo_flags: int
    accuracy_by_category: dict = field(default_factory=dict)
    accuracy_by_threat: dict = field(default_factory=dict)


class MLFeedbackService:
    """Service for collecting and managing ML feedback."""

    def __init__(self, feedback_dir: Optional[str] = None):
        self.feedback_dir = Path(feedback_dir or os.getenv(
            "ML_FEEDBACK_DIR",
            "/tmp/goodshepherd/ml_feedback"
        ))
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self._feedback_file = self.feedback_dir / "feedback.jsonl"

    async def submit_feedback(
        self,
        event_id: str,
        feedback: dict,
        analyst_id: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Submit feedback for an event."""
        async def _submit(sess: AsyncSession) -> dict:
            # Get original event
            query = select(EventRecord).where(EventRecord.id == UUID(event_id))
            result = await sess.execute(query)
            event = result.scalar_one_or_none()

            if not event:
                raise ValueError(f"Event {event_id} not found")

            # Extract original ML analysis
            original_ml = None
            if event.raw:
                try:
                    raw_data = json.loads(event.raw)
                    original_ml = raw_data.get("ml_analysis", {})
                except (json.JSONDecodeError, TypeError):
                    pass

            # Create feedback record
            feedback_record = MLFeedback(
                event_id=event_id,
                analyst_id=analyst_id,
                timestamp=datetime.utcnow(),
                corrected_category=feedback.get("corrected_category"),
                corrected_threat_level=feedback.get("corrected_threat_level"),
                is_disinformation=feedback.get("is_disinformation", False),
                analyst_notes=feedback.get("analyst_notes"),
                original_category=event.category,
                original_threat_level=event.threat_level,
                original_disinfo_score=(
                    original_ml.get("disinfo", {}).get("risk_score")
                    if original_ml else None
                ),
            )

            # Save to file for training
            self._save_feedback(feedback_record)

            # Update event if corrections provided
            updates = {}
            if feedback.get("corrected_category") and feedback["corrected_category"] != event.category:
                updates["category"] = feedback["corrected_category"]
            if feedback.get("corrected_threat_level") and feedback["corrected_threat_level"] != event.threat_level:
                updates["threat_level"] = feedback["corrected_threat_level"]
            if feedback.get("is_disinformation"):
                updates["verification_status"] = "disinformation"
                updates["credibility_score"] = 0.1

            if updates:
                await sess.execute(
                    update(EventRecord)
                    .where(EventRecord.id == UUID(event_id))
                    .values(**updates)
                )
                await sess.commit()

            return {
                "success": True,
                "event_id": event_id,
                "corrections_applied": list(updates.keys()),
            }

        if session:
            return await _submit(session)
        else:
            async with session_scope() as sess:
                return await _submit(sess)

    def _save_feedback(self, feedback: MLFeedback):
        """Save feedback to JSONL file for training."""
        record = {
            "event_id": feedback.event_id,
            "analyst_id": feedback.analyst_id,
            "timestamp": feedback.timestamp.isoformat(),
            "corrected_category": feedback.corrected_category,
            "corrected_threat_level": feedback.corrected_threat_level,
            "is_disinformation": feedback.is_disinformation,
            "analyst_notes": feedback.analyst_notes,
            "original_category": feedback.original_category,
            "original_threat_level": feedback.original_threat_level,
            "original_disinfo_score": feedback.original_disinfo_score,
        }

        with open(self._feedback_file, "a") as f:
            f.write(json.dumps(record) + "\n")

        logger.info(f"Saved ML feedback for event {feedback.event_id}")

    def get_feedback_stats(self) -> FeedbackStats:
        """Get statistics about collected feedback."""
        if not self._feedback_file.exists():
            return FeedbackStats(
                total_feedback=0,
                category_corrections=0,
                threat_corrections=0,
                disinfo_flags=0,
            )

        total = 0
        category_corrections = 0
        threat_corrections = 0
        disinfo_flags = 0
        category_matches = {}
        threat_matches = {}

        with open(self._feedback_file, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    total += 1

                    if record.get("corrected_category"):
                        category_corrections += 1
                        orig = record.get("original_category", "unknown")
                        if orig not in category_matches:
                            category_matches[orig] = {"correct": 0, "incorrect": 0}
                        category_matches[orig]["incorrect"] += 1
                    elif record.get("original_category"):
                        orig = record["original_category"]
                        if orig not in category_matches:
                            category_matches[orig] = {"correct": 0, "incorrect": 0}
                        category_matches[orig]["correct"] += 1

                    if record.get("corrected_threat_level"):
                        threat_corrections += 1
                        orig = record.get("original_threat_level", "unknown")
                        if orig not in threat_matches:
                            threat_matches[orig] = {"correct": 0, "incorrect": 0}
                        threat_matches[orig]["incorrect"] += 1
                    elif record.get("original_threat_level"):
                        orig = record["original_threat_level"]
                        if orig not in threat_matches:
                            threat_matches[orig] = {"correct": 0, "incorrect": 0}
                        threat_matches[orig]["correct"] += 1

                    if record.get("is_disinformation"):
                        disinfo_flags += 1

                except json.JSONDecodeError:
                    continue

        # Compute accuracy
        accuracy_by_category = {}
        for cat, counts in category_matches.items():
            total_cat = counts["correct"] + counts["incorrect"]
            if total_cat > 0:
                accuracy_by_category[cat] = round(counts["correct"] / total_cat * 100, 1)

        accuracy_by_threat = {}
        for level, counts in threat_matches.items():
            total_level = counts["correct"] + counts["incorrect"]
            if total_level > 0:
                accuracy_by_threat[level] = round(counts["correct"] / total_level * 100, 1)

        return FeedbackStats(
            total_feedback=total,
            category_corrections=category_corrections,
            threat_corrections=threat_corrections,
            disinfo_flags=disinfo_flags,
            accuracy_by_category=accuracy_by_category,
            accuracy_by_threat=accuracy_by_threat,
        )

    def export_training_data(self, output_path: str) -> dict:
        """Export feedback data for model retraining."""
        if not self._feedback_file.exists():
            return {"success": False, "error": "No feedback data available"}

        training_data = {
            "category_corrections": [],
            "threat_corrections": [],
            "disinfo_labels": [],
        }

        with open(self._feedback_file, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)

                    if record.get("corrected_category"):
                        training_data["category_corrections"].append({
                            "event_id": record["event_id"],
                            "original": record.get("original_category"),
                            "corrected": record["corrected_category"],
                        })

                    if record.get("corrected_threat_level"):
                        training_data["threat_corrections"].append({
                            "event_id": record["event_id"],
                            "original": record.get("original_threat_level"),
                            "corrected": record["corrected_threat_level"],
                        })

                    if record.get("is_disinformation"):
                        training_data["disinfo_labels"].append({
                            "event_id": record["event_id"],
                            "is_disinfo": True,
                            "original_score": record.get("original_disinfo_score"),
                        })

                except json.JSONDecodeError:
                    continue

        with open(output_path, "w") as f:
            json.dump(training_data, f, indent=2)

        return {
            "success": True,
            "output_path": output_path,
            "category_corrections": len(training_data["category_corrections"]),
            "threat_corrections": len(training_data["threat_corrections"]),
            "disinfo_labels": len(training_data["disinfo_labels"]),
        }


# Singleton instance
_ml_feedback_service: Optional[MLFeedbackService] = None


def get_ml_feedback_service() -> MLFeedbackService:
    """Get or create ML feedback service singleton."""
    global _ml_feedback_service
    if _ml_feedback_service is None:
        _ml_feedback_service = MLFeedbackService()
    return _ml_feedback_service
