"""
Region model for geographic area state tracking.
Central to the World Situational Awareness concept.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship, deferred
import enum

# Try to import geoalchemy2, fall back to Text column if not available
try:
    from geoalchemy2 import Geometry
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from backend.core.database import Base


class RegionStatus(str, enum.Enum):
    """Overall status classification for a region."""
    GREEN = "green"      # Stable, normal conditions
    YELLOW = "yellow"    # Elevated concern, monitoring
    RED = "red"          # Critical, active issues


class RegionType(str, enum.Enum):
    """Type of region for hierarchy."""
    GLOBAL = "global"        # Global level
    CONTINENT = "continent"  # Continent level
    COUNTRY = "country"      # Country level
    ADMIN1 = "admin1"        # State/Province level
    ADMIN2 = "admin2"        # County/District level
    CITY = "city"            # City level
    CUSTOM = "custom"        # Custom-defined region


class Region(Base):
    """
    Geographic region for state tracking.
    
    This is the core concept of World Situational Awareness:
    - Each region maintains a continuously updated state
    - Multiple dimensions tracked (physical, migration, security, etc.)
    - Hierarchical (country > state > city)
    - Status classification for quick assessment
    
    The output is a LIVE OPERATIONAL PICTURE, not a feed reader.
    """
    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    name = Column(String(255), nullable=False, index=True)
    iso_code = Column(String(10), nullable=True, index=True)
    
    # Region type and hierarchy
    region_type = Column(
        SQLEnum(RegionType),
        nullable=False,
        default=RegionType.COUNTRY
    )
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey('regions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Geometry - only use PostGIS if available, otherwise skip
    # NOTE: This column is deferred and optional for dev environments
    # geom column is not created in init_db.py for non-PostGIS setups
    
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    
    # Overall status
    status = Column(
        SQLEnum(RegionStatus),
        nullable=False,
        default=RegionStatus.GREEN
    )
    status_reason = Column(Text, nullable=True)
    status_updated_at = Column(DateTime, nullable=True)
    
    # Composite state scores (0-100)
    physical_state_score = Column(
        Float,
        nullable=True,
        comment="Physical infrastructure and environment (0=good, 100=critical)"
    )
    migration_pressure_score = Column(
        Float,
        nullable=True,
        comment="Migration pressure and flows (0=low, 100=extreme)"
    )
    security_stability_score = Column(
        Float,
        nullable=True,
        comment="Security and stability (0=stable, 100=critical)"
    )
    socioeconomic_stress_score = Column(
        Float,
        nullable=True,
        comment="Socioeconomic conditions (0=stable, 100=critical)"
    )
    information_reliability_score = Column(
        Float,
        nullable=True,
        comment="Reliability of information from region (0=unreliable, 100=reliable)"
    )
    
    # Metadata
    population = Column(Integer, nullable=True)
    area_sq_km = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Summary
    summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for hierarchy
    parent = relationship("Region", remote_side=[id], backref="children")

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def coordinates(self) -> tuple:
        """Get center coordinates as (lat, lon) tuple."""
        if self.center_lat is not None and self.center_lon is not None:
            return (self.center_lat, self.center_lon)
        return None
    
    @property
    def composite_risk_score(self) -> float:
        """
        Calculate composite risk score from all dimensions.
        Higher score = higher risk.
        """
        scores = [
            self.physical_state_score,
            self.migration_pressure_score,
            self.security_stability_score,
            self.socioeconomic_stress_score
        ]
        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return 0.0
        return sum(valid_scores) / len(valid_scores)
    
    def compute_status(self) -> RegionStatus:
        """
        Compute status from composite risk score.
        
        Returns:
            RegionStatus based on risk thresholds
        """
        risk = self.composite_risk_score
        if risk < 30:
            return RegionStatus.GREEN
        elif risk < 70:
            return RegionStatus.YELLOW
        else:
            return RegionStatus.RED
    
    def update_status(self, reason: str = None) -> None:
        """
        Update status based on current scores.
        
        Args:
            reason: Optional reason for status change
        """
        new_status = self.compute_status()
        if new_status != self.status:
            self.status = new_status
            self.status_reason = reason
            self.status_updated_at = datetime.utcnow()
    
    @property
    def is_critical(self) -> bool:
        """Check if region is in critical state."""
        return self.status == RegionStatus.RED
