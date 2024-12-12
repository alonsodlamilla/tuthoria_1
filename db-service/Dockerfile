FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p logs

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM builder as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
ENV PYTHONPATH=/app

# Initialize database and start service with reload
CMD python scripts/db_init.py && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Production stage
FROM builder as production
COPY . .
ENV PYTHONPATH=/app

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Initialize database and start service with gunicorn and IPv6 support
CMD ["sh", "-c", "python scripts/db_init.py && gunicorn app:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind [::]:8000"]