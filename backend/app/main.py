"""FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routers import auth, metrics, profile, sync

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Fitbit Recovery Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(metrics.router)
app.include_router(profile.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "mock_mode": settings.use_mock_provider}
