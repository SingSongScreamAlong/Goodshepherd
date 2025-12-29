"""
Regions router for managing geographic regions and their states.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.region import Region, RegionStatus, RegionType
from backend.models.indicator import Indicator
from backend.services.region_state_service import region_state_service

router = APIRouter(prefix="/regions", tags=["regions"])


# Pydantic schemas
class RegionScores(BaseModel):
    physical: Optional[float]
    migration: Optional[float]
    security: Optional[float]
    socioeconomic: Optional[float]
    information_reliability: Optional[float]


class RegionSummary(BaseModel):
    id: UUID
    name: str
    iso_code: Optional[str]
    region_type: str
    status: str
    composite_risk: float
    
    class Config:
        from_attributes = True


class RegionDetail(BaseModel):
    id: UUID
    name: str
    iso_code: Optional[str]
    region_type: str
    status: str
    status_reason: Optional[str]
    status_updated_at: Optional[datetime]
    center_lat: Optional[float]
    center_lon: Optional[float]
    scores: RegionScores
    composite_risk: float
    incident_count: Optional[int] = 0
    indicator_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class IndicatorSummary(BaseModel):
    id: UUID
    name: str
    domain: str
    value: float
    delta_24h: Optional[float]
    delta_7d: Optional[float]
    confidence: float
    trend: str
    
    class Config:
        from_attributes = True


class RegionListResponse(BaseModel):
    regions: List[RegionSummary]
    total: int
    by_status: dict


@router.get("", response_model=RegionListResponse)
async def list_regions(
    status: Optional[str] = None,
    region_type: Optional[str] = None,
    parent_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """List regions with filtering."""
    query = db.query(Region)
    
    if status:
        try:
            query = query.filter(Region.status == RegionStatus(status))
        except ValueError:
            pass
    
    if region_type:
        try:
            query = query.filter(Region.region_type == RegionType(region_type))
        except ValueError:
            pass
    
    if parent_id:
        query = query.filter(Region.parent_id == parent_id)
    
    regions = query.order_by(Region.name).all()
    
    # Count by status
    status_counts = {
        "green": sum(1 for r in regions if r.status == RegionStatus.GREEN),
        "yellow": sum(1 for r in regions if r.status == RegionStatus.YELLOW),
        "red": sum(1 for r in regions if r.status == RegionStatus.RED)
    }
    
    return RegionListResponse(
        regions=[
            RegionSummary(
                id=r.id,
                name=r.name,
                iso_code=r.iso_code,
                region_type=r.region_type.value,
                status=r.status.value,
                composite_risk=r.composite_risk_score
            )
            for r in regions
        ],
        total=len(regions),
        by_status=status_counts
    )


@router.get("/critical", response_model=List[RegionSummary])
async def get_critical_regions(db: Session = Depends(get_db)):
    """Get all RED status regions."""
    regions = region_state_service.get_critical_regions(db)
    return [
        RegionSummary(
            id=r.id,
            name=r.name,
            iso_code=r.iso_code,
            region_type=r.region_type.value,
            status=r.status.value,
            composite_risk=r.composite_risk_score
        )
        for r in regions
    ]


@router.get("/elevated", response_model=List[RegionSummary])
async def get_elevated_regions(db: Session = Depends(get_db)):
    """Get all YELLOW status regions."""
    regions = region_state_service.get_elevated_regions(db)
    return [
        RegionSummary(
            id=r.id,
            name=r.name,
            iso_code=r.iso_code,
            region_type=r.region_type.value,
            status=r.status.value,
            composite_risk=r.composite_risk_score
        )
        for r in regions
    ]


@router.get("/{region_id}", response_model=RegionDetail)
async def get_region(
    region_id: UUID,
    db: Session = Depends(get_db)
):
    """Get single region with full details."""
    region = db.query(Region).filter(Region.id == region_id).first()
    
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Get counts
    from backend.models.event import Event
    incident_count = db.query(Event).filter(Event.region_id == region_id).count()
    indicator_count = db.query(Indicator).filter(Indicator.region_id == region_id).count()
    
    return RegionDetail(
        id=region.id,
        name=region.name,
        iso_code=region.iso_code,
        region_type=region.region_type.value,
        status=region.status.value,
        status_reason=region.status_reason,
        status_updated_at=region.status_updated_at,
        center_lat=region.center_lat,
        center_lon=region.center_lon,
        scores=RegionScores(
            physical=region.physical_state_score,
            migration=region.migration_pressure_score,
            security=region.security_stability_score,
            socioeconomic=region.socioeconomic_stress_score,
            information_reliability=region.information_reliability_score
        ),
        composite_risk=region.composite_risk_score,
        incident_count=incident_count,
        indicator_count=indicator_count
    )


@router.get("/{region_id}/indicators", response_model=List[IndicatorSummary])
async def get_region_indicators(
    region_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all indicators for a region."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    indicators = db.query(Indicator).filter(
        Indicator.region_id == region_id
    ).order_by(Indicator.domain, Indicator.name).all()
    
    return [
        IndicatorSummary(
            id=i.id,
            name=i.name,
            domain=i.domain.value,
            value=i.value,
            delta_24h=i.delta_24h,
            delta_7d=i.delta_7d,
            confidence=i.confidence,
            trend=i.trend_direction
        )
        for i in indicators
    ]


@router.post("/{region_id}/refresh")
async def refresh_region(
    region_id: UUID,
    db: Session = Depends(get_db)
):
    """Refresh region status from incidents and indicators."""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    old_status = region.status
    
    # Update from indicators and incidents
    region_state_service.update_region_from_indicators(region, db)
    changes = region_state_service.update_region_from_incidents(region, db)
    
    db.commit()
    
    return {
        "region_id": str(region_id),
        "old_status": old_status.value,
        "new_status": region.status.value,
        "changes": changes
    }


@router.post("/refresh-all")
async def refresh_all_regions():
    """Refresh status for all regions."""
    result = region_state_service.refresh_all_regions()
    return result
