"""Sync route: trigger a pull from the provider."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.sync import run_sync

router = APIRouter(tags=["sync"])


@router.post("/sync")
def sync(lookback_days: Optional[int] = None, db: Session = Depends(get_db)) -> dict:
    try:
        return run_sync(db, lookback_days)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Sync failed: {exc}") from exc
