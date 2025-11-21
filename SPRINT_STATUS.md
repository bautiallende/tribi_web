# 📊 Sprint Status — Phase 6 (Infrastructure / Security / Observability)

_Last updated: 2025-11-21_

## Snapshot

- **Branch:** `develop`
- **CI:** ✅ `.github/workflows/ci.yml` (backend, web, mobile) — runs on pushes/PRs to `main` & `develop` with concurrency guard.
- **Focus:** Phase 6 hardening (security defaults, observability, CI/CD, documentation).

## Recent Highlights

1. **Security defaults** — Cookies auto-align with environment (`Secure`/`SameSite`), per-IP OTP quotas throttle shared networks, and Stripe webhooks enforce signature validation. See `apps/backend/app/api/auth.py` + `docs/SECURITY_ROTATION.md`.
2. **Observability** — Structured logging with request IDs, optional Sentry integration, and `/health` + `/health/full` endpoints documented in `docs/OBSERVABILITY.md`.
3. **CI/CD** — GitHub Actions lint/test backend (Python 3.10/3.11), lint/typecheck/build the web app (Node 18/20), and typecheck the Expo mobile app. Manual release flow captured in `docs/CI_CD.md`.

## Backend Status — ✅ Feature Complete

- Auth, catalog, orders, payments, admin, and background jobs are live.
- Structured logging defined in `app/core/logging_utils.py`; each request receives an `X-Request-ID` echoed back.
- Health probes:
  - `GET /health` → `{ "status": "ok" }`
  - `GET /health/full` → includes DB connectivity + scheduler state.
- Key tests: `test_auth_cookies.py`, `test_auth_rate_limit.py`, `test_health.py` (run via `pytest apps/backend/tests`).

## Web Status — ✅ Admin + Catalog Delivered

- Next.js App Router pages cover marketing, catalog, checkout, and `/admin` dashboards.
- CI enforces `npm run lint`, `npm run typecheck`, and `npm run build` on Node 18/20.
- Observability env vars bubble through `.env` + `next.config.js` for telemetry alignment.

## Mobile Status — 🚧 QA Ready

- Expo app includes catalog browsing, OTP login, checkout, and account views.
- `npm run typecheck` ensures TS safety (wired into CI). Lint/tests to follow once scripts exist.

## CI/CD & Release Flow

- Workflow file: `.github/workflows/ci.yml` (concurrency guard, pip/npm caches, multi-runtime matrix).
- Release doc: `docs/CI_CD.md` covers verification, merge strategy, tagging, smoke tests, and post-deploy monitoring.
- Next automation target: add deployment stages once hosting targets are finalized.

## Observability & Operations

- Configure via env vars: `LOG_LEVEL`, `LOG_FORMAT`, `ENABLE_REQUEST_LOGS`, `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_PROFILES_SAMPLE_RATE`.
- `docs/OBSERVABILITY.md` details alerting playbooks (logs, Sentry, `/health` monitors).
- `/health/full` output is ready for uptime monitors—surface alerts if status != `ok` or DB fails.

## Outstanding Work

- [ ] Finalize doc refresh (roll Phase 6 changes into README, tutorials, and roadmap summary).
- [ ] Define Phase 7 scope (deployment automation + advanced analytics).

## Quick Commands

```powershell
# Backend dev server
cd apps/backend
uvicorn app.main:app --reload

# Backend tests + lint
pytest tests -v --tb=short
ruff check .

# Web dev server
cd apps/web
npm run dev

# Mobile typecheck
cd apps/mobile
npm run typecheck

# Run full CI steps locally (pre-PR)

npm install
```

## Verification Checklist

- [x] OTP login issues secure cookies + enforces per-IP quota.
- [x] `/health` + `/health/full` return `status=ok` locally.
- [x] CI green on latest `develop` push.
- [ ] Docs updated to include Phase 6 changelog + operator instructions.
      Create `apps/web/utils/api.ts`:
