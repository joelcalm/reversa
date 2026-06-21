#!/bin/sh
# Render / production entrypoint: download the SQLite DB once, then start uvicorn.
# Local docker-compose: mount ./data and set BOE_DB_PATH — download is skipped if the file exists.
set -e

DB_PATH="${BOE_DB_PATH:-/tmp/boe_graph.db}"
DB_URL="${BOE_DB_URL:-https://github.com/joelcalm/reversa/releases/download/db-v1/boe_graph.db}"
PORT="${PORT:-8000}"

if [ "${BOE_DB_SKIP_DOWNLOAD}" = "1" ]; then
  echo "BOE_DB_SKIP_DOWNLOAD=1 — using existing database at ${DB_PATH}"
elif [ -f "$DB_PATH" ]; then
  echo "Database already present at ${DB_PATH} ($(du -h "$DB_PATH" | cut -f1))"
else
  echo "Downloading database from ${DB_URL} ..."
  mkdir -p "$(dirname "$DB_PATH")"
  curl -fsSL "$DB_URL" -o "$DB_PATH"
  echo "Downloaded $(du -h "$DB_PATH" | cut -f1) to ${DB_PATH}"
  export BOE_SKIP_INIT_DB=1
fi

export BOE_DB_PATH="$DB_PATH"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
