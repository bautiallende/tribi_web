# Admin Panel Documentation

## Overview

The Tribi Admin Panel provides role-based access control for managing catalog data including countries, carriers, and eSIM plans. Only users with their email addresses in the `ADMIN_EMAILS` configuration can access admin endpoints and interfaces.

## Table of Contents

- [Admin Permissions](#admin-permissions)
- [Environment Configuration](#environment-configuration)
- [Assigning Admins](#assigning-admins)
- [API Endpoints](#api-endpoints)
- [Web Interface](#web-interface)
- [Security Considerations](#security-considerations)
- [Testing](#testing)

---

## Admin Permissions

### How It Works

Admin access is controlled through a simple email whitelist approach:

1. **Configuration**: Admin emails are stored in the `ADMIN_EMAILS` environment variable
2. **Authentication**: Users must first authenticate using the standard auth flow (OTP code)
3. **Authorization**: The `get_current_admin()` dependency checks if the authenticated user's email is in the admin list
4. **Case-Insensitive**: Email comparison is case-insensitive (e.g., `Admin@tribi.app` matches `admin@tribi.app`)

### Authorization Flow

```
User Request
    ↓
1. get_current_user() → Validate JWT/Cookie → Extract email
    ↓
2. get_current_admin() → Check if email in ADMIN_EMAILS
    ↓
3. If YES: Proceed to endpoint
   If NO:  Return 403 Forbidden
```

### Code Example

```python
# Backend: app/api/auth.py
def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and validate they are an admin."""
    if current_user.email.lower() not in settings.admin_emails_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

---

## Environment Configuration

### Backend Configuration

Add the `ADMIN_EMAILS` variable to your `.env` file:

```bash
# Admin Access (comma-separated list of admin emails)
ADMIN_EMAILS=admin@tribi.app,superuser@tribi.app,operations@tribi.app
```

**Format Rules:**
- Comma-separated list of email addresses
- No spaces around commas (spaces are automatically stripped)
- Case-insensitive matching
- Empty string or omitted variable = no admins (all access denied)

**Example Configurations:**

```bash
# Single admin
ADMIN_EMAILS=admin@tribi.app

# Multiple admins
ADMIN_EMAILS=admin@tribi.app,ops@tribi.app,dev@tribi.app

# No admins (blocks all admin access)
ADMIN_EMAILS=
```

### Settings Class

The configuration is parsed in `app/core/config.py`:

```python
class Settings(BaseSettings):
    # Admin Access
    ADMIN_EMAILS: str = ""  # Comma-separated list
    
    @property
    def admin_emails_list(self) -> list[str]:
        """Parse admin emails from comma-separated string."""
        if not self.ADMIN_EMAILS:
            return []
        return [email.strip().lower() for email in self.ADMIN_EMAILS.split(",") if email.strip()]
```

---

## Assigning Admins

### Adding a New Admin

1. **Stop the backend server** (if running)
2. **Edit `.env` file**:
   ```bash
   # Add the new admin email to the comma-separated list
   ADMIN_EMAILS=existing@tribi.app,newadmin@tribi.app
   ```
3. **Restart the backend server**
4. **Verify access**: New admin logs in and navigates to `/admin`

### Removing an Admin

1. **Stop the backend server**
2. **Edit `.env` file**: Remove the email from the list
3. **Restart the backend server**
4. **Revoke active sessions** (optional): Admin tokens remain valid until expiration. To force logout:
   - Wait for JWT expiration (default: 24 hours)
   - Or implement token revocation list (future enhancement)

### Production Deployment

**Environment Variables:**
- Use secure secret management (e.g., AWS Secrets Manager, Azure Key Vault)
- Never commit `.env` files with real admin emails to version control
- Rotate admin credentials periodically

**Kubernetes Example:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tribi-secrets
stringData:
  ADMIN_EMAILS: "admin@tribi.app,ops@tribi.app"
```

**Docker Compose Example:**
```yaml
services:
  backend:
    environment:
      - ADMIN_EMAILS=admin@tribi.app,ops@tribi.app
```

---

## API Endpoints

All admin endpoints require the `get_current_admin` dependency. Requests must include valid authentication (JWT Bearer token or httpOnly cookie).

### Countries

#### List Countries
```http
GET /admin/countries?q=&page=1&page_size=20
```

**Query Parameters:**
- `q` (string, optional): Search by name or ISO2 code
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 20, max: 100): Items per page

**Response:**
```json
{
  "items": [
    {"id": 1, "iso2": "US", "name": "United States"},
    {"id": 2, "iso2": "MX", "name": "Mexico"}
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

#### Create Country
```http
POST /admin/countries
Content-Type: application/json

{
  "iso2": "US",
  "name": "United States"
}
```

**Validation:**
- `iso2`: Exactly 2 alphabetic characters (auto-uppercased)
- `name`: 1-255 characters, required
- Duplicate ISO2 returns `409 Conflict`

**Response:** `201 Created`
```json
{
  "id": 1,
  "iso2": "US",
  "name": "United States"
}
```

#### Update Country
```http
PUT /admin/countries/{country_id}
Content-Type: application/json

{
  "iso2": "GB",
  "name": "United Kingdom"
}
```

**Validation:**
- All fields optional (partial update)
- Same validation as create
- Returns `404 Not Found` if country doesn't exist

**Response:** `200 OK`

#### Delete Country
```http
DELETE /admin/countries/{country_id}
```

**Constraints:**
- Cannot delete if plans reference this country (returns `409 Conflict`)
- Returns `404 Not Found` if country doesn't exist

**Response:** `204 No Content`

---

### Carriers

#### List Carriers
```http
GET /admin/carriers?q=&page=1&page_size=20
```

**Query Parameters:**
- `q` (string, optional): Search by name
- `page`, `page_size`: Same as countries

#### Create Carrier
```http
POST /admin/carriers
Content-Type: application/json

{
  "name": "AT&T"
}
```

**Validation:**
- `name`: 1-255 characters, required, cannot be empty/whitespace
- Duplicate name returns `409 Conflict`

**Response:** `201 Created`

#### Update Carrier
```http
PUT /admin/carriers/{carrier_id}
Content-Type: application/json

{
  "name": "New Name"
}
```

**Response:** `200 OK`

#### Delete Carrier
```http
DELETE /admin/carriers/{carrier_id}
```

**Constraints:**
- Cannot delete if plans reference this carrier (returns `409 Conflict`)

**Response:** `204 No Content`

---

### Plans

#### List Plans
```http
GET /admin/plans?q=&country_id=&carrier_id=&page=1&page_size=20
```

**Query Parameters:**
- `q` (string, optional): Search by plan name
- `country_id` (integer, optional): Filter by country ID
- `carrier_id` (integer, optional): Filter by carrier ID
- `page`, `page_size`: Same as countries

#### Create Plan
```http
POST /admin/plans
Content-Type: application/json

{
  "country_id": 1,
  "carrier_id": 2,
  "name": "USA 10GB",
  "data_gb": 10.0,
  "duration_days": 30,
  "price_usd": 25.50,
  "description": "Best plan for USA",
  "is_unlimited": false
}
```

**Validation:**
- `country_id`: Must exist (returns `404 Not Found`)
- `carrier_id`: Must exist (returns `404 Not Found`)
- `price_usd`: Must be >= 0
- `duration_days`: Must be > 0
- `data_gb`: Must be >= 0
- `is_unlimited`: Boolean (default: false)

**Response:** `201 Created`

#### Update Plan
```http
PUT /admin/plans/{plan_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "price_usd": 30.00
}
```

**Validation:**
- All fields optional (partial update)
- Same validation as create

**Response:** `200 OK`

#### Delete Plan
```http
DELETE /admin/plans/{plan_id}
```

**Note:** Plans can be deleted even if orders reference them (historical data preserved).

**Response:** `204 No Content`

---

## Web Interface

### Accessing the Admin Panel

1. **Navigate to** `http://localhost:3000/admin` (or your deployed URL)
2. **Authentication Check**: If not logged in, redirected to `/auth/login?redirect=/admin`
3. **Authorization Check**: If logged in but not admin, shows "Access Denied" page
4. **Admin Dashboard**: If authorized, shows dashboard with links to Countries, Carriers, Plans

### Dashboard Features

- **Countries Section**: Manage countries and ISO2 codes
- **Carriers Section**: Manage mobile network carriers
- **Plans Section**: Manage eSIM data plans and pricing

### Planned Features (Roadmap)

The following features are documented but not yet implemented:

1. **Countries Admin Section** (`/admin/countries`):
   - List view with search, sort, pagination
   - Create/edit form with ISO2 validation
   - Delete confirmation modal
   - Optimistic UI updates
   - Toast notifications

2. **Carriers Admin Section** (`/admin/carriers`):
   - List view with search, sort, pagination
   - Create/edit form
   - Delete confirmation modal
   - Optimistic UI

3. **Plans Admin Section** (`/admin/plans`):
   - List view with search, sort, pagination
   - Filters: country, carrier
   - Create/edit form with dropdowns
   - Delete confirmation modal
   - Optimistic UI

---

## Security Considerations

### Authentication

- **Multi-Factor**: OTP-based login (email verification)
- **Rate Limiting**: 1 code/60s, 5 codes/24h per email+IP
- **Session Management**: httpOnly cookies (web) + Bearer tokens (mobile)
- **Token Expiry**: 24 hours (configurable via `JWT_EXPIRES_MIN`)

### Authorization

- **Principle of Least Privilege**: Only whitelisted emails have admin access
- **No Role Escalation**: Users cannot grant themselves admin privileges
- **Explicit Deny**: Empty `ADMIN_EMAILS` denies all admin access
- **Audit Trail**: Consider logging admin actions (future enhancement)

### Best Practices

1. **Minimal Admin Count**: Only assign admin role to necessary personnel
2. **Email Security**: Use corporate emails with 2FA
3. **Regular Audits**: Review admin list periodically
4. **Monitor Access**: Log and alert on admin endpoint usage
5. **Secure Credentials**: Never expose `ADMIN_EMAILS` in client-side code
6. **HTTPS Only**: Always use HTTPS in production for cookie security
7. **CORS Configuration**: Restrict `FRONTEND_ORIGINS` to known domains

### Potential Vulnerabilities

| Risk | Mitigation |
|------|------------|
| **Email Spoofing** | Use verified email providers (AWS SES, SendGrid) |
| **Token Theft** | httpOnly cookies, SameSite=Lax, Secure flag in prod |
| **Brute Force** | Rate limiting on auth endpoints |
| **Session Hijacking** | Short token expiry, IP validation (optional) |
| **CSRF** | SameSite cookies, CSRF tokens (if needed) |

---

## Testing

### Backend Tests

#### Admin Authentication Tests

**File:** `tests/test_admin_auth.py`

Tests:
- ✅ Admin user can access admin endpoints
- ✅ Case-insensitive email matching
- ✅ Non-admin user receives 403
- ✅ Empty admin list denies all access
- ✅ Multiple admin emails supported

**Run:**
```bash
cd apps/backend
pytest tests/test_admin_auth.py -v
```

#### Admin CRUD Tests

**File:** `tests/test_admin_crud.py`

Tests (68 total):
- **Countries**: Create, list, search, update, delete, duplicate validation, ISO2 format, referential integrity
- **Carriers**: Create, list, search, update, delete, duplicate validation, empty name validation, referential integrity
- **Plans**: Create, list, search, filter, update, delete, price validation, duration validation, foreign key validation

**Run:**
```bash
pytest tests/test_admin_crud.py -v
```

### Manual Testing

#### 1. Admin Access Test
```bash
# Set admin email
echo "ADMIN_EMAILS=test@example.com" >> apps/backend/.env

# Start backend
cd apps/backend
uvicorn app.main:app --reload

# Request auth code
curl -X POST http://localhost:8000/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Verify code (get token from email)
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}' \
  -c cookies.txt

# Test admin endpoint
curl -X GET http://localhost:8000/admin/countries \
  -b cookies.txt
```

#### 2. Non-Admin Test
```bash
# Use different email
curl -X POST http://localhost:8000/auth/request-code \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Verify and try admin endpoint
curl -X POST http://localhost:8000/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}' \
  -c user-cookies.txt

curl -X GET http://localhost:8000/admin/countries \
  -b user-cookies.txt
# Should return 403 Forbidden
```

#### 3. Web Interface Test

1. Start web server: `cd apps/web && npm run dev`
2. Navigate to `http://localhost:3000/admin`
3. If not logged in, should redirect to login
4. After login with admin email, should show dashboard
5. After login with non-admin email, should show "Access Denied"

---

## Troubleshooting

### "Access Denied" for Valid Admin

**Possible Causes:**
1. Email case mismatch (should be case-insensitive, but verify)
2. Extra whitespace in `.env` file
3. Backend not restarted after changing `ADMIN_EMAILS`
4. User logged in with different email than configured

**Solution:**
```bash
# Check parsed admin list
cd apps/backend
python -c "from app.core.config import settings; print(settings.admin_emails_list)"

# Verify user email
# In backend logs, check the email from JWT token
```

### Admin Endpoints Return 401

**Cause:** Not authenticated

**Solution:**
- Verify JWT token is valid and not expired
- Check cookies are sent with request (credentials: "include")
- Try logging out and logging back in

### Cannot Delete Country/Carrier

**Cause:** Plans reference the entity

**Solution:**
1. List plans: `GET /admin/plans?country_id=X`
2. Delete or reassign dependent plans
3. Retry deletion

---

## Future Enhancements

Potential improvements for the admin system:

1. **Granular Permissions**: Role-based access (admin, editor, viewer)
2. **Audit Logging**: Track all admin actions with timestamps and user
3. **Bulk Operations**: Import/export CSV for catalog data
4. **Admin Dashboard Analytics**: Count of countries, carriers, plans, recent changes
5. **Activity Feed**: Recent admin actions visible in dashboard
6. **Two-Factor Authentication**: Additional layer for admin accounts
7. **IP Whitelisting**: Restrict admin access to specific IPs
8. **Session Management**: View active sessions, force logout
9. **Data Validation**: Advanced rules (e.g., price must match currency)
10. **Soft Delete**: Mark entities as inactive instead of hard delete

---

## Summary

The Tribi Admin Panel provides a secure, simple approach to role-based access control:

- **Configuration-Based**: Admin access controlled via `ADMIN_EMAILS` environment variable
- **Stateless Authorization**: No database tables for roles/permissions
- **Reuses Authentication**: Leverages existing JWT/cookie auth system
- **Explicit Deny**: Defaults to no access unless explicitly granted
- **RESTful API**: Standard CRUD operations with validation
- **Web Interface**: Protected routes with auth checks

For questions or issues, refer to the [API Examples](./API_EXAMPLES.md) and [Testing Guide](./TESTING.md).
