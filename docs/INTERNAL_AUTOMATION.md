# Internal Automation (Billing, CRM, Support)

_Updated: 2025-11-20_

This document captures the scope, implementation notes, and validation steps for **Phase 4** of the autonomy roadmap. Each subsection will be kept current as code ships to `develop` so finance, support, and engineering teams share the same playbook.

## 1. Billing & Accounting Exports

**Goal:** generate auditable records for every paid order and provide accounting-friendly exports on demand or via schedule.

### Deliverables

- Invoice/comprobante entity (unique number, order linkage, totals, tax breakdown, currency, PDF/HTML payload reference).
- Export service capable of emitting CSV and XLSX snapshots (daily / monthly sales, currency totals, tax buckets).
- Admin endpoint namespace (`GET /api/admin/exports/sales`) with role checks and signed URLs.

### Operational Notes

- Storage: invoices live in the primary DB + optional blob storage for PDFs.
- Numbering: configurable prefix/sequence per currency; collisions rejected.
- Time zones: exports default to UTC with optional `tz` query parameter; always include timezone info in headers.
- Env knobs: `INVOICE_PREFIX` drives numbering, `SALES_EXPORT_FILENAME` sets the downloaded CSV base name.

### Verification Checklist

1. Create a paid order via checkout; confirm invoice record is generated automatically.
2. Hit `GET /api/admin/exports/sales?period=daily` and download CSV; verify totals against database query.
3. Attempt export as non-admin user → receive `403`.

## 2. CRM & Support Tickets

**Goal:** provide full customer context (profile + order history) and a lightweight ticketing flow for support teams inside the existing admin panel.

### Deliverables

- ✅ `support_tickets` data model linked to users/orders with lifecycle states (`open`, `in_progress`, `resolved`, `archived`).
- ✅ Backend aggregation for `/admin/users` returning contact info, order totals, ARPU (minor units), last order timestamp, and open ticket counts.
- ✅ Admin-only APIs expose SLA metadata (due date, reminder counters, escalation level) plus a full audit history for every ticket change.
- ✅ React admin pages (users list, support board) consume the CRM APIs with inline filters, status changes, SLA badges, and ticket creation enhancements.

### Operational Notes

- Notes accept plaintext/Markdown; sanitization occurs client-side before rendering.
- Ticket audit fields (`created_by`, `updated_by`) use the acting admin email for quick traceability.
- Every ticket response now embeds `due_at`, `last_reminder_at`, `reminder_count`, `escalation_level`, and a chronological `audits` array describing lifecycle changes (status, priority, notes, reminders, escalations, SLA overrides).
- Filters: ticket endpoints accept `status`, `priority`, `user_id`, `order_id`; pagination mirrors other admin APIs.
- Admins can override `due_at` via PATCH requests; otherwise values are derived from configurable SLA windows (see settings table below).

### Verification Checklist

1. `GET /admin/users?q=email` returns matching records with `total_orders`, `total_spent_minor_units`, and `open_tickets` populated.
2. `PATCH /admin/users/{user_id}/notes` updates `internal_notes` and persists text in DB.
3. Create → update support ticket via `POST /admin/support/tickets` and `PATCH /admin/support/tickets/{id}`; verify status transitions, SLA metadata (`due_at`, `reminder_count`), and audit trail entries.

## 3. Scheduled Jobs & Reminders

**Goal:** automate proactive communication for expiring eSIMs and internal health summaries.

### Deliverables

- ✅ Background scheduler (FastAPI lifespan task) configured in backend with opt-in via `JOB_ENABLED`.
- ✅ Jobs:
  - **Ticket SLA reminders:** run continuously, find tickets approaching due time, increment reminder counters, and log audits for traceability.
  - **Ticket escalations:** when a ticket remains overdue past the configurable grace period, bump the escalation level, push status to `in_progress`, and record audits.
  - **Support digests:** emit daily + weekly log summaries (open/overdue counts, recent reminders) for operations monitoring.
- ✅ Failure monitoring: every job cycle and digest write structured logs; exceptions are caught and logged with stack traces.

### Operational Notes

- Enable jobs by exporting `JOB_ENABLED=true` before launching Uvicorn/Gunicorn. The default remains `False` to avoid unintended background activity.
- Timing knobs live in `app/core/config.py`:
  - `SUPPORT_SLA_HOURS_*` set the default due windows per priority.
  - `SUPPORT_REMINDER_LEAD_MINUTES` and `SUPPORT_REMINDER_INTERVAL_MINUTES` control reminder cadence.
  - `SUPPORT_ESCALATION_GRACE_MINUTES` and `SUPPORT_MAX_ESCALATION_LEVEL` guard escalations.
  - `SUPPORT_DIGEST_HOUR_UTC` + `JOB_LOOP_INTERVAL_SECONDS` configure scheduler cadence.
- Reminders/escalations currently log to the backend console; integration with Slack/email can plug into the same job hooks.
- Digests are logged (JSON metrics payload); once email is wired, reuse `run_support_digest` to fan out notifications.

### Verification Checklist

1. Enable jobs locally by exporting `JOB_ENABLED=true` and starting the backend (`uvicorn app.main:app --reload`). Watch logs for `Ticket SLA job` entries.
2. Use `pytest tests/test_support_jobs.py -k reminder` to validate reminder/escalation logic without running the whole server.
3. Seed tickets that are overdue vs. approaching SLA and confirm reminder/escalation audit entries show up under `/admin/support/tickets` responses.

## 4. Documentation & Handover

- Keep this file updated whenever new automation ships.
- Link to supporting runbooks in `docs/ADMIN.md` and `docs/manual_smoke_tests.md`.
- When Phase 4 completes, summarize accomplishments + tests in `ROADMAP_AUTOMATION.md`.

> Until all deliverables are marked ✅, treat the above as living requirements. Use checklists in PRs to avoid regressions.
