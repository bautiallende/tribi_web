from datetime import datetime, timedelta
from typing import cast

from app.models import User
from app.services.analytics import AnalyticsEventType, record_event


def test_admin_analytics_endpoints(client, admin_headers, db_session):
    user = User(email="insights@tribi.test")
    db_session.add(user)
    db_session.commit()

    base = datetime.utcnow().replace(microsecond=0)
    plan_id = 1

    def add_event(
        event_type: AnalyticsEventType, days_ago: int, amount_minor_units: int = 0
    ):
        occurred_at = base - timedelta(days=days_ago)
        record_event(
            db_session,
            event_type=event_type,
            user_id=cast(int, user.id),
            order_id=1000 + days_ago,
            plan_id=plan_id,
            amount_minor_units=amount_minor_units,
            currency="USD",
            metadata={"source": "pytest"},
            occurred_at=occurred_at,
        )

    add_event(AnalyticsEventType.USER_SIGNUP, days_ago=2)
    add_event(AnalyticsEventType.USER_SIGNUP, days_ago=1)
    add_event(AnalyticsEventType.CHECKOUT_STARTED, days_ago=1)
    add_event(AnalyticsEventType.PAYMENT_SUCCEEDED, days_ago=1, amount_minor_units=9900)
    add_event(AnalyticsEventType.ESIM_ACTIVATED, days_ago=0)

    db_session.commit()

    start = (base - timedelta(days=3)).isoformat()
    end = (base + timedelta(days=1)).isoformat()

    overview = client.get(
        "/admin/analytics/overview",
        params={"start_date": start, "end_date": end},
        headers=admin_headers,
    )
    assert overview.status_code == 200
    overview_data = overview.json()
    assert overview_data["total_signups"] == 2
    assert overview_data["payments"] == 1
    assert overview_data["activations"] == 1
    assert overview_data["top_plans"][0]["payments"] == 1

    timeseries = client.get(
        "/admin/analytics/timeseries",
        params={"start_date": start, "end_date": end},
        headers=admin_headers,
    )
    assert timeseries.status_code == 200
    points = timeseries.json()["points"]
    assert len(points) >= 3
    latest = points[-1]
    assert latest["esim_activated"] >= 0

    projections = client.get(
        "/admin/analytics/projections",
        params={"window_days": 7, "horizon_days": 3},
        headers=admin_headers,
    )
    assert projections.status_code == 200
    projection_data = projections.json()
    assert "revenue_next_days_minor_units" in projection_data
    assert "growth_rate" in projection_data
