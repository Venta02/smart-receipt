.PHONY: help install dev test lint format clean docker-up docker-down

help:
	@echo "smart-receipt Development Commands"
	@echo ""
	@echo "  make install      Install Python dependencies"
	@echo "  make dev          Run the API server in development mode"
	@echo "  make test         Run the test suite"
	@echo "  make lint         Run linters"
	@echo "  make format       Auto format code"
	@echo "  make docker-up    Start Redis and monitoring services"
	@echo "  make docker-down  Stop services"
	@echo "  make clean        Remove cached files"

install:
	pip install -r requirements.txt

dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/ scripts/
	ruff check --fix src/ tests/

docker-up:
	docker compose up -d redis
	@echo "Redis started on localhost:6379"

docker-up-full:
	docker compose up -d
	@echo "All services started"
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache htmlcov .coverage
