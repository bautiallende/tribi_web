from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..db.session import get_db
from ..models import Country, Plan
from ..schemas import CountryRead, PlanRead, PlanDetail

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/countries", response_model=list[CountryRead])
def get_countries(
    q: str = Query("", description="Search by name or ISO2 prefix"),
    db: Session = Depends(get_db),
):
    """
    Get countries with optional search filter.
    Filter by q: searches in name or iso2 (case-insensitive prefix match).
    """
    query = db.query(Country)

    if q:
        search_term = f"{q}%"
        query = query.filter(
            or_(
                Country.name.ilike(search_term),
                Country.iso2.ilike(search_term),
            )
        )

    return query.order_by(Country.name).all()


@router.get("/plans", response_model=list[PlanRead])
def get_plans(
    country: str | None = Query(None, description="Filter by country ISO2"),
    min_gb: float | None = Query(None, description="Min data GB"),
    max_gb: float | None = Query(None, description="Max data GB"),
    max_price: float | None = Query(None, description="Max price USD"),
    days: int | None = Query(None, description="Duration in days"),
    db: Session = Depends(get_db),
):
    """
    Get plans with optional filters.
    Filters: country (ISO2), min_gb, max_gb, max_price, days.
    Results ordered by price ascending.
    """
    query = db.query(Plan)

    if country:
        country_obj = db.query(Country).filter(Country.iso2.ilike(country)).first()
        if country_obj:
            query = query.filter(Plan.country_id == country_obj.id)

    if min_gb is not None:
        query = query.filter(Plan.data_gb >= min_gb)

    if max_gb is not None:
        query = query.filter(Plan.data_gb <= max_gb)

    if max_price is not None:
        query = query.filter(Plan.price_usd <= max_price)

    if days is not None:
        query = query.filter(Plan.duration_days == days)

    return query.order_by(Plan.price_usd).all()


@router.get("/plans/{plan_id}", response_model=PlanDetail)
def get_plan_detail(plan_id: int, db: Session = Depends(get_db)):
    """Get plan detail by ID."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
