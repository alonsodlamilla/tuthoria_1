# Build stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Only installs production requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM builder as development

# Installs additional development requirements
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Add the project root to PYTHONPATH
ENV PYTHONPATH=/app

# Use development server with reload
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8502", "--reload"]

# Production stage
FROM python:3.10-slim as production

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copies only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Add the project root to PYTHONPATH
ENV PYTHONPATH=/app

# Use production server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8502"]