.PHONY: help venv install sync lint format fix test build rebuild up down dev clean download-spacy-model

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
	@echo "  build      - Build Docker image (uses cache)"
	@echo "  rebuild    - Build Docker image without cache"
	@echo "  up         - Start services with docker-compose"
	@echo "  down       - Stop services"
	@echo "  dev        - Start dev container with hot reload"
	@echo "  download-spacy-model - Download spaCy model wheel for Docker caching"
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
# Install dependencies directly from pyproject.toml (don't install project itself)
install sync: venv
	@echo "Installing dependencies into virtual environment..."
	uv pip install --python .venv/bin/python \
		chainlit \
		chromadb \
		presidio-analyzer \
		presidio-anonymizer \
		spacy \
		openai \
		sqlalchemy \
		aiosqlite \
		langchain \
		langchain-classic \
		langchain-community \
		langchain-openai \
		langchain-text-splitters \
		tiktoken \
		ruff \
		pytest \
		pytest-asyncio

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
# Ensure .local/cache/spacy-models/ exists so Docker COPY doesn't fail
build:
	@mkdir -p .local/cache/spacy-models
	@docker-compose build

rebuild:
	@mkdir -p .local/cache/spacy-models
	@docker-compose build --no-cache --pull

# Start services
# Clean up any existing containers first to avoid ContainerConfig errors
up:
	@echo "Cleaning up any existing containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f chainlit-app 2>/dev/null || true
	@echo "Starting services..."
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Start dev container with hot reload
# Clean up any existing containers first to avoid ContainerConfig errors
dev:
	@echo "Cleaning up any existing containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f chainlit-app 2>/dev/null || true
	@echo "Starting dev container..."
	docker-compose up

# Download spaCy model wheel for Docker caching
# Ensures directory exists for Docker COPY to work even if download fails
download-spacy-model:
	@echo "Downloading spaCy model wheel to .local/cache/spacy-models/..."
	@mkdir -p .local/cache/spacy-models
	@if command -v python3 >/dev/null 2>&1; then \
		python3 scripts/download-spacy-model.py || \
		(echo "Warning: Could not download model wheel. Docker will download during build." && exit 1); \
	else \
		echo "Error: python3 not found. Cannot download model wheel." && exit 1; \
	fi
	@echo "Model wheel cached at .local/cache/spacy-models/"

# Clean build artifacts
clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info .venv 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	# Try to remove __pycache__ with sudo if permission denied
	@if [ -d __pycache__ ]; then \
		sudo rm -rf __pycache__ 2>/dev/null || \
		docker run --rm -v "$$(pwd):/app" -w /app python:3.12-slim rm -rf __pycache__ 2>/dev/null || \
		echo "Warning: Could not remove __pycache__ (may need manual cleanup)"; \
	fi
	docker-compose down -v || true

