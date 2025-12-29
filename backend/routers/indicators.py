"""
Indicators router for managing regional indicators.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.indicator import Indicator, IndicatorDomain

router = APIRouter(prefix="/indicators", tags=["indicators"])


# Pydantic schemas
class IndicatorResponse(BaseModel):
    id: UUID
    region_id: UUID
    name: str
    domain: str
    description: Optional[str]
    value: float
    delta_24h: Optional[float]
    delta_7d: Optional[float]
    confidence: float
    trend: str
    is_concerning: bool
    measured_at: datetime
    
    class Config:
        from_attributes = True


class IndicatorUpdate(BaseModel):
    value: float
    confidence: Optional[float] = None


class IndicatorCreate(BaseModel):
    region_id: UUID
    name: str
    domain: str
    description: Optional[str] = None
    value: float = 50.0
    confidence: float = 50.0


class IndicatorListResponse(BaseModel):
    indicators: List[IndicatorResponse]
    total: int
    concerning_count: int


@router.get("", response_model=IndicatorListResponse)
async def list_indicators(
    domain: Optional[str] = None,
    region_id: Optional[UUID] = None,
    concerning_only: bool = False,
    db: Session = Depends(get_db)
):
    """List indicators with filtering."""
    query = db.query(Indicator)
    
    if domain:
        try:
            query = query.filter(Indicator.domain == IndicatorDomain(domain))
        except ValueError:
            pass
    
    if region_id:
        query = query.filter(Indicator.region_id == region_id)
    
    indicators = query.order_by(Indicator.domain, Indicator.name).all()
    
    if concerning_only:
        indicators = [i for i in indicators if i.is_concerning]
    
    concerning = sum(1 for i in indicators if i.is_concerning)
    
    return IndicatorListResponse(
        indicators=[
            IndicatorResponse(
                id=i.id,
                region_id=i.region_id,
                name=i.name,
                domain=i.domain.value,
                description=i.description,
                value=i.value,
                delta_24h=i.delta_24h,
                delta_7d=i.delta_7d,
                confidence=i.confidence,
                trend=i.trend_direction,
                is_concerning=i.is_concerning,
                measured_at=i.measured_at
            )
            for i in indicators
        ],
        total=len(indicators),
        concerning_count=concerning
    )


@router.get("/concerning", response_model=List[IndicatorResponse])
async def get_concerning_indicators(
    db: Session = Depends(get_db)
):
    """Get all indicators above 70 (concerning level)."""
    indicators = db.query(Indicator).filter(
        Indicator.value > 70
    ).order_by(Indicator.value.desc()).all()
    
    return [
        IndicatorResponse(
            id=i.id,
            region_id=i.region_id,
            name=i.name,
            domain=i.domain.value,
            description=i.description,
            value=i.value,
            delta_24h=i.delta_24h,
            delta_7d=i.delta_7d,
            confidence=i.confidence,
            trend=i.trend_direction,
            is_concerning=i.is_concerning,
            measured_at=i.measured_at
        )
        for i in indicators
    ]


@router.get("/trending", response_model=List[IndicatorResponse])
async def get_trending_indicators(
    direction: str = "increasing",
    db: Session = Depends(get_db)
):
    """Get indicators with significant trends."""
    indicators = db.query(Indicator).all()
    
    if direction == "increasing":
        filtered = [i for i in indicators if (i.delta_7d or 0) > 5]
        filtered.sort(key=lambda x: x.delta_7d or 0, reverse=True)
    else:
        filtered = [i for i in indicators if (i.delta_7d or 0) < -5]
        filtered.sort(key=lambda x: x.delta_7d or 0)
    
    return [
        IndicatorResponse(
            id=i.id,
            region_id=i.region_id,
            name=i.name,
            domain=i.domain.value,
            description=i.description,
            value=i.value,
            delta_24h=i.delta_24h,
            delta_7d=i.delta_7d,
            confidence=i.confidence,
            trend=i.trend_direction,
            is_concerning=i.is_concerning,
            measured_at=i.measured_at
        )
        for i in filtered[:20]
    ]


@router.get("/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(
    indicator_id: UUID,
    db: Session = Depends(get_db)
):
    """Get single indicator."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    return IndicatorResponse(
        id=indicator.id,
        region_id=indicator.region_id,
        name=indicator.name,
        domain=indicator.domain.value,
        description=indicator.description,
        value=indicator.value,
        delta_24h=indicator.delta_24h,
        delta_7d=indicator.delta_7d,
        confidence=indicator.confidence,
        trend=indicator.trend_direction,
        is_concerning=indicator.is_concerning,
        measured_at=indicator.measured_at
    )


@router.put("/{indicator_id}", response_model=IndicatorResponse)
async def update_indicator(
    indicator_id: UUID,
    update: IndicatorUpdate,
    db: Session = Depends(get_db)
):
    """Update indicator value."""
    indicator = db.query(Indicator).filter(Indicator.id == indicator_id).first()
    
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    # Record new value (handles delta calculation)
    indicator.record_value(update.value)
    
    if update.confidence is not None:
        indicator.confidence = update.confidence
    
    db.commit()
    db.refresh(indicator)
    
    return IndicatorResponse(
        id=indicator.id,
        region_id=indicator.region_id,
        name=indicator.name,
        domain=indicator.domain.value,
        description=indicator.description,
        value=indicator.value,
        delta_24h=indicator.delta_24h,
        delta_7d=indicator.delta_7d,
        confidence=indicator.confidence,
        trend=indicator.trend_direction,
        is_concerning=indicator.is_concerning,
        measured_at=indicator.measured_at
    )


@router.post("", response_model=IndicatorResponse)
async def create_indicator(
    data: IndicatorCreate,
    db: Session = Depends(get_db)
):
    """Create new indicator."""
    # Verify region exists
    from backend.models.region import Region
    region = db.query(Region).filter(Region.id == data.region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    try:
        domain = IndicatorDomain(data.domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {data.domain}")
    
    indicator = Indicator(
        region_id=data.region_id,
        name=data.name,
        domain=domain,
        description=data.description,
        value=data.value,
        confidence=data.confidence,
        measured_at=datetime.utcnow()
    )
    
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    
    return IndicatorResponse(
        id=indicator.id,
        region_id=indicator.region_id,
        name=indicator.name,
        domain=indicator.domain.value,
        description=indicator.description,
        value=indicator.value,
        delta_24h=indicator.delta_24h,
        delta_7d=indicator.delta_7d,
        confidence=indicator.confidence,
        trend=indicator.trend_direction,
        is_concerning=indicator.is_concerning,
        measured_at=indicator.measured_at
    )
