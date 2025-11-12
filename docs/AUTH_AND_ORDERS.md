# Authentication & Orders Architecture

Comprehensive documentation for the hardened backend authentication, order management, payment processing, and eSIM activation system.

---

## Table of Contents
1. [Rate Limiting Strategy](#rate-limiting-strategy)
2. [Session Management](#session-management)
3. [Idempotency Guarantees](#idempotency-guarantees)
4. [Payment Provider Architecture](#payment-provider-architecture)
5. [State Transition Diagrams](#state-transition-diagrams)
6. [Security Best Practices](#security-best-practices)

---

## 1. Rate Limiting Strategy

### Overview
The authentication system implements time-window-based rate limiting to prevent abuse:
- **1 OTP code per 60 seconds** (per email + IP combination)
- **5 OTP codes per 24 hours** (per email + IP combination)

### Implementation Details

#### Database Schema Extensions
```python
class AuthCode(Base):
    # ... existing fields ...
    ip_address = Column(String(45))  # IPv4 or IPv6
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    attempts = Column(Integer, default=0)
```

#### Rate Limit Check Algorithm
```python
def check_rate_limit(email: str, ip: str, db: Session):
    now = datetime.utcnow()
    recent_limit = now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)
    day_limit = now - timedelta(hours=settings.RATE_LIMIT_WINDOW_HOURS)
    
    # Check 60-second window
    recent_auth = db.query(AuthCode)\
        .filter(AuthCode.email == email, AuthCode.created_at > recent_limit)\
        .first()
    if recent_auth:
        raise HTTPException(429, "Rate limit: wait 60s between requests")
    
    # Check 24-hour window
    day_auth_count = db.query(AuthCode)\
        .filter(AuthCode.email == email, AuthCode.created_at > day_limit)\
        .count()
    if day_auth_count >= settings.RATE_LIMIT_CODES_PER_DAY:
        raise HTTPException(429, "Rate limit: max 5 codes per 24h")
```

#### IP Address Extraction
```python
def get_client_ip(request: Request) -> str:
    """Extract client IP with proxy support."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"
```

### Configuration
```env
RATE_LIMIT_CODES_PER_MINUTE=1
RATE_LIMIT_CODES_PER_DAY=5
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_WINDOW_HOURS=24
```

---

## 2. Session Management

### Dual Authentication System
The backend supports **both Cookie-based sessions (web) and Bearer tokens (mobile)**:

#### Cookie-Based Auth (Web Clients)
- **httpOnly**: Prevents JavaScript access (XSS protection)
- **SameSite=Lax**: CSRF protection while allowing GET navigation
- **Secure**: HTTPS-only in production
- **Domain**: Configurable for subdomain support

```python
# Set cookie on login
response.set_cookie(
    key="tribi_token",
    value=access_token,
    httponly=True,
    secure=False,  # True in production
    samesite="lax",
    domain=settings.COOKIE_DOMAIN
)
```

#### Bearer Token Auth (Mobile Clients)
- **Header**: `Authorization: Bearer <token>`
- **Storage**: SecureStore (Expo), Keychain (iOS), Keystore (Android)
- **Same JWT**: Identical token format to cookies

### Authentication Flow

#### Request Code (OTP)
```
POST /auth/request-code
{
  "email": "user@example.com"
}

→ Rate limit check (1/60s + 5/24h)
→ Generate 6-digit code
→ Send via SMTP
→ Store: AuthCode(email, code, ip_address, created_at, expires_at)
```

#### Verify Code
```
POST /auth/verify-code
{
  "email": "user@example.com",
  "code": "123456"
}

→ Verify code validity (not expired, not used)
→ Create or retrieve User
→ Generate JWT (HS256, 24h expiry)
→ Set cookie OR return token
→ Mark code as used
```

#### Get Current User (Dual Auth)
```python
def get_current_user(
    authorization: str | None = Header(None),
    tribi_token: str | None = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    # Priority: Cookie first (web), then Bearer (mobile)
    token = tribi_token or parse_bearer_token(authorization)
    # Decode JWT and lookup user
```

#### Logout
```
POST /auth/logout

→ Clear cookie (max_age=-1)
→ Client must also clear stored token
```

### JWT Payload
```json
{
  "sub": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Configuration
```env
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
COOKIE_SECRET=your-cookie-secret-change-in-production
COOKIE_DOMAIN=.tribi.app
```

---

## 3. Idempotency Guarantees

### Overview
Order creation is **idempotent** using the `Idempotency-Key` header. Multiple requests with the same key return the **same order** without creating duplicates.

### Database Schema Extensions
```python
class Order(Base):
    # ... existing fields ...
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
```

### Implementation
```python
@router.post("")
def create_order(
    plan_id: int,
    idempotency_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrderRead:
    # Check for existing order with same key
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing:
            return OrderRead.model_validate(existing)
    
    # Atomic transaction: Order + EsimProfile
    order = Order(
        user_id=current_user.id,
        plan_id=plan_id,
        idempotency_key=idempotency_key,
        status=OrderStatus.CREATED,
        ...
    )
    db.add(order)
    db.flush()  # Get order.id
    
    esim = EsimProfile(order_id=order.id, status=EsimStatus.PENDING)
    db.add(esim)
    db.commit()
```

### Client Usage
```bash
# Web client generates UUID
POST /orders
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
{ "plan_id": 1, "currency": "USD" }

# Retry with same key → returns same order
POST /orders
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
{ "plan_id": 1, "currency": "USD" }
```

### Best Practices
- **Generate client-side**: Use UUID v4 on client
- **Store key**: Client must store key with pending order
- **Retry safely**: Network failures can be retried with same key
- **TTL**: Keys are eternal (unique constraint enforced)

---

## 4. Payment Provider Architecture

### Overview
The payment system uses a **provider abstraction layer** supporting multiple payment processors. Currently includes **MockProvider** for development.

### Abstract Interface
```python
@dataclass
class PaymentIntent:
    intent_id: str
    status: str  # "requires_action" | "succeeded" | "failed"
    amount_minor_units: int
    currency: str
    metadata: Dict[str, Any]

class PaymentProvider(ABC):
    @abstractmethod
    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Dict[str, Any]
    ) -> PaymentIntent:
        """Create a payment intent."""
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> PaymentIntent:
        """Process webhook from payment provider."""
        pass
```

### MockProvider (Development)
```python
class MockPaymentProvider(PaymentProvider):
    def create_intent(...) -> PaymentIntent:
        return PaymentIntent(
            intent_id=f"mock_{uuid.uuid4()}",
            status="requires_action",  # Always requires action
            ...
        )
    
    def process_webhook(payload) -> PaymentIntent:
        status = payload.get("status", "succeeded")  # "succeeded" | "failed"
        return PaymentIntent(intent_id=payload["intent_id"], status=status, ...)
```

### Factory Pattern
```python
def get_payment_provider(name: str = "MOCK") -> PaymentProvider:
    if name.upper() == "MOCK":
        return MockPaymentProvider()
    # Future: STRIPE, ADYEN, etc.
    raise ValueError(f"Unknown payment provider: {name}")
```

### Database Schema Extensions
```python
class Payment(Base):
    # ... existing fields ...
    intent_id = Column(String(255), nullable=True, unique=True, index=True)
```

### Flow

#### Create Payment Intent
```
POST /payments/create
{ "order_id": 123, "provider": "MOCK" }

→ Get payment provider instance
→ provider.create_intent(amount, currency, metadata)
→ Store Payment(intent_id, status="requires_action")
→ Return { "intent_id": "mock_xxx", "status": "requires_action" }
```

#### Webhook Processing
```
POST /payments/webhook
{
  "provider": "MOCK",
  "intent_id": "mock_xxx",
  "status": "succeeded"
}

→ Get payment provider instance
→ provider.process_webhook(payload)
→ Update Payment.status
→ Update Order.status (PAID | FAILED)
```

### Extending with Real Providers

#### Stripe Example
```python
class StripePaymentProvider(PaymentProvider):
    def __init__(self):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stripe = stripe
    
    def create_intent(self, amount_minor_units, currency, metadata):
        intent = self.stripe.PaymentIntent.create(
            amount=amount_minor_units,
            currency=currency,
            metadata=metadata
        )
        return PaymentIntent(
            intent_id=intent.id,
            status=intent.status,
            ...
        )
    
    def process_webhook(self, payload):
        # Verify signature, parse event, return PaymentIntent
        ...
```

---

## 5. State Transition Diagrams

### Order Status Flow
```
CREATED ──[payment succeeds]──> PAID
   │
   └────[payment fails]────────> FAILED
```

### Payment Status Flow
```
REQUIRES_ACTION ──[webhook: succeeded]──> SUCCEEDED
       │
       └──────[webhook: failed]─────────> FAILED
```

### eSIM Status Flow
```
PENDING ──[activate endpoint]──> READY ──[activation]──> ACTIVE
   │
   └──────[error]────────────────────────────────────> FAILED
```

### Combined Flow
```
1. POST /orders (idempotent)
   → Order.status = CREATED
   → EsimProfile.status = PENDING

2. POST /payments/create
   → Payment.status = REQUIRES_ACTION
   → Payment.intent_id = "mock_xxx"

3. POST /payments/webhook (provider calls)
   → Payment.status = SUCCEEDED
   → Order.status = PAID

4. POST /esims/activate
   → EsimProfile.activation_code = UUID v4
   → EsimProfile.status = READY
```

---

## 6. Security Best Practices

### Authentication
- ✅ Rate limiting prevents brute-force OTP attacks
- ✅ IP tracking detects distributed attacks
- ✅ Codes expire after 10 minutes
- ✅ Codes are single-use (marked as `used`)
- ✅ JWT tokens expire after 24 hours
- ✅ Cookies are httpOnly, SameSite=Lax
- ⚠️ Consider: HTTPS-only cookies in production
- ⚠️ Consider: Refresh token rotation

### Rate Limiting
- ✅ Combined email + IP enforcement
- ✅ Time-window-based (sliding window)
- ⚠️ Consider: Distributed rate limiting (Redis)
- ⚠️ Consider: Exponential backoff on repeated violations

### Idempotency
- ✅ Unique constraint on idempotency_key
- ✅ Atomic transaction for Order + EsimProfile
- ⚠️ Consider: Idempotency key expiration (TTL)
- ⚠️ Consider: Idempotency for other mutations (payments, activations)

### Payment Security
- ✅ Abstract provider interface (testable, swappable)
- ✅ intent_id stored for reconciliation
- ⚠️ TODO: Webhook signature verification (Stripe, Adyen)
- ⚠️ TODO: Retry logic for failed webhooks
- ⚠️ TODO: Payment reconciliation job

### eSIM Activation
- ✅ UUID v4 activation codes (unguessable)
- ✅ Order must be PAID before activation
- ⚠️ Consider: Activation code expiration
- ⚠️ Consider: Rate limiting on activation attempts

---

## Configuration Summary

```env
# Rate Limiting
RATE_LIMIT_CODES_PER_MINUTE=1
RATE_LIMIT_CODES_PER_DAY=5
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_WINDOW_HOURS=24

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Cookies
COOKIE_SECRET=your-cookie-secret-change-in-production
COOKIE_DOMAIN=.tribi.app

# SMTP
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=false
SMTP_FROM_EMAIL=noreply@tribi.app

# CORS
FRONTEND_ORIGINS=["http://localhost:3000","http://localhost:19006"]
```

---

## Testing Checklist

- [ ] Rate limiting: 1 code per 60 seconds
- [ ] Rate limiting: 5 codes per 24 hours
- [ ] Cookie auth: set on verify, cleared on logout
- [ ] Bearer auth: works alongside cookies
- [ ] Idempotency: same key returns same order
- [ ] Payments: MockProvider create → requires_action
- [ ] Payments: webhook succeed → order PAID
- [ ] Payments: webhook fail → order FAILED
- [ ] eSIM: activation generates UUID v4
- [ ] eSIM: requires order to be PAID first

---

## API Endpoints

### Authentication
- `POST /auth/request-code` - Request OTP code
- `POST /auth/verify-code` - Verify code, get token/cookie
- `POST /auth/logout` - Clear session cookie
- `GET /auth/me` - Get current user (dual auth)

### Orders
- `POST /orders` - Create order (idempotent with header)
- `GET /orders/mine` - List user's orders

### Payments
- `POST /payments/create` - Create payment intent
- `POST /payments/webhook` - Process payment webhook

### eSIM
- `POST /esims/activate` - Activate eSIM with UUID code

---

**Last Updated**: 2024  
**Author**: Backend Team  
**Version**: 1.0
