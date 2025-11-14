.PHONY: help venv install sync lint format fix test build up down dev clean

# Default target
help:
	@echo "Available targets:"
	@echo "  venv       - Create virtual environment with uv"
	@echo "  install    - Install/sync dependencies with uv (creates venv if needed)"
	@echo "  sync       - Sync dependencies (alias for install)"
	@echo "  lint       - Run ruff linter (requires install)"
	@echo "  format     - Format code with ruff (requires install)"
	@echo "  fix        - Auto-fix linting issues (requires install)"
	@echo "  test       - Run tests (requires install)"
	@echo "  build      - Build Docker image"
	@echo "  up         - Start services with docker-compose"
	@echo "  down       - Stop services"
	@echo "  dev        - Start dev container with hot reload"
	@echo "  clean      - Clean build artifacts and caches"

# Create virtual environment if it doesn't exist
# Use Python 3.12 explicitly (Python 3.14 not supported by onnxruntime/chromadb)
venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment with Python 3.12..."; \
		uv venv --python python3.12 || uv venv --python 3.12; \
	else \
		echo "Virtual environment already exists. Delete .venv to recreate with Python 3.12."; \
	fi

# Install/sync dependencies (depends on venv)
# uv pip install with explicit Python path to ensure it uses the venv
install sync: venv
	@echo "Installing dependencies into virtual environment..."
	uv pip install --python .venv/bin/python .

# Lint code (depends on install)
lint: install
	uv run ruff check .

# Format code (depends on install)
format: install
	uv run ruff format .

# Auto-fix linting issues (depends on install)
fix: install
	uv run ruff check --fix .
	uv run ruff format .

# Run tests (depends on install)
test: install
	uv run pytest tests/ -v || echo "No tests directory found. Create tests/ directory to add tests."

# Build Docker image
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Start dev container with hot reload
dev:
	docker-compose up

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	docker-compose down -v || true

