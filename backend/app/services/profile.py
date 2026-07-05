"""User profile / settings helpers and HR-zone math."""
from __future__ import annotations

import statistics

from sqlalchemy.orm import Session

from ..models import DailyMetric, UserProfile

ZONE_NAMES = ["Z1 Recovery", "Z2 Aerob", "Z3 Tempo", "Z4 Schwelle", "Z5 VO2max"]

# Threshold-anchored running zones as fraction of LTHR (~LT2), Friel-style.
LTHR_BOUNDS = [0.0, 0.85, 0.90, 0.95, 1.02, 10.0]
# Karvonen fallback as fraction of HR reserve.
HRR_BOUNDS = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]


def get_profile(db: Session) -> UserProfile:
    prof = db.get(UserProfile, 1)
    if prof is None:
        prof = UserProfile(id=1)
        db.add(prof)
        db.commit()
        db.refresh(prof)
    return prof


def update_profile(db: Session, data: dict) -> UserProfile:
    prof = get_profile(db)
    for key in (
        "max_hr",
        "lthr",
        "zone_method",
        "resting_hr_override",
        "sleep_need_mode",
        "sleep_need_minutes",
        "training_goal",
    ):
        if key in data and data[key] is not None:
            setattr(prof, key, data[key])
    db.commit()
    db.refresh(prof)
    return prof


def effective_resting_hr(prof: UserProfile, rows: list[DailyMetric]) -> float:
    if prof.resting_hr_override:
        return float(prof.resting_hr_override)
    vals = [r.resting_hr for r in rows[-30:] if r.resting_hr is not None]
    return round(statistics.median(vals), 1) if vals else 55.0


def effective_lthr(prof: UserProfile) -> int:
    """LTHR if set, else bootstrapped from max HR (~90%)."""
    return int(prof.lthr) if prof.lthr else round(0.90 * prof.max_hr)


def zone_bounds(prof: UserProfile, resting_hr: float) -> list[dict]:
    max_hr = prof.max_hr
    if prof.zone_method == "threshold":
        lthr = effective_lthr(prof)
        zones = []
        for i in range(5):
            lo = LTHR_BOUNDS[i] * lthr if i > 0 else 0.5 * lthr
            hi = LTHR_BOUNDS[i + 1] * lthr if i < 4 else max_hr
            zones.append(
                {
                    "zone": i + 1,
                    "name": ZONE_NAMES[i],
                    "hr_low": round(lo),
                    "hr_high": round(hi),
                    "basis": f"{int(LTHR_BOUNDS[i]*100) if i>0 else 50}–"
                    f"{int(LTHR_BOUNDS[i+1]*100) if i<4 else '+'}% LTHR",
                }
            )
        return zones

    # Karvonen
    hrr = max(1.0, max_hr - resting_hr)
    zones = []
    for i in range(5):
        lo = resting_hr + HRR_BOUNDS[i] * hrr
        hi = resting_hr + HRR_BOUNDS[i + 1] * hrr
        zones.append(
            {
                "zone": i + 1,
                "name": ZONE_NAMES[i],
                "hr_low": round(lo),
                "hr_high": round(hi),
                "basis": f"{int(HRR_BOUNDS[i]*100)}–{int(HRR_BOUNDS[i+1]*100)}% HFR",
            }
        )
    return zones
