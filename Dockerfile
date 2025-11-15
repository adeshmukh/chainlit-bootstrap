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
# Install everything declared in pyproject.toml to stay in sync automatically
RUN uv pip install --system .

# Install spaCy model: use cached wheel if available, otherwise download
# Copy installation script and cached model wheel directory (if it exists)
# Directory is ensured to exist by Makefile build target
COPY scripts/install-spacy-model.sh /tmp/install-spacy-model.sh
# Copy directory contents - will copy nothing if directory is empty or doesn't exist
# Using COPY with directory path - works even if empty (in BuildKit) or use wildcard pattern
COPY .local/cache/spacy-models/ /tmp/spacy-models/
RUN chmod +x /tmp/install-spacy-model.sh && \
    /tmp/install-spacy-model.sh

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

