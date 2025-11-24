"""
Clustering service for grouping similar events.
Detects and merges duplicate/related events from multiple sources.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import re

from backend.core.logging import get_logger
from backend.models.event import Event, EventCategory

logger = get_logger(__name__)


class ClusteringService:
    """Service for clustering similar events."""

    def __init__(self):
        """Initialize clustering service."""
        # Similarity thresholds
        self.time_window_hours = 24  # Events within 24 hours can cluster
        self.location_distance_km = 50  # Events within 50km can cluster (placeholder)
        self.text_similarity_threshold = 0.6  # Jaccard similarity threshold

    def should_cluster(
        self,
        event1: Event,
        event2: Event
    ) -> bool:
        """
        Determine if two events should be clustered together.

        Events cluster when they:
        - Are in the same category
        - Occur within time window
        - Share location or are geographically close
        - Have similar content (text similarity)

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if events should cluster, False otherwise
        """
        # Must be same category
        if event1.category != event2.category:
            return False

        # Must be within time window
        time_diff = abs((event1.timestamp - event2.timestamp).total_seconds() / 3600)
        if time_diff > self.time_window_hours:
            return False

        # Check location similarity
        location_match = self._check_location_similarity(event1, event2)

        # Check text similarity
        text_similarity = self._calculate_text_similarity(
            event1.full_text or event1.summary,
            event2.full_text or event2.summary
        )

        # Cluster if location matches AND text is somewhat similar
        # OR if text is very similar regardless of location
        if location_match and text_similarity >= 0.4:
            logger.debug(
                "Events clustered by location and text",
                event1_id=str(event1.id),
                event2_id=str(event2.id),
                similarity=text_similarity
            )
            return True

        if text_similarity >= self.text_similarity_threshold:
            logger.debug(
                "Events clustered by high text similarity",
                event1_id=str(event1.id),
                event2_id=str(event2.id),
                similarity=text_similarity
            )
            return True

        return False

    def _check_location_similarity(self, event1: Event, event2: Event) -> bool:
        """
        Check if two events have similar locations.

        Args:
            event1: First event
            event2: Second event

        Returns:
            True if locations are similar
        """
        # Check location name match (case-insensitive, fuzzy)
        if event1.location_name and event2.location_name:
            loc1_normalized = self._normalize_location(event1.location_name)
            loc2_normalized = self._normalize_location(event2.location_name)

            # Exact match
            if loc1_normalized == loc2_normalized:
                return True

            # Contains match (e.g., "Berlin" in "Berlin, Germany")
            if loc1_normalized in loc2_normalized or loc2_normalized in loc1_normalized:
                return True

        # Check coordinate proximity (if both have coordinates)
        if (event1.location_lat and event1.location_lon and
            event2.location_lat and event2.location_lon):
            distance = self._haversine_distance(
                event1.location_lat, event1.location_lon,
                event2.location_lat, event2.location_lon
            )
            if distance <= self.location_distance_km:
                return True

        # Check entity location overlap
        if event1.entity_list and event2.entity_list:
            locs1 = set(loc.lower() for loc in event1.entity_list.get("locations", []))
            locs2 = set(loc.lower() for loc in event2.entity_list.get("locations", []))

            if locs1 and locs2:
                overlap = locs1.intersection(locs2)
                if len(overlap) > 0:
                    return True

        return False

    def _normalize_location(self, location: str) -> str:
        """Normalize location string for comparison."""
        # Remove common suffixes and normalize
        normalized = location.lower().strip()
        normalized = re.sub(r',.*$', '', normalized)  # Remove everything after comma
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        return normalized

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in kilometers

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using Jaccard similarity of word sets.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Tokenize and normalize
        words1 = set(self._tokenize(text1.lower()))
        words2 = set(self._tokenize(text2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        return intersection / union

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of word tokens
        """
        # Remove punctuation and split
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        words = text_clean.split()

        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}
        words = [w for w in words if len(w) > 2 and w not in stop_words]

        return words

    def find_clusters(self, events: List[Event]) -> Dict[UUID, List[Event]]:
        """
        Group events into clusters.

        Args:
            events: List of events to cluster

        Returns:
            Dictionary mapping cluster_id to list of events
        """
        logger.info("Finding clusters", event_count=len(events))

        if not events:
            return {}

        # Build cluster groups using union-find approach
        clusters: Dict[UUID, List[Event]] = {}
        event_to_cluster: Dict[UUID, UUID] = {}

        for i, event in enumerate(events):
            # Check if this event already has a cluster
            if event.id in event_to_cluster:
                continue

            # Create new cluster for this event
            cluster_id = event.cluster_id or uuid4()
            clusters[cluster_id] = [event]
            event_to_cluster[event.id] = cluster_id

            # Find similar events to add to cluster
            for other_event in events[i + 1:]:
                if other_event.id in event_to_cluster:
                    continue

                if self.should_cluster(event, other_event):
                    # Add to same cluster
                    clusters[cluster_id].append(other_event)
                    event_to_cluster[other_event.id] = cluster_id

        logger.info(
            "Clustering complete",
            total_events=len(events),
            cluster_count=len(clusters),
            avg_cluster_size=sum(len(c) for c in clusters.values()) / len(clusters) if clusters else 0
        )

        return clusters


# Global service instance
clustering_service = ClusteringService()
