#!/bin/bash
# Install spaCy model from cached wheel if available, otherwise download
set -e

MODEL_NAME="en_core_web_sm"
CACHE_DIR="/tmp/spacy-models"

# Check if cached wheel exists
if ls ${CACHE_DIR}/en_core_web_sm*.whl 1> /dev/null 2>&1; then
    echo "Installing spaCy model from cached wheel..."
    pip install --no-cache-dir ${CACHE_DIR}/en_core_web_sm*.whl
    python -m spacy link en_core_web_sm en_core_web_sm --force || true
else
    echo "Downloading spaCy model (cache not found)..."
    python -m spacy download en_core_web_sm
fi

