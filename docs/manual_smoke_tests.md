# Manual Smoke Tests - Tribi eSIM Platform

This document provides comprehensive manual testing steps for both web and mobile applications after the recent regression fixes and improvements.

## Prerequisites

Before testing, ensure:

1. **Backend is running:**

   ```bash
   cd apps/backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Database is running (MySQL):**

   - Docker: `docker-compose -f infrastructure/docker-compose.yml up -d`
   - Or local MySQL on port 3306

3. **Backend migrations applied:**

   ```bash
   cd apps/backend
   alembic upgrade head
   ```

4. **Check backend health:**
   - Open: http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

---

## BACKEND API TESTS – INVENTORY & PROVIDER FLOW

### Test A: Inventory-First eSIM Activation

1. **Seed inventory row** (psql/MySQL shell):

   ```sql
   INSERT INTO esim_inventory (plan_id, activation_code, iccid, qr_payload, instructions, status)
   VALUES (123, 'INV-SMOKE-001', '89010000000000000123', 'LPA:1$INV-SMOKE-001', 'Scan QR to install', 'AVAILABLE');
   ```

   Replace `plan_id` with the plan you will purchase.

2. **Authenticate and create a paid order** using the backend tests helper or curl:

   ```bash
   # Request + verify OTP to obtain token (reuse web auth steps)
   curl -H "Authorization: Bearer $TOKEN" -d '{"plan_id":123,"currency":"USD"}' http://localhost:8000/api/orders
   curl -H "Authorization: Bearer $TOKEN" -d '{"order_id":<ORDER_ID>,"provider":"MOCK"}' http://localhost:8000/api/payments/create
   curl -X POST http://localhost:8000/api/payments/webhook -d '{"provider":"MOCK","intent_id":"<INTENT_ID>","status":"succeeded"}'
   ```

3. **Activate the eSIM**:

   ```bash
   curl -H "Authorization: Bearer $TOKEN" -d '{"order_id":<ORDER_ID>}' http://localhost:8000/api/esims/activate | jq
   ```

   - **Expected:**
     - Response status `200`.
     - `inventory_item_id` matches the seeded row.
     - `status` becomes `active` and `activation_code` equals `INV-SMOKE-001`.
   - **DB check:** `SELECT status, assigned_at FROM esim_inventory WHERE id=<inventory_id>;` should return `ASSIGNED` with `assigned_at` populated.

4. **Idempotency check:** repeat the `activate` call. Response should be `200` with identical payload (same activation code, timestamps unchanged).

### Test B: Provider Fallback (No Inventory)

1. Ensure no AVAILABLE inventory for the target plan/country.
2. Repeat order creation and payment steps above.
3. Activate the eSIM. Expected results:
   - Response still `200` with generated activation code/ICCID.
   - Database now has a freshly created `esim_inventory` row linked to the profile (`inventory_item_id` not null, status `ASSIGNED`).
4. Inspect backend logs for `ConnectedYou dry-run payload` (when `ESIM_PROVIDER=CONNECTED_YOU`) or `LocalEsimProvider` messages.

### Test C: Provider Failure Handling

1. Temporarily patch the provider (python shell or tests) to raise `EsimProvisioningError` or set `ESIM_PROVIDER=CONNECTED_YOU` with invalid credentials.
2. Trigger activation with no inventory available.
3. **Expected:** HTTP `502`, JSON detail "Unable to provision eSIM". Profile remains in `pending_activation`, `inventory_item_id` stays null.

Document results (success/failure, inventory IDs) in the QA log for traceability.

---

## WEB APPLICATION TESTS

### Setup Web App

```bash
cd apps/web
npm install
set PORT=3100           # Windows
# export PORT=3100      # Linux/Mac
npm run dev
```

Open: http://localhost:3100

---

### Test 1: Home Page & Country Search

**Steps:**

1. Navigate to http://localhost:3100
2. Observe the hero section with "Stay Connected Everywhere" heading
3. Click "Get Started Now" button

   - **Expected:** Smooth scroll to country picker card
   - **Console:** Should log `📱 Get Started clicked - scrolling to country picker`

4. In the country picker input, type "Spain"

   - **Expected:** Dropdown shows Spain with flag 🇪🇸
   - **Console:** Should log:
     - `🌍 Fetching countries from: http://localhost:8000/api/countries`
     - `✅ Countries loaded: <N> countries`
     - `🔍 Country search query: Spain`

5. Click on "Spain" in the dropdown
   - **Expected:** Navigate to `/plans/ES`
   - **Console:** Should log `🧭 Country selected: {name: "Spain", iso2: "ES", ...}`

**What to verify:**

- ✅ Countries load without "Unable to load countries" error
- ✅ Search filtering works
- ✅ Navigation to plans page works
- ✅ No "Unexpected token '<'" JSON errors in console
- ✅ Text is readable with good contrast

---

### Test 2: OTP Authentication Flow

**Steps:**

1. Navigate to http://localhost:3100/auth
2. Enter email: `test@example.com`
3. Click "Get OTP Code"

   - **Expected:**
     - Message: "OTP sent to test@example.com. Check your email or backend console!"
     - OTP input field appears
   - **Console (Browser):**
     - `🔑 Requesting OTP for: test@example.com`
     - `🔗 Endpoint: http://localhost:8000/api/auth/request-code`
     - `✅ OTP sent successfully`
   - **Console (Backend):**
     - Should print: `OTP Code for test@example.com: XXXXXX` (6-digit code)

4. Copy the 6-digit OTP code from the backend console
5. Enter the code in the web UI
6. Click "Verify"
   - **Expected:**
     - Message: "Login successful! Redirecting..."
     - Redirect to `/account` after 1 second
   - **Console:**
     - `🔐 Verifying code for: test@example.com`
     - `✅ Login successful: {token: "...", ...}`
     - `💾 Token stored in localStorage`

**What to verify:**

- ✅ No "Unexpected token '<'" error
- ✅ Token is stored in localStorage (check DevTools > Application > Local Storage)
- ✅ Redirect to account page works
- ✅ No 404 errors in network tab

---

### Test 3: Account Page

**After logging in from Test 2:**

1. You should be at http://localhost:3100/account
2. **Expected:**
   - User email displayed
   - "My Orders" section visible
   - Either shows orders or "No orders yet"
   - **Console:**
     - `👤 Fetching user profile...`
     - `✅ User profile loaded: {email: "test@example.com", ...}`
     - `📦 Fetching orders...`
     - `✅ Orders loaded: <N> orders`
     - `📶 Fetching eSIMs...`
     - `✅ eSIMs loaded: <N> eSIMs`

**What to verify:**

- ✅ No auth errors or redirects to login
- ✅ User data loads from `/api/auth/me`
- ✅ Orders load from `/api/orders/mine`
- ✅ eSIMs load from `/api/esims/mine`
- ✅ All API calls use `http://localhost:8000` not Next.js server

---

### Test 4: Admin Access

**Setup:**

1. Ensure your test email is in the backend `ADMIN_EMAILS` list
   - Edit `apps/backend/.env`: `ADMIN_EMAILS=test@example.com,admin@tribi.app`
   - Restart backend

**Steps:**

1. Log in with an admin email (from Test 2)
2. Navigate to http://localhost:3100/admin
3. **Expected:**
   - Loading spinner briefly shows
   - Admin panel appears with "Dashboard" heading
   - Three cards: Countries, Carriers, Plans
   - **Console:**
     - `🔐 Admin layout: Checking authentication...`
     - `🔗 Checking auth at: http://localhost:8000/api/auth/me`
     - `✅ User authenticated: test@example.com`
     - `🔍 Checking admin privileges for: test@example.com`
     - `✅ Admin access confirmed for: test@example.com`

**What to verify:**

- ✅ Admin panel loads without being redirected to `/auth`
- ✅ No hard-coded `http://localhost:8000` errors
- ✅ If user is NOT admin, see clear denial message with email

**Non-admin test:**

1. Log in with `nonAdmin@example.com` (not in ADMIN_EMAILS)
2. Navigate to http://localhost:3100/admin
3. **Expected:**
   - Access Denied screen
   - Message: "User nonAdmin@example.com does not have admin privileges"
   - **Console:** `❌ User nonAdmin@example.com is not admin - 403 Forbidden`

---

### Test 5: Contrast & Button Functionality

**Check all pages for:**

- Text is clearly readable on all backgrounds
- Primary buttons (blue/indigo) have white text
- Buttons respond to clicks (check console for logs)
- "Get Started Now" scrolls to country picker
- "Explore Plans Now" scrolls to top then country picker

---

## MOBILE APPLICATION TESTS

### Setup Mobile App

```bash
cd apps/mobile
npm install
npx expo start
```

Press `a` for Android emulator or `i` for iOS simulator, or scan QR code with Expo Go.

---

### Test 6: Mobile App Startup

**Steps:**

1. Start the mobile app
2. **Expected:**
   - App opens without crashing
   - No "Failed to resolve plugin for module expo-updates" error
   - Auth screen appears if not logged in
   - **Console (Metro bundler):**
     - Should see: `🚫 OTA update error ignored in dev build` (if updates fail)
     - Should NOT crash with "failed to download remote updates"

**What to verify:**

- ✅ App starts successfully
- ✅ No plugin errors
- ✅ If OTA updates fail, error is logged but app continues

---

### Test 7: Mobile OTP Login

**Steps:**

1. On the Auth Email screen, enter: `mobileuser@example.com`
2. Tap "Get OTP Code"

   - **Expected:** Navigate to code entry screen
   - **Console (Backend):** Prints OTP code
   - **Console (Mobile):**
     - `📡 API Request: POST /api/auth/request-code`
     - `✅ API Success: {...}`

3. Enter the 6-digit code from backend console
4. Tap "Verify"
   - **Expected:** Navigate to main app (Countries tab)
   - **Console:**
     - `📡 API Request: POST /api/auth/verify`
     - `✅ API Success: {token: "...", user: {...}}`

**What to verify:**

- ✅ OTP request works
- ✅ Code verification works
- ✅ Token stored in SecureStore
- ✅ Navigation to main tabs works

---

### Test 8: Mobile Country & Plans Browse

**Steps:**

1. From the Countries screen, tap the search bar
2. Type "France"
3. Tap on "France" in the results

   - **Expected:** Navigate to Plans screen showing French plans
   - **Console:**
     - `📡 API Request: GET /api/plans?country=FR`
     - `✅ API Success: [...]`

4. View plans with data amounts, prices, carriers

**What to verify:**

- ✅ Countries load and display
- ✅ Search filters countries
- ✅ Plans load for selected country
- ✅ Plan details show correctly

---

### Test 9: Mobile Account Screen

**Steps:**

1. Navigate to the "Account" tab
2. **Expected:**

   - User email displayed
   - Orders section shows orders or "No orders yet"
   - **Console:**
     - `📦 Mobile: Fetching orders and eSIMs...`
     - `✅ Mobile: Loaded <N> orders`
     - `📍 Mobile: Sample order: {...}`
     - `✅ Mobile: Loaded <N> eSIMs`
     - `📱 Mobile: Sample eSIM: {...}`
     - `🔗 Mobile: Mapped eSIM <id> to order <id>` (for each eSIM)

3. Pull down to refresh
   - **Expected:** Refresh indicator shows, data reloads

**What to verify:**

- ✅ Orders load from `/api/orders/mine`
- ✅ eSIMs load from `/api/esims/mine`
- ✅ Order cards show plan details (country, data, duration)
- ✅ eSIM status and activation codes display correctly
- ✅ Logging shows order/eSIM count and samples

---

### Test 10: Mobile Checkout (if applicable)

**Steps:**

1. From a plan details screen, tap "Buy Plan"
2. Navigate through checkout flow
3. For demo/test purposes, payment should succeed with MOCK provider
4. After payment, verify:
   - Order appears in Account screen
   - eSIM is created and associated with order
   - **Console logs order and eSIM creation**

---

## Common Issues & Solutions

### Issue: "Unable to load countries"

**Solution:**

- Check backend is running on port 8000
- Check CORS is enabled in backend
- Verify `NEXT_PUBLIC_API_BASE` is NOT set to wrong value (should be empty or `http://localhost:8000`)

### Issue: "Unexpected token '<'" JSON error

**Solution:**

- This means the web app is hitting the Next.js server instead of the backend
- Verify `apiUrl()` is being used from `@/lib/apiConfig`
- Check that API_BASE defaults to `http://localhost:8000` when env var is not set

### Issue: Mobile "expo-updates" plugin error

**Solution:**

- Verify `plugins` array is removed from `app.config.js`
- Only keep the `updates` object with `enabled: false`

### Issue: Admin access denied

**Solution:**

- Add user email to `ADMIN_EMAILS` in `apps/backend/.env`
- Restart backend
- Check console logs for the exact reason access was denied

### Issue: Orders don't show in account

**Solution:**

- Check auth token is present in localStorage (web) or SecureStore (mobile)
- Verify `/api/orders/mine` endpoint returns data in backend console
- Check network tab for 401/403 errors

---

## Expected Console Log Patterns

### Good Web Auth Flow:

```
🔑 Requesting OTP for: test@example.com
🔗 Endpoint: http://localhost:8000/api/auth/request-code
🌐 API Request: POST http://localhost:8000/api/auth/request-code
📥 API Response: 200 OK
✅ API Success: {message: "OTP sent"}
✅ OTP sent successfully
```

### Good Mobile Startup:

```
🚫 OTA update error ignored in dev build: [optional error message]
📡 API Request: GET /api/countries
✅ API Success: [...150 countries...]
```

### Good Account Load:

```
👤 Fetching user profile...
📦 Fetching orders...
📶 Fetching eSIMs...
✅ User profile loaded: {email: "test@example.com"}
✅ Orders loaded: 3 orders
✅ eSIMs loaded: 2 eSIMs
```

---

## Summary Checklist

### Web

- [ ] Home page loads, country picker works
- [ ] OTP login flow works end-to-end
- [ ] Account page loads user data and orders
- [ ] Admin panel accessible for admin users
- [ ] Admin panel denies non-admin users with clear message
- [ ] All buttons have actions or are disabled
- [ ] Text contrast is good on all pages
- [ ] No JSON parse errors in console
- [ ] All API calls go to backend (port 8000)

### Mobile

- [ ] App starts without plugin errors
- [ ] OTA update errors are non-fatal
- [ ] OTP login flow works
- [ ] Countries load and are searchable
- [ ] Plans load for selected country
- [ ] Account screen shows orders and eSIMs
- [ ] Logging shows detailed order/eSIM info
- [ ] Refresh works on account screen

---

## Test Data

**Test users:**

- `test@example.com` (add to ADMIN_EMAILS for admin test)
- `user@example.com`
- `mobileuser@example.com`

**OTP codes:**

- Backend prints the code to console
- For demo: any 6-digit code works if backend is in dev mode

**Test countries:**

- Spain (ES)
- France (FR)
- United States (US)

---

## Regression Tests Passed

After implementing all fixes, verify these specific regressions are resolved:

1. ✅ Mobile app starts without expo-updates PluginError
2. ✅ Web OTP login does NOT show "Unexpected token '<'" JSON error
3. ✅ Web country picker loads countries successfully
4. ✅ Admin layout uses correct API_BASE and checks admin properly
5. ✅ Buttons on home page have real actions
6. ✅ Mobile account screen loads enriched order/eSIM data with logging

---

**End of Manual Smoke Tests**

For automated tests, see:

- Backend: `apps/backend/tests/`
- Web: (to be added)
- Mobile: (to be added)
