# Analytics & Funnel Visibility

_Updated: 2025-11-20_

Phase 5 introduces a lightweight analytics stack so product, support, and finance teams can track how many users move through the funnel (signup → checkout → payment → eSIM activation) plus understand which plans generate the most revenue. This document explains how the stack is stitched together and how to operate it day to day.

## Event Instrumentation

All events are stored in the new `analytics_events` table (`apps/backend/app/models/analytics.py`). Each record captures:

- `event_type`: Enum – one of `user_signup`, `checkout_started`, `payment_succeeded`, `esim_activated`.
- Foreign keys: `user_id`, `order_id`, `plan_id` (optional per event type).
- Commerce context: `amount_minor_units`, `currency`, `metadata` JSON (for plan snapshot, provider refs, etc.).
- Timestamps: `occurred_at` (when it happened) and `created_at`.

Events are created through `app.services.analytics.record_event`. Touchpoints:

| Flow                 | Location                                                             | Event                                                                       |
| -------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| New user OTP request | `app/api/auth.py::request_code`                                      | `user_signup` (only once per email, after the user row is created)          |
| Checkout creation    | `app/api/orders.py::create_order`                                    | `checkout_started` (stores plan snapshot + amount)                          |
| Payment success      | `app/api/orders.py` inside payment intent creation + webhook handler | `payment_succeeded` (guards double counting by checking status transitions) |
| eSIM activation      | `app/api/orders.py::activate_esim`                                   | `esim_activated` (tracks inventory/provisioning references)                 |

Because `record_event` only stages objects on the active SQLAlchemy session, events participate in the same transaction as the business action. Rollbacks erase both order/payment data and the analytics row, keeping the counts consistent.

## Backend Surface Area

FastAPI exposes three new admin-only endpoints (documented in `apps/backend/app/api/admin.py`):

| Endpoint                           | Description                                                                                       |
| ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| `GET /admin/analytics/overview`    | Returns aggregate funnel metrics + top plans for a date range (defaults to last 30 days).         |
| `GET /admin/analytics/timeseries`  | Daily buckets for each event type + revenue. Accepts optional `event_types[]` filters.            |
| `GET /admin/analytics/projections` | Moving-average projection service. Tunable `window_days` (history) and `horizon_days` (forecast). |

Common query params:

- `start_date`, `end_date`: ISO timestamps (UTC). If omitted we use `[now-29d, now]`.
- `event_types`: Repeat param using enum values.
- Guard rails: ranges clamped to 365 days max, projection windows between 3 and 90 days, horizon between 1 and 30 days.

Environment knobs (documented in `.env.example` and `apps/backend/.env.example`):

```
ANALYTICS_DEFAULT_RANGE_DAYS=30
ANALYTICS_PROJECTION_WINDOW_DAYS=14
ANALYTICS_PROJECTION_HORIZON_DAYS=7
```

## Admin Dashboard

`apps/web/app/admin/analytics/page.tsx` renders the dashboard using the endpoints above:

- Date pickers + quick range buttons (7/30/90 days) and filter chips for each event type.
- KPI cards (signups, checkout starts, payments, activations, revenue) with conversion ratios.
- Revenue trend bar chart + detailed table per day.
- Configurable projection panel (window / horizon selects) with forecasted revenue/signups and growth rate.
- Top plans table sorted by revenue for the selected window.

The navigation card on `/admin` now links to this page so admins can get to insights in one click.

## Database Migration

Run Alembic revision `20251121_add_analytics_events` to create the `analytics_events` table. Apply with `alembic upgrade head` or the `Backend: Run Migrations` VS Code task.

```bash
cd apps/backend
alembic upgrade head
```

## Tests

New coverage lives in `apps/backend/tests/test_analytics.py`:

- Seeds synthetic events via `record_event`.
- Verifies overview metrics, timeseries payloads, and projections endpoints all respond with sane aggregates.
- Ensures admin auth guard continues to apply (existing fixtures mock admin access).

Run it standalone:

```bash
cd apps/backend
pytest tests/test_analytics.py -q
```

## Operational Notes

- Because events live in MySQL alongside the core data, backups automatically capture analytics as well.
- The projections endpoint falls back to a friendly "Not enough data" note when insufficient history exists.
- Dashboard requests pass through `apiUrl` with cookies/bearer tokens, so admin auth is still required. If an admin sees a blank state, check for browser auth or backend logs for 401s.
- Future ideas: push events to a data warehouse, add cohort filters, wire real BI charts. For now this gives the team immediate visibility without new infrastructure.
