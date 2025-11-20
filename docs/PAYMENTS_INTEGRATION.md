# Payments Integration (Stripe)

_Last updated: 2025-11-20_

This guide documents the production-ready Stripe integration that now powers Tribi checkout flows. It explains the environment variables you must configure, how the backend and frontend interact, webhook setup, and how to test the flow end to end.

## Environment Variables

Add the following values to your `.env` (backend) and `.env.local` (web) files. All keys already exist in `.env.example`.

| Variable                 | Description                                                                                 | Example       |
| ------------------------ | ------------------------------------------------------------------------------------------- | ------------- |
| `PAYMENT_PROVIDER`       | Default provider enum used by the backend. Use `STRIPE` in production.                      | `STRIPE`      |
| `STRIPE_SECRET_KEY`      | Server-side API key (starts with `sk_live_` or `sk_test_`). Needed by the backend provider. | `sk_test_123` |
| `STRIPE_PUBLISHABLE_KEY` | Client-side key injected into the web app via `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.         | `pk_test_123` |
| `STRIPE_WEBHOOK_SECRET`  | Secret generated from the Stripe CLI/dashboard for the payments webhook endpoint.           | `whsec_abc`   |
| `DEFAULT_CURRENCY`       | Fallback ISO currency; used when orders do not override `currency`.                         | `USD`         |

> **Note:** For the Next.js app you must expose the publishable key as `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`. The backend reads the same value from `STRIPE_PUBLISHABLE_KEY` when returning a PaymentIntent to the client.

## Backend Flow

File references:

- `apps/backend/app/services/payment_providers.py`
- `apps/backend/app/api/orders.py`

The flow is split across three responsibilities:

1. **Payment Intent creation** – `POST /api/payments/create`
   - Requires an authenticated user and `order_id`.
   - Delegates to `StripePaymentProvider.create_intent`, which normalizes currency, attaches metadata (`order_id`, `user_id`), and optionally forwards an idempotency key (header `Idempotency-Key`).
   - Stores a Payment row linked to the order and returns `{ intent_id, client_secret, publishable_key }`.
2. **Webhook handling** – `POST /api/payments/webhook`
   - Stripe sends PaymentIntent lifecycle events.
   - `StripePaymentProvider.parse_webhook_payload` verifies the `Stripe-Signature` header using `STRIPE_WEBHOOK_SECRET`.
   - `process_webhook` maps the Stripe payload into the internal `PaymentIntent` dataclass; `_map_payment_status` updates both the Payment and Order rows.
3. **eSIM fulfillment** – `POST /api/esims/activate`
   - Called after the client confirms the PaymentIntent.
   - Guards on ownership + order status. When successful it populates `activation_code`, `qr_payload`, and returns the `EsimProfileRead` payload shown on the success screen.

### Status Mapping

Stripe → Tribi mapping lives in `_map_payment_status`:

- `succeeded` → `PaymentStatus.SUCCEEDED` → order becomes `OrderStatus.PAID`.
- `payment_failed` → `PaymentStatus.FAILED` → order becomes `OrderStatus.PAYMENT_FAILED`.
- Everything else → `PaymentStatus.REQUIRES_ACTION` (order stays `CREATED`).

## Frontend Flow (Next.js)

File reference: `apps/web/app/checkout/page.tsx`.

The React page has five UI states (`review`, `collect`, `processing`, `success`, `error`). The steps are:

1. Resolve `auth_token` from `localStorage`, block navigation if missing.
2. Fetch `/api/orders/mine` and cache the selected order details (`order_id` comes from the query string).
3. When the user clicks **Start Stripe Checkout**, call `POST /api/payments/create` and store the returned `client_secret`/`publishable_key`.
4. Render `<Elements>` with the `client_secret`, `<PaymentElement>`, and `<LinkAuthenticationElement>`.
5. Call `stripe.confirmPayment({ redirect: 'if_required' })` inside the form handler.
6. After a successful confirmation, call `POST /api/esims/activate` to provision the actual eSIM and show activation information plus copy helpers.

Because the backend returns the publishable key, the page can load Stripe via `loadStripe(publishableKey)` dynamically. Until the first PaymentIntent is created it falls back to `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` for development.

## Webhook Configuration

1. Start the backend (`make dev` or VS Code task `All: Start Development (Monorepo)`).
2. Use the Stripe CLI to forward events:

   ```bash
   stripe listen --forward-to http://localhost:8000/api/payments/webhook
   ```

3. Copy the printed `whsec_...` secret into `STRIPE_WEBHOOK_SECRET`.
4. Trigger test events, e.g. `stripe trigger payment_intent.succeeded`.
5. Watch backend logs; you should see `intent_status` updates and the linked order status flipping to `paid`.

In production deploys, configure the webhook endpoint in the Stripe dashboard with the same secret and ensure the infra layer terminates TLS before forwarding to FastAPI.

## Testing & Verification

### Automated

Run the dedicated provider tests (already wired into CI):

```bash
cd apps/backend
pytest tests/test_payments_stripe.py
```

These tests cover intent creation arguments, webhook parsing, signature verification, and error handling when the header is absent.

### Manual Smoke Test

1. Start Docker infrastructure + backend + web: `make dev` or the VS Code tasks listed in `README.md`.
2. Create an order via the web app (select a plan, proceed to checkout) or the `POST /api/orders` API.
3. Navigate to `/checkout?order_id=<ID>` and click **Start Stripe Checkout**.
4. Use a Stripe test card (e.g. `4242 4242 4242 4242`, any future expiry) in the PaymentElement.
5. After confirmation, ensure the eSIM activation card renders and verify the order status in `/account` is **Paid**.
6. Optional: fire a webhook event to confirm webhook idempotency (`stripe trigger payment_intent.succeeded`).

### Troubleshooting

- Missing `client_secret` usually means `STRIPE_SECRET_KEY` is incorrect or the backend default provider is not `STRIPE`.
- Webhook `400 Missing intent_id` indicates Stripe is sending an event type we do not parse; confirm the endpoint is configured for `payment_intent.*` events.
- If the UI stalls on “Processing…”, open DevTools → Network to confirm `/api/esims/activate` returned 200. A 409 often means the order never became `paid` (check webhook delivery).

## Operational Checklist

- [x] Backend provider + webhook path implemented and covered by tests.
- [x] Web checkout flow upgraded to Stripe Elements.
- [x] Documented environment and verification steps (this file).
- [ ] Mobile client still uses the legacy mock checkout; update after Phase 1. (See `ROADMAP_AUTOMATION.md`.)

Keep this document up to date whenever new providers, currencies, or flows are added.
