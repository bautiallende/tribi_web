# ConnectedYou Integration Blueprint

_Last updated: 2025-11-20_

This note tracks everything needed to flip Tribi from the local eSIM generator to the ConnectedYou platform. The code scaffolding already exists (`app/services/esim_providers.py`), so connecting “for real” becomes a configuration exercise.

## 1. Credentials & Environment

| Variable                        | Description                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| `ESIM_PROVIDER`                 | Set to `CONNECTED_YOU` once we are ready for live traffic.                                       |
| `CONNECTED_YOU_BASE_URL`        | Sandbox: `https://sandbox.api.connectedyou.com`; Production will be shared by ConnectedYou.      |
| `CONNECTED_YOU_API_KEY`         | API key issued per partner. Required when `CONNECTED_YOU_DRY_RUN=false`.                         |
| `CONNECTED_YOU_PARTNER_ID`      | Partner identifier appended to each request. Required for both dry-run and live.                 |
| `CONNECTED_YOU_TIMEOUT_SECONDS` | HTTP timeout (seconds). Default: 15.                                                             |
| `CONNECTED_YOU_DRY_RUN`         | When `true`, we skip the HTTP call and return deterministic fake payloads (used in dev/staging). |

Store the secrets in `.env` (backend) and the deployment vault once provided.

## 2. API Contract (Draft)

```
POST /partners/orders
Headers:
  Content-Type: application/json
  x-api-key: <CONNECTED_YOU_API_KEY>
Body:
{
  "partnerId": "<CONNECTED_YOU_PARTNER_ID>",
  "orderReference": "order-<OrderID>",
  "planCode": "<External Plan Code>",
  "countryIso2": "ES",
  "quantity": 1,
  "customer": { "email": "user@example.com", "name": "Test User" },
  "metadata": { "order_id": 123, "plan_name": "Spain 5GB" }
}
```

Expected response (simplified):

```
{
  "data": {
    "orderReference": "order-123",
    "activationCode": "LPA:1$XYZ",
    "iccid": "8901120200045678901",
    "qrCode": "LPA:1$XYZ",
    "instructions": "Install via Settings..."
  }
}
```

Every response is stored on `esim_profiles.provider_payload` for auditing.

## 3. Current Code Path

1. `/api/esims/activate` fetches the configured provider via `get_esim_provider()`.
2. When `ESIM_PROVIDER=LOCAL`, the legacy UUID behavior persists but records now receive `provider_reference=None`, `provisioned_at`, and `provider_payload` metadata.
3. When `ESIM_PROVIDER=CONNECTED_YOU` **and** `CONNECTED_YOU_DRY_RUN=true`, the provider logs the payload we would send and returns fake but realistic activation data.
4. Once `CONNECTED_YOU_DRY_RUN=false`, the provider will POST to `CONNECTED_YOU_BASE_URL` and persist the actual activation data. All failures raise `EsimProvisioningError`, which surfaces as HTTP 502 to the client and logs details for ops.

## 4. Go-Live Checklist

- [ ] Receive sandbox credentials from ConnectedYou and validate via `pytest apps/backend/tests/test_esim_providers.py -k connected_you` (adjust fixtures) plus a manual `/api/esims/activate` call with `CONNECTED_YOU_DRY_RUN=false` against sandbox.
- [ ] Map catalog SKUs to ConnectedYou `planCode` values (extend `Plan.plan_snapshot` with `external_id`).
- [ ] Confirm webhook/notification expectations (do they send status updates? implement later if needed).
- [ ] Update `docs/manual_smoke_tests.md` to include “ConnectedYou activation” scenario.
- [ ] For production deploys, rotate secrets via the infra vault and set `ESIM_PROVIDER=CONNECTED_YOU`, `CONNECTED_YOU_DRY_RUN=false`.

## 5. Troubleshooting Notes

- Missing `partnerId`/`apiKey` ⇒ the provider raises `EsimProvisioningError` before making the HTTP call. Check environment variables.
- HTTP `4xx/5xx` ⇒ logged at `ERROR` level with the exception message; the response body is stored inside the raised exception message and the API returns `502` to the client.
- Duplicate activation attempts: `EsimProfile.provisioned_at` and `provider_reference` are already populated after the first success. Future calls should detect this (next task: add guard + idempotent response).

Keeping this doc up to date shortens the handoff when ConnectedYou finalizes onboarding.
