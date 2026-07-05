"""FastAPI application entry point.

Liefert zusätzlich das gebaute Frontend (frontend/dist) aus, wenn es
existiert — dann läuft die komplette App als EIN Prozess unter
http://localhost:8000 (Grundlage der Doppelklick-Starter). Im Dev-Betrieb
(Vite auf :5173) ändert sich nichts.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db
from .routers import auth, metrics, profile, sync

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="JarvisHealth", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Das Frontend ruft alles unter /api/... auf. Vite-Dev-Proxy und nginx
# strippen das Präfix; wenn das Backend direkt angesprochen wird (Ein-
# Prozess-Betrieb), übernimmt diese Middleware dasselbe.
@app.middleware("http")
async def strip_api_prefix(request, call_next):
    path = request.scope.get("path", "")
    if path.startswith("/api/"):
        request.scope["path"] = path[4:]
    return await call_next(request)


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


# Gebautes Frontend als Catch-all mounten (nach den API-Routen).
_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="spa")
