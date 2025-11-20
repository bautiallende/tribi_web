# Roadmap Towards Autonomous Operation

_Updated: 2025-11-20_

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
- [ ] Ensure `/api/esims/activate` only issues real codes (or inventory assignments) once payment is confirmed, with retry/idempotency controls. _In progress:_ provider abstraction wired but still returns dry-run payloads until secrets provided.
- [ ] Build admin/import tooling or provider integration scripts plus customer notifications (email with QR/code) after activation.
- [ ] Add regression tests for activation edge cases and document the flow in `docs/ESIM_AUTOMATION.md`. _Doc updated with ConnectedYou plan; tests partially added (`test_esim_providers.py`)._

## Phase 3 – Full Admin Panel

- [ ] Enforce admin auth (backend guard + frontend routing) and expose `/api/admin/*` endpoints for catalog, orders, payments, eSIMs, and inventory.
- [ ] Ship responsive `/admin` UI (tables, filters, CRUD modals, toasts) covering catalog management, order/payment visibility, and eSIM stock alerts.
- [ ] Provide admin-focused tests plus `docs/ADMIN_PANEL.md` describing permissions, modules, and operational runbooks.

## Phase 4 – Internal Automation (Billing, CRM, Support)

- [ ] Implement invoicing/export jobs (PDF/CSV) and admin download endpoints.
- [ ] Model support tickets + CRM fields, expose APIs/UI for lifecycle management, and ensure audit trails.
- [ ] Schedule background jobs (reminders, daily/weekly summaries) with observability around failures.
- [ ] Document processes inside `docs/INTERNAL_AUTOMATION.md` with playbooks for finance/support teams.

## Phase 5 – Analytics, Dashboards & Projections

- [ ] Capture core product/commerce events (signup, checkout started, payment succeeded, eSIM activated) in a dedicated store.
- [ ] Deliver backend analytics endpoints plus admin dashboards (charts, KPIs, trends) surfacing sales, conversion, and top SKUs.
- [ ] Implement simple projection models (e.g., linear trend, moving average) and document assumptions in `docs/ANALYTICS.md`.

## Phase 6 – Infrastructure, Security & Observability Hardening

- [ ] Enforce production-grade security defaults (cookies, secret rotation, webhook signatures, rate-limit tuning) and document rotations.
- [ ] Add centralized logging/monitoring (e.g., Sentry, structured logs, dashboards) with alerting on health endpoints or job failures.
- [ ] Upgrade CI/CD to cover multi-language tests, builds, artifact publishing, and eventual deployment automation, documenting the release flow.
- [ ] Keep `README.md` + this roadmap updated as each milestone moves to ✅.

> **How to use this file:** Before starting any new effort, update the relevant checklist here, link to supporting docs/PRs, and ensure test evidence is noted. Treat unchecked items as actionable backlog.
