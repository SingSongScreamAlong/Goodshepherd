"""
Region State Service for tracking multi-dimensional regional states.
Provides live operational picture of geographic areas.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.region import Region, RegionStatus
from backend.models.indicator import Indicator, IndicatorDomain
from backend.models.event import Event, IncidentStatus, IncidentSeverity

logger = get_logger(__name__)


class RegionStateService:
    """
    Service for managing and computing regional states.
    
    The core concept: model REGIONS, not people.
    Each region maintains a continuously updated multi-dimensional state:
    - Physical (infrastructure, environment)
    - Migration pressure
    - Security/stability
    - Socioeconomic stress
    - Information reliability
    
    Output is a LIVE OPERATIONAL PICTURE.
    """
    
    def __init__(self):
        """Initialize region state service."""
        # Weights for composite status calculation
        self.DIMENSION_WEIGHTS = {
            "physical": 0.15,
            "migration": 0.25,
            "security": 0.30,
            "socioeconomic": 0.20,
            "information": 0.10
        }
        
        # Status thresholds
        self.YELLOW_THRESHOLD = 40  # Above this = YELLOW
        self.RED_THRESHOLD = 70      # Above this = RED
    
    def compute_region_status(self, region: Region) -> RegionStatus:
        """
        Compute overall status from dimensional scores.
        
        Uses weighted average of all dimensions.
        
        Args:
            region: Region to compute status for
            
        Returns:
            RegionStatus (GREEN/YELLOW/RED)
        """
        scores = {
            "physical": region.physical_state_score or 0,
            "migration": region.migration_pressure_score or 0,
            "security": region.security_stability_score or 0,
            "socioeconomic": region.socioeconomic_stress_score or 0,
            "information": 100 - (region.information_reliability_score or 50)  # Invert: low reliability = high concern
        }
        
        # Weighted average
        weighted_sum = sum(
            scores[dim] * self.DIMENSION_WEIGHTS[dim]
            for dim in scores
        )
        
        if weighted_sum >= self.RED_THRESHOLD:
            return RegionStatus.RED
        elif weighted_sum >= self.YELLOW_THRESHOLD:
            return RegionStatus.YELLOW
        else:
            return RegionStatus.GREEN
    
    def update_region_from_incidents(
        self,
        region: Region,
        db: Session,
        hours: int = 24
    ) -> Dict[str, float]:
        """
        Update region scores based on recent incidents.
        
        Args:
            region: Region to update
            db: Database session
            hours: Lookback period
            
        Returns:
            Dict of score changes
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent incidents in this region
        incidents = db.query(Event).filter(
            Event.region_id == region.id,
            Event.timestamp >= since,
            Event.status != IncidentStatus.DEBUNKED
        ).all()
        
        if not incidents:
            return {}
        
        # Calculate impact by category
        category_impacts = {
            "security": 0.0,
            "migration": 0.0,
            "infrastructure": 0.0,
            "health": 0.0,
            "political": 0.0,
            "economic": 0.0
        }
        
        severity_multipliers = {
            IncidentSeverity.CRITICAL: 3.0,
            IncidentSeverity.HIGH: 2.0,
            IncidentSeverity.MEDIUM: 1.0,
            IncidentSeverity.LOW: 0.5
        }
        
        for incident in incidents:
            cat = incident.category.value.lower()
            multiplier = severity_multipliers.get(incident.severity, 1.0)
            confidence = incident.confidence_score or 0.5
            
            # Only count if at least DEVELOPING status
            if incident.status == IncidentStatus.UNVERIFIED:
                continue
            
            impact = multiplier * confidence * 5  # Base impact of 5 points
            
            if cat in ["security", "crime", "protest"]:
                category_impacts["security"] += impact
            elif cat == "migration":
                category_impacts["migration"] += impact
            elif cat in ["infrastructure", "disaster"]:
                category_impacts["infrastructure"] += impact
            elif cat == "health":
                category_impacts["health"] += impact
            elif cat in ["political", "religious_freedom", "cultural_tension"]:
                category_impacts["political"] += impact
            elif cat == "economic":
                category_impacts["economic"] += impact
        
        # Apply impacts to regional scores (with decay)
        changes = {}
        
        if category_impacts["security"] > 0:
            old = region.security_stability_score or 30
            new = min(100, old + category_impacts["security"])
            region.security_stability_score = new
            changes["security"] = new - old
        
        if category_impacts["migration"] > 0:
            old = region.migration_pressure_score or 30
            new = min(100, old + category_impacts["migration"])
            region.migration_pressure_score = new
            changes["migration"] = new - old
        
        if category_impacts["infrastructure"] > 0:
            old = region.physical_state_score or 20
            new = min(100, old + category_impacts["infrastructure"])
            region.physical_state_score = new
            changes["physical"] = new - old
        
        # Update overall status
        new_status = self.compute_region_status(region)
        if new_status != region.status:
            old_status = region.status
            region.status = new_status
            region.status_updated_at = datetime.utcnow()
            region.status_reason = f"Status changed from {old_status.value} based on recent incident activity"
            
            logger.info(
                "Region status changed",
                region=region.name,
                old_status=old_status.value,
                new_status=new_status.value
            )
        
        return changes
    
    def update_region_from_indicators(
        self,
        region: Region,
        db: Session
    ) -> None:
        """
        Update region scores from indicator values.
        
        Args:
            region: Region to update
            db: Database session
        """
        indicators = db.query(Indicator).filter(
            Indicator.region_id == region.id
        ).all()
        
        domain_scores = {
            IndicatorDomain.SECURITY: [],
            IndicatorDomain.MIGRATION: [],
            IndicatorDomain.INFRASTRUCTURE: [],
            IndicatorDomain.ECONOMIC: [],
            IndicatorDomain.HEALTH: [],
            IndicatorDomain.GEOPOLITICAL: [],
        }
        
        for indicator in indicators:
            if indicator.domain in domain_scores:
                # Weight by confidence
                weighted_value = indicator.value * (indicator.confidence / 100)
                domain_scores[indicator.domain].append(weighted_value)
        
        # Average each domain
        if domain_scores[IndicatorDomain.SECURITY]:
            region.security_stability_score = sum(domain_scores[IndicatorDomain.SECURITY]) / len(domain_scores[IndicatorDomain.SECURITY])
        
        if domain_scores[IndicatorDomain.MIGRATION]:
            region.migration_pressure_score = sum(domain_scores[IndicatorDomain.MIGRATION]) / len(domain_scores[IndicatorDomain.MIGRATION])
        
        if domain_scores[IndicatorDomain.INFRASTRUCTURE]:
            region.physical_state_score = sum(domain_scores[IndicatorDomain.INFRASTRUCTURE]) / len(domain_scores[IndicatorDomain.INFRASTRUCTURE])
        
        if domain_scores[IndicatorDomain.ECONOMIC]:
            region.socioeconomic_stress_score = sum(domain_scores[IndicatorDomain.ECONOMIC]) / len(domain_scores[IndicatorDomain.ECONOMIC])
    
    def get_regions_by_status(
        self,
        status: RegionStatus,
        db: Session = None
    ) -> List[Region]:
        """
        Get all regions with a specific status.
        
        Args:
            status: Status to filter by
            db: Optional database session
            
        Returns:
            List of regions
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        
        try:
            return db.query(Region).filter(
                Region.status == status
            ).order_by(Region.name).all()
        finally:
            if close_db:
                db.close()
    
    def get_critical_regions(self, db: Session = None) -> List[Region]:
        """Get all RED status regions."""
        return self.get_regions_by_status(RegionStatus.RED, db)
    
    def get_elevated_regions(self, db: Session = None) -> List[Region]:
        """Get all YELLOW status regions."""
        return self.get_regions_by_status(RegionStatus.YELLOW, db)
    
    def get_region_summary(
        self,
        region: Region
    ) -> Dict[str, Any]:
        """
        Get summary of region state.
        
        Args:
            region: Region to summarize
            
        Returns:
            Summary dict
        """
        return {
            "id": str(region.id),
            "name": region.name,
            "status": region.status.value,
            "scores": {
                "physical": region.physical_state_score,
                "migration": region.migration_pressure_score,
                "security": region.security_stability_score,
                "socioeconomic": region.socioeconomic_stress_score,
                "information_reliability": region.information_reliability_score
            },
            "composite_risk": region.composite_risk_score,
            "status_reason": region.status_reason,
            "status_updated_at": region.status_updated_at.isoformat() if region.status_updated_at else None
        }
    
    def calculate_deltas(
        self,
        region: Region,
        db: Session,
        hours: int = 24
    ) -> Dict[str, float]:
        """
        Calculate score changes over time period.
        
        Note: This requires historical score storage.
        For now, uses indicator deltas as proxy.
        
        Args:
            region: Region to analyze
            db: Database session
            hours: Hours to look back
            
        Returns:
            Dict of dimension deltas
        """
        # Get indicators with deltas
        indicators = db.query(Indicator).filter(
            Indicator.region_id == region.id
        ).all()
        
        deltas = {}
        
        for indicator in indicators:
            if hours <= 24 and indicator.delta_24h:
                deltas[f"{indicator.domain.value}_{indicator.name}"] = indicator.delta_24h
            elif hours <= 168 and indicator.delta_7d:  # 7 days
                deltas[f"{indicator.domain.value}_{indicator.name}"] = indicator.delta_7d
        
        return deltas
    
    def refresh_all_regions(self) -> Dict[str, Any]:
        """
        Refresh status for all regions.
        
        Returns:
            Summary of changes
        """
        db = SessionLocal()
        
        try:
            regions = db.query(Region).all()
            
            changes = {
                "total": len(regions),
                "status_changes": [],
                "updated": 0
            }
            
            for region in regions:
                old_status = region.status
                
                # Update from indicators
                self.update_region_from_indicators(region, db)
                
                # Update from incidents
                self.update_region_from_incidents(region, db)
                
                # Check for status change
                new_status = self.compute_region_status(region)
                if new_status != old_status:
                    region.status = new_status
                    region.status_updated_at = datetime.utcnow()
                    changes["status_changes"].append({
                        "region": region.name,
                        "from": old_status.value,
                        "to": new_status.value
                    })
                
                changes["updated"] += 1
            
            db.commit()
            
            logger.info(
                "Refreshed all regions",
                total=changes["total"],
                status_changes=len(changes["status_changes"])
            )
            
            return changes
            
        finally:
            db.close()


# Global service instance
region_state_service = RegionStateService()
