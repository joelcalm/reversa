FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY app ./app
COPY scripts ./scripts

ENV BOE_DB_PATH=/data/processed/boe_graph.db
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
