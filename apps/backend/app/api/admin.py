from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..db.session import get_db
from ..models import Country, Carrier, Plan, User
from ..schemas.catalog import CountryRead, CarrierRead, PlanRead
from ..schemas.admin import (
    CountryCreate,
    CountryUpdate,
    CarrierCreate,
    CarrierUpdate,
    PlanCreate,
    PlanUpdate,
    PaginatedResponse,
)
from .auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ========================================
# Countries CRUD
# ========================================

@router.get("/countries", response_model=PaginatedResponse)
def list_countries(
    q: str = Query("", description="Search by name or ISO2"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field: name, iso2"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all countries with search, sorting, and pagination (admin only)."""
    query = db.query(Country)
    
    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Country.name.ilike(search_term),
                Country.iso2.ilike(search_term),
            )
        )
    
    # Count total
    total = query.count()
    
    # Sorting
    sort_column = getattr(Country, sort_by, Country.name)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    return {
        "items": [CountryRead.from_orm(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/countries", response_model=CountryRead, status_code=status.HTTP_201_CREATED)
def create_country(
    payload: CountryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new country (admin only)."""
    # Validate ISO2 uppercase
    iso2 = payload.iso2.upper()
    if len(iso2) != 2 or not iso2.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISO2 must be exactly 2 uppercase letters"
        )
    
    # Check for duplicate
    existing = db.query(Country).filter(Country.iso2 == iso2).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Country with ISO2 '{iso2}' already exists"
        )
    
    country = Country(iso2=iso2, name=payload.name)
    db.add(country)
    db.commit()
    db.refresh(country)
    
    return CountryRead.from_orm(country)


@router.put("/countries/{country_id}", response_model=CountryRead)
def update_country(
    country_id: int,
    payload: CountryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update an existing country (admin only)."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Update ISO2 if provided
    if payload.iso2 is not None:
        iso2 = payload.iso2.upper()
        if len(iso2) != 2 or not iso2.isalpha():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ISO2 must be exactly 2 uppercase letters"
            )
        
        # Check for duplicate (excluding current country)
        existing = db.query(Country).filter(
            Country.iso2 == iso2,
            Country.id != country_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Country with ISO2 '{iso2}' already exists"
            )
        
        country.iso2 = iso2  # type: ignore
    
    # Update name if provided
    if payload.name is not None:
        country.name = payload.name  # type: ignore
    
    db.commit()
    db.refresh(country)
    
    return CountryRead.from_orm(country)


@router.delete("/countries/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country(
    country_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a country (admin only). Fails if referenced by plans."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Check for dependent plans
    plans_count = db.query(func.count(Plan.id)).filter(Plan.country_id == country_id).scalar()
    if plans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete country: {plans_count} plan(s) reference it"
        )
    
    db.delete(country)
    db.commit()


# ========================================
# Carriers CRUD
# ========================================

@router.get("/carriers", response_model=PaginatedResponse)
def list_carriers(
    q: str = Query("", description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all carriers with search and pagination (admin only)."""
    query = db.query(Carrier)
    
    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(Carrier.name.ilike(search_term))
    
    # Count total
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(Carrier.name).offset(offset).limit(page_size).all()
    
    return {
        "items": [CarrierRead.from_orm(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/carriers", response_model=CarrierRead, status_code=status.HTTP_201_CREATED)
def create_carrier(
    payload: CarrierCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new carrier (admin only)."""
    # Validate name
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrier name cannot be empty"
        )
    
    # Check for duplicate
    existing = db.query(Carrier).filter(Carrier.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Carrier '{payload.name}' already exists"
        )
    
    carrier = Carrier(name=payload.name)
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    
    return CarrierRead.from_orm(carrier)


@router.put("/carriers/{carrier_id}", response_model=CarrierRead)
def update_carrier(
    carrier_id: int,
    payload: CarrierUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update an existing carrier (admin only)."""
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    
    # Update name if provided
    if payload.name is not None:
        if not payload.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Carrier name cannot be empty"
            )
        
        # Check for duplicate (excluding current carrier)
        existing = db.query(Carrier).filter(
            Carrier.name == payload.name,
            Carrier.id != carrier_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Carrier '{payload.name}' already exists"
            )
        
        carrier.name = payload.name  # type: ignore
    
    db.commit()
    db.refresh(carrier)
    
    return CarrierRead.from_orm(carrier)


@router.delete("/carriers/{carrier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a carrier (admin only). Fails if referenced by plans."""
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    
    # Check for dependent plans
    plans_count = db.query(func.count(Plan.id)).filter(Plan.carrier_id == carrier_id).scalar()
    if plans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete carrier: {plans_count} plan(s) reference it"
        )
    
    db.delete(carrier)
    db.commit()


# ========================================
# Plans CRUD
# ========================================

@router.get("/plans", response_model=PaginatedResponse)
def list_plans(
    q: str = Query("", description="Search by name"),
    country_id: int | None = Query(None, description="Filter by country ID"),
    carrier_id: int | None = Query(None, description="Filter by carrier ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all plans with search, filters, and pagination (admin only)."""
    query = db.query(Plan)
    
    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(Plan.name.ilike(search_term))
    
    # Filters
    if country_id is not None:
        query = query.filter(Plan.country_id == country_id)
    
    if carrier_id is not None:
        query = query.filter(Plan.carrier_id == carrier_id)
    
    # Count total
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    items = query.order_by(Plan.name).offset(offset).limit(page_size).all()
    
    return {
        "items": [PlanRead.from_orm(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new plan (admin only)."""
    # Validate price
    if payload.price_usd < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be non-negative"
        )
    
    # Validate duration
    if payload.duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be positive"
        )
    
    # Validate country exists
    country = db.query(Country).filter(Country.id == payload.country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {payload.country_id} not found"
        )
    
    # Validate carrier exists
    carrier = db.query(Carrier).filter(Carrier.id == payload.carrier_id).first()
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carrier with ID {payload.carrier_id} not found"
        )
    
    plan = Plan(
        country_id=payload.country_id,
        carrier_id=payload.carrier_id,
        name=payload.name,
        data_gb=payload.data_gb,
        duration_days=payload.duration_days,
        price_usd=payload.price_usd,
        description=payload.description,
        is_unlimited=payload.is_unlimited,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return PlanRead.from_orm(plan)


@router.put("/plans/{plan_id}", response_model=PlanRead)
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update an existing plan (admin only)."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Validate and update country_id
    if payload.country_id is not None:
        country = db.query(Country).filter(Country.id == payload.country_id).first()
        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country with ID {payload.country_id} not found"
            )
        plan.country_id = payload.country_id  # type: ignore
    
    # Validate and update carrier_id
    if payload.carrier_id is not None:
        carrier = db.query(Carrier).filter(Carrier.id == payload.carrier_id).first()
        if not carrier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Carrier with ID {payload.carrier_id} not found"
            )
        plan.carrier_id = payload.carrier_id  # type: ignore
    
    # Update other fields
    if payload.name is not None:
        plan.name = payload.name  # type: ignore
    
    if payload.data_gb is not None:
        plan.data_gb = payload.data_gb  # type: ignore
    
    if payload.duration_days is not None:
        if payload.duration_days <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be positive"
            )
        plan.duration_days = payload.duration_days  # type: ignore
    
    if payload.price_usd is not None:
        if payload.price_usd < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be non-negative"
            )
        plan.price_usd = payload.price_usd  # type: ignore
    
    if payload.description is not None:
        plan.description = payload.description  # type: ignore
    
    if payload.is_unlimited is not None:
        plan.is_unlimited = payload.is_unlimited  # type: ignore
    
    db.commit()
    db.refresh(plan)
    
    return PlanRead.from_orm(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a plan (admin only)."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Note: Could add check for orders referencing this plan
    # For now, allow deletion (orders will retain plan_id as historical data)
    
    db.delete(plan)
    db.commit()
