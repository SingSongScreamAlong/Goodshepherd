"""
Reports router for generating and managing situational reports.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.models.report import Report, ReportType, ReportStatus
from backend.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


# Pydantic schemas
class ReportSummary(BaseModel):
    id: UUID
    report_type: str
    title: str
    status: str
    created_at: datetime
    published_at: Optional[datetime]
    incident_count: int
    
    class Config:
        from_attributes = True


class ReportDetail(BaseModel):
    id: UUID
    report_type: str
    title: str
    status: str
    executive_summary: Optional[str]
    narrative_markdown: Optional[str]
    key_developments: Optional[List[dict]]
    areas_to_watch: Optional[List[dict]]
    forward_outlook: Optional[str]
    confidence_notes: Optional[str]
    included_incident_ids: Optional[List[str]]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime
    published_at: Optional[datetime]
    pdf_url: Optional[str]
    docx_url: Optional[str]
    
    class Config:
        from_attributes = True


class CreateDailySitrepRequest(BaseModel):
    title: Optional[str] = None
    region_ids: Optional[List[UUID]] = None


class CreateWeeklyBriefRequest(BaseModel):
    title: Optional[str] = None
    region_ids: Optional[List[UUID]] = None


class ReportListResponse(BaseModel):
    reports: List[ReportSummary]
    total: int


@router.get("", response_model=ReportListResponse)
async def list_reports(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List reports with filtering."""
    query = db.query(Report)
    
    if report_type:
        try:
            query = query.filter(Report.report_type == ReportType(report_type))
        except ValueError:
            pass
    
    if status:
        try:
            query = query.filter(Report.status == ReportStatus(status))
        except ValueError:
            pass
    
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).limit(limit).all()
    
    return ReportListResponse(
        reports=[
            ReportSummary(
                id=r.id,
                report_type=r.report_type.value,
                title=r.title,
                status=r.status.value,
                created_at=r.created_at,
                published_at=r.published_at,
                incident_count=len(r.included_incident_ids or [])
            )
            for r in reports
        ],
        total=total
    )


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """Get single report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportDetail(
        id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        status=report.status.value,
        executive_summary=report.executive_summary,
        narrative_markdown=report.narrative_markdown,
        key_developments=report.key_developments,
        areas_to_watch=report.areas_to_watch,
        forward_outlook=report.forward_outlook,
        confidence_notes=report.confidence_notes,
        included_incident_ids=report.included_incident_ids,
        period_start=report.period_start,
        period_end=report.period_end,
        created_at=report.created_at,
        published_at=report.published_at,
        pdf_url=report.pdf_url,
        docx_url=report.docx_url
    )


@router.post("/daily-sitrep", response_model=ReportSummary)
async def create_daily_sitrep(
    request: CreateDailySitrepRequest,
    db: Session = Depends(get_db)
):
    """Generate a new Daily SITREP."""
    # TODO: Get actual user ID from auth
    author_id = UUID('00000000-0000-0000-0000-000000000000')
    
    report = report_service.generate_daily_sitrep(
        author_id=author_id,
        region_scope=request.region_ids,
        title=request.title
    )
    
    return ReportSummary(
        id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        status=report.status.value,
        created_at=report.created_at,
        published_at=report.published_at,
        incident_count=len(report.included_incident_ids or [])
    )


@router.post("/weekly-brief", response_model=ReportSummary)
async def create_weekly_brief(
    request: CreateWeeklyBriefRequest,
    db: Session = Depends(get_db)
):
    """Generate a new Weekly Brief."""
    author_id = UUID('00000000-0000-0000-0000-000000000000')
    
    report = report_service.generate_weekly_brief(
        author_id=author_id,
        region_scope=request.region_ids,
        title=request.title
    )
    
    return ReportSummary(
        id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        status=report.status.value,
        created_at=report.created_at,
        published_at=report.published_at,
        incident_count=len(report.included_incident_ids or [])
    )


@router.post("/{report_id}/publish")
async def publish_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """Publish a report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.publish()
    db.commit()
    
    return {"status": "published", "report_id": str(report_id)}


@router.get("/{report_id}/export/{format}")
async def export_report(
    report_id: UUID,
    format: str,
    db: Session = Depends(get_db)
):
    """Export report in specified format (pdf/docx)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")
    
    # TODO: Implement actual export logic
    # For now, return placeholder
    return {
        "report_id": str(report_id),
        "format": format,
        "status": "pending",
        "message": "Export functionality will be implemented with weasyprint/python-docx"
    }
