# Database Seeding Guide

This guide explains how to populate the Tribi database with initial data for the catalog feature (countries, carriers, and eSIM plans).

## Overview

The seed process is **idempotent** — running it multiple times is safe and won't create duplicate data. The seed script checks if countries already exist before inserting data.

## Prerequisites

- Backend services running (`make dev` or `docker-compose up -d`)
- MySQL database initialized and accessible
- Python 3.10+ with dependencies installed

## Method 1: Using Seed Script (Recommended)

### Step 1: Apply Migrations

First, ensure the database schema is created:

```bash
cd apps/backend
alembic upgrade head
```

This creates the `countries`, `carriers`, and `plans` tables with proper indices and relationships.

### Step 2: Run Seed Script

Execute the seed script to populate tables:

```bash
cd apps/backend
python -c "from app.seed import seed_database; seed_database()"
```

Or create a simple runner script:

```bash
# apps/backend/seed_runner.py
from app.seed import seed_database

if __name__ == "__main__":
    seed_database()
    print("Seeding completed successfully!")
```

Then run:
```bash
python seed_runner.py
```

### Step 3: Verify Data

Check the data was inserted:

```bash
# In MySQL
SELECT COUNT(*) FROM countries;   -- Should be 15
SELECT COUNT(*) FROM carriers;     -- Should be 4
SELECT COUNT(*) FROM plans;        -- Should be 12
```

Or via the API:

```bash
curl http://localhost:8000/api/countries
curl http://localhost:8000/api/plans
```

## Method 2: Manual Seeding via MySQL

If you prefer to seed manually or need to customize data:

### Countries

```sql
INSERT INTO countries (iso2, name) VALUES
('AR', 'Argentina'),
('BR', 'Brazil'),
('CL', 'Chile'),
('CO', 'Colombia'),
('MX', 'Mexico'),
('ES', 'Spain'),
('FR', 'France'),
('IT', 'Italy'),
('DE', 'Germany'),
('PT', 'Portugal'),
('US', 'United States'),
('CA', 'Canada'),
('AU', 'Australia'),
('JP', 'Japan'),
('SG', 'Singapore');
```

### Carriers

```sql
INSERT INTO carriers (name) VALUES
('Claro'),
('Movistar'),
('Vodafone'),
('Orange');
```

### Plans

```sql
INSERT INTO plans (country_id, carrier_id, name, data_gb, duration_days, price_usd, description, is_unlimited) VALUES
(1, 1, '3GB 7 Days', 3.00, 7, 9.99, '3GB high-speed data for 7 days', 0),
(1, 2, '5GB 14 Days', 5.00, 14, 14.99, '5GB high-speed data for 14 days', 0),
(2, 1, '2GB 7 Days', 2.00, 7, 7.99, '2GB high-speed data for 7 days', 0),
(3, 3, '10GB 30 Days', 10.00, 30, 24.99, '10GB high-speed data for 30 days', 0),
(4, 2, '5GB 10 Days', 5.00, 10, 12.99, '5GB high-speed data for 10 days', 0),
(5, 1, '3GB 7 Days', 3.00, 7, 9.99, '3GB high-speed data for 7 days', 0),
(6, 4, '4GB 7 Days', 4.00, 7, 11.99, '4GB high-speed data for 7 days', 0),
(7, 3, '5GB 14 Days', 5.00, 14, 14.99, '5GB high-speed data for 14 days', 0),
(8, 2, '6GB 14 Days', 6.00, 14, 16.99, '6GB high-speed data for 14 days', 0),
(9, 1, '8GB 30 Days', 8.00, 30, 19.99, '8GB high-speed data for 30 days', 0),
(10, 4, '3GB 7 Days', 3.00, 7, 9.99, '3GB high-speed data for 7 days', 0),
(11, 2, 'Unlimited 30 Days', 0.00, 30, 29.99, 'Unlimited data for 30 days', 1);
```

## Seed Data Details

### 15 Countries

Spread across Latin America, Europe, Asia-Pacific, and North America for comprehensive coverage:

| Country | Code | Region |
|---------|------|--------|
| Argentina | AR | Latin America |
| Brazil | BR | Latin America |
| Chile | CL | Latin America |
| Colombia | CO | Latin America |
| Mexico | MX | Latin America |
| Spain | ES | Europe |
| France | FR | Europe |
| Italy | IT | Europe |
| Germany | DE | Europe |
| Portugal | PT | Europe |
| United States | US | North America |
| Canada | CA | North America |
| Australia | AU | Asia-Pacific |
| Japan | JP | Asia-Pacific |
| Singapore | SG | Asia-Pacific |

### 4 Carriers

Major telecommunications providers with global presence:

- **Claro** - Leading in Latin America
- **Movistar** - Strong in Spain and Latin America
- **Vodafone** - European telecom giant
- **Orange** - European carrier with global reach

### 12 Plans

Realistic pricing (₹$7.99–$29.99) and data allocations:

| Plan | Data | Duration | Price |
|------|------|----------|-------|
| 2GB 7 Days | 2 GB | 7 days | $7.99 |
| 3GB 7 Days | 3 GB | 7 days | $9.99 |
| 5GB 10 Days | 5 GB | 10 days | $12.99 |
| 4GB 7 Days | 4 GB | 7 days | $11.99 |
| 5GB 14 Days | 5 GB | 14 days | $14.99 |
| 6GB 14 Days | 6 GB | 14 days | $16.99 |
| 8GB 30 Days | 8 GB | 30 days | $19.99 |
| 10GB 30 Days | 10 GB | 30 days | $24.99 |
| Unlimited 30 Days | Unlimited | 30 days | $29.99 |

(Plus a few country-specific variations)

## Accessing the Seeded Data

### Via REST API

```bash
# Get all countries
curl http://localhost:8000/api/countries

# Search for a specific country
curl http://localhost:8000/api/countries?q=argentina

# Get plans for Argentina
curl http://localhost:8000/api/plans?country=ar

# Get plans under $15
curl http://localhost:8000/api/plans?max_price=15

# Get plans with at least 5GB
curl http://localhost:8000/api/plans?min_gb=5

# Get a specific plan by ID
curl http://localhost:8000/api/plans/1
```

### Via Web Frontend

1. Navigate to `http://localhost:3000`
2. Use the search box to find a country
3. Click on a country to view its available plans
4. Plans are displayed sorted by price (lowest first)

### Via Mobile App

1. Start the mobile dev server: `cd apps/mobile && npm start`
2. Scan QR code or open Expo app
3. Browse countries with search
4. Tap a country to view plans

## Troubleshooting

### "UNIQUE constraint failed: countries.iso2"

This means countries have already been seeded. The seed script is idempotent and will skip if data exists.

**Solution:** Either run the script again (it's safe) or check your data in the database.

### "no such table: countries"

The migration hasn't been applied yet.

**Solution:** Run `alembic upgrade head` first.

### Missing environment variables

If seeding fails with environment errors, ensure `.env` is set up:

```bash
cp .env.example .env
```

And the backend is configured to connect to MySQL.

## Modifying Seed Data

Edit the seed data before running the script:

1. **File:** `apps/backend/app/seed/seed_data.json`
2. **Format:** JSON with `countries`, `carriers`, `plans` arrays
3. **Add/remove/modify** entries as needed
4. **Re-run:** `python -c "from app.seed import seed_database; seed_database()"`

**Note:** If you want to replace existing data entirely, you may need to:
1. Drop the tables: `alembic downgrade base`
2. Recreate: `alembic upgrade head`
3. Re-seed: `python -c "from app.seed import seed_database; seed_database()"`

## Performance Notes

- Seeding 15 countries + 4 carriers + 12 plans takes < 1 second
- Seed script uses batch inserts for efficiency
- Indices on `country.iso2`, `country.name`, and `plan.price_usd` improve query performance for the API

## Next Steps

Once seeded, the catalog is ready for:
- Frontend testing with real data
- API integration testing
- Performance testing and optimization
- Custom plan addition/editing (future phases)
