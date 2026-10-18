FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal for fast cold starts
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root (see DEPLOYMENT.md / cloudbuild), so paths
# are relative to the repo root, not this backend/ folder.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY data ./data

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

