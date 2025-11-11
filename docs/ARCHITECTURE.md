# Architecture

## Monorepo Structure

The monorepo is organized as follows:

*   `apps/`: Contains the main applications (backend, web, mobile).
    *   `apps/backend`: FastAPI application.
    *   `apps/web`: Next.js application.
    *   `apps/mobile`: Expo application.
*   `packages/`: Contains shared packages.
    *   `packages/ui`: Shared UI components.
*   `infrastructure/`: Contains Docker Compose files and other infrastructure-related configuration.
*   `docs/`: Contains documentation.
*   `.github/`: Contains GitHub Actions workflows.

## Backend

The backend is a FastAPI application with the following structure:

*   `app/`: Main application directory.
    *   `api/`: API endpoints.
    *   `core/`: Core application logic.
    *   `models/`: SQLAlchemy models.
    *   `schemas/`: Pydantic schemas.
    *   `db/`: Database connection and session management.
*   `alembic/`: Alembic migrations.
*   `tests/`: PyTest tests.

## Web

The web application is a Next.js application with the following structure:

*   `app/`: App Router directory.
*   `components/`: React components.
*   `lib/`: Utility functions.
*   `styles/`: Global styles.
*   `i18n/`: Internationalization files.

## Mobile

The mobile application is an Expo application with the following structure:

*   `app/`: Main application directory.
*   `components/`: React components.
*   `navigation/`: React Navigation configuration.
*   `store/`: State management (Zustand or Redux Toolkit).

## Shared UI

The `packages/ui` directory contains shared UI components that can be used in the web application.

## Health Check Flow

1.  **Web/Mobile Application:** Makes a `GET` request to `${BACKEND_URL}/health`.
2.  **Backend Application:** The FastAPI application receives the request and returns `{"status": "ok"}`.
3.  **Database:** The backend may optionally check the database connection as part of its health check.