# Architecture

**Note:** This file should be in the `docs/` directory, but due to limitations in the current environment, it is placed in the root directory.

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

The `packages/ui` directory contains shared UI components that can be used in both the web and mobile applications.
