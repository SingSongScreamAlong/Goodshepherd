"""
Normalization Service for processing RawObservations into Incidents.
Handles location extraction, timestamp normalization, and classification.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
from uuid import uuid4

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.raw_observation import RawObservation
from backend.models.event import Event, EventCategory, IncidentStatus, IncidentSeverity
from backend.models.incident_evidence import IncidentEvidence, EvidenceType
from backend.services.enrichment import enrichment_pipeline

logger = get_logger(__name__)


class NormalizationService:
    """
    Service for normalizing RawObservations into Incidents.
    
    Pipeline:
    1. Extract locations with geo-confidence
    2. Extract/normalize timestamps
    3. Auto-classify category
    4. Suggest severity
    5. Tag domains
    6. Create Incident with evidence linkage
    """
    
    def __init__(self):
        """Initialize normalization service."""
        self.enrichment = enrichment_pipeline
        
        # Category keywords for fallback classification
        self.category_keywords = {
            EventCategory.SECURITY: [
                "attack", "bombing", "shooting", "violence", "terror", 
                "militia", "armed", "conflict", "raid", "assault"
            ],
            EventCategory.MIGRATION: [
                "migrant", "refugee", "asylum", "border", "crossing",
                "deportation", "sanctuary", "undocumented", "caravan"
            ],
            EventCategory.POLITICAL: [
                "election", "vote", "government", "president", "minister",
                "parliament", "senate", "congress", "policy", "law"
            ],
            EventCategory.DISASTER: [
                "earthquake", "flood", "hurricane", "tornado", "tsunami",
                "wildfire", "volcano", "disaster", "emergency", "evacuation"
            ],
            EventCategory.INFRASTRUCTURE: [
                "power outage", "blackout", "water", "road closure",
                "bridge", "airport", "port", "railway", "internet"
            ],
            EventCategory.HEALTH: [
                "outbreak", "epidemic", "pandemic", "disease", "hospital",
                "vaccination", "quarantine", "infection", "health emergency"
            ],
            EventCategory.ECONOMIC: [
                "economy", "inflation", "unemployment", "market", "trade",
                "currency", "bank", "recession", "gdp", "poverty"
            ]
        }
        
        # Severity indicators
        self.severity_indicators = {
            IncidentSeverity.CRITICAL: [
                "mass casualty", "widespread", "major", "catastrophic",
                "national emergency", "breaking", "urgent", "critical"
            ],
            IncidentSeverity.HIGH: [
                "serious", "significant", "severe", "dangerous",
                "casualties", "injured", "death", "killed"
            ],
            IncidentSeverity.MEDIUM: [
                "moderate", "concerning", "developing", "ongoing"
            ],
            IncidentSeverity.LOW: [
                "minor", "small", "local", "isolated", "limited"
            ]
        }
    
    def process_observation(
        self,
        observation: RawObservation
    ) -> Optional[Event]:
        """
        Process a single RawObservation into an Incident.
        
        Args:
            observation: RawObservation to process
            
        Returns:
            Created Incident/Event or None
        """
        if observation.processed:
            return None
        
        logger.info(
            "Processing observation",
            observation_id=str(observation.id)
        )
        
        try:
            # Get the raw content
            content = observation.raw_text or ""
            title = observation.title or ""
            full_text = f"{title}\n\n{content}"
            
            # Try LLM enrichment first
            enrichment_data = {}
            try:
                enrichment_data = self.enrichment.enrich(
                    text=full_text,
                    title=title
                )
            except Exception as e:
                logger.warning(
                    "LLM enrichment failed, using fallback",
                    error=str(e)
                )
            
            # Extract or use enriched data
            category = self._extract_category(full_text, enrichment_data)
            severity = self._extract_severity(full_text, enrichment_data)
            
            # Get location data
            location_data = self._extract_location(
                full_text,
                enrichment_data,
                observation.extracted_locations
            )
            
            # Get timestamp
            occurred_at = observation.extracted_timestamp or observation.collected_at
            
            # Calculate initial confidence
            confidence = self._calculate_initial_confidence(
                observation,
                enrichment_data
            )
            
            # Determine initial status from confidence
            status = self._confidence_to_status(confidence)
            
            # Create incident
            incident = Event(
                title=title[:300] if title else None,
                timestamp=observation.collected_at,
                occurred_at=occurred_at,
                summary=enrichment_data.get("summary", title[:500]),
                full_text=full_text,
                description=content[:2000] if len(content) > 2000 else content,
                category=category,
                severity=severity,
                status=status,
                confidence_score=confidence,
                relevance_score=enrichment_data.get("relevance_score", 0.5),
                sentiment=enrichment_data.get("sentiment"),
                location_lat=location_data.get("lat"),
                location_lon=location_data.get("lon"),
                location_name=location_data.get("name"),
                entity_list=enrichment_data.get("entity_list", {}),
                source_list=[{
                    "url": observation.original_url,
                    "collected_at": observation.collected_at.isoformat(),
                    "source_id": str(observation.source_id)
                }],
                tags=self._extract_domain_tags(full_text, category)
            )
            
            # Mark observation as processed
            observation.processed = True
            observation.processed_at = datetime.utcnow()
            
            logger.info(
                "Observation processed",
                observation_id=str(observation.id),
                category=category.value,
                severity=severity.value,
                confidence=confidence
            )
            
            return incident
            
        except Exception as e:
            observation.processing_error = str(e)
            logger.error(
                "Error processing observation",
                observation_id=str(observation.id),
                error=str(e)
            )
            return None
    
    def process_batch(
        self,
        limit: int = 100
    ) -> Tuple[int, int]:
        """
        Process a batch of unprocessed observations.
        
        Args:
            limit: Maximum observations to process
            
        Returns:
            Tuple of (processed_count, incident_count)
        """
        db = SessionLocal()
        processed = 0
        incidents_created = 0
        
        try:
            # Get unprocessed observations
            observations = db.query(RawObservation).filter(
                RawObservation.processed == False
            ).limit(limit).all()
            
            logger.info(
                "Processing observation batch",
                count=len(observations)
            )
            
            for observation in observations:
                incident = self.process_observation(observation)
                
                if incident:
                    # Add to database
                    db.add(incident)
                    
                    # Create evidence linkage
                    evidence = IncidentEvidence(
                        incident_id=incident.id,
                        observation_id=observation.id,
                        evidence_type=EvidenceType.TEXT,
                        excerpt=observation.title or observation.raw_text[:500],
                        weight=1.0
                    )
                    db.add(evidence)
                    
                    incidents_created += 1
                
                processed += 1
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error("Batch processing error", error=str(e))
        finally:
            db.close()
        
        logger.info(
            "Batch processing complete",
            processed=processed,
            incidents_created=incidents_created
        )
        
        return processed, incidents_created
    
    def _extract_category(
        self,
        text: str,
        enrichment: Dict[str, Any]
    ) -> EventCategory:
        """Extract category from text or enrichment."""
        # Use enrichment if available
        if enrichment.get("category"):
            cat_value = enrichment["category"]
            if isinstance(cat_value, EventCategory):
                return cat_value
            try:
                return EventCategory(cat_value)
            except ValueError:
                pass
        
        # Fallback to keyword matching
        text_lower = text.lower()
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return EventCategory.OTHER
    
    def _extract_severity(
        self,
        text: str,
        enrichment: Dict[str, Any]
    ) -> IncidentSeverity:
        """Extract severity from text."""
        text_lower = text.lower()
        
        for severity, indicators in self.severity_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return severity
        
        return IncidentSeverity.MEDIUM
    
    def _extract_location(
        self,
        text: str,
        enrichment: Dict[str, Any],
        extracted: Optional[List] = None
    ) -> Dict[str, Any]:
        """Extract location data."""
        # Use pre-extracted locations
        if extracted and len(extracted) > 0:
            loc = extracted[0]
            return {
                "name": loc.get("name"),
                "lat": loc.get("lat"),
                "lon": loc.get("lon"),
                "confidence": loc.get("confidence", 0.5)
            }
        
        # Use enrichment entity list
        entities = enrichment.get("entity_list", {})
        locations = entities.get("locations", [])
        
        if locations:
            return {
                "name": locations[0],
                "lat": None,
                "lon": None,
                "confidence": 0.3
            }
        
        return {}
    
    def _calculate_initial_confidence(
        self,
        observation: RawObservation,
        enrichment: Dict[str, Any]
    ) -> float:
        """Calculate initial confidence score."""
        # Get source trust baseline
        source_trust = 50  # Default
        if observation.source and hasattr(observation.source, 'trust_baseline'):
            source_trust = observation.source.trust_baseline
        
        # Start with source trust (normalized to 0-1)
        confidence = source_trust / 100.0
        
        # Boost for enrichment confidence
        if enrichment.get("confidence_score"):
            confidence = (confidence + enrichment["confidence_score"]) / 2
        
        # Boost for having location
        if observation.extracted_locations:
            confidence = min(1.0, confidence + 0.1)
        
        # Boost for longer content
        text_len = len(observation.raw_text or "")
        if text_len > 500:
            confidence = min(1.0, confidence + 0.05)
        
        return round(confidence, 2)
    
    def _confidence_to_status(self, confidence: float) -> IncidentStatus:
        """Map confidence score to incident status.
        
        Thresholds set high because lives depend on accuracy:
        - < 40%: UNVERIFIED
        - 40-74%: DEVELOPING  
        - 75%+: CORROBORATED
        - CONFIRMED: Admin only
        """
        conf_percent = confidence * 100
        
        if conf_percent < 40:
            return IncidentStatus.UNVERIFIED
        elif conf_percent < 75:
            return IncidentStatus.DEVELOPING
        else:
            # Max algorithmic status - CONFIRMED requires admin action
            return IncidentStatus.CORROBORATED
    
    def _extract_domain_tags(
        self,
        text: str,
        category: EventCategory
    ) -> List[str]:
        """Extract domain tags for multi-dimensional tracking."""
        tags = []
        
        # Map category to domain
        category_domain_map = {
            EventCategory.SECURITY: "security",
            EventCategory.MIGRATION: "migration",
            EventCategory.POLITICAL: "geopolitical",
            EventCategory.DISASTER: "infrastructure",
            EventCategory.INFRASTRUCTURE: "infrastructure",
            EventCategory.HEALTH: "health",
            EventCategory.ECONOMIC: "economic",
        }
        
        if category in category_domain_map:
            tags.append(category_domain_map[category])
        
        # Additional domain detection
        text_lower = text.lower()
        if "migration" in text_lower or "refugee" in text_lower:
            if "migration" not in tags:
                tags.append("migration")
        if "economic" in text_lower or "trade" in text_lower:
            if "economic" not in tags:
                tags.append("economic")
        
        return tags


# Global service instance
normalization_service = NormalizationService()
