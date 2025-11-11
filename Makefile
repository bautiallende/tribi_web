.PHONY: dev

dev:
	@echo "Starting development environment..."
	@docker-compose up -d db mailhog
	@echo "Exporting environment variables..."
	@export $(cat .env | xargs)
	@echo "Starting backend..."
	@cd apps/backend && uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} &
	@echo "Starting web..."
	@cd apps/web && npm run dev &
