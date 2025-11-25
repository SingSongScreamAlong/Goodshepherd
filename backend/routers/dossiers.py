"""
API endpoints for dossiers and watchlists.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.core.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.dossier import Dossier, Watchlist, DossierType
from backend.schemas.dossier import (
    DossierCreate, DossierUpdate, DossierResponse, DossierStats,
    WatchlistCreate, WatchlistUpdate, WatchlistResponse, WatchlistWithDossiers
)
from backend.services.dossier_service import DossierService

router = APIRouter(prefix="/dossiers", tags=["dossiers"])
watchlist_router = APIRouter(prefix="/watchlists", tags=["watchlists"])


# ===== Dossier Endpoints =====

@router.get("", response_model=List[DossierResponse])
def list_dossiers(
    dossier_type: Optional[DossierType] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all dossiers for the user's organization."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    query = db.query(Dossier).filter(Dossier.organization_id == org_id)

    if dossier_type:
        query = query.filter(Dossier.dossier_type == dossier_type)

    if search:
        query = query.filter(Dossier.name.ilike(f'%{search}%'))

    dossiers = query.order_by(Dossier.updated_at.desc()).limit(limit).offset(offset).all()
    return dossiers


@router.post("", response_model=DossierResponse, status_code=201)
def create_dossier(
    dossier_data: DossierCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    # Check for duplicate name
    existing = db.query(Dossier).filter(
        Dossier.organization_id == org_id,
        Dossier.name == dossier_data.name,
        Dossier.dossier_type == dossier_data.dossier_type
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dossier with name '{dossier_data.name}' and type '{dossier_data.dossier_type}' already exists"
        )

    dossier = Dossier(
        organization_id=org_id,
        **dossier_data.model_dump()
    )

    db.add(dossier)
    db.commit()
    db.refresh(dossier)

    # Update statistics
    service = DossierService(db)
    service.update_dossier_stats(dossier.id)

    db.refresh(dossier)
    return dossier


@router.get("/{dossier_id}", response_model=DossierResponse)
def get_dossier(
    dossier_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    dossier = db.query(Dossier).filter(
        Dossier.id == dossier_id,
        Dossier.organization_id == org_id
    ).first()

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    return dossier


@router.patch("/{dossier_id}", response_model=DossierResponse)
def update_dossier(
    dossier_id: UUID,
    dossier_data: DossierUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    dossier = db.query(Dossier).filter(
        Dossier.id == dossier_id,
        Dossier.organization_id == org_id
    ).first()

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Update fields
    update_data = dossier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dossier, field, value)

    db.commit()
    db.refresh(dossier)

    return dossier


@router.delete("/{dossier_id}", status_code=204)
def delete_dossier(
    dossier_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    dossier = db.query(Dossier).filter(
        Dossier.id == dossier_id,
        Dossier.organization_id == org_id
    ).first()

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    db.delete(dossier)
    db.commit()


@router.get("/{dossier_id}/stats", response_model=DossierStats)
def get_dossier_statistics(
    dossier_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    dossier = db.query(Dossier).filter(
        Dossier.id == dossier_id,
        Dossier.organization_id == org_id
    ).first()

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    service = DossierService(db)
    stats = service.get_dossier_stats(dossier_id)

    return stats


@router.post("/{dossier_id}/refresh", response_model=DossierResponse)
def refresh_dossier_stats(
    dossier_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually refresh event statistics for a dossier."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    dossier = db.query(Dossier).filter(
        Dossier.id == dossier_id,
        Dossier.organization_id == org_id
    ).first()

    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    service = DossierService(db)
    service.update_dossier_stats(dossier_id)

    db.refresh(dossier)
    return dossier


# ===== Watchlist Endpoints =====

@watchlist_router.get("", response_model=List[WatchlistResponse])
def list_watchlists(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all watchlists for the current user."""
    query = db.query(Watchlist).filter(Watchlist.user_id == current_user.id)

    if is_active is not None:
        query = query.filter(Watchlist.is_active == (1 if is_active else 0))

    watchlists = query.order_by(Watchlist.updated_at.desc()).all()

    # Add dossier count to each watchlist
    result = []
    for wl in watchlists:
        wl_dict = WatchlistResponse.model_validate(wl).model_dump()
        wl_dict['dossier_count'] = len(wl.dossiers)
        result.append(WatchlistResponse(**wl_dict))

    return result


@watchlist_router.post("", response_model=WatchlistResponse, status_code=201)
def create_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new watchlist."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    watchlist = Watchlist(
        organization_id=org_id,
        user_id=current_user.id,
        name=watchlist_data.name,
        description=watchlist_data.description,
        priority=watchlist_data.priority,
        is_active=1 if watchlist_data.is_active else 0,
        notification_enabled=1 if watchlist_data.notification_enabled else 0
    )

    # Add dossiers
    if watchlist_data.dossier_ids:
        dossiers = db.query(Dossier).filter(
            Dossier.id.in_(watchlist_data.dossier_ids),
            Dossier.organization_id == org_id
        ).all()
        watchlist.dossiers = dossiers

    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    # Add dossier count
    response = WatchlistResponse.model_validate(watchlist).model_dump()
    response['dossier_count'] = len(watchlist.dossiers)
    return WatchlistResponse(**response)


@watchlist_router.get("/{watchlist_id}", response_model=WatchlistWithDossiers)
def get_watchlist(
    watchlist_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific watchlist with full dossier details."""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Build response with dossiers
    response = WatchlistWithDossiers.model_validate(watchlist).model_dump()
    response['dossier_count'] = len(watchlist.dossiers)
    response['dossiers'] = [DossierResponse.model_validate(d) for d in watchlist.dossiers]
    return WatchlistWithDossiers(**response)


@watchlist_router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(
    watchlist_id: UUID,
    watchlist_data: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a watchlist."""
    if not current_user.organizations:
        raise HTTPException(status_code=400, detail="User not associated with any organization")

    org_id = current_user.organizations[0].id

    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Update fields
    update_data = watchlist_data.model_dump(exclude_unset=True, exclude={'dossier_ids'})
    for field, value in update_data.items():
        if field in ['is_active', 'notification_enabled']:
            setattr(watchlist, field, 1 if value else 0)
        else:
            setattr(watchlist, field, value)

    # Update dossiers if provided
    if watchlist_data.dossier_ids is not None:
        dossiers = db.query(Dossier).filter(
            Dossier.id.in_(watchlist_data.dossier_ids),
            Dossier.organization_id == org_id
        ).all()
        watchlist.dossiers = dossiers

    db.commit()
    db.refresh(watchlist)

    response = WatchlistResponse.model_validate(watchlist).model_dump()
    response['dossier_count'] = len(watchlist.dossiers)
    return WatchlistResponse(**response)


@watchlist_router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(
    watchlist_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a watchlist."""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).first()

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    db.delete(watchlist)
    db.commit()
