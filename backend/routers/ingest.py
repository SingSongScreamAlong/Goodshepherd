"""
Ingest and fusion administration endpoints.
"""
from typing import Annotated
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.core.database import get_db
from backend.core.logging import get_logger
from backend.models.event import Event
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services.clustering import clustering_service
from backend.services.fusion import fusion_service

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/fusion/run")
def run_fusion(
    hours_back: int = Query(24, description="Process events from last N hours"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run fusion on recent events to detect and merge clusters.

    This endpoint:
    1. Finds events from the last N hours
    2. Groups them into clusters using similarity detection
    3. Assigns cluster IDs to related events

    Note: This is a batch operation and may take time for large datasets.

    Args:
        hours_back: Number of hours to look back for events
        current_user: Current authenticated user
        db: Database session

    Returns:
        Summary of fusion results
    """
    logger.info(
        "Fusion requested",
        user_id=str(current_user.id),
        hours_back=hours_back
    )

    # Get recent events without cluster IDs
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

    events = db.query(Event).filter(
        and_(
            Event.timestamp >= cutoff_time,
            Event.cluster_id == None
        )
    ).all()

    if not events:
        logger.info("No events to cluster")
        return {
            "status": "success",
            "message": "No unclustered events found",
            "events_processed": 0,
            "clusters_created": 0
        }

    logger.info("Found events for clustering", count=len(events))

    # Find clusters
    clusters = clustering_service.find_clusters(events)

    # Assign cluster IDs to events
    clusters_created = 0
    events_clustered = 0

    for cluster_id, cluster_events in clusters.items():
        if len(cluster_events) > 1:
            # Only assign cluster ID if multiple events
            clusters_created += 1

            for event in cluster_events:
                event.cluster_id = cluster_id
                events_clustered += 1

    db.commit()

    logger.info(
        "Fusion complete",
        events_processed=len(events),
        clusters_created=clusters_created,
        events_clustered=events_clustered
    )

    return {
        "status": "success",
        "message": f"Processed {len(events)} events, created {clusters_created} clusters",
        "events_processed": len(events),
        "clusters_created": clusters_created,
        "events_clustered": events_clustered
    }


@router.get("/health")
def ingest_health():
    """
    Health check for ingest subsystem.

    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "services": {
            "clustering": "available",
            "fusion": "available"
        }
    }
