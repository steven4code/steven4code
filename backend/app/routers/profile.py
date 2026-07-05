"""User profile / settings routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.dashboard import _load
from ..services.profile import (
    effective_lthr,
    effective_resting_hr,
    get_profile,
    update_profile,
    zone_bounds,
)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileIn(BaseModel):
    max_hr: Optional[int] = None
    lthr: Optional[int] = None
    zone_method: Optional[str] = None
    resting_hr_override: Optional[int] = None
    sleep_need_mode: Optional[str] = None
    sleep_need_minutes: Optional[int] = None
    training_goal: Optional[str] = None


def _serialize(db: Session) -> dict:
    prof = get_profile(db)
    rows, _ = _load(db)
    resting = effective_resting_hr(prof, rows)
    return {
        "max_hr": prof.max_hr,
        "lthr": prof.lthr,
        "lthr_effective": effective_lthr(prof),
        "zone_method": prof.zone_method,
        "resting_hr_override": prof.resting_hr_override,
        "resting_hr_effective": resting,
        "sleep_need_mode": prof.sleep_need_mode,
        "sleep_need_minutes": prof.sleep_need_minutes,
        "training_goal": prof.training_goal,
        "zones": zone_bounds(prof, resting),
    }


@router.get("")
def read_profile(db: Session = Depends(get_db)) -> dict:
    return _serialize(db)


@router.put("")
def write_profile(payload: ProfileIn, db: Session = Depends(get_db)) -> dict:
    update_profile(db, payload.model_dump(exclude_none=True))
    return _serialize(db)
