# Neural Terminal - Makefile
# Standard commands for development workflow

.PHONY: help install update test test-unit test-integration test-e2e test-coverage lint format format-check migrate migrate-create run db-init db-backup db-vacuum db-stats db-health db-purge db-purge-days db-purge-all db-purge-dry-run docker-build docker-run docker-compose-up docker-compose-down docker-push clean

# Default target
help:
	@echo "Neural Terminal - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make update           Update dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-e2e         Run end-to-end tests only"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (ruff + mypy)"
	@echo "  make format           Format code (black + ruff)"
	@echo "  make format-check     Check code formatting"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          Run database migrations"
	@echo "  make migrate-create   Create new migration (use: make migrate-create message='description')"
	@echo ""
	@echo "Application:"
	@echo "  make run              Run the Streamlit application"
	@echo ""
	@echo "Database Management:"
	@echo "  make db-init          Initialize database for production"
	@echo "  make db-backup        Create database backup"
	@echo "  make db-vacuum        Vacuum database to reclaim space"
	@echo "  make db-stats         Show database statistics"
	@echo "  make db-health        Check database health"
	@echo ""
	@echo "Data Purge:"
	@echo "  make db-purge         Purge conversations older than 30 days"
	@echo "  make db-purge-days DAYS=7   Purge conversations older than N days"
	@echo "  make db-purge-all     Purge ALL conversations"
	@echo "  make db-purge-dry-run Show what would be purged (no changes)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build        Build Docker image"
	@echo "  make docker-run          Run Docker container"
	@echo "  make docker-compose-up   Start with docker-compose"
	@echo "  make docker-compose-down Stop docker-compose"
	@echo "  make docker-push         Push image to registry"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Clean generated files"

# ============================================================================
# Installation
# ============================================================================
install:
	poetry install

update:
	poetry update

# ============================================================================
# Testing
# ============================================================================
test:
	poetry run pytest -v --cov=src/neural_terminal --cov-report=term-missing

test-unit:
	poetry run pytest tests/unit -v

test-integration:
	poetry run pytest tests/integration -v

test-e2e:
	poetry run pytest tests/e2e -v

test-coverage:
	poetry run pytest --cov=src/neural_terminal --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

# ============================================================================
# Code Quality
# ============================================================================
lint:
	@echo "Running ruff..."
	poetry run ruff check src tests
	@echo "Running mypy..."
	poetry run mypy src

format:
	@echo "Running black..."
	poetry run black src tests
	@echo "Running ruff..."
	poetry run ruff check --fix src tests

format-check:
	poetry run black --check src tests

# ============================================================================
# Database
# ============================================================================
migrate:
	poetry run alembic upgrade head

migrate-create:
	@if [ -z "$(message)" ]; then \
		echo "Usage: make migrate-create message='description'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(message)"

# ============================================================================
# Database Management
# ============================================================================
db-init:
	@echo "Initializing database for production..."
	PYTHONPATH=src poetry run python scripts/init_db.py

db-backup:
	@echo "Creating database backup..."
	PYTHONPATH=src poetry run python scripts/init_db.py --backup

db-vacuum:
	@echo "Vacuuming database..."
	PYTHONPATH=src poetry run python scripts/init_db.py --vacuum

db-stats:
	@echo "Database statistics:"
	PYTHONPATH=src poetry run python scripts/init_db.py --stats

db-health:
	@echo "Checking database health..."
	PYTHONPATH=src poetry run python scripts/health_check.py

# ============================================================================
# Data Management
# ============================================================================
db-purge:
	@echo "Purging conversations older than 30 days..."
	PYTHONPATH=src poetry run python scripts/purge_conversations.py

db-purge-days:
	@echo "Purging conversations older than $(DAYS) days..."
	PYTHONPATH=src poetry run python scripts/purge_conversations.py --days $(DAYS)

db-purge-all:
	@echo "Purging ALL conversations..."
	PYTHONPATH=src poetry run python scripts/purge_conversations.py --all

db-purge-dry-run:
	@echo "Showing what would be purged (dry run)..."
	PYTHONPATH=src poetry run python scripts/purge_conversations.py --dry-run

# ============================================================================
# Application
# ============================================================================
run:
	poetry run streamlit run app.py --server.port=7860

# ============================================================================
# Docker
# ============================================================================
docker-build:
	@echo "Building Docker image..."
	docker build -t neural-terminal:latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 7860:7860 \
		-e OPENROUTER_API_KEY=$(OPENROUTER_API_KEY) \
		-v $(PWD)/data:/app/data \
		neural-terminal:latest

docker-compose-up:
	@echo "Starting with docker-compose..."
	docker-compose up -d

docker-compose-down:
	@echo "Stopping docker-compose..."
	docker-compose down

docker-push:
	@echo "Pushing to registry..."
	docker tag neural-terminal:latest $(REGISTRY)/neural-terminal:latest
	docker push $(REGISTRY)/neural-terminal:latest

# ============================================================================
# Maintenance
# ============================================================================
clean:
	@echo "Cleaning Python cache files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleaning directories..."
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf .mypy_cache/ 2>/dev/null || true
	rm -rf *.egg-info/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	@echo "Cleaning database files..."
	rm -f *.db 2>/dev/null || true
	rm -f test.db 2>/dev/null || true
	@echo "Clean complete!"
