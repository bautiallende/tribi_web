.PHONY: help dev backend web mobile test lint build infra-up infra-down

help:
	@echo "Tribi Monorepo - Available Commands"
	@echo "=================================="
	@echo "make dev         - Start all services (docker, backend, web)"
	@echo "make backend     - Start backend only"
	@echo "make web         - Start web only"
	@echo "make mobile      - Start mobile app"
	@echo "make test        - Run all tests"
	@echo "make lint        - Run linters"
	@echo "make build       - Build all apps"
	@echo "make infra-up    - Start infrastructure (docker-compose)"
	@echo "make infra-down  - Stop infrastructure"

infra-up:
	docker compose -f infrastructure/docker-compose.yml up -d

infra-down:
	docker compose -f infrastructure/docker-compose.yml down

backend: infra-up
	cd apps/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

mobile:
	cd apps/mobile && npx expo start

dev: infra-up
	@echo "Starting all services..."
	@cd apps/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
	@cd apps/web && npm run dev

test:
	cd apps/backend && pytest
	cd apps/web && npm run build

lint:
	@echo "Linting all apps..."
	pre-commit run --all-files || true

build:
	@echo "Building all apps..."
	cd apps/backend && echo "Backend is ready to run"
	cd apps/web && npm run build
	cd apps/mobile && echo "Mobile is ready with expo"
