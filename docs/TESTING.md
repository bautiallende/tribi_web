# Testing Guide

## Backend Testing (pytest)

The backend uses pytest with SQLite for isolated, fast unit testing.

### Setup

```bash
cd apps/backend

# Ensure dependencies are installed
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_verify_code_success -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run with detailed output
pytest tests/ -vv -s
```

### Test Database

Tests use a **temporary file-based SQLite database** to ensure:
- ✅ Test isolation (each test gets fresh DB)
- ✅ Data persistence across sessions (unlike in-memory)
- ✅ Proper multi-test coordination
- ✅ Fast execution

**Location:** `${TEMP}/tmp*.db` (automatically cleaned up)

### Test Structure

Each test file follows this pattern:

```python
@pytest.fixture
def temp_db_file():
    """Create temporary SQLite database for tests"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        yield tmp.name
    Path(tmp.name).unlink(missing_ok=True)

@pytest.fixture
def session(temp_db_file):
    """Create database session"""
    engine = create_engine(f"sqlite:///{temp_db_file}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def test_client(session):
    """Override get_db dependency for testing"""
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Test Coverage

**Current Test Suite: 8/8 PASSING** ✅

#### Auth Tests (5 tests)
- `test_request_code_creates_user`: Validates OTP request endpoint
- `test_verify_code_success`: Tests successful OTP verification → JWT issuance
- `test_verify_code_invalid`: Tests invalid OTP handling
- `test_get_me_success`: Tests JWT validation and user profile retrieval
- `test_get_me_no_token`: Tests 401 response without token

#### Existing Tests (3 tests)
- `test_health`: Health check endpoint
- `test_read_health`: Redundant health check
- `test_health_check` (catalog): Catalog health

### Mocking & Isolation

**Email Sending (SMTP):**
```python
@patch('app.api.auth.send_email_smtp')
def test_request_code_creates_user(mock_send_email, test_client):
    # send_email_smtp is mocked, no real SMTP connection attempted
    response = test_client.post('/auth/request-code', ...)
    assert mock_send_email.called
```

This prevents:
- ❌ Connecting to MailHog/SMTP during tests
- ❌ Sending real emails
- ❌ Flaky tests due to network issues

### Environment Variables for Testing

Tests don't require `.env` setup because:
1. Fixtures override database connection (SQLite)
2. SMTP is mocked
3. JWT generation uses hardcoded `JWT_SECRET="dev-secret"`

### Debugging Tests

```bash
# Show print statements and logging
pytest tests/test_auth.py -s

# Stop on first failure
pytest tests/test_auth.py -x

# Only re-run failed tests
pytest tests/ --lf

# Enter debugger on failure
pytest tests/test_auth.py --pdb
```

### CI Integration

GitHub Actions runs tests on every push:

```yaml
# .github/workflows/ci.yml
- name: Run Backend Tests
  run: |
    cd apps/backend
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

## Web Testing (Next.js)

### Build Testing

```bash
cd apps/web

# Build for production
npm run build

# Run linting
npm run lint

# If linting errors found:
npm run lint -- --fix
```

### Dev Testing

```bash
cd apps/web

# Start dev server
npm run dev

# Open http://localhost:3000

# Test flows:
# 1. /auth → login with any email + code 000000
# 2. /account → view profile (requires login)
# 3. /plans/us → browse plans
# 4. Select plan → /checkout → complete order
```

### Integration Testing

To test end-to-end flow:

```bash
# Terminal 1: Start backend
cd apps/backend
python -m uvicorn app.main:app --reload

# Terminal 2: Start web
cd apps/web
npm run dev

# Terminal 3: Navigate and test in browser
# http://localhost:3000 → login flow
```

## Performance

### Backend Test Execution Time

```
Total: ~1 second
- Database setup: ~200ms
- Auth tests: ~300ms
- Health tests: ~50ms
- Cleanup: ~100ms
```

### Web Build Time

```
Production build: ~20-30 seconds
- Compilation: ~10s
- Type checking: ~8s
- Optimization: ~5s
```

## Troubleshooting

### Test Failure: "IntegrityError: NOT NULL constraint failed"

**Cause:** Model requires fields that aren't provided in test fixtures

**Solution:** Update fixture to include all required fields (e.g., `amount_minor_units` for Order)

### Test Failure: "PermissionError: database is locked"

**Cause:** Previous test didn't properly close database connection

**Solution:** Ensure `session.close()` in fixture teardown

### Test Failure: "ModuleNotFoundError"

**Cause:** Missing dependencies or wrong PYTHONPATH

**Solution:**
```bash
pip install -r requirements.txt
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

### Web Build Failure: "Cannot find module"

**Cause:** UI package not linked or NEXT_PUBLIC_API_BASE not set

**Solution:**
```bash
npm install
export NEXT_PUBLIC_API_BASE=http://localhost:8000
npm run build
```

## Best Practices

✅ **Do:**
- Write tests for new endpoints
- Use fixtures for common setup
- Mock external services (SMTP, payment providers)
- Test both success and error paths
- Run tests before committing

❌ **Don't:**
- Skip tests in CI/CD pipeline
- Commit failing tests
- Test external APIs directly (mock instead)
- Use real databases in tests

## See Also

- Backend: `apps/backend/tests/`
- Web: `apps/web/` (no dedicated test directory yet)
- CI/CD: `.github/workflows/ci.yml`
- Architecture: `docs/ARCHITECTURE.md`
