FROM python:3.11-slim

# curl: download boe_graph.db from GitHub release on first start (Render).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir -e .

COPY scripts ./scripts

RUN chmod +x scripts/render-start.sh

# Render: DB downloaded to /tmp on startup. docker-compose: override with a volume mount.
ENV BOE_DB_PATH=/tmp/boe_graph.db
ENV BOE_DB_URL=https://github.com/joelcalm/reversa/releases/download/db-v1/boe_graph.db

EXPOSE 8000

CMD ["scripts/render-start.sh"]
