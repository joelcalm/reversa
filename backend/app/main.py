"""FastAPI application entrypoint for the BOE Knowledge Graph backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router as api_router
from app.db.session import init_db

app = FastAPI(
    title="BOE Knowledge Graph API",
    version=__version__,
    description=(
        "Mapping Spain's consolidated legislation as a graph of amendments, "
        "repeals and citations."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    # Ensure the schema exists even if ingestion has not run yet.
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "boe-knowledge-graph", "version": __version__}


app.include_router(api_router, prefix="/api")
