# Multi-stage build for PsyWiz Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash psywiz

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app/ app/
COPY run.py .
COPY .env.example .env

# Create necessary directories
RUN mkdir -p model_cache/embeddings vector_db logs && \
    chown -R psywiz:psywiz /app

# Switch to non-root user
USER psywiz

# Pre-download embedding model (optional - can be done at runtime)
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='./model_cache/embeddings')"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]

# Production stage (multi-stage optimization)
FROM base as production

# Copy only production requirements
COPY requirements.txt .
RUN pip install --no-dev -r requirements.txt

# Optimize for production
ENV LOG_LEVEL=INFO
ENV DEBUG=false

# Use production command with multiple workers
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]