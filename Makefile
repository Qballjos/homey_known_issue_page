.PHONY: help install dev test lint clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       Install production and development dependencies"
	@echo "  make dev           Start local development server with auto-reload"
	@echo "  make test          Run pytest automated test suite"
	@echo "  make lint          Run linter check"
	@echo "  make docker-build  Build Docker container image"
	@echo "  make docker-up     Start Docker Compose stack in background"
	@echo "  make docker-down   Stop Docker Compose stack"
	@echo "  make clean         Remove Python bytecode and test caches"

install:
	pip install -r requirements.txt

dev:
	PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

test:
	PYTHONPATH=. pytest -v tests/

lint:
	python -m py_compile app/main.py app/**/*.py tests/*.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t homey-known-issues:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down
