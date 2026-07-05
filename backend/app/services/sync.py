"""Sync service: pull from the active provider and upsert into SQLite."""
from __future__ import annotations

import datetime as dt
import logging
import threading

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import DailyMetric, Workout
from ..providers import get_provider
from ..providers.base import DailyMetricData, WorkoutData

log = logging.getLogger(__name__)

# Serialize syncs so concurrent calls (e.g. React StrictMode double-invoke or a
# user clicking Sync mid-sync) can't race on inserts.
_sync_lock = threading.Lock()

_DAILY_FIELDS = (
    "hrv_rmssd",
    "resting_hr",
    "sleeping_hr",
    "respiratory_rate",
    "spo2",
    "skin_temp_dev",
    "vo2max",
    "sleep_minutes",
    "sleep_efficiency",
    "deep_minutes",
    "rem_minutes",
    "light_minutes",
    "awake_minutes",
    "sleep_latency_min",
    "awakenings",
    "sleep_onset_min",
    "sleep_score",
    "steps",
    "distance_km",
    "active_energy_kcal",
    "azm",
)


def _upsert_daily(db: Session, data: DailyMetricData) -> bool:
    row = db.scalar(select(DailyMetric).where(DailyMetric.date == data.date))
    created = False
    if row is None:
        row = DailyMetric(date=data.date)
        db.add(row)
        created = True
    for field in _DAILY_FIELDS:
        value = getattr(data, field)
        if value is not None:  # don't clobber existing values on partial fetches
            setattr(row, field, value)
    if data.hr_zone_minutes is not None:
        zm = (list(data.hr_zone_minutes) + [0.0] * 5)[:5]
        row.hr_z1_min, row.hr_z2_min, row.hr_z3_min, row.hr_z4_min, row.hr_z5_min = zm
    if data.intraday_zones is not None:
        import json
        row.intraday_zones = json.dumps(data.intraday_zones)
    if data.sleep_stages is not None:
        import json
        row.sleep_stages = json.dumps(data.sleep_stages)
    row.source = data.source
    return created


def _upsert_workout(db: Session, w: WorkoutData) -> bool:
    row = None
    if w.external_id:
        row = db.scalar(select(Workout).where(Workout.external_id == w.external_id))
    if row is None:
        row = db.scalar(
            select(Workout).where(Workout.date == w.date, Workout.type == w.type)
        )
    created = False
    if row is None:
        row = Workout(date=w.date, type=w.type)
        db.add(row)
        created = True
    row.external_id = w.external_id
    row.start = w.start
    row.duration_min = w.duration_min
    row.distance_km = w.distance_km
    row.avg_hr = w.avg_hr
    row.max_hr = w.max_hr
    row.rpe = w.rpe
    zm = (list(w.zone_minutes) + [0.0] * 5)[:5]
    row.z1_min, row.z2_min, row.z3_min, row.z4_min, row.z5_min = zm
    row.source = w.source
    return created


def run_sync(db: Session, lookback_days: int | None = None) -> dict:
    provider = get_provider()
    if not provider.is_authenticated():
        raise PermissionError(
            "Provider is not authenticated. For Google Health, open /auth/login. "
            "Or set USE_MOCK_PROVIDER=true to use sample data."
        )

    days = lookback_days or settings.sync_lookback_days
    end = dt.date.today()
    start = end - dt.timedelta(days=days)

    with _sync_lock:
        metrics = provider.fetch_daily_metrics(start, end)
        daily_created = sum(1 for m in metrics if _upsert_daily(db, m))

        workouts = provider.fetch_workouts(start, end)
        wk_created = sum(1 for w in workouts if _upsert_workout(db, w))

        db.commit()
    return {
        "provider": provider.name,
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "daily": {"fetched": len(metrics), "created": daily_created},
        "workouts": {"fetched": len(workouts), "created": wk_created},
        "synced_at": dt.datetime.utcnow().isoformat() + "Z",
    }
