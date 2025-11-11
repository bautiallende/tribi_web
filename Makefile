.PHONY: dev

dev:
	docker-compose -f infrastructure/docker-compose.yml up -d
	export $(cat .env | xargs)
	cd apps/backend && uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} &
	cd apps/web && npm run dev
