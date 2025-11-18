# Tribi Monorepo

This repository contains the source code for Tribi, a service for selling eSIMs for tourism.

## Stack

- **Monorepo:** npm workspaces for unified dependency management
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Web:** Next.js 14 (App Router), TypeScript, Tailwind CSS, React Query, i18n
- **Mobile:** Expo, React Native, React Navigation, TypeScript
- **Database:** MySQL 8, migrations via Alembic
- **Infrastructure:** Docker Compose (MySQL + MailHog)
- **CI/CD:** GitHub Actions (Python 3.10/3.11, Node 18/20)
- **Code Quality:** Pre-commit hooks (black, ruff, eslint, prettier)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for backend)
- Node.js 18+ (for web)
- npm workspaces support

### Setup

1. **Clone and enter directory:**

   ```bash
   git clone <repository-url>
   cd tribi
   ```

2. **Set up environment variables:**

   ```bash
   cp .env.example .env
   ```

   Key variables to configure:

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

3. **Install pre-commit hooks (optional but recommended):**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Running the Application

**Start all services (infrastructure + backend + web):**

```bash
make dev
```

This command:

- Starts Docker Compose (MySQL + MailHog)
- Launches backend on `http://localhost:8000`
- Launches web app on `http://localhost:3000`

**Start individual services:**

```bash
make infra-up      # Start Docker services only
make backend       # Backend only (hot reload)
make web           # Web only (hot reload)
make mobile        # Mobile app with Expo
```

## Available Commands

| Command           | Description                               |
| ----------------- | ----------------------------------------- |
| `make dev`        | Start all services (docker, backend, web) |
| `make backend`    | Start backend with hot reload             |
| `make web`        | Start web with hot reload                 |
| `make mobile`     | Start mobile app                          |
| `make test`       | Run backend tests + build web             |
| `make lint`       | Run pre-commit hooks                      |
| `make build`      | Build all apps                            |
| `make infra-up`   | Start Docker services                     |
| `make infra-down` | Stop Docker services                      |

## Per-App Commands

### Backend

```bash
cd apps/backend

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Web

```bash
cd apps/web

# Development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

### Mobile

```bash
cd apps/mobile

# Start Expo
npx expo start

# Android
npx expo start --android

# iOS
npx expo start --ios
```

## Catalog Feature (eSIM Plans)

The app includes a complete catalog feature for browsing and filtering eSIM plans by country.

### Initial Setup

1. **Apply database migrations:**

   ```bash
   cd apps/backend
   alembic upgrade head
   ```

2. **Seed initial data (countries, carriers, plans):**

   ```bash
   python -c "from app.seed import seed_database; seed_database()"
   ```

   This populates the database with 15 countries, 4 carriers, and 12 realistic eSIM plans.

   See [SEEDING.md](./docs/SEEDING.md) for detailed seeding instructions.

### Accessing the Catalog

**Web:**

- Home page: `http://localhost:3000/`
- Search for countries with autocomplete
- Click a country to view available plans
- Plans sorted by price (lowest first)

**Mobile:**

- Browse countries with search functionality
- Tap a country to see its plans
- Display plan details (data, duration, price)

**API:**

- `GET /api/countries` - List all countries, optional search: `?q=argentina`
- `GET /api/plans` - List plans with optional filters:
  - `?country=ar` - Plans for Argentina
  - `?max_price=15` - Plans at or under $15
  - `?min_gb=5` - Plans with at least 5GB
  - `?days=7` - Plans with 7-day duration
- `GET /api/plans/{id}` - Get full plan details

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for endpoint specifications and database design.

## API Endpoints

### Health Check

- **Backend:** `GET http://localhost:8000/health`
  - Response: `{"status": "ok"}`
- **Web:** `GET http://localhost:3000/health`
  - Displays backend health status
- **Mobile:** Health screen fetches backend status

## Project Structure

```
tribi/
├── apps/
│   ├── backend/               # FastAPI application
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/config.py
│   │   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── requirements.txt
│   │   └── package.json
│   │
│   ├── web/                   # Next.js application
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   └── health/page.tsx
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   └── tailwind.config.ts
│   │
│   └── mobile/                # Expo application
│       ├── App.tsx
│       ├── app.json
│       ├── package.json
│       └── babel.config.js
│
├── packages/
│   └── ui/                    # Shared UI components
│       ├── src/
│       │   ├── Button.tsx
│       │   └── Card.tsx
│       ├── index.tsx
│       └── package.json
│
├── infrastructure/
│   └── docker-compose.yml     # MySQL + MailHog
│
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture
│   └── README.md
│
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
│
├── .env.example               # Environment variables template
├── .pre-commit-config.yaml    # Pre-commit hooks config
├── Makefile                   # Development commands
├── package.json               # Root (npm workspaces)
└── README.md                  # This file
```

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed architecture information.

## Database

MySQL is managed via Docker Compose. Migrations use Alembic:

```bash
cd apps/backend

# View migration status
alembic current

# Create new migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on:

- Push to `main` and `develop` branches
- Pull requests

**Matrix Builds:**

- Backend: Python 3.10, 3.11
- Web: Node 18.x, 20.x

Each job runs pytest/npm build independently.

## Code Quality

Pre-commit hooks configured in `.pre-commit-config.yaml`:

- **Python:** black, ruff (formatting + linting)
- **JavaScript/TypeScript:** eslint, prettier (linting + formatting)
- **General:** trailing whitespace, end-of-file fixer, YAML check

Install hooks:

```bash
pre-commit install
```

Run manually:

```bash
pre-commit run --all-files
```

## Environment Variables

See `.env.example` for all available variables. Key variables:

```bash
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=tribi
MYSQL_PASSWORD=tribi
MYSQL_DB=tribi
MYSQL_ROOT_PASSWORD=tribi_root

# Frontend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_API_BASE=http://localhost:8000
```

## Troubleshooting

### Port already in use

```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (web)
lsof -ti:3000 | xargs kill -9
```

### Docker issues

```bash
# Clean up Docker
docker compose -f infrastructure/docker-compose.yml down
docker volume prune

# Restart
make infra-up
```

### Python dependencies

```bash
cd apps/backend
pip install --upgrade pip
pip install -r requirements.txt
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `pre-commit run --all-files` to check code quality
4. Commit with a descriptive message
5. Push and create a PR

## License

See LICENSE file.
