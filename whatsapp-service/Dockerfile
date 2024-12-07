FROM python:3.10-slim as production

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add the project root to PYTHONPATH
ENV PYTHONPATH=/app

# Use production server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]