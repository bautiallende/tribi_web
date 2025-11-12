# API Examples (cURL)

Base URL: `http://localhost:8000`

## Authentication

### 1. Request OTP Code

```bash
curl -X POST http://localhost:8000/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response:**
```json
{
  "message": "OTP sent to user@example.com"
}
```

**What happens:**
- Generates 6-digit OTP code
- Stores in `auth_codes` table with 10-minute expiry
- Sends email via SMTP (check MailHog at http://localhost:1025)

---

### 2. Verify OTP Code

```bash
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "code": "123456"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

**What happens:**
- Validates OTP code exists and hasn't expired
- Marks `auth_code.used = true`
- Issues JWT token (HS256)
- Returns user profile

---

### 3. Get Current User Profile

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "User Name"
}
```

**Status Codes:**
- `200`: Success
- `401`: Invalid or missing token

---

## Orders

### 1. Create Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "plan_id": 1,
    "currency": "USD"
  }'
```

**Response:**
```json
{
  "id": 42,
  "plan_id": 1,
  "status": "created",
  "currency": "USD",
  "amount_minor_units": 1000,
  "created_at": "2025-11-12T18:30:00"
}
```

**Status Codes:**
- `201`: Order created
- `401`: Unauthorized (missing/invalid token)
- `404`: Plan not found

---

### 2. List User's Orders

```bash
curl -X GET http://localhost:8000/orders/mine \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response:**
```json
[
  {
    "id": 42,
    "plan_id": 1,
    "status": "paid",
    "currency": "USD",
    "amount_minor_units": 1000,
    "created_at": "2025-11-12T18:30:00"
  },
  {
    "id": 41,
    "plan_id": 2,
    "status": "created",
    "currency": "USD",
    "amount_minor_units": 1999,
    "created_at": "2025-11-12T18:25:00"
  }
]
```

**Status Codes:**
- `200`: Success (empty list if no orders)
- `401`: Unauthorized

---

## Payments

### 1. Create MOCK Payment

```bash
curl -X POST http://localhost:8000/payments/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "order_id": 42,
    "provider": "MOCK"
  }'
```

**Response:**
```json
{
  "status": "succeeded",
  "provider": "MOCK"
}
```

**What happens:**
- Creates Payment record
- Immediately marks as `succeeded` (MOCK provider)
- Updates Order status to `paid`

**Status Codes:**
- `201`: Payment created
- `401`: Unauthorized
- `404`: Order not found

---

### 2. Payment Webhook (Provider Callback)

```bash
curl -X POST http://localhost:8000/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 42,
    "provider": "STRIPE",
    "status": "succeeded"
  }'
```

**Response:**
```json
{
  "status": "ok"
}
```

**What happens:**
- Updates Payment and Order status based on webhook data
- No authentication required (provider sends from webhook)

**Status Codes:**
- `200`: Webhook processed
- `404`: Order not found
- `400`: Missing required fields

---

## eSIM

### 1. Activate eSIM

```bash
curl -X POST http://localhost:8000/esims/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "order_id": 42
  }'
```

**Response:**
```json
{
  "id": 15,
  "order_id": 42,
  "activation_code": "550e8400-e29b-41d4-a716-446655440000",
  "iccid": null,
  "status": "pending",
  "created_at": "2025-11-12T18:35:00"
}
```

**What happens:**
- Verifies order status is `paid`
- Creates EsimProfile with UUID4 activation_code
- Status set to `pending`

**Status Codes:**
- `201`: eSIM activated
- `400`: Order not paid yet
- `401`: Unauthorized
- `404`: Order not found

---

## Testing Helper Functions

### Login Flow (Get JWT Token)

```bash
#!/bin/bash

# Request OTP
curl -X POST http://localhost:8000/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Verify OTP (check code from MailHog or use 000000 for test)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "000000"
  }' | jq -r '.token')

echo "JWT Token: $TOKEN"

# Use token in subsequent requests
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### End-to-End Order Flow

```bash
#!/bin/bash

API="http://localhost:8000"

# 1. Get token
echo "1. Requesting OTP..."
curl -s -X POST $API/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{"email": "buyer@example.com"}'

echo "2. Verifying OTP (check email for code)..."
TOKEN=$(curl -s -X POST $API/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@example.com",
    "code": "000000"
  }' | jq -r '.token')

echo "Token: $TOKEN"

# 2. Create order
echo "3. Creating order..."
ORDER=$(curl -s -X POST $API/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "plan_id": 1,
    "currency": "USD"
  }' | jq '.id')

echo "Order ID: $ORDER"

# 3. Create payment
echo "4. Creating payment..."
curl -s -X POST $API/payments/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"order_id\": $ORDER, \"provider\": \"MOCK\"}"

# 4. Activate eSIM
echo "5. Activating eSIM..."
curl -s -X POST $API/esims/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"order_id\": $ORDER}"

# 5. View account
echo "6. Viewing account..."
curl -s -X GET $API/orders/mine \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## Common Headers

All requests should include:
```
Content-Type: application/json
```

Protected endpoints require:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Error Responses

### 401 Unauthorized
```json
{"detail": "Not authenticated"}
```

### 404 Not Found
```json
{"detail": "Order not found"}
```

### 400 Bad Request
```json
{"detail": "Invalid code"}
```

---

## Testing with MailHog

MailHog runs at `http://localhost:1025` (SMTP) and `http://localhost:8025` (Web UI)

1. Make OTP request: `POST /auth/request-code`
2. Open browser: `http://localhost:8025`
3. Check inbox for email with 6-digit code
4. Use code in verify request: `POST /auth/verify`

---

## Tips

- Replace `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` with actual token
- Use `jq` to pretty-print JSON: `curl ... | jq '.'`
- Use `-s` flag to suppress curl progress: `curl -s ...`
- Store token in variable: `TOKEN=$(curl ... | jq -r '.token')`
- Use `@-` to read from stdin: `curl -d @- << EOF ... EOF`
