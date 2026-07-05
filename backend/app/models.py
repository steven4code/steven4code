"""SQLAlchemy ORM models."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class OAuthToken(Base):
    """Stores the OAuth tokens for a provider. Single-user app: one row per
    provider, refreshed in place."""

    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DailyMetric(Base):
    """One row per calendar day with the raw daily metrics we pull from the
    health provider. Derived scores (recovery, sleep score) are computed in the
    service layer so the formula can change without re-syncing."""

    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, unique=True, index=True)

    # Recovery inputs (nocturnal where possible)
    hrv_rmssd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resting_hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleeping_hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    respiratory_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spo2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Nightly skin temperature deviation from personal baseline (deg C).
    skin_temp_dev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Fitness
    vo2max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Sleep (minutes per stage + summary)
    sleep_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep_efficiency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deep_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rem_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    light_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    awake_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep_latency_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    awakenings: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Minutes after local midnight that sleep began (for consistency/timing).
    sleep_onset_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Native sleep score from the provider, if available (else computed).
    sleep_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Activity & all-day load
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_energy_kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    azm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # All-day time in each of the 5 HR zones (minutes).
    hr_z1_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr_z2_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr_z3_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr_z4_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hr_z5_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # JSON: 24 hourly buckets of [z1..z5] minutes (for the intraday strain curve).
    intraday_zones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON: ordered hypnogram segments [{"stage": "deep|light|rem|awake", "min": float}].
    sleep_stages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Workout(Base):
    """A single training session (run, padel, ride, ...). Zone minutes are the
    time spent in each of the 5 HR zones as reported/derived for the session."""

    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    start: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    type: Mapped[str] = mapped_column(String(24))  # run | padel | ride | other
    duration_min: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_hr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Session RPE (0-10), optional manual input; captures anaerobic load.
    rpe: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    z1_min: Mapped[float] = mapped_column(Float, default=0.0)
    z2_min: Mapped[float] = mapped_column(Float, default=0.0)
    z3_min: Mapped[float] = mapped_column(Float, default=0.0)
    z4_min: Mapped[float] = mapped_column(Float, default=0.0)
    z5_min: Mapped[float] = mapped_column(Float, default=0.0)

    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class UserProfile(Base):
    """Single-row user profile / settings (id == 1)."""

    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    max_hr: Mapped[int] = mapped_column(Integer, default=194)
    # Lactate-threshold HR (~LT2). If null, bootstrapped from max_hr.
    lthr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # "threshold" (LTHR-anchored) or "karvonen" (%HRR).
    zone_method: Mapped[str] = mapped_column(String(12), default="threshold")
    # If set, overrides the resting HR derived from daily data.
    resting_hr_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # "auto" estimates sleep need from behaviour + load; "manual" uses the value.
    sleep_need_mode: Mapped[str] = mapped_column(String(8), default="auto")
    sleep_need_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    training_goal: Mapped[str] = mapped_column(String(24), default="run_5_10k")
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
