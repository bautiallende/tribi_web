# Security Secret Rotation Guide

_Updated: 2025-11-21_

This runbook documents how to rotate every secret that protects authentication, payments, and provisioning flows. Follow these steps whenever a credential reaches its TTL or is suspected to be compromised.

## Scope & Owners

| Secret                     | Purpose                               | Storage                                                    | Default TTL | Owner         |
| -------------------------- | ------------------------------------- | ---------------------------------------------------------- | ----------- | ------------- |
| `JWT_SECRET`               | Sign user session tokens              | Backend `.env`, GitHub Actions secret `BACKEND_JWT_SECRET` | 90 days     | Backend lead  |
| `COOKIE_SECRET`            | Encrypt legacy cookies + CSRF entropy | Backend `.env`, GitHub Actions secret `COOKIE_SECRET`      | 90 days     | Backend lead  |
| `STRIPE_SECRET_KEY`        | Create/confirm payment intents        | Backend `.env`, Stripe dashboard                           | 60 days     | Payments lead |
| `STRIPE_WEBHOOK_SECRET`    | Verify Stripe webhook signatures      | Backend `.env`, Stripe dashboard                           | 60 days     | Payments lead |
| `CONNECTED_YOU_API_KEY`    | Provision eSIM inventory              | Backend `.env`, ConnectedYou console                       | 60 days     | Ops lead      |
| `CONNECTED_YOU_PARTNER_ID` | Associate API requests with Tribi     | Backend `.env`                                             | 180 days    | Ops lead      |
| `ESIM_PROVIDER` creds      | Any future provider tokens            | Backend `.env`                                             | 60 days     | Ops lead      |

> **Tip:** Keep staging and production secrets distinct. Rotate staging first to validate the playbook.

## General Rotation Procedure

1. **Schedule a window** during a low-traffic period. Inform support so they can watch login/payment channels.
2. **Generate a new value** using a hardware password manager or `openssl rand -hex 32`. Never reuse secrets across environments.
3. **Update secrets in source-of-truth vaults** (1Password, Azure Key Vault, etc.) and mirror them into `.env`, Kubernetes/Compose secrets, and GitHub Actions variables.
4. **Deploy in two steps**: first update background workers (if any), then API servers to avoid signature mismatches.
5. **Validate** using the smoke tests in `docs/manual_smoke_tests.md` (login, checkout, eSIM activation) plus `pytest apps/backend/tests/test_auth_cookies.py` and `pytest apps/backend/tests/test_auth_rate_limit.py::test_rate_limit_ip_daily_cap`.
6. **Purge residual sessions** when appropriate (see below) and monitor logs/alerts for anomalies for at least 30 minutes.

## JWT & Cookie Secrets

1. Generate two random strings (one per secret).
2. Update `.env`, `apps/backend/.env`, deployment secrets, and CI/CD secrets.
3. Redeploy backend. Existing JWTs will become invalid; notify users 10 minutes before redeploy so they expect a forced sign-in.
4. Verify:
   - POST `/api/auth/request-code` and `/api/auth/verify` succeed.
   - Cookie attributes show the expected `Secure`/`SameSite` flags (see `apps/backend/app/api/auth.py`).
   - `tests/test_auth_cookies.py` and `tests/test_auth_rate_limit.py` pass.

## Stripe API & Webhook Secrets

1. In the Stripe dashboard, create a new **restricted** secret key scoped to PaymentIntents + Webhooks.
2. Update backend env files and secrets store with `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`.
3. Run `stripe listen --forward-to localhost:8000/api/payments/webhook` locally to confirm the webhook secret before promoting to production.
4. Deploy backend, then trigger a $0.50 test payment to confirm `payment_intent.succeeded` updates orders.
5. Remove the previous webhook signing secret from Stripe once the new one is confirmed.

## ConnectedYou / eSIM Provider Tokens

1. Generate a new API key + partner token in the ConnectedYou console.
2. Update `CONNECTED_YOU_API_KEY`, `CONNECTED_YOU_PARTNER_ID`, and any provider-specific secrets.
3. Restart the backend job runner (if enabled) plus the API process.
4. Issue a staging order and confirm `/api/esims/activate` can reserve/provision inventory.

## Emergency Rotation

If a secret is suspected compromised:

1. Revoke the old secret in the provider dashboard immediately.
2. Rotate using the steps above but add:
   - Purge outstanding JWT cookies by redeploying and, if necessary, clearing CDN caches.
   - Temporarily force OTP max attempts to `RATE_LIMIT_CODES_PER_DAY=2` to slow attackers.
3. Conduct a post-incident review and document findings in `REGRESSIONS_FIXED.md`.

## References

- Enforcement logic: `apps/backend/app/api/auth.py`, `apps/backend/app/services/payment_providers.py`
- Config knobs: `apps/backend/app/core/config.py`, `.env.example`, `apps/backend/.env.example`
- Observability: follow-ups tracked under "Phase 6" in `docs/ROADMAP_AUTOMATION.md`
