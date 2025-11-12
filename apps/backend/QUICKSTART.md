# 🚀 Quick Start - MySQL Local Development

## Setup (one-time)

```powershell
# Navigate to backend
cd apps/backend

# Create MySQL database and tables
python setup_mysql.py

# You should see:
# ✅ Database 'tribi_dev' created successfully!
# ✅ All tables created successfully!
```

## Daily Development

### Start Backend Server

```powershell
cd apps/backend
python -m uvicorn app.main:app --reload
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Run Tests

```powershell
cd apps/backend
python -m pytest tests/ -v
# Should show: 8 passed (5 auth + 3 existing)
```

### Run Alembic Migrations

```powershell
cd apps/backend
alembic upgrade head
```

### Check Database

```powershell
# Connect to MySQL
mysql -h localhost -u root -p1234 -D tribi_dev

# List tables
SHOW TABLES;

# View users table
SELECT * FROM users;
```

## Environment

Created: `.env` file with credentials
```
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=tribi_dev
MYSQL_HOST=localhost:3306
```

⚠️ This is for LOCAL DEV ONLY. In production, use secure env vars.

## Next Steps

- [ ] Start server: `python -m uvicorn app.main:app --reload`
- [ ] Run tests: `python -m pytest tests/ -v`
- [ ] Create web pages: `/auth`, `/checkout`, `/orders`, `/account`
- [ ] Create mobile screens: OTP, purchase flow
- [ ] Update docs and CI
