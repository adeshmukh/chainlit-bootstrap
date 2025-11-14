# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir --root-user-action=ignore uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install Python dependencies using uv
# Install all dependencies listed in pyproject.toml
RUN uv pip install --system \
    chainlit \
    chromadb \
    presidio-analyzer \
    presidio-anonymizer \
    spacy \
    openai \
    sqlalchemy \
    aiosqlite \
    asyncpg \
    langchain \
    langchain-classic \
    langchain-community \
    langchain-openai \
    langchain-text-splitters \
    tiktoken

# Download spaCy model for Presidio
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Expose Chainlit port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=8000
ENV PIP_ROOT_USER_ACTION=ignore

# Run Chainlit application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]

