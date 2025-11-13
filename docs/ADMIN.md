# Admin Panel Documentation

## Overview

The admin panel provides a comprehensive interface for managing the core data of the eSIM marketplace:
- **Countries**: Manage available countries with ISO codes
- **Carriers**: Manage mobile carriers/operators  
- **Plans**: Manage eSIM data plans with pricing and specifications

All admin pages include modern UX features:
- ✅ Debounced search (300ms)
- ✅ Column sorting (ascending/descending)
- ✅ Pagination (20 items per page)
- ✅ Toast notifications (success/error/info/warning)
- ✅ Confirmation dialogs before destructive actions
- ✅ Form validation with clear error messages
- ✅ Skeleton loaders during data fetch
- ✅ CSV import/export for bulk operations

## Admin Access

Access is restricted to users with verified email addresses listed in the `ADMIN_EMAILS` environment variable (comma-separated list).

Example:
```bash
ADMIN_EMAILS=admin@tribi.com,manager@tribi.com
```

Users must:
1. Sign in via `/auth/signin`
2. Complete email verification
3. Have their email in the whitelist
4. Access admin routes at `/admin/*`

## Features by Section

### Countries Management (`/admin/countries`)

- **List View**: Paginated table with search and sorting
- **Search**: Real-time search by country name or ISO code (debounced 300ms)
- **Sorting**: Click column headers to sort by ISO2 or Name (asc/desc)
- **Create**: Add new country with ISO2 (2 letters) and name (min 2 chars)
- **Edit**: Update existing country details
- **Delete**: Remove country with confirmation dialog
- **Validation**:
  - ISO2: Exactly 2 uppercase letters
  - Name: Minimum 2 characters

### Carriers Management (`/admin/carriers`)

- **List View**: Paginated table with search and sorting
- **Search**: Real-time search by carrier name
- **Sorting**: Click column headers to sort by ID or Name
- **Create**: Add new carrier with name
- **Edit**: Update carrier name
- **Delete**: Remove carrier with confirmation dialog
- **Validation**:
  - Name: 2-100 characters

### Plans Management (`/admin/plans`)

- **List View**: Paginated table with search, filters, and sorting
- **Search**: Real-time search by plan name
- **Filters**: 
  - Country dropdown (filter by country_id)
  - Carrier dropdown (filter by carrier_id)
- **Sorting**: Click headers to sort by Name, Price, Duration, or Data (asc/desc)
- **Create**: Add new plan with all specifications
- **Edit**: Update existing plan details
- **Delete**: Remove plan with confirmation dialog
- **CSV Export**: Download all plans as CSV file
- **CSV Import**: Bulk create/update plans from CSV file
- **Validation**:
  - Name: Required
  - Country: Must exist in database
  - Carrier: Must exist in database
  - Data (GB): Positive number (0 for unlimited)
  - Is Unlimited: Boolean checkbox
  - Duration (days): Positive integer
  - Price (USD): Positive decimal

## API Endpoints

All endpoints require authentication and admin privileges.

### Countries Endpoints

#### List Countries
```http
GET /admin/countries?q=spain&sort_by=name&sort_order=asc&page=1&page_size=20
```

**Query Parameters**:
- `q` (optional): Search query for name or ISO code
- `sort_by` (optional): Sort field (`name` or `iso2`, default: `name`)
- `sort_order` (optional): Sort direction (`asc` or `desc`, default: `asc`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response**:
```json
{
  "countries": [
    {
      "id": 1,
      "iso2": "ES",
      "name": "Spain"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/admin/countries?q=united&sort_by=name&sort_order=asc" \
  --cookie "session=your_session_token"
```

#### Create Country
```http
POST /admin/countries
Content-Type: application/json

{
  "iso2": "FR",
  "name": "France"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/admin/countries" \
  -H "Content-Type: application/json" \
  -d '{"iso2":"FR","name":"France"}' \
  --cookie "session=your_session_token"
```

#### Update Country
```http
PUT /admin/countries/{id}
Content-Type: application/json

{
  "iso2": "FR",
  "name": "France (Updated)"
}
```

#### Delete Country
```http
DELETE /admin/countries/{id}
```

**Example**:
```bash
curl -X DELETE "http://localhost:8000/admin/countries/5" \
  --cookie "session=your_session_token"
```

### Carriers Endpoints

#### List Carriers
```http
GET /admin/carriers?q=vodafone&sort_by=name&sort_order=asc&page=1&page_size=20
```

**Query Parameters**:
- `q` (optional): Search query for carrier name
- `sort_by` (optional): Sort field (`name` or `id`, default: `name`)
- `sort_order` (optional): Sort direction (`asc` or `desc`, default: `asc`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response**:
```json
{
  "carriers": [
    {
      "id": 1,
      "name": "Vodafone"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### Create Carrier
```http
POST /admin/carriers
Content-Type: application/json

{
  "name": "Orange"
}
```

#### Update Carrier
```http
PUT /admin/carriers/{id}
Content-Type: application/json

{
  "name": "Orange Mobile"
}
```

#### Delete Carrier
```http
DELETE /admin/carriers/{id}
```

### Plans Endpoints

#### List Plans
```http
GET /admin/plans?q=unlimited&country_id=1&carrier_id=2&sort_by=price_usd&sort_order=asc&page=1&page_size=20
```

**Query Parameters**:
- `q` (optional): Search query for plan name
- `country_id` (optional): Filter by country
- `carrier_id` (optional): Filter by carrier
- `sort_by` (optional): Sort field (`name`, `price_usd`, `duration_days`, `data_gb`, default: `name`)
- `sort_order` (optional): Sort direction (`asc` or `desc`, default: `asc`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response**:
```json
{
  "plans": [
    {
      "id": 1,
      "name": "Spain 10GB - 30 Days",
      "country_id": 1,
      "carrier_id": 2,
      "data_gb": 10.0,
      "is_unlimited": false,
      "duration_days": 30,
      "price_usd": 25.00,
      "description": "Perfect for tourists"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### Create Plan
```http
POST /admin/plans
Content-Type: application/json

{
  "name": "France 20GB - 30 Days",
  "country_id": 2,
  "carrier_id": 3,
  "data_gb": 20.0,
  "is_unlimited": false,
  "duration_days": 30,
  "price_usd": 35.00,
  "description": "High-speed data"
}
```

#### Update Plan
```http
PUT /admin/plans/{id}
Content-Type: application/json

{
  "name": "France 20GB - 30 Days (Updated)",
  "price_usd": 32.00
}
```

#### Delete Plan
```http
DELETE /admin/plans/{id}
```

#### Export Plans (CSV)
```http
GET /admin/plans/export
```

Downloads a CSV file (`plans_export.csv`) containing all plans with the following columns:

**Example**:
```bash
curl -X GET "http://localhost:8000/admin/plans/export" \
  --cookie "session=your_session_token" \
  -o plans_export.csv
```

**Response**: CSV file download

#### Import Plans (CSV)
```http
POST /admin/plans/import
Content-Type: multipart/form-data

file: <CSV file>
```

Bulk creates or updates plans from a CSV file. Uses transaction safety (all-or-nothing).

**Example**:
```bash
curl -X POST "http://localhost:8000/admin/plans/import" \
  -F "file=@plans.csv" \
  --cookie "session=your_session_token"
```

**Response**:
```json
{
  "success": true,
  "created": 15,
  "updated": 3,
  "errors": []
}
```

Or on error:
```json
{
  "success": false,
  "created": 0,
  "updated": 0,
  "errors": [
    "Row 2: Invalid country_id: 999",
    "Row 5: Missing required field: name"
  ]
}
```

## CSV Import/Export Guide

### Export Format

The export endpoint generates a CSV with the following columns:

```csv
id,name,country_id,carrier_id,data_gb,is_unlimited,duration_days,price_usd,description
1,Spain 10GB - 30 Days,1,2,10.0,false,30,25.00,Perfect for tourists
2,France Unlimited - 7 Days,2,3,0.0,true,7,15.00,High-speed unlimited
```

### Import Format

To import plans, create a CSV file with the same structure:

**Column Descriptions**:
- `id` (optional): If provided, updates existing plan. If omitted or empty, creates new plan.
- `name` (required): Plan display name
- `country_id` (required): Must match an existing country ID in the database
- `carrier_id` (required): Must match an existing carrier ID in the database
- `data_gb` (required): Data allowance in GB (use 0 for unlimited plans)
- `is_unlimited` (required): `true` or `false` (case-insensitive)
- `duration_days` (required): Plan duration in days (positive integer)
- `price_usd` (required): Price in USD (decimal, e.g., 25.00)
- `description` (optional): Detailed plan description

**Example Import File** (`plans_import.csv`):
```csv
id,name,country_id,carrier_id,data_gb,is_unlimited,duration_days,price_usd,description
,New Plan 5GB,1,2,5.0,false,15,12.50,Starter package
,New Plan 20GB,2,3,20.0,false,30,40.00,Premium package
42,Update Existing Plan,1,2,10.0,false,30,28.00,Updated description
```

### Import Rules

1. **Create vs Update**:
   - Empty or omitted `id` → Creates new plan
   - Existing `id` → Updates plan with that ID

2. **Validation**:
   - All required fields must be present
   - `country_id` must exist in countries table
   - `carrier_id` must exist in carriers table
   - Numeric fields must be valid numbers
   - `is_unlimited` must be boolean (true/false)
   - `data_gb`, `duration_days`, `price_usd` must be positive

3. **Transaction Safety**:
   - All rows are validated before any changes
   - If ANY row has errors, NO changes are applied (rollback)
   - Database remains unchanged if import fails
   - Up to 10 errors are returned for debugging

4. **Error Messages**:
   - Include row number for easy identification
   - Describe specific validation failure
   - Example: `Row 5: Invalid country_id: 999 - Country does not exist`

### Import Workflow

1. **Export existing data** (optional backup):
   ```bash
   # Click "📥 Export CSV" button in Plans admin
   # Or use API: GET /admin/plans/export
   ```

2. **Prepare CSV file**:
   - Use exported CSV as template
   - Add new rows (omit `id` column or leave empty)
   - Modify existing rows (include `id` to update)
   - Validate country_id and carrier_id match your database

3. **Import file**:
   - Click file input in Plans admin
   - Select your CSV file
   - Wait for validation and processing
   - Review results in toast notification

4. **Handle errors**:
   - If import fails, review error messages
   - Fix issues in CSV file
   - Re-import corrected file

## Common Workflows

### Adding a New Country, Carrier, and Plan

1. **Add Country**:
   - Navigate to `/admin/countries`
   - Click "Create Country"
   - Enter ISO2 code (e.g., "IT")
   - Enter name (e.g., "Italy")
   - Click "Create"
   - Note the country_id from the table

2. **Add Carrier**:
   - Navigate to `/admin/carriers`
   - Click "Create Carrier"
   - Enter name (e.g., "TIM")
   - Click "Create"
   - Note the carrier_id from the table

3. **Add Plan**:
   - Navigate to `/admin/plans`
   - Click "Create Plan"
   - Select country from dropdown
   - Select carrier from dropdown
   - Fill in plan details (name, data, duration, price)
   - Click "Create"

### Bulk Importing Plans

**Scenario**: You have 100 new plans to add from a partner carrier.

1. **Prepare data**:
   - Export existing plans as CSV (backup)
   - Open in spreadsheet software
   - Add new rows with plan details
   - Ensure country_id and carrier_id are correct
   - Leave `id` column empty for new plans

2. **Validate data**:
   - Check all required fields are present
   - Verify country_id values exist in countries table
   - Verify carrier_id values exist in carriers table
   - Ensure prices are formatted as decimals (25.00)
   - Ensure is_unlimited is "true" or "false"

3. **Import**:
   - Navigate to `/admin/plans`
   - Click file input
   - Select your CSV file
   - Wait for processing
   - Check toast notification for results

4. **Verify**:
   - If successful: See "Imported: X created, Y updated"
   - If failed: Review error messages
   - Use search/filters to verify imported plans

### Updating Multiple Plans

**Scenario**: Increase prices for all Spain plans by 10%.

1. **Export current data**:
   - Navigate to `/admin/plans`
   - Filter by Spain (country_id)
   - Click "📥 Export CSV"

2. **Modify prices**:
   - Open CSV in spreadsheet
   - Update `price_usd` column (multiply by 1.1)
   - Keep `id` column intact (for updates)
   - Save file

3. **Import updates**:
   - Click file input in Plans admin
   - Select modified CSV
   - Import will update existing plans (matched by id)
   - Verify results in toast notification

## Limits and Constraints

### Pagination Limits
- Default page size: 20 items
- Maximum page size: 100 items
- Frontend enforces 20 items per page for consistency

### Search and Filtering
- Search is case-insensitive
- Search debounce: 300ms (prevents excessive API calls)
- Multiple filters can be combined (search + country + carrier)

### Field Validation Limits
- Country ISO2: Exactly 2 uppercase letters
- Country Name: 2-200 characters
- Carrier Name: 2-100 characters
- Plan Name: 1-200 characters
- Plan Data (GB): 0-999 (0 = unlimited)
- Plan Duration: 1-365 days
- Plan Price: 0.01-9999.99 USD
- Plan Description: 0-1000 characters (optional)

### CSV Import Limits
- Maximum file size: 10MB (configurable in backend)
- Recommended: Import in batches of 500 rows or less
- Transaction timeout: 30 seconds
- Error reporting: Up to 10 errors returned (to prevent huge responses)

### Rate Limiting
- Admin endpoints: 100 requests per minute per IP
- CSV export: 10 exports per minute per user
- CSV import: 5 imports per minute per user

## Troubleshooting

### 403 Forbidden Error

**Symptom**: Cannot access `/admin/*` routes, see "Access Denied" message.

**Causes**:
1. User email not in `ADMIN_EMAILS` environment variable
2. Email not verified
3. Session expired

**Solutions**:
1. Verify `ADMIN_EMAILS` contains your email address
2. Check email for verification link and complete verification
3. Sign out and sign in again to refresh session
4. Check backend logs for detailed error messages

### Search Not Working

**Symptom**: Search input doesn't filter results.

**Causes**:
1. Debounce delay (300ms) - still typing
2. Network error preventing API call
3. Backend search logic issue

**Solutions**:
1. Wait 300ms after typing stops
2. Check browser console for network errors
3. Verify backend is running and accessible
4. Test API directly: `GET /admin/countries?q=spain`

### CSV Import Fails

**Symptom**: Import returns errors, no plans created.

**Common Errors**:

1. **"Missing required field: name"**
   - Ensure all required columns are present
   - Check for empty cells in required columns

2. **"Invalid country_id: 999"**
   - Verify country_id exists in countries table
   - Export countries list to get valid IDs

3. **"Invalid carrier_id: 888"**
   - Verify carrier_id exists in carriers table
   - Export carriers list to get valid IDs

4. **"Invalid data type for price_usd"**
   - Ensure prices are formatted as decimals (25.00, not "$25")
   - Remove currency symbols and commas

5. **"is_unlimited must be true or false"**
   - Use lowercase "true" or "false" (not "yes/no" or "1/0")

**Solutions**:
1. Download export CSV as template
2. Validate data in spreadsheet before import
3. Import small batches first (10-20 rows) to test
4. Read error messages carefully - they include row numbers
5. Check that CSV is UTF-8 encoded (not ISO-8859-1)

### Sorting Not Working

**Symptom**: Clicking column headers doesn't sort data.

**Causes**:
1. Column is not sortable (check for ↕️ icon)
2. Network error during re-fetch
3. Backend sorting parameter issue

**Solutions**:
1. Verify column has sort icon (↕️)
2. Check browser console for errors
3. Test API directly with `?sort_by=name&sort_order=asc`

### Toast Notifications Not Appearing

**Symptom**: No success/error messages after actions.

**Causes**:
1. ToastProvider not wrapping component
2. JavaScript error preventing toast display
3. Toast hidden behind other elements (z-index issue)

**Solutions**:
1. Verify `<ToastProvider>` in admin layout
2. Check browser console for React errors
3. Inspect element - toast should have `z-50` class

## Security Considerations

### Access Control
- All admin routes require authentication
- Email verification required
- Whitelist-based access (`ADMIN_EMAILS`)
- Session-based authentication with secure cookies

### Data Validation
- All inputs validated on frontend and backend
- SQL injection prevention via ORM (SQLAlchemy)
- XSS prevention via React (auto-escaping)
- CSRF protection via SameSite cookies

### Audit Logging
- *(Not yet implemented)*
- Future: Log all admin actions (create, update, delete)
- Future: Track who performed each action and when
- Future: Store IP addresses for security audits

### Rate Limiting
- Protects against abuse and DoS attacks
- Per-IP and per-user limits
- Stricter limits on expensive operations (CSV import/export)

### File Upload Security
- CSV imports: Max 10MB file size
- File type validation (must be text/csv)
- Content validation before processing
- Transaction safety prevents partial imports

## Future Enhancements

- [ ] Audit logging for all admin actions
- [ ] Bulk delete (select multiple items, delete all)
- [ ] Advanced filters (date ranges, price ranges)
- [ ] Column visibility toggle (show/hide columns)
- [ ] Export filtered/searched results (not just all data)
- [ ] Real-time collaboration (see other admins' edits)
- [ ] Undo/redo functionality
- [ ] Keyboard shortcuts (Ctrl+S to save, etc.)
- [ ] Dark mode for admin panel
- [ ] Mobile-responsive admin panel

## Support

For issues or questions:
1. Check this documentation first
2. Review API examples above
3. Check backend logs for detailed errors
4. Test API endpoints directly with curl
5. Contact development team

**API Base URL**: `http://localhost:8000` (development)

**Admin Panel URL**: `http://localhost:3000/admin` (development)
