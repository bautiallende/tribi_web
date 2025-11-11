# Tribi Monorepo

This repository contains the source code for Tribi, a service for selling eSIMs for tourism.

## Stack

*   **Monorepo:** Managed with npm workspaces.
*   **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2.
*   **Web:** Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui.
*   **Mobile:** Expo, React Navigation, TypeScript.
*   **Database:** MySQL 8.
*   **Infrastructure:** Docker Compose.
*   **CI/CD:** GitHub Actions.

## How to run locally

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd tribi
    ```
2.  **Set up environment variables:**
    Copy the `.env.example` file to `.env` and fill in the required values.
    ```bash
    cp .env.example .env
    ```
3.  **Start the infrastructure:**
    This will start the MySQL database and MailHog.
    ```bash
    docker-compose up -d
    ```
4.  **Run the development servers:**
    This will start the backend and web applications.
    ```bash
    make dev
    ```

## How to add new modules

To add a new application, create a new directory under the `apps` directory. For a new shared package, create a new directory under the `packages` directory.

## Monorepo Structure

The monorepo is organized as follows:

*   `apps/`: Contains the main applications (backend, web, mobile).
*   `packages/`: Contains shared packages (e.g., UI components).
*   `infrastructure/`: Contains Docker Compose files and other infrastructure-related configuration.
*   `docs/`: Contains documentation.
*   `.github/`: Contains GitHub Actions workflows.
