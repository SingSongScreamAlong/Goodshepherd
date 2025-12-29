"""
Indicator model for tracking slow-moving trends.
Provides time-series data for regional state tracking.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from backend.core.database import Base


class IndicatorDomain(str, enum.Enum):
    """Domain classification for indicators."""
    GEOPOLITICAL = "geopolitical"      # Political stability, governance
    MIGRATION = "migration"            # Migration flows, pressure
    SECURITY = "security"              # Security threats, violence
    ECONOMIC = "economic"              # Economic conditions, stress
    INFRASTRUCTURE = "infrastructure"  # Infrastructure conditions
    HEALTH = "health"                  # Health conditions, outbreaks
    ENVIRONMENTAL = "environmental"    # Environmental conditions


class Indicator(Base):
    """
    Indicator for tracking slow-moving regional trends.
    
    Unlike incidents (discrete events), indicators represent
    continuous measurements that change over time:
    - Migration pressure
    - Economic stress
    - Security stability
    - Infrastructure condition
    
    Supports delta calculations for trend detection.
    """
    __tablename__ = "indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Region reference
    region_id = Column(
        UUID(as_uuid=True),
        ForeignKey('regions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Indicator identification
    name = Column(String(255), nullable=False, index=True)
    domain = Column(
        SQLEnum(IndicatorDomain),
        nullable=False,
        index=True
    )
    
    description = Column(Text, nullable=True)
    
    # Current value and deltas
    value = Column(
        Float,
        nullable=False,
        default=50.0,
        comment="Current value (0-100 scale)"
    )
    delta_24h = Column(
        Float,
        nullable=True,
        comment="Change in last 24 hours"
    )
    delta_7d = Column(
        Float,
        nullable=True,
        comment="Change in last 7 days"
    )
    
    # Confidence in the indicator
    confidence = Column(
        Float,
        nullable=False,
        default=50.0,
        comment="Confidence in this measurement (0-100)"
    )
    
    # Evidence supporting this indicator
    evidence_links = Column(
        JSON,
        nullable=True,
        comment="List of observation IDs supporting this indicator"
    )
    
    # Historical tracking
    historical_values = Column(
        JSON,
        nullable=True,
        comment="Recent historical values [{timestamp, value}]"
    )
    
    # Timestamps
    measured_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    region = relationship("Region", backref="indicators")

    def __repr__(self) -> str:
        return f"<Indicator(id={self.id}, name={self.name}, region={self.region_id}, value={self.value})>"
    
    @property
    def trend_direction(self) -> str:
        """Get trend direction based on 7d delta."""
        if self.delta_7d is None:
            return "stable"
        elif self.delta_7d > 5:
            return "increasing"
        elif self.delta_7d < -5:
            return "decreasing"
        return "stable"
    
    @property
    def is_concerning(self) -> bool:
        """Check if indicator is at a concerning level (>70)."""
        return self.value > 70
    
    def record_value(self, new_value: float) -> None:
        """
        Record a new value and update deltas.
        
        Args:
            new_value: New indicator value
        """
        now = datetime.utcnow()
        
        # Store old value in history
        history = self.historical_values or []
        history.append({
            "timestamp": self.measured_at.isoformat() if self.measured_at else now.isoformat(),
            "value": self.value
        })
        # Keep last 30 entries
        self.historical_values = history[-30:]
        
        # Calculate delta from previous
        old_value = self.value
        self.delta_24h = new_value - old_value
        
        # Calculate 7d delta from history
        if len(history) >= 7:
            week_ago_value = history[-7].get("value", old_value)
            self.delta_7d = new_value - week_ago_value
        
        # Update current value
        self.value = new_value
        self.measured_at = now
