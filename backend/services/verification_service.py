"""
Verification Service for incident confidence scoring and status management.
Implements the verification engine with corroboration and source trust.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.event import Event, IncidentStatus
from backend.models.source import Source

logger = get_logger(__name__)


class VerificationService:
    """
    Service for verifying incidents and managing confidence scores.
    
    Implements:
    - Source trust_baseline integration
    - Independent corroboration boost
    - Visual evidence verification boost
    - Geo/time consistency checks
    - Admin override with audit trail
    
    Confidence to Status mapping:
    < 30  -> Unverified
    30-59 -> Developing
    60-84 -> Corroborated
    85+   -> Confirmed
    """
    
    def __init__(self):
        """Initialize verification service."""
        # Confidence thresholds - set high because lives depend on accuracy
        # Note: CONFIRMED status requires admin verification - cannot be set algorithmically
        self.UNVERIFIED_THRESHOLD = 40   # Below 40% = unsubstantiated
        self.DEVELOPING_THRESHOLD = 75   # 40-74% = still developing
        # CORROBORATED requires 75%+ (strong multi-source evidence)
        # CONFIRMED requires explicit admin verification
        
        # Boost values
        self.CORROBORATION_BOOST = 0.10  # Per additional source
        self.VISUAL_EVIDENCE_BOOST = 0.15
        self.OFFICIAL_SOURCE_BOOST = 0.20
        
        # Penalty values
        self.RECYCLED_MEDIA_PENALTY = -0.15
        self.GEO_INCONSISTENCY_PENALTY = -0.10
        self.TIME_INCONSISTENCY_PENALTY = -0.10
    
    def calculate_confidence(
        self,
        incident: Event,
        source_trust: int = 50,
        corroboration_count: int = 1,
        has_visual_evidence: bool = False,
        has_official_confirmation: bool = False,
        has_recycled_media: bool = False,
        geo_consistent: bool = True,
        time_consistent: bool = True
    ) -> float:
        """
        Calculate confidence score for an incident.
        
        Args:
            incident: The incident to score
            source_trust: Trust baseline of primary source (0-100)
            corroboration_count: Number of independent sources
            has_visual_evidence: Whether verified visual evidence exists
            has_official_confirmation: Whether official source confirmed
            has_recycled_media: Whether media appears recycled
            geo_consistent: Whether location data is consistent
            time_consistent: Whether timing is consistent
            
        Returns:
            Confidence score 0.0-1.0
        """
        # Start with source trust baseline (normalized)
        base_confidence = source_trust / 100.0
        
        # Apply corroboration boost
        # Diminishing returns: +10%, +8%, +6%, +4%, +2% for each additional
        if corroboration_count > 1:
            for i in range(1, min(corroboration_count, 6)):
                boost = max(0.02, self.CORROBORATION_BOOST - (i - 1) * 0.02)
                base_confidence += boost
        
        # Apply evidence boosts
        if has_visual_evidence:
            base_confidence += self.VISUAL_EVIDENCE_BOOST
        
        if has_official_confirmation:
            base_confidence += self.OFFICIAL_SOURCE_BOOST
        
        # Apply penalties
        if has_recycled_media:
            base_confidence += self.RECYCLED_MEDIA_PENALTY
        
        if not geo_consistent:
            base_confidence += self.GEO_INCONSISTENCY_PENALTY
        
        if not time_consistent:
            base_confidence += self.TIME_INCONSISTENCY_PENALTY
        
        # Clamp to valid range
        confidence = max(0.0, min(1.0, base_confidence))
        
        return round(confidence, 2)
    
    def confidence_to_status(self, confidence: float) -> IncidentStatus:
        """
        Map confidence score to verification status.
        
        Note: CONFIRMED status is NEVER set algorithmically.
        It requires explicit admin verification.
        
        Args:
            confidence: Confidence score 0.0-1.0
            
        Returns:
            Appropriate IncidentStatus (max: CORROBORATED)
        """
        conf_percent = confidence * 100
        
        if conf_percent < self.UNVERIFIED_THRESHOLD:
            return IncidentStatus.UNVERIFIED
        elif conf_percent < self.DEVELOPING_THRESHOLD:
            return IncidentStatus.DEVELOPING
        else:
            # Max algorithmic status is CORROBORATED
            # CONFIRMED requires admin verification
            return IncidentStatus.CORROBORATED
    
    def update_incident_verification(
        self,
        incident: Event,
        new_confidence: Optional[float] = None,
        recalculate: bool = True
    ) -> IncidentStatus:
        """
        Update incident verification status based on confidence.
        
        Args:
            incident: Incident to update
            new_confidence: Optional new confidence score
            recalculate: Whether to recalculate from evidence
            
        Returns:
            New status
        """
        if new_confidence is not None:
            incident.confidence_score = new_confidence
        
        # Calculate new status
        new_status = self.confidence_to_status(incident.confidence_score or 0)
        
        # Update if changed
        if incident.status != new_status:
            old_status = incident.status
            incident.status = new_status
            
            logger.info(
                "Incident status updated",
                incident_id=str(incident.id),
                old_status=old_status.value,
                new_status=new_status.value,
                confidence=incident.confidence_score
            )
        
        return new_status
    
    def apply_corroboration(
        self,
        incident: Event,
        corroborating_sources: List[Source]
    ) -> float:
        """
        Apply corroboration boost from multiple sources.
        
        Args:
            incident: Incident to boost
            corroborating_sources: List of corroborating sources
            
        Returns:
            New confidence score
        """
        current = incident.confidence_score or 0.5
        
        for source in corroborating_sources:
            # Boost based on source trust
            trust_factor = source.trust_baseline / 100.0
            boost = self.CORROBORATION_BOOST * trust_factor
            current = min(1.0, current + boost)
        
        incident.confidence_score = round(current, 2)
        self.update_incident_verification(incident)
        
        return incident.confidence_score
    
    def admin_override(
        self,
        incident: Event,
        new_status: IncidentStatus,
        admin_id: UUID,
        notes: str = None
    ) -> None:
        """
        Apply admin override to incident status.
        
        Args:
            incident: Incident to override
            new_status: New status to set
            admin_id: ID of admin making override
            notes: Optional notes explaining override
        """
        old_status = incident.status
        
        incident.status = new_status
        incident.admin_override_by = admin_id
        incident.admin_override_at = datetime.utcnow()
        incident.admin_notes = notes
        
        logger.info(
            "Admin override applied",
            incident_id=str(incident.id),
            old_status=old_status.value,
            new_status=new_status.value,
            admin_id=str(admin_id),
            notes=notes
        )
    
    def debunk_incident(
        self,
        incident: Event,
        admin_id: UUID,
        reason: str
    ) -> None:
        """
        Mark incident as debunked.
        
        Args:
            incident: Incident to debunk
            admin_id: ID of admin debunking
            reason: Reason for debunking
        """
        self.admin_override(
            incident=incident,
            new_status=IncidentStatus.DEBUNKED,
            admin_id=admin_id,
            notes=f"DEBUNKED: {reason}"
        )
        
        # Set confidence to 0
        incident.confidence_score = 0.0
    
    def confirm_incident(
        self,
        incident: Event,
        admin_id: UUID,
        notes: str = None
    ) -> None:
        """
        Manually confirm an incident.
        
        Args:
            incident: Incident to confirm
            admin_id: ID of admin confirming
            notes: Optional confirmation notes
        """
        self.admin_override(
            incident=incident,
            new_status=IncidentStatus.CONFIRMED,
            admin_id=admin_id,
            notes=notes or "Manually confirmed by analyst"
        )
        
        # Ensure confidence is at confirmation level
        if (incident.confidence_score or 0) < 0.85:
            incident.confidence_score = 0.85
    
    def get_verification_queue(
        self,
        limit: int = 50
    ) -> List[Event]:
        """
        Get incidents pending verification.
        
        Args:
            limit: Maximum items to return
            
        Returns:
            List of unverified/developing incidents
        """
        db = SessionLocal()
        
        try:
            queue = db.query(Event).filter(
                Event.status.in_([
                    IncidentStatus.UNVERIFIED,
                    IncidentStatus.DEVELOPING
                ])
            ).order_by(
                Event.created_at.desc()
            ).limit(limit).all()
            
            return queue
            
        finally:
            db.close()


# Global service instance
verification_service = VerificationService()
