"""Provider abstraction: anything that can return daily health metrics and
training sessions."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class DailyMetricData:
    """Normalized daily metrics returned by a provider for a single day.

    All fields are optional because a given day may be missing some signals
    (e.g. no sleep recorded, or HRV not measured)."""

    date: dt.date
    hrv_rmssd: float | None = None
    resting_hr: float | None = None
    sleeping_hr: float | None = None
    respiratory_rate: float | None = None
    spo2: float | None = None
    skin_temp_dev: float | None = None
    vo2max: float | None = None
    sleep_minutes: float | None = None
    sleep_efficiency: float | None = None
    deep_minutes: float | None = None
    rem_minutes: float | None = None
    light_minutes: float | None = None
    awake_minutes: float | None = None
    sleep_latency_min: float | None = None
    awakenings: int | None = None
    sleep_onset_min: float | None = None  # minutes after midnight sleep began
    sleep_score: float | None = None
    # Activity & all-day load
    steps: int | None = None
    distance_km: float | None = None
    active_energy_kcal: float | None = None
    azm: int | None = None
    hr_zone_minutes: list[float] | None = None        # all-day [z1..z5] minutes
    intraday_zones: list[list[float]] | None = None    # 24 x [z1..z5] minutes
    sleep_stages: list | None = None                   # ordered [{stage,min}] hypnogram
    source: str = "unknown"


@dataclass
class WorkoutData:
    """A single training session with per-zone time (minutes)."""

    date: dt.date
    type: str  # run | padel | ride | other
    duration_min: float
    external_id: str | None = None
    start: dt.datetime | None = None
    distance_km: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    rpe: float | None = None
    zone_minutes: list[float] = field(default_factory=lambda: [0.0] * 5)  # z1..z5
    source: str = "unknown"


class HealthProvider(Protocol):
    """A source of daily health metrics and workouts."""

    name: str

    def is_authenticated(self) -> bool: ...

    def fetch_daily_metrics(
        self, start: dt.date, end: dt.date
    ) -> list[DailyMetricData]: ...

    def fetch_workouts(self, start: dt.date, end: dt.date) -> list[WorkoutData]: ...
