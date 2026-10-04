.PHONY: setup test test-backend test-frontend run-api run-worker run-web migrate docker-up docker-down

setup:
	python -m venv .venv
	./.venv/bin/pip install -e "./backend[dev]"
	cd web && npm install

test: test-backend test-frontend

test-backend:
	pytest -c backend/pyproject.toml backend/tests -q

test-frontend:
	cd web && npx vitest run

run-api:
	uvicorn backend.app.main:app --reload --port 8000

run-merged: build-frontend
	uvicorn backend.app.main:app --reload --port 8000

build-frontend:
	cd web && npm run build

run-worker:
	arq backend.app.worker.settings.WorkerSettings

run-web:
	cd web && npm run dev

migrate:
	cd backend && alembic upgrade head

docker-up:
	docker compose up -d

docker-down:
	docker compose down
