import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..db.session import get_db
from ..models import (
    Carrier,
    Country,
    EsimInventory,
    EsimProfile,
    Invoice,
    Order,
    Payment,
    Plan,
    SupportTicket,
    SupportTicketAudit,
    User,
)
from ..models.auth_models import (
    EsimInventoryStatus,
    EsimStatus,
    OrderStatus,
    PaymentStatus,
    SupportTicketEventType,
    SupportTicketPriority,
    SupportTicketStatus,
)
from ..schemas.admin import (
    AdminEsimProfileRead,
    AdminInventoryRead,
    AdminInventoryStats,
    AdminOrderRead,
    AdminPaymentRead,
    AdminStockAlert,
    AdminUserDetail,
    AdminUserSummary,
    AnalyticsOverviewResponse,
    AnalyticsProjectionResponse,
    AnalyticsTimeseriesResponse,
    CarrierCreate,
    CarrierUpdate,
    CountryCreate,
    CountryUpdate,
    PaginatedResponse,
    PlanCreate,
    PlanUpdate,
    SupportTicketAuditRead,
    SupportTicketCreate,
    SupportTicketRead,
    SupportTicketUpdate,
    UserNotesUpdate,
)
from ..schemas.catalog import CarrierRead, CountryRead, PlanRead
from ..services import (
    AnalyticsEventType,
    get_overview_metrics,
    get_projections,
    get_timeseries,
)
from ..services.billing import build_sales_export_csv
from ..services.support import get_support_automation_service
from .auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])
support_automation = get_support_automation_service()


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
    _: User = Depends(get_current_admin),
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
        "items": [CountryRead.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post(
    "/countries", response_model=CountryRead, status_code=status.HTTP_201_CREATED
)
def create_country(
    payload: CountryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create a new country (admin only)."""
    # Validate ISO2 uppercase
    iso2 = payload.iso2.upper()
    if len(iso2) != 2 or not iso2.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISO2 must be exactly 2 uppercase letters",
        )

    # Check for duplicate
    existing = db.query(Country).filter(Country.iso2 == iso2).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Country with ISO2 '{iso2}' already exists",
        )

    country = Country(iso2=iso2, name=payload.name)
    db.add(country)
    db.commit()
    db.refresh(country)

    return CountryRead.model_validate(country)


@router.put("/countries/{country_id}", response_model=CountryRead)
def update_country(
    country_id: int,
    payload: CountryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
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
                detail="ISO2 must be exactly 2 uppercase letters",
            )

        # Check for duplicate (excluding current country)
        existing = (
            db.query(Country)
            .filter(Country.iso2 == iso2, Country.id != country_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Country with ISO2 '{iso2}' already exists",
            )

        country.iso2 = iso2  # type: ignore

    # Update name if provided
    if payload.name is not None:
        country.name = payload.name  # type: ignore

    db.commit()
    db.refresh(country)

    return CountryRead.model_validate(country)


@router.delete("/countries/{country_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_country(
    country_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Delete a country (admin only). Fails if referenced by plans."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Check for dependent plans
    plans_count = db.query(Plan).filter(Plan.country_id == country_id).count()
    if plans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete country: {plans_count} plan(s) reference it",
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
    sort_by: str = Query("name", description="Sort field: name, id"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all carriers with search, sorting, and pagination (admin only)."""
    query = db.query(Carrier)

    # Search
    if q:
        search_term = f"%{q}%"
        query = query.filter(Carrier.name.ilike(search_term))

    # Count total
    total = query.count()

    # Sorting
    sort_column = getattr(Carrier, sort_by, Carrier.name)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)

    # Paginate
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": [CarrierRead.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post(
    "/carriers", response_model=CarrierRead, status_code=status.HTTP_201_CREATED
)
def create_carrier(
    payload: CarrierCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create a new carrier (admin only)."""
    # Validate name
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrier name cannot be empty",
        )

    # Check for duplicate
    existing = db.query(Carrier).filter(Carrier.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Carrier '{payload.name}' already exists",
        )

    carrier = Carrier(name=payload.name)
    db.add(carrier)
    db.commit()
    db.refresh(carrier)

    return CarrierRead.model_validate(carrier)


@router.put("/carriers/{carrier_id}", response_model=CarrierRead)
def update_carrier(
    carrier_id: int,
    payload: CarrierUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
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
                detail="Carrier name cannot be empty",
            )

        # Check for duplicate (excluding current carrier)
        existing = (
            db.query(Carrier)
            .filter(Carrier.name == payload.name, Carrier.id != carrier_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Carrier '{payload.name}' already exists",
            )

        carrier.name = payload.name  # type: ignore

    db.commit()
    db.refresh(carrier)

    return CarrierRead.model_validate(carrier)


@router.delete("/carriers/{carrier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Delete a carrier (admin only). Fails if referenced by plans."""
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    # Check for dependent plans
    plans_count = db.query(Plan).filter(Plan.carrier_id == carrier_id).count()
    if plans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete carrier: {plans_count} plan(s) reference it",
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
    sort_by: str = Query(
        "name", description="Sort field: name, price_usd, duration_days, data_gb"
    ),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """List all plans with search, filters, sorting, and pagination (admin only)."""
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

    # Sorting
    sort_column = getattr(Plan, sort_by, Plan.name)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)

    # Paginate
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": [PlanRead.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Create a new plan (admin only)."""
    # Validate price
    if payload.price_usd < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be non-negative"
        )

    # Validate duration
    if payload.duration_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Duration must be positive"
        )

    # Validate country exists
    country = db.query(Country).filter(Country.id == payload.country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {payload.country_id} not found",
        )

    # Validate carrier exists
    carrier = db.query(Carrier).filter(Carrier.id == payload.carrier_id).first()
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carrier with ID {payload.carrier_id} not found",
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

    return PlanRead.model_validate(plan)


@router.put("/plans/{plan_id}", response_model=PlanRead)
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
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
                detail=f"Country with ID {payload.country_id} not found",
            )
        plan.country_id = payload.country_id  # type: ignore

    # Validate and update carrier_id
    if payload.carrier_id is not None:
        carrier = db.query(Carrier).filter(Carrier.id == payload.carrier_id).first()
        if not carrier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Carrier with ID {payload.carrier_id} not found",
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
                detail="Duration must be positive",
            )
        plan.duration_days = payload.duration_days  # type: ignore

    if payload.price_usd is not None:
        if payload.price_usd < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be non-negative",
            )
        plan.price_usd = payload.price_usd  # type: ignore

    if payload.description is not None:
        plan.description = payload.description  # type: ignore

    if payload.is_unlimited is not None:
        plan.is_unlimited = payload.is_unlimited  # type: ignore

    db.commit()
    db.refresh(plan)

    return PlanRead.model_validate(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Delete a plan (admin only)."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Note: Could add check for orders referencing this plan
    # For now, allow deletion (orders will retain plan_id as historical data)

    db.delete(plan)
    db.commit()


# ========================================
# CSV Import/Export for Plans
# ========================================


@router.get("/plans/export")
async def export_plans_csv(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Export all plans to CSV (admin only)."""
    plans = db.query(Plan).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "id",
            "name",
            "country_id",
            "carrier_id",
            "data_gb",
            "is_unlimited",
            "duration_days",
            "price_usd",
            "description",
        ]
    )

    # Write data
    for plan in plans:
        writer.writerow(
            [
                plan.id,
                plan.name,
                plan.country_id,
                plan.carrier_id,
                str(plan.data_gb),
                plan.is_unlimited,
                plan.duration_days,
                str(plan.price_usd),
                plan.description or "",
            ]
        )

    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=plans_export.csv"},
    )


@router.post("/plans/import")
async def import_plans_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Import plans from CSV (admin only)."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV"
        )

    # Read CSV
    contents = await file.read()
    csv_text = contents.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_text))

    created_count = 0
    updated_count = 0
    errors = []

    for row_num, row in enumerate(
        csv_reader, start=2
    ):  # start=2 because row 1 is header
        try:
            # Validate required fields
            required = [
                "name",
                "country_id",
                "carrier_id",
                "data_gb",
                "duration_days",
                "price_usd",
            ]
            missing = [f for f in required if not row.get(f)]
            if missing:
                errors.append(f"Row {row_num}: Missing fields: {', '.join(missing)}")
                continue

            # Parse data
            plan_data = {
                "name": row["name"].strip(),
                "country_id": int(row["country_id"]),
                "carrier_id": int(row["carrier_id"]),
                "data_gb": Decimal(row["data_gb"]),
                "is_unlimited": row.get("is_unlimited", "false").lower()
                in ("true", "1", "yes"),
                "duration_days": int(row["duration_days"]),
                "price_usd": Decimal(row["price_usd"]),
                "description": row.get("description", "").strip() or None,
            }

            # Validate country exists
            country = (
                db.query(Country).filter(Country.id == plan_data["country_id"]).first()
            )
            if not country:
                errors.append(
                    f"Row {row_num}: Country ID {plan_data['country_id']} not found"
                )
                continue

            # Validate carrier exists
            carrier = (
                db.query(Carrier).filter(Carrier.id == plan_data["carrier_id"]).first()
            )
            if not carrier:
                errors.append(
                    f"Row {row_num}: Carrier ID {plan_data['carrier_id']} not found"
                )
                continue

            # Check if plan exists (by id if provided, or create new)
            plan_id = row.get("id")
            if plan_id and plan_id.strip():
                # Update existing
                plan = db.query(Plan).filter(Plan.id == int(plan_id)).first()
                if plan:
                    for key, value in plan_data.items():
                        setattr(plan, key, value)
                    updated_count += 1
                else:
                    errors.append(
                        f"Row {row_num}: Plan ID {plan_id} not found for update"
                    )
                    continue
            else:
                # Create new
                plan = Plan(**plan_data)
                db.add(plan)
                created_count += 1

        except ValueError as exc:
            errors.append(f"Row {row_num}: Invalid data format - {exc}")
        except (KeyError, TypeError) as exc:
            errors.append(f"Row {row_num}: Missing or invalid column - {exc}")
        except SQLAlchemyError as exc:
            errors.append(f"Row {row_num}: Database error - {exc}")

    # Commit if no errors
    if not errors:
        db.commit()
        return {
            "success": True,
            "created": created_count,
            "updated": updated_count,
            "errors": [],
        }
    else:
        db.rollback()
        return {
            "success": False,
            "created": 0,
            "updated": 0,
            "errors": errors[:10],  # Limit to first 10 errors
        }


# ========================================
# Orders & Payments Management
# ========================================


@router.get("/orders", response_model=PaginatedResponse)
def list_orders(
    order_status: str | None = Query(None, description="Filter by order status"),
    payment_status: str
    | None = Query(None, description="Filter by latest payment status"),
    user_q: str
    | None = Query(None, description="Search by user email or name (case-insensitive)"),
    plan_id: int | None = Query(None, description="Filter by plan ID"),
    start_date: datetime
    | None = Query(None, description="Filter orders created after this ISO datetime"),
    end_date: datetime
    | None = Query(None, description="Filter orders created before this ISO datetime"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "created_at", description="Sort field: created_at, amount, status"
    ),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.plan),
            joinedload(Order.esim_profile).joinedload(EsimProfile.inventory_item),
            joinedload(Order.payments),
        )
        .order_by(None)
    )

    if order_status:
        status_enum = _parse_enum(OrderStatus, order_status, "order status")
        query = query.filter(Order.status == status_enum)

    if payment_status:
        payment_enum = _parse_enum(PaymentStatus, payment_status, "payment status")
        query = query.filter(Order.payments.any(Payment.status == payment_enum))

    if user_q:
        search_term = f"%{user_q}%"
        query = query.filter(
            Order.user.has(
                or_(
                    User.email.ilike(search_term),
                    User.name.ilike(search_term),
                )
            )
        )

    if plan_id is not None:
        query = query.filter(Order.plan_id == plan_id)

    if start_date:
        query = query.filter(Order.created_at >= start_date)

    if end_date:
        query = query.filter(Order.created_at <= end_date)

    sort_map = {
        "created_at": Order.created_at,
        "amount": Order.amount_minor_units,
        "status": Order.status,
    }
    sort_column = sort_map.get(sort_by, Order.created_at)
    sort_expression = (
        sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc()
    )

    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(sort_expression).offset(offset).limit(page_size).all()

    payload = [_serialize_admin_order(order) for order in orders]

    return {
        "items": payload,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/orders/{order_id}", response_model=AdminOrderRead)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.plan),
            joinedload(Order.esim_profile).joinedload(EsimProfile.inventory_item),
            joinedload(Order.payments),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return _serialize_admin_order(order)


@router.get("/payments", response_model=PaginatedResponse)
def list_payments(
    provider: str | None = Query(None, description="Filter by provider"),
    payment_status: str | None = Query(None, description="Filter by status"),
    intent_q: str | None = Query(None, description="Search by intent ID"),
    order_id: int | None = Query(None, description="Filter by order ID"),
    start_date: datetime | None = Query(None, description="Created after"),
    end_date: datetime | None = Query(None, description="Created before"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = (
        db.query(Payment)
        .options(joinedload(Payment.order).joinedload(Order.user))
        .order_by(None)
    )

    if provider:
        provider_normalized = provider.upper()
        query = query.filter(func.upper(Payment.provider) == provider_normalized)

    if payment_status:
        status_enum = _parse_enum(PaymentStatus, payment_status, "payment status")
        query = query.filter(Payment.status == status_enum)

    if intent_q:
        search_term = f"%{intent_q}%"
        query = query.filter(Payment.intent_id.ilike(search_term))

    if order_id is not None:
        query = query.filter(Payment.order_id == order_id)

    if start_date:
        query = query.filter(Payment.created_at >= start_date)

    if end_date:
        query = query.filter(Payment.created_at <= end_date)

    sort_expression = (
        Payment.created_at.desc()
        if sort_order.lower() == "desc"
        else Payment.created_at.asc()
    )

    total = query.count()
    offset = (page - 1) * page_size
    payments = query.order_by(sort_expression).offset(offset).limit(page_size).all()

    items = [_serialize_admin_payment(payment) for payment in payments]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ========================================
# eSIM Profiles & Inventory
# ========================================


@router.get("/esims", response_model=PaginatedResponse)
def list_esim_profiles(
    esim_status: str | None = Query(None, description="Filter by eSIM status"),
    user_q: str | None = Query(None, description="Search by user email or name"),
    order_id: int | None = Query(None, description="Filter by order ID"),
    plan_id: int | None = Query(None, description="Filter by plan ID"),
    inventory_status: str
    | None = Query(None, description="Filter by associated inventory status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = (
        db.query(EsimProfile)
        .options(
            joinedload(EsimProfile.user),
            joinedload(EsimProfile.order).joinedload(Order.plan),
            joinedload(EsimProfile.inventory_item),
        )
        .order_by(None)
    )

    if esim_status:
        status_enum = _parse_enum(EsimStatus, esim_status, "esim status")
        query = query.filter(EsimProfile.status == status_enum)

    if user_q:
        search_term = f"%{user_q}%"
        query = query.filter(
            EsimProfile.user.has(
                or_(
                    User.email.ilike(search_term),
                    User.name.ilike(search_term),
                )
            )
        )

    if order_id is not None:
        query = query.filter(EsimProfile.order_id == order_id)

    if plan_id is not None:
        query = query.filter(EsimProfile.plan_id == plan_id)

    if inventory_status:
        inventory_enum = _parse_enum(
            EsimInventoryStatus, inventory_status, "inventory status"
        )
        query = query.filter(
            EsimProfile.inventory_item.has(EsimInventory.status == inventory_enum)
        )

    total = query.count()
    offset = (page - 1) * page_size
    profiles = (
        query.order_by(EsimProfile.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [_serialize_admin_esim(profile) for profile in profiles]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/inventory", response_model=PaginatedResponse)
def list_inventory(
    inventory_status: str
    | None = Query(None, description="Filter by inventory status"),
    plan_id: int | None = Query(None, description="Filter by plan ID"),
    carrier_id: int | None = Query(None, description="Filter by carrier ID"),
    country_id: int | None = Query(None, description="Filter by country ID"),
    q: str | None = Query(None, description="Search activation code or ICCID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query(
        "created_at", description="Sort field: created_at, status, plan_id"
    ),
    sort_order: str = Query("desc", description="Sort order"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(EsimInventory).order_by(None)

    if inventory_status:
        status_enum = _parse_enum(
            EsimInventoryStatus, inventory_status, "inventory status"
        )
        query = query.filter(EsimInventory.status == status_enum)

    if plan_id is not None:
        query = query.filter(EsimInventory.plan_id == plan_id)

    if carrier_id is not None:
        query = query.filter(EsimInventory.carrier_id == carrier_id)

    if country_id is not None:
        query = query.filter(EsimInventory.country_id == country_id)

    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                EsimInventory.activation_code.ilike(search_term),
                EsimInventory.iccid.ilike(search_term),
            )
        )

    sort_map = {
        "created_at": EsimInventory.created_at,
        "status": EsimInventory.status,
        "plan_id": EsimInventory.plan_id,
    }
    sort_column = sort_map.get(sort_by, EsimInventory.created_at)
    sort_expression = (
        sort_column.desc() if sort_order.lower() == "desc" else sort_column.asc()
    )

    total = query.count()
    offset = (page - 1) * page_size
    inventory_items = (
        query.order_by(sort_expression).offset(offset).limit(page_size).all()
    )

    items = [_serialize_inventory_item(item) for item in inventory_items]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/inventory/stats", response_model=AdminInventoryStats)
def inventory_stats(
    low_stock_threshold: int = Query(10, ge=1, le=1000, description="Alert threshold"),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    totals: dict[str, int] = {status.value: 0 for status in EsimInventoryStatus}
    status_counts: defaultdict[str, int] = defaultdict(int)
    for (status_value,) in db.query(EsimInventory.status).all():
        key = (
            status_value.value if hasattr(status_value, "value") else str(status_value)
        )
        status_counts[key] += 1
    for key, count in status_counts.items():
        totals[key] = count

    available_rows = (
        db.query(EsimInventory.plan_id, Plan.name)
        .join(Plan, Plan.id == EsimInventory.plan_id)
        .filter(EsimInventory.status == EsimInventoryStatus.AVAILABLE)
        .all()
    )
    plan_counts: Counter[int] = Counter()
    plan_names: dict[int, str] = {}
    for plan_id, plan_name in available_rows:
        if plan_id is None:
            continue
        plan_id_int = cast(int, plan_id)
        plan_counts[plan_id_int] += 1
        if plan_name is not None:
            plan_names[plan_id_int] = plan_name

    alerts = [
        AdminStockAlert(
            plan_id=plan_id,
            plan_name=plan_names.get(plan_id, "Unknown"),
            available=count,
        )
        for plan_id, count in plan_counts.items()
        if count <= low_stock_threshold
    ]
    alerts.sort(key=lambda alert: alert.available)

    return AdminInventoryStats(
        totals=totals,
        low_stock_threshold=low_stock_threshold,
        low_stock_alerts=alerts,
    )


@router.post("/inventory/import")
async def import_inventory_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV"
        )

    contents = await file.read()
    csv_text = contents.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_text))

    created = 0
    updated = 0
    errors: list[str] = []

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            activation_code = (row.get("activation_code") or "").strip()
            if not activation_code:
                errors.append(f"Row {row_num}: activation_code is required")
                continue

            status_value = row.get("status", "available").lower()
            status_enum = _parse_enum(
                EsimInventoryStatus, status_value, "inventory status"
            )

            plan_id = int(row["plan_id"]) if row.get("plan_id") else None
            carrier_id = int(row["carrier_id"]) if row.get("carrier_id") else None
            country_id = int(row["country_id"]) if row.get("country_id") else None

            inventory = (
                db.query(EsimInventory)
                .filter(EsimInventory.activation_code == activation_code)
                .first()
            )

            payload = {
                "plan_id": plan_id,
                "carrier_id": carrier_id,
                "country_id": country_id,
                "activation_code": activation_code,
                "iccid": (row.get("iccid") or None),
                "qr_payload": (row.get("qr_payload") or None),
                "instructions": (row.get("instructions") or None),
                "status": status_enum,
                "provider_reference": (row.get("provider_reference") or None),
            }

            if inventory:
                for key, value in payload.items():
                    setattr(inventory, key, value)
                updated += 1
            else:
                inventory = EsimInventory(**payload)
                db.add(inventory)
                created += 1

        except ValueError as exc:
            errors.append(f"Row {row_num}: invalid value - {exc}")
        except (KeyError, TypeError) as exc:
            errors.append(f"Row {row_num}: missing or invalid column - {exc}")

    if errors:
        db.rollback()
        return {
            "success": False,
            "created": 0,
            "updated": 0,
            "errors": errors[:10],
        }

    db.commit()
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "errors": [],
    }


# ========================================
# CRM / Users & Support
# ========================================


def _user_metrics_query(db: Session):
    orders_stats = (
        db.query(
            Order.user_id.label("user_id"),
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.amount_minor_units), 0).label("total_spent"),
            func.max(Order.created_at).label("last_order_at"),
        )
        .group_by(Order.user_id)
        .subquery()
    )

    open_statuses = [
        SupportTicketStatus.OPEN,
        SupportTicketStatus.IN_PROGRESS,
    ]
    tickets_stats = (
        db.query(
            SupportTicket.user_id.label("user_id"),
            func.count(SupportTicket.id).label("open_tickets"),
        )
        .filter(SupportTicket.status.in_(open_statuses))
        .group_by(SupportTicket.user_id)
        .subquery()
    )

    total_orders_col = func.coalesce(orders_stats.c.total_orders, 0)
    total_spent_col = func.coalesce(orders_stats.c.total_spent, 0)
    last_order_col = orders_stats.c.last_order_at
    open_tickets_col = func.coalesce(tickets_stats.c.open_tickets, 0)

    query = (
        db.query(
            User,
            total_orders_col.label("total_orders"),
            total_spent_col.label("total_spent"),
            last_order_col.label("last_order_at"),
            open_tickets_col.label("open_tickets"),
        )
        .outerjoin(orders_stats, orders_stats.c.user_id == User.id)
        .outerjoin(tickets_stats, tickets_stats.c.user_id == User.id)
    )

    sort_columns = {
        "created_at": User.created_at,
        "last_login": User.last_login,
        "total_orders": total_orders_col,
        "total_spent": total_spent_col,
        "last_order_at": last_order_col,
        "open_tickets": open_tickets_col,
    }

    return query, sort_columns


def _serialize_user_detail_row(row) -> AdminUserDetail:
    user: User = row[0]
    total_orders = int(row.total_orders or 0)
    total_spent = int(row.total_spent or 0)
    last_order_at = row.last_order_at
    open_tickets = int(row.open_tickets or 0)

    return AdminUserDetail(
        id=cast(int, user.id),
        email=cast(str | None, user.email),
        name=cast(str | None, user.name),
        created_at=cast(datetime, user.created_at),
        last_login=cast(datetime | None, user.last_login),
        total_orders=total_orders,
        total_spent_minor_units=total_spent,
        last_order_at=cast(datetime | None, last_order_at),
        internal_notes=cast(str | None, user.internal_notes),
        open_tickets=open_tickets,
    )


def _get_user_detail(db: Session, user_id: int) -> AdminUserDetail | None:
    query, _ = _user_metrics_query(db)
    row = query.filter(User.id == user_id).first()
    if not row:
        return None
    return _serialize_user_detail_row(row)


def _support_ticket_query(db: Session):
    return db.query(SupportTicket).options(
        joinedload(SupportTicket.user),
        joinedload(SupportTicket.audit_entries),
    )


@router.get("/users", response_model=PaginatedResponse[AdminUserDetail])
def list_users(
    q: str = Query("", description="Search by email or name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query(
        "created_at",
        description=(
            "Sort field: created_at, last_login, total_orders, total_spent, last_order_at, open_tickets"
        ),
    ),
    sort_order: str = Query("desc", description="Sort order asc/desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query, sort_columns = _user_metrics_query(db)

    if q:
        term = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.email).like(term),
                func.lower(User.name).like(term),
            )
        )

    total = query.count()
    sort_column = sort_columns.get(sort_by, User.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    rows = query.offset(offset).limit(page_size).all()
    items = [_serialize_user_detail_row(row) for row in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.patch("/users/{user_id}/notes", response_model=AdminUserDetail)
def update_user_notes(
    user_id: int,
    payload: UserNotesUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(user, "internal_notes", payload.internal_notes)
    db.commit()
    db.refresh(user)

    detail = _get_user_detail(db, user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User detail not available")
    return detail


def _serialize_support_ticket(ticket: SupportTicket) -> SupportTicketRead:
    def _serialize_audit(entry: SupportTicketAudit) -> SupportTicketAuditRead:
        event_value = (
            entry.event_type.value
            if hasattr(entry.event_type, "value")
            else str(entry.event_type)
        )
        if entry.from_status is not None:
            from_status = (
                entry.from_status.value
                if hasattr(entry.from_status, "value")
                else str(entry.from_status)
            )
        else:
            from_status = None

        if entry.to_status is not None:
            to_status = (
                entry.to_status.value
                if hasattr(entry.to_status, "value")
                else str(entry.to_status)
            )
        else:
            to_status = None

        return SupportTicketAuditRead(
            id=cast(int, entry.id),
            event_type=event_value,
            actor=cast(str | None, entry.actor),
            from_status=from_status,
            to_status=to_status,
            notes=cast(str | None, entry.notes),
            metadata=cast(dict[str, Any] | None, entry.extra_metadata),
            created_at=cast(datetime, entry.created_at),
        )

    status_value = (
        ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status)
    )
    priority_value = (
        ticket.priority.value
        if hasattr(ticket.priority, "value")
        else str(ticket.priority)
    )

    user_summary = _serialize_admin_user(ticket.user)
    if not user_summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Support ticket is missing user context",
        )

    return SupportTicketRead(
        id=cast(int, ticket.id),
        user=user_summary,
        order_id=cast(int | None, ticket.order_id),
        status=status_value,
        priority=priority_value,
        subject=cast(str, ticket.subject),
        description=cast(str | None, ticket.description),
        internal_notes=cast(str | None, ticket.internal_notes),
        created_by=cast(str | None, ticket.created_by),
        updated_by=cast(str | None, ticket.updated_by),
        created_at=cast(datetime, ticket.created_at),
        updated_at=cast(datetime, ticket.updated_at),
        resolved_at=cast(datetime | None, ticket.resolved_at),
        due_at=cast(datetime | None, ticket.due_at),
        last_reminder_at=cast(datetime | None, ticket.last_reminder_at),
        reminder_count=cast(
            int,
            ticket.reminder_count if ticket.reminder_count is not None else 0,
        ),
        escalation_level=cast(
            int,
            ticket.escalation_level if ticket.escalation_level is not None else 0,
        ),
        audits=[_serialize_audit(entry) for entry in ticket.audit_entries],
    )


@router.get("/support/tickets", response_model=PaginatedResponse[SupportTicketRead])
def list_support_tickets(
    status_filter: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    user_id: int | None = Query(None, gt=0),
    order_id: int | None = Query(None, gt=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = _support_ticket_query(db).order_by(SupportTicket.created_at.desc())

    if status_filter:
        status_enum = _parse_enum(
            SupportTicketStatus, status_filter, "support ticket status"
        )
        query = query.filter(SupportTicket.status == status_enum)

    if priority:
        priority_enum = _parse_enum(
            SupportTicketPriority, priority, "support ticket priority"
        )
        query = query.filter(SupportTicket.priority == priority_enum)

    if user_id:
        query = query.filter(SupportTicket.user_id == user_id)

    if order_id:
        query = query.filter(SupportTicket.order_id == order_id)

    total = query.count()
    offset = (page - 1) * page_size
    tickets = query.offset(offset).limit(page_size).all()

    items = [_serialize_support_ticket(ticket) for ticket in tickets]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post(
    "/support/tickets",
    response_model=SupportTicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    payload: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.order_id:
        order = (
            db.query(Order)
            .filter(Order.id == payload.order_id, Order.user_id == user.id)
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Order not found for user")

    priority_enum = (
        _parse_enum(SupportTicketPriority, payload.priority, "priority")
        if payload.priority
        else SupportTicketPriority.NORMAL
    )

    actor_email = cast(str | None, current_admin.email)

    ticket = SupportTicket(
        user_id=user.id,
        order_id=payload.order_id,
        subject=payload.subject,
        description=payload.description,
        internal_notes=payload.internal_notes,
        priority=priority_enum,
        status=SupportTicketStatus.OPEN,
        created_by=actor_email,
        updated_by=actor_email,
    )

    support_automation.ensure_due_at(ticket, due_override=payload.due_at)

    db.add(ticket)
    db.flush()

    support_automation.record_audit(
        db,
        ticket,
        event_type=SupportTicketEventType.CREATED,
        actor=actor_email,
        notes="Ticket created",
        metadata={
            "priority": priority_enum.value,
            "due_at": ticket.due_at.isoformat() if ticket.due_at is not None else None,
            "order_id": payload.order_id,
        },
        to_status=SupportTicketStatus.OPEN,
    )

    db.commit()

    created = _support_ticket_query(db).filter(SupportTicket.id == ticket.id).first()
    if not created:
        raise HTTPException(status_code=404, detail="Ticket not found after creation")

    return _serialize_support_ticket(created)


@router.patch("/support/tickets/{ticket_id}", response_model=SupportTicketRead)
def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    ticket = _support_ticket_query(db).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    actor_email = cast(str | None, current_admin.email)
    events: list[dict[str, Any]] = []

    previous_status = ticket.status
    previous_priority = ticket.priority
    original_due = ticket.due_at
    priority_changed = False

    if payload.status:
        status_enum = _parse_enum(
            SupportTicketStatus, payload.status, "support ticket status"
        )
        if status_enum != ticket.status:
            ticket.status = status_enum  # type: ignore[assignment]
            if status_enum == SupportTicketStatus.RESOLVED:
                setattr(ticket, "resolved_at", datetime.utcnow())
            elif status_enum in (
                SupportTicketStatus.OPEN,
                SupportTicketStatus.IN_PROGRESS,
            ):
                setattr(ticket, "resolved_at", None)

            events.append(
                {
                    "event_type": SupportTicketEventType.STATUS_CHANGED,
                    "actor": actor_email,
                    "from_status": previous_status,
                    "to_status": status_enum,
                    "metadata": {"source": "admin_api"},
                }
            )
            previous_status = status_enum

    if payload.priority:
        priority_enum = _parse_enum(
            SupportTicketPriority, payload.priority, "support ticket priority"
        )
        if priority_enum != ticket.priority:
            ticket.priority = priority_enum  # type: ignore[assignment]
            events.append(
                {
                    "event_type": SupportTicketEventType.PRIORITY_CHANGED,
                    "actor": actor_email,
                    "metadata": {
                        "from": (
                            previous_priority.value
                            if hasattr(previous_priority, "value")
                            else str(previous_priority)
                        ),
                        "to": priority_enum.value,
                    },
                }
            )
            previous_priority = priority_enum
            priority_changed = True

    if payload.description is not None:
        setattr(ticket, "description", payload.description)

    if payload.internal_notes is not None:
        notes_before = ticket.internal_notes or ""
        setattr(ticket, "internal_notes", payload.internal_notes)
        notes_after = payload.internal_notes or ""
        if notes_after != notes_before:
            events.append(
                {
                    "event_type": SupportTicketEventType.NOTE_ADDED,
                    "actor": actor_email,
                    "notes": "Internal notes updated",
                }
            )

    due_override = payload.due_at
    sla_reason = None
    if due_override is not None:
        sla_reason = "manual_override"
    elif priority_changed:
        sla_reason = "priority_changed"

    if due_override is not None or priority_changed:
        before_due = ticket.due_at
        new_due = support_automation.ensure_due_at(ticket, due_override=due_override)
        if new_due != before_due:
            events.append(
                {
                    "event_type": SupportTicketEventType.SLA_UPDATED,
                    "actor": actor_email,
                    "notes": "Ticket due date updated",
                    "metadata": {
                        "previous_due_at": (
                            before_due.isoformat() if before_due is not None else None
                        ),
                        "due_at": new_due.isoformat(),
                        "reason": sla_reason,
                    },
                }
            )

    sla_event_recorded = any(
        event.get("event_type") == SupportTicketEventType.SLA_UPDATED
        for event in events
    )

    if original_due is None and not sla_event_recorded:
        new_due = support_automation.ensure_due_at(ticket)
        events.append(
            {
                "event_type": SupportTicketEventType.SLA_UPDATED,
                "actor": actor_email,
                "notes": "Ticket due date initialized",
                "metadata": {
                    "previous_due_at": None,
                    "due_at": new_due.isoformat(),
                    "reason": "backfill",
                },
            }
        )

    setattr(ticket, "updated_by", actor_email)
    setattr(ticket, "updated_at", datetime.utcnow())

    for event_payload in events:
        support_automation.record_audit(db, ticket, **event_payload)

    db.commit()

    updated = _support_ticket_query(db).filter(SupportTicket.id == ticket.id).first()
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found after update")

    return _serialize_support_ticket(updated)


# ========================================
# Billing & Exports
# ========================================


def _resolve_export_window(
    period: str,
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime]:
    normalized = period.lower()
    now = datetime.utcnow()

    if normalized == "daily":
        start = start_date or datetime(now.year, now.month, now.day)
        end = end_date or (start + timedelta(days=1))
    elif normalized == "monthly":
        start = start_date or datetime(now.year, now.month, 1)
        if end_date:
            end = end_date
        else:
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1)
            else:
                end = start.replace(month=start.month + 1, day=1)
    elif normalized == "custom":
        if not start_date or not end_date:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="start_date and end_date are required for custom exports",
            )
        start, end = start_date, end_date
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Use daily, monthly, or custom.",
        )

    if start >= end:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    return start, end


def _resolve_analytics_range(
    start_date: datetime | None,
    end_date: datetime | None,
) -> tuple[datetime, datetime]:
    """Normalize analytics window with sane defaults."""

    end = end_date or datetime.utcnow()
    default_days = max(1, settings.ANALYTICS_DEFAULT_RANGE_DAYS)
    start = start_date or (end - timedelta(days=default_days - 1))

    start_floor = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end_ceiling = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    if start_floor > end_ceiling:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    max_window_days = 365
    if (end_ceiling - start_floor).days > max_window_days:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Analytics range too large (max 365 days)",
        )

    return start_floor, end_ceiling


@router.get("/exports/sales")
def export_sales_report(
    period: str = Query(
        "daily",
        description="Interval to export (daily, monthly, custom)",
    ),
    start_date: datetime
    | None = Query(None, description="ISO timestamp start (required for custom)"),
    end_date: datetime
    | None = Query(None, description="ISO timestamp end (required for custom)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    start, end = _resolve_export_window(period, start_date, end_date)

    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.user))
        .filter(Invoice.issued_at >= start, Invoice.issued_at < end)
        .order_by(Invoice.issued_at.asc())
        .all()
    )

    csv_buffer = build_sales_export_csv(invoices)
    filename = (
        f"{settings.SALES_EXPORT_FILENAME}-"
        f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}.csv"
    )
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers=headers,
    )


# ========================================
# Analytics & Insights
# ========================================


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview(
    start_date: datetime
    | None = Query(None, description="UTC start datetime (defaults to last N days)"),
    end_date: datetime
    | None = Query(None, description="UTC end datetime (defaults to now)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    start, end = _resolve_analytics_range(start_date, end_date)
    metrics = get_overview_metrics(db, start=start, end=end)
    return AnalyticsOverviewResponse(**cast(dict[str, Any], metrics))


@router.get("/analytics/timeseries", response_model=AnalyticsTimeseriesResponse)
def analytics_timeseries(
    start_date: datetime | None = Query(None, description="UTC range start"),
    end_date: datetime | None = Query(None, description="UTC range end"),
    event_types: list[str]
    | None = Query(
        None,
        description="Optional event types to include (repeat param)",
    ),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    start, end = _resolve_analytics_range(start_date, end_date)
    filters = _parse_event_type_filters(event_types)
    payload = get_timeseries(db, start=start, end=end, event_types=filters)
    return AnalyticsTimeseriesResponse(**cast(dict[str, Any], payload))


@router.get("/analytics/projections", response_model=AnalyticsProjectionResponse)
def analytics_projections(
    window_days: int = Query(
        settings.ANALYTICS_PROJECTION_WINDOW_DAYS,
        ge=3,
        le=90,
        description="Historical window size for moving average",
    ),
    horizon_days: int = Query(
        settings.ANALYTICS_PROJECTION_HORIZON_DAYS,
        ge=1,
        le=30,
        description="Forward-looking projection horizon",
    ),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    payload = get_projections(db, window_days=window_days, horizon_days=horizon_days)
    return AnalyticsProjectionResponse(**cast(dict[str, Any], payload))


# ========================================
# Helpers
# ========================================


def _parse_enum(enum_cls, value: str, field_name: str):
    normalized = value.strip().lower()
    for member in enum_cls:
        if member.name.lower() == normalized or member.value.lower() == normalized:
            return member
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid {field_name}: {value}",
    )


def _parse_event_type_filters(
    event_types: list[str] | None,
) -> list[AnalyticsEventType] | None:
    if not event_types:
        return None

    resolved: list[AnalyticsEventType] = []
    for raw in event_types:
        normalized = raw.strip().lower()
        matched = None
        for event in AnalyticsEventType:
            if event.value == normalized or event.name.lower() == normalized:
                matched = event
                break
        if not matched:
            valid = ", ".join(evt.value for evt in AnalyticsEventType)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event_type '{raw}'. Use one of: {valid}",
            )
        resolved.append(matched)
    return resolved


def _serialize_admin_user(user: User | None) -> AdminUserSummary | None:
    if not user:
        return None
    return AdminUserSummary(
        id=cast(int, user.id),
        email=cast(str | None, user.email),
        name=cast(str | None, user.name),
    )


def _extract_plan_snapshot(order: Order) -> dict[str, Any] | None:
    snapshot = cast(dict[str, Any] | None, getattr(order, "plan_snapshot", None))
    if snapshot:
        return snapshot
    plan = getattr(order, "plan", None)
    if not plan:
        return None
    return {
        "id": cast(int, plan.id),
        "name": plan.name,
        "country_id": plan.country_id,
        "carrier_id": plan.carrier_id,
        "data_gb": float(plan.data_gb) if plan.data_gb is not None else None,
        "duration_days": plan.duration_days,
        "price_usd": float(plan.price_usd) if plan.price_usd is not None else None,
    }


def _serialize_admin_payment(payment: Payment) -> AdminPaymentRead:
    order = getattr(payment, "order", None)
    amount_minor_units = (
        int(order.amount_minor_units)
        if order and order.amount_minor_units is not None
        else 0
    )
    currency = str(order.currency) if order and order.currency else None
    provider = (
        payment.provider.value
        if hasattr(payment.provider, "value")
        else str(payment.provider)
    )
    status_value = (
        payment.status.value
        if hasattr(payment.status, "value")
        else str(payment.status)
    )

    return AdminPaymentRead(
        id=cast(int, payment.id),
        order_id=cast(int, payment.order_id),
        provider=provider,
        status=status_value,
        intent_id=cast(str | None, payment.intent_id),
        created_at=cast(datetime, payment.created_at),
        order_amount_minor_units=amount_minor_units,
        order_currency=currency,
    )


def _serialize_admin_esim(esim: EsimProfile | None) -> AdminEsimProfileRead | None:
    if not esim:
        return None
    status_value = (
        esim.status.value if hasattr(esim.status, "value") else str(esim.status)
    )
    return AdminEsimProfileRead(
        id=cast(int, esim.id),
        order_id=cast(int | None, esim.order_id),
        status=status_value,
        activation_code=cast(str | None, esim.activation_code),
        iccid=cast(str | None, esim.iccid),
        inventory_item_id=cast(int | None, esim.inventory_item_id),
        plan_id=cast(int | None, esim.plan_id),
        country_id=cast(int | None, esim.country_id),
        carrier_id=cast(int | None, esim.carrier_id),
        provisioned_at=cast(datetime | None, esim.provisioned_at),
        provider_reference=cast(str | None, esim.provider_reference),
        created_at=cast(datetime, esim.created_at),
    )


def _serialize_admin_order(order: Order) -> AdminOrderRead:
    status_value = (
        order.status.value if hasattr(order.status, "value") else str(order.status)
    )
    currency = str(order.currency or "USD")
    raw_amount = cast(int | None, order.amount_minor_units)
    amount_minor_units = raw_amount if raw_amount is not None else 0
    user = _serialize_admin_user(getattr(order, "user", None))
    payments = [
        _serialize_admin_payment(payment)
        for payment in sorted(
            getattr(order, "payments", []),
            key=lambda p: p.created_at or datetime.min,
            reverse=True,
        )
    ]

    return AdminOrderRead(
        id=cast(int, order.id),
        status=status_value,
        currency=currency,
        amount_minor_units=amount_minor_units,
        created_at=cast(datetime, order.created_at),
        plan_id=cast(int | None, order.plan_id),
        plan_snapshot=_extract_plan_snapshot(order),
        user=user,
        payments=payments,
        esim_profile=_serialize_admin_esim(getattr(order, "esim_profile", None)),
    )


def _serialize_inventory_item(item: EsimInventory) -> AdminInventoryRead:
    status_value = (
        item.status.value if hasattr(item.status, "value") else str(item.status)
    )
    return AdminInventoryRead(
        id=cast(int, item.id),
        plan_id=cast(int | None, item.plan_id),
        carrier_id=cast(int | None, item.carrier_id),
        country_id=cast(int | None, item.country_id),
        status=status_value,
        activation_code=cast(str | None, item.activation_code),
        iccid=cast(str | None, item.iccid),
        qr_payload=cast(str | None, item.qr_payload),
        instructions=cast(str | None, item.instructions),
        provider_reference=cast(str | None, item.provider_reference),
        reserved_at=cast(datetime | None, item.reserved_at),
        assigned_at=cast(datetime | None, item.assigned_at),
        created_at=cast(datetime, item.created_at),
        updated_at=cast(datetime | None, item.updated_at),
    )
