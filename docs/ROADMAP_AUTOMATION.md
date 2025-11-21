# Roadmap Towards Autonomous Operation

_Updated: 2025-11-21_

This document tracks the execution status for each phase required to bring Tribi to a fully autonomous operation. Every phase below contains a checklist that should be marked complete only when the underlying deliverables are demonstrably finished in `develop` (tests, docs, and deploy guides updated).

## Phase 0 – Baseline Verification & Smoke Tests

- [x] Read the core context docs (README, ARCHITECTURE, SPRINT_STATUS, BACKEND_HARDENING_COMPLETE, UI_POLISH_SUMMARY, MOBILE_APP_SUMMARY, REGRESSIONS_FIXED).
- [ ] Validate local start commands via `make` _and_ VS Code tasks (`Docker: Start Infrastructure`, `Backend/Web/Mobile` launchers).
- [ ] Document manual verification of backend `GET /health`, web `/health`, `/`, `/auth`, `/account`, and the happy-path mobile flow (login → browse → checkout → account) following `docs/manual_smoke_tests.md`.
- [ ] Capture any deviations/regressions in `REGRESSIONS_FIXED.md` or new tickets before advancing to Phase 1.

## Phase 1 – Real Payment Integration (Stripe-first)

- [x] Decide on provider + mode (Stripe PaymentIntents + verified webhooks) and capture env requirements (`docs/PAYMENTS_INTEGRATION.md`).
- [x] Extend backend payment provider abstraction with a production-grade implementation (`StripePaymentProvider`) plus secure webhook handling and idempotent intents.
- [x] Replace web checkout flow with real payment UX (Stripe Elements) and document the temporary state for mobile (legacy flow remains).
- [x] Add automated tests (provider mocks + webhook handling) and author `docs/PAYMENTS_INTEGRATION.md` with verification steps.

## Phase 2 – Real eSIM Provisioning / Inventory Automation

- [x] Pick initial provisioning strategy (ConnectedYou API-first) and update models/schemas accordingly (`provider_reference`, `provisioned_at`, `provider_payload`).
- [x] Ensure `/api/esims/activate` only issues real codes (or inventory assignments) once payment is confirmed, with retry/idempotency controls. _Status:_ live endpoint now reserves stock first and falls back to provider provisioning with idempotent updates.
- [ ] Build admin/import tooling or provider integration scripts plus customer notifications (email with QR/code) after activation. _Remaining:_ outbound messaging + final provider secrets.
- [x] Add regression tests for activation edge cases and document the flow in `docs/ESIM_AUTOMATION.md`.

## Phase 3 – Full Admin Panel

- [x] Enforce admin auth (backend guard + frontend routing) and expose `/api/admin/*` endpoints for catalog, orders, payments, eSIMs, and inventory. _Refs:_ `apps/backend/app/api/admin.py`, `docs/ADMIN.md`.
- [x] Ship responsive `/admin` UI (tables, filters, CRUD modals, toasts) covering catalog management, order/payment visibility, and eSIM stock alerts. _Refs:_ `apps/web/app/admin/*`.
- [x] Provide admin-focused tests plus docs describing permissions, modules, and operational runbooks. _Refs:_ `tests/test_admin_management.py`, `docs/ADMIN.md`, `docs/manual_smoke_tests.md`.

## Phase 4 – Internal Automation (Billing, CRM, Support)

- [x] Implement invoicing/export jobs (PDF/CSV) and admin download endpoints. _Refs:_ `/admin/exports/sales`, `services/billing.py`, `tests/test_billing_exports.py`.
- [x] Model support tickets + CRM fields, expose APIs/UI for lifecycle management, and ensure audit trails. _Refs:_ `apps/backend/app/models/auth_models.py`, `apps/backend/app/api/admin.py`, `apps/web/app/admin/support/page.tsx`, tests in `tests/test_admin_crm.py`.
- [x] Schedule background jobs (reminders, daily/weekly summaries) with observability around failures. _Refs:_ `app/jobs/*`, `app/main.py`, `tests/test_support_jobs.py`.
- [x] Document processes inside `docs/INTERNAL_AUTOMATION.md` with playbooks for finance/support teams. _Refs:_ `docs/INTERNAL_AUTOMATION.md`.

## Phase 5 – Analytics, Dashboards & Projections

- [x] Capture core product/commerce events (signup, checkout started, payment succeeded, eSIM activated) in a dedicated store.
- [x] Deliver backend analytics endpoints plus admin dashboards (charts, KPIs, trends) surfacing sales, conversion, and top SKUs.
- [x] Implement simple projection models (e.g., linear trend, moving average) and document assumptions in `docs/ANALYTICS.md`.

## Phase 6 – Infrastructure, Security & Observability Hardening

- [x] Enforce production-grade security defaults (cookie flags, secret rotation, webhook signatures, rate-limit tuning) and document rotations. _Refs:_ `apps/backend/app/api/auth.py`, `apps/backend/tests/test_auth_rate_limit.py`, `docs/SECURITY_ROTATION.md`, `BACKEND_HARDENING_COMPLETE.md`.
- [x] Add centralized logging/monitoring (structured logging, request IDs, optional Sentry, `/health` probes) with alerting hooks. _Refs:_ `apps/backend/app/core/logging_utils.py`, `apps/backend/app/main.py`, `docs/OBSERVABILITY.md`.
- [x] Upgrade CI/CD to cover multi-language tests/builds (backend, web, mobile) and document release steps. _Refs:_ `.github/workflows/ci.yml`, `docs/CI_CD.md`.
- [x] Keep `README.md`, `SPRINT_STATUS.md`, and this roadmap updated as each milestone moves to ✅. _Refs:_ `README.md`, `SPRINT_STATUS.md`.

> **How to use this file:** Before starting any new effort, update the relevant checklist here, link to supporting docs/PRs, and ensure test evidence is noted. Treat unchecked items as actionable backlog.
