# Observability & Alerting

_Updated: 2025-11-21_

Phase 6 introduces a lightweight observability stack so every environment emits structured logs, forwards errors to an APM (Sentry), and exposes health endpoints that can drive uptime checks.

## Logging

- Configure via the following env vars (`.env` + `apps/backend/.env`):
  - `LOG_LEVEL` (`DEBUG|INFO|WARNING|ERROR|CRITICAL`, default `INFO`).
  - `LOG_FORMAT` (`console` or `json`). JSON output is compatible with Logstash, Datadog, and CloudWatch Logs.
  - `ENABLE_REQUEST_LOGS` (`true|false`) toggles the HTTP access log middleware.
- Every request receives an `X-Request-ID` header. Pass your own header to propagate IDs from API gateways. Each log line includes `request_id` for correlation.
- The formatter lives in `apps/backend/app/core/logging_utils.py`. It injects context vars and supports JSON encoding for ingestion pipelines.
- Background jobs write structured metrics via `logger.info("Ticket SLA job", extra={"metrics": stats})`. The new formatter preserves the metrics under the same JSON payload.

## Error Monitoring (Sentry)

- Set `SENTRY_DSN` plus optional sampling controls `SENTRY_TRACES_SAMPLE_RATE` and `SENTRY_PROFILES_SAMPLE_RATE`.
- When configured, `app/main.py` bootstraps Sentry’s FastAPI integration and tags each event with `environment=settings.ENVIRONMENT`.
- Use staging DSNs to exercise the integration before production. Disable traces by leaving the sample rates at `0.0`.

## Health Endpoints

| Endpoint           | Purpose                      | Response             |
| ------------------ | ---------------------------- | -------------------- | ------------------------------------- | ----------------------------------------------------------- |
| `GET /health`      | Lightweight liveness probe   | `{ "status": "ok" }` |
| `GET /health/full` | Readiness + dependency check | `{ "status": "ok     | degraded", "database": {"status": "ok | error"}, "jobs": {"enabled": bool, "running": bool, ...} }` |

- `/health/full` executes `SELECT 1` via SQLAlchemy and reports job scheduler status (running, last digest timestamps). Integrate this endpoint with uptime monitors and alert if `status != ok`.

## Alerting Playbook

1. **Logging alerts:** configure your log pipeline to watch for `level >= ERROR` and filter on `request_failed` or `healthcheck_db_failed` messages.
2. **Sentry alerts:** use Sentry’s issue alerting to notify #ops on new issues or sustained error rates.
3. **Health checks:** set a synthetic monitor to query `/health` every minute and `/health/full` every 5 minutes. Alert when:
   - Liveness fails (no response / non-200).
   - Readiness returns `status=degraded` or `database.status=error`.

## Validation Checklist

- [ ] `LOG_FORMAT=json` produces valid JSON entries.
- [ ] `X-Request-ID` header is echoed back and visible in logs.
- [ ] Sentry receives a test exception (set DSN + trigger `/boom` in staging).
- [ ] `/health` and `/health/full` succeed locally and in staging. Hook into your infrastructure monitors.
