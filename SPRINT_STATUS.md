# 📊 Sprint Status: Backend + MySQL ✅ | Web/Mobile 🚧

## Current State

### Backend: ✅ 100% COMPLETE

**Database & Models:**
- ✅ MySQL `tribi_dev` schema created
- ✅ All 8 tables created (users, auth_codes, orders, payments, esim_profiles, etc.)
- ✅ Setup script: `python setup_mysql.py`

**API Endpoints:**
- ✅ `POST /auth/request-code` - OTP email request
- ✅ `POST /auth/verify` - OTP verification + JWT issuance
- ✅ `GET /auth/me` - User profile (JWT protected)
- ✅ `POST /orders` - Create order (JWT protected)
- ✅ `GET /orders/mine` - List user orders (JWT protected)
- ✅ `POST /payments/create` - MOCK payment (JWT protected)
- ✅ `POST /payments/webhook` - Payment webhook
- ✅ `POST /esims/activate` - Activate eSIM stub (JWT protected)

**Testing:**
- ✅ 5 auth endpoint tests PASSING
- ✅ 3 existing tests PASSING
- ✅ **Total: 8/8 tests PASSING** ✅

**Configuration:**
- ✅ `.env` file with credentials (root:1234@localhost)
- ✅ All env vars loaded from config.py
- ✅ JWT, Email, Payment, Database settings configured

### Documentation:
- ✅ `MYSQL_SETUP.md` - Complete MySQL guide
- ✅ `QUICKSTART.md` - Daily dev workflow

---

## Next Steps: Web UI 🚧

### Task 1: Create Web Pages

**Pages to Create:**
1. `/auth` - OTP Input Form
   - Email input
   - OTP 6-digit input field
   - JWT token storage (httpOnly cookie)
   - Redirect to /plans after login

2. `/checkout/[orderId]` - Payment Confirmation
   - Show plan details
   - Show price
   - MOCK payment button
   - Confirmation screen

3. `/orders/[orderId]` - Order Details
   - Order status (created/paid/failed)
   - eSIM activation code (if paid)
   - QR code or download option

4. `/account` - User Profile
   - Show user email/name
   - List all user's orders
   - Show active eSIMs

**Tech Stack:**
- Next.js 14+ (existing)
- TailwindCSS (existing)
- TypeScript
- API client: fetch or axios

**Flow:**
```
/plans/[iso2]
    ↓ [Select Plan]
/checkout/[orderId] (POST /orders)
    ↓ [Pay MOCK]
/orders/[orderId] (GET /orders/mine)
    ↓ [Activate eSIM]
/account (GET /auth/me)
```

### Task 2: API Integration Utilities

Create `apps/web/utils/api.ts`:
- Fetch JWT from cookie
- Axios/fetch wrapper with auth headers
- Error handling
- Types for responses

Create `apps/web/utils/esimSupport.ts`:
- Detect device support (iPhone XS+, Android 5+)
- Show warnings/compatibility notices

### Task 3: Mobile Screens

**Screens:**
- OTP Input (similar to web)
- Plan Selection + Purchase
- Order Status
- Account / eSIM Management

**Tech:**
- React Native / Expo
- SecureStore for JWT
- Same backend API

---

## How to Use MySQL Setup

### One-time Setup

```powershell
cd apps/backend
python setup_mysql.py
```

### Daily Development

```powershell
# Terminal 1: Start Backend
cd apps/backend
python -m uvicorn app.main:app --reload
# http://localhost:8000/docs

# Terminal 2: Start Web
cd apps/web
npm run dev
# http://localhost:3000

# Terminal 3: Run Tests
cd apps/backend
python -m pytest tests/ -v -w  # -w to avoid warnings
```

### Check Database

```powershell
mysql -h localhost -u root -p1234 -D tribi_dev

# View tables
SHOW TABLES;

# Check users
SELECT * FROM users;
```

---

## Env Configuration

File: `apps/backend/.env`

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=tribi_dev
JWT_SECRET=dev-secret-key-change-in-prod
PAYMENT_PROVIDER=MOCK
```

---

## Success Criteria for Web Pages

- [ ] /auth page works (OTP request → verify → JWT)
- [ ] /checkout creates order via API
- [ ] /orders shows order status + activation code
- [ ] /account shows user profile + orders
- [ ] JWT persisted in httpOnly cookie
- [ ] CORS working (localhost:3000 ↔ :8000)
- [ ] All pages responsive

---

## Git Status

- Latest commit: "feat: setup MySQL local development environment"
- Branch: main
- Tests: ✅ 8/8 passing

---

## Commands Reference

```powershell
# Setup MySQL (one-time)
python setup_mysql.py

# Run backend
python -m uvicorn app.main:app --reload

# Run tests
python -m pytest tests/ -v

# Run web
npm run dev

# Database CLI
mysql -h localhost -u root -p1234 -D tribi_dev
```

---

**Next Action:** Start with creating `/auth` page component → integrate with POST /auth/request-code endpoint
