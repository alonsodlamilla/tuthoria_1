FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Add the project root to PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "langchainService.py"]