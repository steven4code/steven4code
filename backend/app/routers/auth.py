"""OAuth login/callback routes for the Google Health API."""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from ..config import settings
from ..providers.google_health import (
    build_authorization_url,
    exchange_code_for_tokens,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory CSRF state store (single-user local app).
_pending_states: set[str] = set()


@router.get("/status")
def auth_status() -> dict:
    from ..providers import get_provider

    provider = get_provider()
    return {
        "provider": provider.name,
        "mock_mode": settings.use_mock_provider,
        "authenticated": provider.is_authenticated(),
    }


@router.get("/login")
def login():
    if settings.use_mock_provider:
        raise HTTPException(
            status_code=400,
            detail="App is in mock mode (USE_MOCK_PROVIDER=true); no login needed.",
        )
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are not configured.",
        )
    state = secrets.token_urlsafe(24)
    _pending_states.add(state)
    return RedirectResponse(build_authorization_url(state))


@router.get("/callback")
def callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    error: Optional[str] = Query(default=None),
):
    if error:
        return HTMLResponse(f"<h3>Login fehlgeschlagen: {error}</h3>", status_code=400)
    if not code or not state or state not in _pending_states:
        return HTMLResponse("<h3>Ungültiger OAuth-Callback.</h3>", status_code=400)
    _pending_states.discard(state)
    try:
        exchange_code_for_tokens(code)
    except Exception as exc:  # noqa: BLE001
        return HTMLResponse(
            f"<h3>Token-Austausch fehlgeschlagen:</h3><pre>{exc}</pre>",
            status_code=500,
        )
    # Bounce back to the frontend.
    return RedirectResponse(f"{settings.frontend_origin}/?connected=1")
