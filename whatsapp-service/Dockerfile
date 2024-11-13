FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV PORT=8501

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]