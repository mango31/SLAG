# syntax=docker/dockerfile:1.4
FROM --platform=linux/amd64 python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies with apt key fix
RUN apt-get update && \
    apt-get install -y gnupg2 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0E98404D386FA1D9 && \
    apt-get install -y \
    gcc \
    g++ \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and setup files
COPY requirements.txt setup.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Create __init__.py files
RUN touch src/__init__.py \
    src/api/__init__.py \
    src/core/__init__.py

# Install local package
RUN pip install -e .

# Production stage
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install production dependencies - minimal set
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/src /app/src
COPY --from=builder /app/setup.py /app/setup.py

# Install uvicorn directly in production stage
RUN pip install uvicorn==0.24.0

# Install local package in production stage
RUN pip install -e .

# Create necessary directories with proper permissions
RUN mkdir -p /app/output/stories /app/output/frameworks /app/logs && \
    chmod -R 777 /app/output /app/logs && \
    chown -R nobody:nogroup /app/output /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER nobody

# Run the API service (no reload in production)
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "900"] 