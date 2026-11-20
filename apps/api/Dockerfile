# FastAPI backend for Cloud Run (build context: apps/api)
#   gcloud run deploy chyron-api --source apps/api --region asia-south1
# Local:  docker build -t chyron-api apps/api && docker run -p 8080:8080 chyron-api
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN useradd -m appuser
WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8080

# Cloud Run injects $PORT
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
