"""
Dossier service for entity/location profile aggregation and statistics.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from backend.models.dossier import Dossier, DossierType
from backend.models.event import Event, EventCategory, SentimentEnum


class DossierService:
    """Service for dossier management and statistics."""

    def __init__(self, db: Session):
        self.db = db

    def update_dossier_stats(self, dossier_id: UUID) -> None:
        """
        Update event statistics for a dossier.
        Counts related events and updates timestamps.
        """
        dossier = self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
        if not dossier:
            return

        # Build query to find related events
        # Match events by entity lists (locations, organizations, groups, topics)
        query_conditions = []

        # Location matching
        if dossier.dossier_type == DossierType.LOCATION and dossier.location_name:
            query_conditions.append(
                Event.entity_list['locations'].astext.contains(f'"{dossier.location_name}"')
            )
            # Also check if location_name matches
            query_conditions.append(Event.location_name.ilike(f'%{dossier.location_name}%'))

        # Organization matching
        if dossier.dossier_type == DossierType.ORGANIZATION:
            query_conditions.append(
                Event.entity_list['organizations'].astext.contains(f'"{dossier.name}"')
            )

        # Group matching
        if dossier.dossier_type == DossierType.GROUP:
            query_conditions.append(
                Event.entity_list['groups'].astext.contains(f'"{dossier.name}"')
            )

        # Topic matching
        if dossier.dossier_type == DossierType.TOPIC:
            query_conditions.append(
                Event.entity_list['topics'].astext.contains(f'"{dossier.name}"')
            )
            query_conditions.append(
                Event.entity_list['keywords'].astext.contains(f'"{dossier.name}"')
            )

        # Person matching (only public officials)
        if dossier.dossier_type == DossierType.PERSON:
            query_conditions.append(
                Event.entity_list['groups'].astext.contains(f'"{dossier.name}"')
            )
            # Note: We intentionally don't track private individuals

        if not query_conditions:
            return

        # Count events and get timestamps
        events = self.db.query(Event).filter(
            or_(*query_conditions),
            Event.organization_id == dossier.organization_id
        ).all()

        if events:
            dossier.event_count = len(events)
            dossier.last_event_timestamp = max(e.timestamp for e in events)
            dossier.first_event_timestamp = min(e.timestamp for e in events)
        else:
            dossier.event_count = 0
            dossier.last_event_timestamp = None
            dossier.first_event_timestamp = None

        dossier.updated_at = datetime.utcnow()
        self.db.commit()

    def get_dossier_stats(self, dossier_id: UUID) -> Dict:
        """
        Get detailed statistics for a dossier.
        Returns event counts, category distribution, sentiment analysis.
        """
        dossier = self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
        if not dossier:
            return {}

        # Build event matching query
        query_conditions = self._build_event_query_conditions(dossier)
        if not query_conditions:
            return {}

        events = self.db.query(Event).filter(
            or_(*query_conditions),
            Event.organization_id == dossier.organization_id
        ).all()

        # Calculate statistics
        now = datetime.utcnow()
        events_7d = [e for e in events if e.timestamp >= now - timedelta(days=7)]
        events_30d = [e for e in events if e.timestamp >= now - timedelta(days=30)]

        # Category distribution
        category_dist = {}
        for event in events:
            cat = event.category.value if event.category else 'unknown'
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # Sentiment distribution
        sentiment_dist = {}
        for event in events:
            sent = event.sentiment.value if event.sentiment else 'unknown'
            sentiment_dist[sent] = sentiment_dist.get(sent, 0) + 1

        return {
            'dossier_id': str(dossier.id),
            'name': dossier.name,
            'dossier_type': dossier.dossier_type.value,
            'event_count': len(events),
            'recent_event_count_7d': len(events_7d),
            'recent_event_count_30d': len(events_30d),
            'last_event_timestamp': dossier.last_event_timestamp,
            'categories': category_dist,
            'sentiment_distribution': sentiment_dist,
        }

    def get_dossier_events(
        self,
        dossier_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Event]:
        """
        Get events related to a dossier.
        Returns paginated list of events.
        """
        dossier = self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
        if not dossier:
            return []

        query_conditions = self._build_event_query_conditions(dossier)
        if not query_conditions:
            return []

        events = self.db.query(Event).filter(
            or_(*query_conditions),
            Event.organization_id == dossier.organization_id
        ).order_by(Event.timestamp.desc()).limit(limit).offset(offset).all()

        return events

    def _build_event_query_conditions(self, dossier: Dossier) -> List:
        """Build SQLAlchemy query conditions for matching events to a dossier."""
        conditions = []

        # Location matching
        if dossier.dossier_type == DossierType.LOCATION and dossier.location_name:
            conditions.append(
                Event.entity_list['locations'].astext.contains(f'"{dossier.location_name}"')
            )
            conditions.append(Event.location_name.ilike(f'%{dossier.location_name}%'))

        # Organization matching
        if dossier.dossier_type == DossierType.ORGANIZATION:
            conditions.append(
                Event.entity_list['organizations'].astext.contains(f'"{dossier.name}"')
            )
            # Check aliases
            if dossier.aliases:
                for alias in dossier.aliases:
                    conditions.append(
                        Event.entity_list['organizations'].astext.contains(f'"{alias}"')
                    )

        # Group matching
        if dossier.dossier_type == DossierType.GROUP:
            conditions.append(
                Event.entity_list['groups'].astext.contains(f'"{dossier.name}"')
            )
            if dossier.aliases:
                for alias in dossier.aliases:
                    conditions.append(
                        Event.entity_list['groups'].astext.contains(f'"{alias}"')
                    )

        # Topic matching
        if dossier.dossier_type == DossierType.TOPIC:
            conditions.append(
                Event.entity_list['topics'].astext.contains(f'"{dossier.name}"')
            )
            conditions.append(
                Event.entity_list['keywords'].astext.contains(f'"{dossier.name}"')
            )

        # Person matching (only public officials)
        if dossier.dossier_type == DossierType.PERSON:
            conditions.append(
                Event.entity_list['groups'].astext.contains(f'"{dossier.name}"')
            )

        return conditions

    def auto_create_dossiers_from_events(
        self,
        organization_id: UUID,
        min_event_count: int = 3
    ) -> List[Dossier]:
        """
        Automatically create dossiers from frequently mentioned entities.
        Useful for discovering important locations/organizations.

        Returns list of newly created dossiers.
        """
        # This is a placeholder for future implementation
        # Would analyze entity_list across events and create dossiers for
        # entities mentioned in at least min_event_count events
        return []
