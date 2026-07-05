"""Metrics / dashboard read routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import dashboard as dash

router = APIRouter(tags=["metrics"])


@router.get("/dashboard")
def dashboard(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    return dash.build_dashboard(db, days)


@router.get("/detail/recovery")
def recovery_detail(
    days: int = Query(default=60, ge=7, le=365), db: Session = Depends(get_db)
) -> dict:
    return dash.build_recovery_detail(db, days)


@router.get("/detail/sleep")
def sleep_detail(
    days: int = Query(default=60, ge=7, le=365), db: Session = Depends(get_db)
) -> dict:
    return dash.build_sleep_detail(db, days)


@router.get("/detail/cardio")
def cardio_detail(db: Session = Depends(get_db)) -> dict:
    return dash.build_cardio_detail(db)


@router.get("/detail/strain")
def strain_detail(
    days: int = Query(default=60, ge=7, le=365), db: Session = Depends(get_db)
) -> dict:
    return dash.build_strain_detail(db, days)
