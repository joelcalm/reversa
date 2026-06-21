# BOE Knowledge Graph — developer workflow
# All Python commands run inside backend/.venv. Frontend uses npm in frontend/.

BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
BACKEND_PORT ?= 8088
FRONTEND_PORT ?= 5173
BACKEND_URL ?= http://127.0.0.1:$(BACKEND_PORT)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Create venv, install backend + frontend deps
	@command -v uv >/dev/null 2>&1 && uv venv $(VENV) --python 3.9 || python3 -m venv $(VENV)
	@command -v uv >/dev/null 2>&1 && uv pip install --python $(PY) -e "$(BACKEND_DIR)[dev]" || $(PIP) install -e "$(BACKEND_DIR)[dev]"
	cd $(FRONTEND_DIR) && npm install

.PHONY: ingest-sample
ingest-sample: ## Ingest a small demo sample (live API, fixture fallback)
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.ingest sample

.PHONY: ingest-sample-offline
ingest-sample-offline: ## Ingest the bundled fixtures only (no network)
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.ingest sample --no-api

.PHONY: ingest-full
ingest-full: ## Ingest the full corpus via pagination (~12k+ norms; cached/resumable)
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.ingest full

.PHONY: ingest-missing
ingest-missing: ## Ingest only norms not yet in the DB (after a capped 10k run)
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.ingest missing

.PHONY: compute
compute: ## Recompute briefings from the existing SQLite database
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.compute_briefings --scope state

.PHONY: export-sample
export-sample: ## Refresh bundled sample fixtures from the live API
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m scripts.export_sample

.PHONY: backend
backend: ## Run the FastAPI backend (http://127.0.0.1:$(BACKEND_PORT))
	cd $(BACKEND_DIR) && $(abspath $(UVICORN)) app.main:app --reload --host 127.0.0.1 --port $(BACKEND_PORT)

.PHONY: frontend
frontend: ## Run the Vite dev server (http://127.0.0.1:$(FRONTEND_PORT))
	cd $(FRONTEND_DIR) && BACKEND_URL=$(BACKEND_URL) npm run dev

.PHONY: dev
dev: ## Run backend and frontend together
	@echo "Starting backend on :$(BACKEND_PORT) and frontend on :$(FRONTEND_PORT)…"
	cd $(BACKEND_DIR) && $(abspath $(UVICORN)) app.main:app --host 127.0.0.1 --port $(BACKEND_PORT) & \
	cd $(FRONTEND_DIR) && BACKEND_URL=$(BACKEND_URL) npm run dev; \
	kill %1 2>/dev/null || true

.PHONY: test
test: ## Run backend tests
	cd $(BACKEND_DIR) && $(abspath $(PY)) -m pytest

.PHONY: lint
lint: ## Lint backend (ruff) and type-check frontend (tsc)
	cd $(BACKEND_DIR) && $(abspath $(VENV))/bin/ruff check app scripts tests
	cd $(FRONTEND_DIR) && npm run lint

.PHONY: build-frontend
build-frontend: ## Production build of the frontend
	cd $(FRONTEND_DIR) && npm run build

.PHONY: clean
clean: ## Remove generated DB, WAL/SHM sidecars, and API cache
	rm -f data/processed/*.db data/processed/*.db-wal data/processed/*.db-shm
	rm -f data/processed/*.sqlite data/processed/*.sqlite3
	rm -f data/processed/data_quality_report.json
	rm -rf data/cache/boe/*
