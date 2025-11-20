import csv
import io
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from ..db.session import get_db
from ..models import (
    Carrier,
    Country,
    EsimInventory,
    EsimProfile,
    Order,
    Payment,
    Plan,
    User,
)
from ..models.auth_models import (
    EsimInventoryStatus,
    EsimStatus,
    OrderStatus,
    PaymentStatus,
)
from ..schemas.admin import (
    AdminEsimProfileRead,
    AdminInventoryRead,
    AdminInventoryStats,
    AdminOrderRead,
    AdminPaymentRead,
    AdminStockAlert,
    AdminUserSummary,
    CarrierCreate,
    CarrierUpdate,
    CountryCreate,
    CountryUpdate,
    PaginatedResponse,
    PlanCreate,
    PlanUpdate,
)
from ..schemas.catalog import CarrierRead, CountryRead, PlanRead
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
