# CI/CD & Release Flow

_Updated: 2025-11-21_

This document describes the GitHub Actions workflows that guard the monorepo plus the manual release steps required until automated deployments are introduced.

## Continuous Integration (ci.yml)

Trigger: every push/PR targeting `main` or `develop`.

Key features:

- **Concurrency guard** cancels redundant runs per ref, keeping queues clean.
- **Backend job** (Python 3.10 & 3.11): installs dependencies, runs `ruff check .`, and executes `pytest tests/ -v --tb=short`.
- **Web job** (Node 18 & 20): `npm ci`, then enforces `npm run lint`, `npm run typecheck`, and `npm run build`.
- **Mobile job** (Node 18): `npm ci` and `npm run typecheck` to ensure Expo code stays type-safe.
- Built-in caching for pip and npm lockfiles to speed pipelines.

### Adding Checks

- Backend tooling can be extended by editing `.github/workflows/ci.yml` to add new steps (e.g., `black --check`).
- Frontend commands run inside app directories—update `apps/web/package.json` scripts as needed.
- Mobile job currently performs TypeScript checks; add lint/tests when those scripts exist.

## Release Process (Manual for now)

1. **Code Freeze:** ensure `develop` is green (CI passing) and docs are up to date (`README.md`, `docs/ROADMAP_AUTOMATION.md`).
2. **Versioning:** bump app versions where necessary (backend `pyproject` when added, web/mobile `package.json`). Tag release with `vYYYY.MM.DD` format.
3. **Merge to Main:** create a PR from `develop` → `main`. CI must succeed. Obtain at least one approval.
4. **Smoke Tests:** after merging, run `make dev` locally or in staging, execute `docs/manual_smoke_tests.md`, and verify `/health/full`.
5. **Deploy:** follow infrastructure-specific steps (Docker/VM/Kubernetes). Ensure `.env` secrets are updated per `docs/SECURITY_ROTATION.md` and observability knobs per `docs/OBSERVABILITY.md`.
6. **Post-Deploy Checks:** monitor Sentry (if enabled), logs, `/health/full`, and admin dashboards for at least 30 minutes.
7. **Tag & Changelog:** push the release tag, update `SPRINT_STATUS.md` or release notes, and communicate to stakeholders.

## Future Automation Ideas

- Add deployment jobs (e.g., to staging/prod) triggered on tags once infrastructure is ready.
- Generate changelogs automatically via `git describe` + conventional commits.
- Gate merges with required status checks (GitHub branch protection on `develop` and `main`).
- Publish Docker images or Expo build artifacts once pipelines are expanded.
