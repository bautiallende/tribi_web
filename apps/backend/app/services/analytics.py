"""Analytics helpers for recording and aggregating funnel metrics."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analytics import AnalyticsEvent, AnalyticsEventType
from app.models.catalog import Plan


def record_event(
    db: Session,
    *,
    event_type: AnalyticsEventType,
    user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    amount_minor_units: Optional[int] = None,
    currency: Optional[str] = None,
    metadata: Optional[dict] = None,
    occurred_at: Optional[dt.datetime] = None,
) -> AnalyticsEvent:
    """Persist a new analytics event without committing the transaction."""

    event = AnalyticsEvent(
        event_type=event_type,
        user_id=user_id,
        order_id=order_id,
        plan_id=plan_id,
        amount_minor_units=amount_minor_units,
        currency=currency or settings.DEFAULT_CURRENCY,
        extra_metadata=metadata or {},
        occurred_at=occurred_at or dt.datetime.utcnow(),
    )
    db.add(event)
    return event


def _apply_window(query, start: dt.datetime, end: dt.datetime):
    return query.filter(AnalyticsEvent.occurred_at >= start).filter(
        AnalyticsEvent.occurred_at <= end
    )


def _event_filters(event_types: Optional[Iterable[AnalyticsEventType]]):
    if not event_types:
        return []
    return [AnalyticsEvent.event_type.in_(list(event_types))]


def get_overview_metrics(
    db: Session,
    *,
    start: dt.datetime,
    end: dt.datetime,
    top_plan_limit: int = 5,
) -> Dict[str, object]:
    base_query = _apply_window(db.query(AnalyticsEvent), start, end)

    totals = (
        base_query.with_entities(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
            func.coalesce(func.sum(AnalyticsEvent.amount_minor_units), 0).label(
                "amount"
            ),
        )
        .group_by(AnalyticsEvent.event_type)
        .all()
    )

    lookup = {row.event_type: row for row in totals}
    signups = lookup.get(AnalyticsEventType.USER_SIGNUP)
    checkouts = lookup.get(AnalyticsEventType.CHECKOUT_STARTED)
    payments = lookup.get(AnalyticsEventType.PAYMENT_SUCCEEDED)
    activations = lookup.get(AnalyticsEventType.ESIM_ACTIVATED)

    total_signups = signups.count if signups else 0
    checkout_started = checkouts.count if checkouts else 0
    total_payments = payments.count if payments else 0
    total_activations = activations.count if activations else 0
    revenue_minor_units = payments.amount if payments else 0

    conversion_rate = (total_payments / checkout_started) if checkout_started else 0.0
    signup_to_payment = (total_payments / total_signups) if total_signups else 0.0
    activation_rate = (total_activations / total_payments) if total_payments else 0.0
    avg_order_value = revenue_minor_units / total_payments if total_payments else 0

    plan_rows = (
        _apply_window(db.query(AnalyticsEvent), start, end)
        .filter(AnalyticsEvent.event_type == AnalyticsEventType.PAYMENT_SUCCEEDED)
        .with_entities(
            AnalyticsEvent.plan_id,
            func.count(AnalyticsEvent.id).label("payments"),
            func.coalesce(func.sum(AnalyticsEvent.amount_minor_units), 0).label(
                "revenue"
            ),
        )
        .group_by(AnalyticsEvent.plan_id)
        .order_by(desc("revenue"))
        .limit(top_plan_limit)
        .all()
    )

    top_plan_ids = [row.plan_id for row in plan_rows if row.plan_id]
    plans = {}
    if top_plan_ids:
        for plan in (
            db.query(Plan)
            .filter(Plan.id.in_(top_plan_ids))
            .with_entities(Plan.id, Plan.name, Plan.data_gb, Plan.duration_days)
        ):
            plans[plan.id] = plan

    top_plans: List[Dict[str, object]] = []
    for row in plan_rows:
        top_plans.append(
            {
                "plan_id": row.plan_id,
                "name": plans.get(row.plan_id).name if row.plan_id in plans else None,
                "payments": row.payments,
                "revenue_minor_units": row.revenue,
                "data_gb": (
                    plans.get(row.plan_id).data_gb if row.plan_id in plans else None
                ),
                "duration_days": (
                    plans.get(row.plan_id).duration_days
                    if row.plan_id in plans
                    else None
                ),
            }
        )

    return {
        "total_signups": total_signups,
        "checkout_started": checkout_started,
        "payments": total_payments,
        "activations": total_activations,
        "revenue_minor_units": revenue_minor_units,
        "conversion_rate": conversion_rate,
        "signup_to_payment": signup_to_payment,
        "activation_rate": activation_rate,
        "average_order_value_minor_units": int(avg_order_value),
        "top_plans": top_plans,
    }


def get_timeseries(
    db: Session,
    *,
    start: dt.datetime,
    end: dt.datetime,
    event_types: Optional[Iterable[AnalyticsEventType]] = None,
) -> Dict[str, List[Dict[str, object]]]:
    day_bucket = func.date(AnalyticsEvent.occurred_at).label("bucket")
    query = (
        _apply_window(db.query(day_bucket, AnalyticsEvent.event_type), start, end)
        .with_entities(
            day_bucket,
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
            func.coalesce(func.sum(AnalyticsEvent.amount_minor_units), 0).label(
                "amount"
            ),
        )
        .group_by(day_bucket, AnalyticsEvent.event_type)
        .order_by(day_bucket)
    )

    for clause in _event_filters(event_types):
        query = query.filter(clause)

    rows = query.all()

    num_days = (end.date() - start.date()).days + 1
    points: Dict[dt.date, Dict[str, object]] = {}
    for i in range(num_days):
        date_key = start.date() + dt.timedelta(days=i)
        points[date_key] = {
            "date": date_key.isoformat(),
            "user_signup": 0,
            "checkout_started": 0,
            "payment_succeeded": 0,
            "esim_activated": 0,
            "revenue_minor_units": 0,
        }

    for row in rows:
        bucket_date = (
            row.bucket
            if isinstance(row.bucket, dt.date)
            else dt.date.fromisoformat(row.bucket)
        )
        entry = points.get(bucket_date)
        if not entry:
            continue
        entry[row.event_type.value] = row.count
        if row.event_type == AnalyticsEventType.PAYMENT_SUCCEEDED:
            entry["revenue_minor_units"] = row.amount

    ordered_points = [
        points[start.date() + dt.timedelta(days=i)] for i in range(num_days)
    ]
    return {"points": ordered_points}


def get_projections(
    db: Session,
    *,
    window_days: int,
    horizon_days: int,
) -> Dict[str, object]:
    end = dt.datetime.utcnow()
    start = end - dt.timedelta(days=window_days)
    day_bucket = func.date(AnalyticsEvent.occurred_at).label("bucket")

    rows = (
        _apply_window(db.query(day_bucket, AnalyticsEvent.event_type), start, end)
        .filter(
            AnalyticsEvent.event_type.in_(
                [
                    AnalyticsEventType.USER_SIGNUP,
                    AnalyticsEventType.PAYMENT_SUCCEEDED,
                ]
            )
        )
        .with_entities(
            day_bucket,
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label("count"),
            func.coalesce(func.sum(AnalyticsEvent.amount_minor_units), 0).label(
                "amount"
            ),
        )
        .group_by(day_bucket, AnalyticsEvent.event_type)
        .order_by(day_bucket)
        .all()
    )

    daily = defaultdict(lambda: {"signups": 0, "payments": 0, "revenue": 0})

    for row in rows:
        bucket_date = (
            row.bucket
            if isinstance(row.bucket, dt.date)
            else dt.date.fromisoformat(row.bucket)
        )
        if row.event_type == AnalyticsEventType.USER_SIGNUP:
            daily[bucket_date]["signups"] = row.count
        else:
            daily[bucket_date]["payments"] = row.count
            daily[bucket_date]["revenue"] = row.amount

    if not daily:
        return {
            "revenue_next_days_minor_units": 0,
            "signups_next_days": 0,
            "avg_daily_revenue_minor_units": 0,
            "avg_daily_signups": 0,
            "growth_rate": 0.0,
            "notes": "Not enough data to project",
        }

    ordered_dates = sorted(daily.keys())
    revenue_values = [daily[d]["revenue"] for d in ordered_dates]
    signup_values = [daily[d]["signups"] for d in ordered_dates]

    avg_daily_revenue = sum(revenue_values) / len(revenue_values)
    avg_daily_signups = sum(signup_values) / len(signup_values)

    projected_revenue = int(avg_daily_revenue * horizon_days)
    projected_signups = int(round(avg_daily_signups * horizon_days))

    first = revenue_values[0]
    last = revenue_values[-1]
    growth_rate = ((last - first) / first) if first else 0.0

    return {
        "revenue_next_days_minor_units": projected_revenue,
        "signups_next_days": projected_signups,
        "avg_daily_revenue_minor_units": int(avg_daily_revenue),
        "avg_daily_signups": avg_daily_signups,
        "growth_rate": growth_rate,
        "notes": "Simple moving average projection over the last"
        f" {window_days} days",
    }
