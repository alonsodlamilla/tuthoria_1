FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only the whatsapp-service files
COPY . .

# Add the project root to PYTHONPATH
ENV PYTHONPATH=/app

CMD gunicorn --bind "0.0.0.0:$PORT" app:app