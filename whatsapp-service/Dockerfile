FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM builder as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
ENV PYTHONPATH=/app
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8501} --reload"]

FROM builder as production
COPY . .
ENV PYTHONPATH=/app
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-8501} --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --log-level info --access-logfile - --error-logfile -"]