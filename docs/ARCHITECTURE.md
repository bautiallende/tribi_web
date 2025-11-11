# Architecture

## Monorepo Structure

The tribi monorepo uses npm workspaces to manage multiple applications and shared packages.

```
tribi/
├── apps/
│   ├── backend/      (FastAPI)
│   ├── web/          (Next.js)
│   └── mobile/       (Expo/React Native)
├── packages/
│   └── ui/           (Shared UI components)
├── infrastructure/   (Docker Compose, env configs)
├── docs/             (Documentation)
├── .github/
│   └── workflows/    (CI/CD)
└── package.json      (Root - npm workspaces)
```

## Backend (FastAPI)

**Location:** `apps/backend/`

Structure:
```
app/
├── api/          (API routes - future expansion)
├── core/         (Configuration, settings)
├── db/           (Database session, models)
├── models/       (SQLAlchemy models)
├── schemas/      (Pydantic schemas)
└── main.py       (FastAPI app entry point)
alembic/          (Database migrations)
tests/            (PyTest unit tests)
requirements.txt  (Python dependencies)
```

**Key Features:**
- `/health` endpoint returns `{"status": "ok"}`
- CORS enabled for frontend communication
- SQLAlchemy + Alembic for database management
- MySQL via Docker Compose
- Environment variables via `.env`

## Web (Next.js)

**Location:** `apps/web/`

Structure:
```
app/
├── page.tsx           (Home page)
├── health/
│   └── page.tsx       (Health status page)
app/
next.config.js        (Next.js configuration)
tailwind.config.ts    (Tailwind CSS config)
package.json          (Dependencies)
tsconfig.json         (TypeScript config)
```

**Key Features:**
- Next.js 14 with App Router
- Tailwind CSS for styling
- React Query for data fetching
- i18n support (ES/EN)
- `/health` page fetches backend health status
- @tribi/ui shared components

## Mobile (Expo)

**Location:** `apps/mobile/`

Structure:
```
App.tsx           (Main navigation)
app.json          (Expo config)
babel.config.js   (Babel config)
package.json      (Dependencies)
```

**Key Features:**
- Expo + React Native
- React Navigation (Stack Navigator)
- Health screen fetches backend status
- TypeScript enabled
- Environment variables via `.env` (EXPO_PUBLIC_API_BASE)

## Shared UI Components

**Location:** `packages/ui/`

Exports:
- `Button` - Custom button component with variants
- `Card` - Card layout components (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter)

Used in web and mobile apps via `@tribi/ui` workspace reference.

## Infrastructure

**Location:** `infrastructure/`

- `docker-compose.yml` - Services:
  - **MySQL 8** on port 3306
  - **MailHog** on ports 1025 (SMTP) and 8025 (UI)

Environment variables in `.env` control service configuration.

## Development Workflow

### Setup
```bash
git clone <repo>
cp .env.example .env
make infra-up
```

### Running Services
```bash
make dev          # Start all (docker + backend + web)
make backend      # Backend only (with hot reload)
make web          # Web only (with hot reload)
make mobile       # Mobile with Expo
```

### Testing & Quality
```bash
make test         # Run tests (backend + web build)
make lint         # Run pre-commit hooks (black, ruff, eslint, prettier)
make build        # Build all apps
```

## CI/CD Pipeline

**Location:** `.github/workflows/ci.yml`

Runs on push to `main` and `develop` branches, and on PRs.

**Matrix builds:**
- **Backend**: Python 3.10, 3.11 (pytest)
- **Web**: Node 18.x, 20.x (build + lint)

Each job runs in parallel for faster feedback.

## Database Migrations

Alembic manages database schema changes.

```bash
cd apps/backend
alembic upgrade head    # Apply migrations
alembic revision --autogenerate -m "Migration name"
```

## Environment Variables

**Root `.env.example`:**
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=tribi
MYSQL_PASSWORD=tribi
MYSQL_DB=tribi
MYSQL_ROOT_PASSWORD=tribi_root
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_API_BASE=http://localhost:8000
```

Each app reads from this root `.env` or can have its own `.env.local`.

## Health Check Flow

1. **Web/Mobile Application:** Makes a `GET` request to `${BACKEND_URL}/health`.
2. **Backend Application:** The FastAPI application receives the request and returns `{"status": "ok"}`.
3. **Database:** The backend may optionally check the database connection as part of its health check.

## Notes

- npm workspaces eliminate need for monorepo tools like Lerna
- Pre-commit hooks ensure code quality before commits
- Makefile provides convenient commands for development
- GitHub Actions runs on every push/PR for automated testing
