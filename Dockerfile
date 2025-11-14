# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install Python dependencies using uv
# Install all dependencies listed in pyproject.toml
RUN uv pip install --system \
    chainlit \
    llama-index \
    llama-index-llms-openai \
    llama-index-llms-anthropic \
    llama-index-embeddings-openai \
    llama-index-embeddings-anthropic \
    chromadb \
    presidio-analyzer \
    presidio-anonymizer \
    spacy \
    openai \
    anthropic \
    sqlalchemy \
    aiosqlite \
    langchain \
    langchain-community \
    langchain-openai \
    langchain-anthropic \
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

# Run Chainlit application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]

