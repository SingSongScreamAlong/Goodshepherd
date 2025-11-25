"""
Dashboard API endpoints for analytics and summaries.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.event import Event, EventCategory, SentimentEnum
from backend.models.dossier import Dossier

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall dashboard summary with key metrics.
    Returns today's activity, trends, and highlights.
    """
    if not current_user.organizations:
        return {"error": "User not associated with any organization"}

    org_id = current_user.organizations[0].id
    now = datetime.utcnow()

    # Time periods
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # Total events
    total_events = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id
    ).scalar() or 0

    # Events today
    events_today = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id,
        Event.timestamp >= today_start
    ).scalar() or 0

    # Events this week
    events_week = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id,
        Event.timestamp >= week_start
    ).scalar() or 0

    # Events this month
    events_month = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id,
        Event.timestamp >= month_start
    ).scalar() or 0

    # High relevance events today
    high_relevance_today = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id,
        Event.timestamp >= today_start,
        Event.relevance_score >= 0.7
    ).scalar() or 0

    # Category distribution (last 7 days)
    category_results = db.query(
        Event.category,
        func.count(Event.event_id)
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= week_start
    ).group_by(Event.category).all()

    category_distribution = {
        cat.value: count for cat, count in category_results if cat
    }

    # Sentiment distribution (last 7 days)
    sentiment_results = db.query(
        Event.sentiment,
        func.count(Event.event_id)
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= week_start,
        Event.sentiment.isnot(None)
    ).group_by(Event.sentiment).all()

    sentiment_distribution = {
        sent.value: count for sent, count in sentiment_results if sent
    }

    # Most active locations (last 7 days)
    location_results = db.query(
        Event.location_name,
        func.count(Event.event_id)
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= week_start,
        Event.location_name.isnot(None)
    ).group_by(Event.location_name).order_by(
        func.count(Event.event_id).desc()
    ).limit(5).all()

    top_locations = [
        {"location": loc, "count": count}
        for loc, count in location_results
    ]

    # Total dossiers
    total_dossiers = db.query(func.count(Dossier.id)).filter(
        Dossier.organization_id == org_id
    ).scalar() or 0

    # Active dossiers (with events in last 7 days)
    active_dossiers = db.query(func.count(Dossier.id)).filter(
        Dossier.organization_id == org_id,
        Dossier.last_event_timestamp >= week_start
    ).scalar() or 0

    # Recent high-priority events
    high_priority = db.query(Event).filter(
        Event.organization_id == org_id,
        Event.timestamp >= today_start,
        Event.relevance_score >= 0.7
    ).order_by(Event.timestamp.desc()).limit(5).all()

    recent_highlights = [
        {
            "event_id": str(e.event_id),
            "summary": e.summary,
            "category": e.category.value if e.category else None,
            "relevance_score": e.relevance_score,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in high_priority
    ]

    return {
        "timestamp": now.isoformat(),
        "total_events": total_events,
        "events_today": events_today,
        "events_week": events_week,
        "events_month": events_month,
        "high_relevance_today": high_relevance_today,
        "category_distribution": category_distribution,
        "sentiment_distribution": sentiment_distribution,
        "top_locations": top_locations,
        "total_dossiers": total_dossiers,
        "active_dossiers": active_dossiers,
        "recent_highlights": recent_highlights,
    }


@router.get("/trends")
def get_trends(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get event trends over time.
    Returns daily event counts, category trends, and sentiment trends.
    """
    if not current_user.organizations:
        return {"error": "User not associated with any organization"}

    org_id = current_user.organizations[0].id
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Daily event counts
    daily_results = db.query(
        func.date(Event.timestamp).label('date'),
        func.count(Event.event_id).label('count')
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= start_date
    ).group_by(func.date(Event.timestamp)).order_by('date').all()

    daily_counts = [
        {"date": str(date), "count": count}
        for date, count in daily_results
    ]

    # Category trends
    category_daily = db.query(
        func.date(Event.timestamp).label('date'),
        Event.category,
        func.count(Event.event_id).label('count')
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= start_date
    ).group_by(func.date(Event.timestamp), Event.category).all()

    category_trends = defaultdict(list)
    for date, category, count in category_daily:
        if category:
            category_trends[category.value].append({
                "date": str(date),
                "count": count
            })

    # Sentiment trends
    sentiment_daily = db.query(
        func.date(Event.timestamp).label('date'),
        Event.sentiment,
        func.count(Event.event_id).label('count')
    ).filter(
        Event.organization_id == org_id,
        Event.timestamp >= start_date,
        Event.sentiment.isnot(None)
    ).group_by(func.date(Event.timestamp), Event.sentiment).all()

    sentiment_trends = defaultdict(list)
    for date, sentiment, count in sentiment_daily:
        if sentiment:
            sentiment_trends[sentiment.value].append({
                "date": str(date),
                "count": count
            })

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "daily_counts": daily_counts,
        "category_trends": dict(category_trends),
        "sentiment_trends": dict(sentiment_trends),
    }


@router.get("/category-analysis")
def get_category_analysis(
    category: EventCategory = Query(...),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis for a specific category.
    """
    if not current_user.organizations:
        return {"error": "User not associated with any organization"}

    org_id = current_user.organizations[0].id
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Total events in category
    total = db.query(func.count(Event.event_id)).filter(
        Event.organization_id == org_id,
        Event.category == category,
        Event.timestamp >= start_date
    ).scalar() or 0

    # Sentiment breakdown
    sentiment_results = db.query(
        Event.sentiment,
        func.count(Event.event_id)
    ).filter(
        Event.organization_id == org_id,
        Event.category == category,
        Event.timestamp >= start_date,
        Event.sentiment.isnot(None)
    ).group_by(Event.sentiment).all()

    sentiment_breakdown = {
        sent.value: count for sent, count in sentiment_results if sent
    }

    # Top locations
    location_results = db.query(
        Event.location_name,
        func.count(Event.event_id)
    ).filter(
        Event.organization_id == org_id,
        Event.category == category,
        Event.timestamp >= start_date,
        Event.location_name.isnot(None)
    ).group_by(Event.location_name).order_by(
        func.count(Event.event_id).desc()
    ).limit(10).all()

    top_locations = [
        {"location": loc, "count": count}
        for loc, count in location_results
    ]

    # Average relevance
    avg_relevance = db.query(func.avg(Event.relevance_score)).filter(
        Event.organization_id == org_id,
        Event.category == category,
        Event.timestamp >= start_date,
        Event.relevance_score.isnot(None)
    ).scalar() or 0.0

    return {
        "category": category.value,
        "period_days": days,
        "total_events": total,
        "sentiment_breakdown": sentiment_breakdown,
        "top_locations": top_locations,
        "average_relevance": round(float(avg_relevance), 2),
    }
