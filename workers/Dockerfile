FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
    src/worker/__init__.py \
    src/core/__init__.py \
    src/core/services/__init__.py \
    src/core/models/__init__.py

# Install local package
RUN pip install -e .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs && \
    chmod -R 777 /app/logs && \
    chown -R nobody:nogroup /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER nobody

# Run the worker service
CMD ["python", "-m", "src.worker.run_worker"] 