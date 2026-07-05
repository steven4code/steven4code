"""Google Health API provider (OAuth 2.0 + REST), built against the official v4
discovery document (health:v4, rev 2026-06-25).

Reads use the `dataPoints.list` method:
  GET v4/users/me/dataTypes/{data-type}/dataPoints?filter=...&pageSize=...
The time window is expressed via an AIP-160 `filter`, NOT startTime/endTime.

Data types (kebab-case) and the fields we read:
  daily-heart-rate-variability        -> dailyHeartRateVariability.averageHeartRateVariabilityMilliseconds
  daily-resting-heart-rate            -> dailyRestingHeartRate.beatsPerMinute
  daily-vo2-max                       -> dailyVo2Max.vo2Max
  daily-oxygen-saturation             -> dailyOxygenSaturation.averagePercentage
  daily-respiratory-rate              -> dailyRespiratoryRate.breathsPerMinute
  daily-sleep-temperature-derivations -> nightly - baseline (deg C)
  sleep                               -> sleep.summary + stagesSummary
  exercise                            -> exercise.metricsSummary (avg HR, distance, HR-zone durations)
"""
from __future__ import annotations

import datetime as dt
import logging
import re

import httpx
from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal
from ..models import OAuthToken
from .base import DailyMetricData, WorkoutData

log = logging.getLogger(__name__)

PROVIDER_NAME = "google_health"

# Data type path name + the filter field used to bound by time.
DAILY_TYPES = {
    "hrv": "daily-heart-rate-variability",
    "resting_hr": "daily-resting-heart-rate",
    "vo2max": "daily-vo2-max",
    "spo2": "daily-oxygen-saturation",
    "respiratory": "daily-respiratory-rate",
    "skin_temp": "daily-sleep-temperature-derivations",
}


# --------------------------------------------------------------------------- #
# OAuth helpers
# --------------------------------------------------------------------------- #
def build_authorization_url(state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.scopes_list),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{settings.oauth_auth_url}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> None:
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = httpx.post(settings.oauth_token_url, data=data, timeout=30)
    resp.raise_for_status()
    _store_token(resp.json())


def _store_token(payload: dict) -> None:
    expires_in = payload.get("expires_in")
    expires_at = (
        dt.datetime.utcnow() + dt.timedelta(seconds=int(expires_in))
        if expires_in
        else None
    )
    with SessionLocal() as db:
        token = db.scalar(select(OAuthToken).where(OAuthToken.provider == PROVIDER_NAME))
        if token is None:
            token = OAuthToken(provider=PROVIDER_NAME)
            db.add(token)
        token.access_token = payload["access_token"]
        if payload.get("refresh_token"):
            token.refresh_token = payload["refresh_token"]
        token.expires_at = expires_at
        token.scope = payload.get("scope")
        db.commit()


# --------------------------------------------------------------------------- #
# Provider
# --------------------------------------------------------------------------- #
class GoogleHealthProvider:
    name = PROVIDER_NAME

    def is_authenticated(self) -> bool:
        with SessionLocal() as db:
            token = db.scalar(select(OAuthToken).where(OAuthToken.provider == PROVIDER_NAME))
            return token is not None and bool(token.access_token)

    def _valid_access_token(self) -> str:
        with SessionLocal() as db:
            token = db.scalar(select(OAuthToken).where(OAuthToken.provider == PROVIDER_NAME))
            if token is None:
                raise RuntimeError("Not authenticated with Google Health. Visit /auth/login.")
            needs_refresh = (
                token.expires_at is not None
                and token.expires_at <= dt.datetime.utcnow() + dt.timedelta(seconds=60)
            )
            if needs_refresh and token.refresh_token:
                self._refresh(token.refresh_token)
                token = db.scalar(select(OAuthToken).where(OAuthToken.provider == PROVIDER_NAME))
            return token.access_token

    def _refresh(self, refresh_token: str) -> None:
        data = {
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        }
        resp = httpx.post(settings.oauth_token_url, data=data, timeout=30)
        resp.raise_for_status()
        _store_token(resp.json())

    # -- REST: list with filter + pagination -------------------------------- #
    def _list(self, data_type: str, filter_str: str, page_size: int = 1000) -> list[dict]:
        url = f"{settings.health_api_base}/users/me/dataTypes/{data_type}/dataPoints"
        headers = {"Authorization": f"Bearer {self._valid_access_token()}"}
        out: list[dict] = []
        page_token = None
        for _ in range(40):  # safety cap
            params = {"filter": filter_str, "pageSize": page_size}
            if page_token:
                params["pageToken"] = page_token
            resp = httpx.get(url, headers=headers, params=params, timeout=60)
            if resp.status_code >= 400:
                log.warning("Google Health %s -> %s: %s", data_type, resp.status_code, resp.text[:400])
                resp.raise_for_status()
            body = resp.json()
            out.extend(body.get("dataPoints", []))
            page_token = body.get("nextPageToken")
            if not page_token:
                break
        return out

    def fetch_daily_metrics(self, start: dt.date, end: dt.date) -> list[DailyMetricData]:
        by_date: dict[dt.date, DailyMetricData] = {}

        def slot(day: dt.date) -> DailyMetricData:
            if day not in by_date:
                by_date[day] = DailyMetricData(date=day, source=self.name)
            return by_date[day]

        lo = start.isoformat()
        hi = (end + dt.timedelta(days=1)).isoformat()  # filter uses `<`

        # Daily summary data types: filter on `<type-snake>.date`.
        daily_specs = [
            ("hrv", "dailyHeartRateVariability", _apply_hrv),
            ("resting_hr", "dailyRestingHeartRate", _apply_resting),
            ("vo2max", "dailyVo2Max", _apply_vo2max),
            ("spo2", "dailyOxygenSaturation", _apply_spo2),
            ("respiratory", "dailyRespiratoryRate", _apply_resp),
            ("skin_temp", "dailySleepTemperatureDerivations", _apply_skin),
        ]
        for key, field, applier in daily_specs:
            dtype = DAILY_TYPES[key]
            snake = dtype.replace("-", "_")
            flt = f'{snake}.date >= "{lo}" AND {snake}.date < "{hi}"'
            try:
                points = self._list(dtype, flt, page_size=1000)
                for p in points:
                    applier(p.get(field), slot)
            except Exception as exc:  # noqa: BLE001
                log.warning("Google Health fetch failed for %s: %s", dtype, exc)

        # Sleep sessions: filter on sleep.interval.end_time (RFC-3339).
        flt = (
            f'sleep.interval.end_time >= "{lo}T00:00:00Z" AND '
            f'sleep.interval.end_time < "{hi}T00:00:00Z"'
        )
        try:
            for p in self._list("sleep", flt, page_size=25):
                _apply_sleep(p.get("sleep"), slot)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google Health fetch failed for sleep: %s", exc)

        # Activity interval types: sum per day.
        self._sum_interval("steps", "steps", "count", lo, hi, slot, "steps", as_int=True)
        self._sum_interval("distance", "distance", "millimeters", lo, hi, slot, "distance_km", scale=1e-6)
        self._sum_interval("active-energy-burned", "activeEnergyBurned", "kcal", lo, hi, slot, "active_energy_kcal")
        self._sum_interval("active-zone-minutes", "activeZoneMinutes", "activeZoneMinutes", lo, hi, slot, "azm", as_int=True)

        # All-day time-in-zone -> per-day [z1..z5] minutes.
        self._all_day_zones(lo, hi, slot)

        # Intraday HR for today -> hourly [z1..z5] minutes (for the live curve).
        try:
            self._intraday_today(end, by_date, slot)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google Health intraday HR failed: %s", exc)

        return [by_date[d] for d in sorted(by_date)]

    # -- additional fetchers ------------------------------------------------ #
    def _sum_interval(self, dtype, field, value_key, lo, hi, slot, attr, scale=1.0, as_int=False):
        snake = dtype.replace("-", "_")
        flt = f'{snake}.interval.civil_start_time >= "{lo}" AND {snake}.interval.civil_start_time < "{hi}"'
        try:
            points = self._list(dtype, flt, page_size=2000)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google Health fetch failed for %s: %s", dtype, exc)
            return
        acc: dict[dt.date, float] = {}
        for p in points:
            obj = p.get(field) or {}
            day = _interval_day(obj.get("interval"))
            val = _f(obj.get(value_key))
            if day is not None and val is not None:
                acc[day] = acc.get(day, 0.0) + val
        for day, total in acc.items():
            total *= scale
            setattr(slot(day), attr, int(round(total)) if as_int else round(total, 2))

    def _all_day_zones(self, lo, hi, slot):
        flt = (
            f'time_in_heart_rate_zone.interval.civil_start_time >= "{lo}" AND '
            f'time_in_heart_rate_zone.interval.civil_start_time < "{hi}"'
        )
        try:
            points = self._list("time-in-heart-rate-zone", flt, page_size=2000)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google Health fetch failed for time-in-heart-rate-zone: %s", exc)
            return
        zmap = {"LIGHT": 1, "MODERATE": 2, "VIGOROUS": 3, "PEAK": 4}  # -> z2..z5
        acc: dict[dt.date, list[float]] = {}
        for p in points:
            obj = p.get("timeInHeartRateZone") or {}
            interval = obj.get("interval") or {}
            day = _interval_day(interval)
            mins = _interval_minutes(interval)
            zi = zmap.get(obj.get("heartRateZoneType"))
            if day is not None and mins and zi is not None:
                acc.setdefault(day, [0.0] * 5)[zi] += mins
        for day, zones in acc.items():
            slot(day).hr_zone_minutes = [round(x, 1) for x in zones]

    def _intraday_today(self, day, by_date, slot):
        from ..services.profile import get_profile, zone_bounds

        with SessionLocal() as db:
            prof = get_profile(db)
            resting = float(prof.resting_hr_override) if prof.resting_hr_override else 55.0
            zones = zone_bounds(prof, resting)
        bounds = [(z["hr_low"], z["hr_high"]) for z in zones]
        nxt = (day + dt.timedelta(days=1)).isoformat()
        flt = (
            f'heart_rate.sample_time.physical_time >= "{day.isoformat()}T00:00:00Z" AND '
            f'heart_rate.sample_time.physical_time < "{nxt}T00:00:00Z"'
        )
        points = self._list("heart-rate", flt, page_size=1000)
        buckets = [[0.0] * 5 for _ in range(24)]
        for p in points:
            hr = p.get("heartRate") or {}
            bpm = _f(hr.get("beatsPerMinute"))
            st = hr.get("sampleTime") or {}
            civ = (st.get("civilTime") or {}).get("time") or {}
            hour = int(civ["hours"]) if "hours" in civ else None
            if hour is None:
                d = _rfc_dt(st.get("physicalTime"))
                hour = d.hour if d else None
            if bpm is None or hour is None or not (0 <= hour < 24):
                continue
            zi = _zone_index(bpm, bounds)
            if zi < 0:  # resting / sub-Z1 -> contributes no load
                continue
            buckets[hour][zi] += 1.0  # ~1 sample/minute
        slot(day).intraday_zones = [[round(x, 1) for x in b] for b in buckets]

    def fetch_workouts(self, start: dt.date, end: dt.date) -> list[WorkoutData]:
        lo = start.isoformat()
        hi = (end + dt.timedelta(days=1)).isoformat()
        flt = (
            f'exercise.interval.civil_start_time >= "{lo}" AND '
            f'exercise.interval.civil_start_time < "{hi}"'
        )
        out: list[WorkoutData] = []
        try:
            for p in self._list("exercise", flt, page_size=25):
                w = _parse_exercise(p.get("exercise"), self.name)
                if w is not None:
                    out.append(w)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google Health fetch failed for exercise: %s", exc)
        return out


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def _f(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _interval_day(interval: dict | None) -> dt.date | None:
    if not interval:
        return None
    civ = (interval.get("civilStartTime") or {}).get("date")
    day = _date_obj(civ)
    if day is not None:
        return day
    d = _rfc_dt(interval.get("startTime"))
    return d.date() if d else None


def _interval_minutes(interval: dict | None) -> float | None:
    if not interval:
        return None
    a = _rfc_dt(interval.get("startTime"))
    b = _rfc_dt(interval.get("endTime"))
    if a and b:
        return max(0.0, (b - a).total_seconds() / 60.0)
    return None


def _zone_index(bpm: float, bounds: list) -> int:
    """Map a heart rate to a zone index 0..4 (Z1..Z5).

    Returns -1 for heart rates *below* the Z1 lower bound (resting / sedentary),
    so that resting time contributes NO cardiovascular load. This is the fix for
    the old "strain maxes out in the morning" bug, where every sedentary minute
    was being counted as Zone 1.
    """
    if not bounds:
        return -1
    if bpm < bounds[0][0]:  # below Z1 lower bound -> resting, not a training zone
        return -1
    for i, (lo, hi) in enumerate(bounds):
        if bpm < hi:
            return i
    return len(bounds) - 1  # at/above the top bound -> top zone


def _date_obj(d: dict | None) -> dt.date | None:
    if not d:
        return None
    try:
        return dt.date(int(d["year"]), int(d["month"]), int(d["day"]))
    except (KeyError, ValueError, TypeError):
        return None


def _rfc_dt(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    m = re.match(r"^(.*\.\d{1,6})\d*([+-]\d{2}:\d{2})?$", s)  # trim >6 frac digits
    if m:
        s = m.group(1) + (m.group(2) or "")
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        try:
            return dt.datetime.fromisoformat(s[:19])
        except ValueError:
            return None


def _dur_min(v) -> float | None:
    """google-duration like '3600s' -> minutes."""
    if v is None:
        return None
    try:
        if isinstance(v, str) and v.endswith("s"):
            return float(v[:-1]) / 60.0
        return float(v) / 60.0
    except (TypeError, ValueError):
        return None


# -- daily appliers (value = the inner object, e.g. dailyHeartRateVariability)
def _apply_hrv(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is None:
        return
    rmssd = v.get("averageHeartRateVariabilityMilliseconds") or v.get(
        "deepSleepRootMeanSquareOfSuccessiveDifferencesMilliseconds"
    )
    if rmssd is not None:
        slot(day).hrv_rmssd = _f(rmssd)


def _apply_resting(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is not None and v.get("beatsPerMinute") is not None:
        slot(day).resting_hr = _f(v["beatsPerMinute"])


def _apply_vo2max(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is not None and v.get("vo2Max") is not None:
        slot(day).vo2max = _f(v["vo2Max"])


def _apply_spo2(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is not None and v.get("averagePercentage") is not None:
        slot(day).spo2 = _f(v["averagePercentage"])


def _apply_resp(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is not None and v.get("breathsPerMinute") is not None:
        slot(day).respiratory_rate = _f(v["breathsPerMinute"])


def _apply_skin(v, slot):
    day = _date_obj((v or {}).get("date"))
    if day is None:
        return
    nightly = _f(v.get("nightlyTemperatureCelsius"))
    baseline = _f(v.get("baselineTemperatureCelsius"))
    if nightly is not None and baseline is not None:
        slot(day).skin_temp_dev = round(nightly - baseline, 2)


_STAGE_FIELD = {"DEEP": "deep_minutes", "REM": "rem_minutes", "LIGHT": "light_minutes"}
_HYP_STAGE = {
    "DEEP": "deep", "REM": "rem", "LIGHT": "light",
    "AWAKE": "awake", "WAKE": "awake", "RESTLESS": "awake", "ASLEEP": "light",
}


def _parse_hypnogram(s):
    """Build an ordered hypnogram from a provider stage-segment list, if present."""
    raw = s.get("stages") or s.get("sleepStages") or s.get("levels")
    if not isinstance(raw, list):
        return None
    out = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        stage = _HYP_STAGE.get((it.get("type") or it.get("stage") or it.get("level") or "").upper())
        mins = _f(it.get("minutes"))
        if mins is None:
            mins = _dur_min(it.get("duration"))
        if mins is None:
            mins = _interval_minutes(it.get("interval"))
        if stage and mins and mins > 0:
            out.append({"stage": stage, "min": round(mins, 1)})
    return out or None


def _apply_sleep(s, slot):
    if not s:
        return
    interval = s.get("interval", {})
    end = interval.get("endTime")
    day = None
    civ_end = interval.get("civilEndTime")
    if civ_end and civ_end.get("date"):
        day = _date_obj(civ_end["date"])
    if day is None and end:
        day = (_rfc_dt(end) or dt.datetime.min).date()
    if day is None:
        return

    summary = s.get("summary", {}) or {}
    in_period = _f(summary.get("minutesInSleepPeriod"))
    asleep = _f(summary.get("minutesAsleep"))
    awake = _f(summary.get("minutesAwake"))

    cur = slot(day)
    # If multiple sleeps for a day, keep the longest (main sleep).
    if cur.sleep_minutes and asleep and asleep <= cur.sleep_minutes:
        return

    cur.sleep_minutes = asleep
    cur.awake_minutes = awake
    if asleep and in_period:
        cur.sleep_efficiency = round(asleep / in_period * 100, 1)
    cur.sleep_latency_min = _f(summary.get("minutesToFallAsleep"))
    cur.deep_minutes = cur.rem_minutes = cur.light_minutes = None
    for st in summary.get("stagesSummary", []) or []:
        field = _STAGE_FIELD.get(st.get("type"))
        if field:
            setattr(cur, field, _f(st.get("minutes")))

    # Optional per-stage hypnogram (when the provider returns stage segments).
    segs = _parse_hypnogram(s)
    if segs:
        cur.sleep_stages = segs

    civ_start = interval.get("civilStartTime", {})
    t = (civ_start or {}).get("time") or {}
    if t:
        h = int(t.get("hours", 0))
        m = int(t.get("minutes", 0))
        cur.sleep_onset_min = float(((h - 21) % 24) * 60 + m)


def _norm_exercise_type(etype: str) -> str:
    s = (etype or "").lower()
    if "padel" in s:
        return "padel"
    if "run" in s or "jog" in s or "treadmill" in s:
        return "run"
    if "bik" in s or "cycl" in s or "spinning" in s:
        return "ride"
    return "other"


def _parse_exercise(e, source: str) -> WorkoutData | None:
    if not e:
        return None
    interval = e.get("interval", {})
    start_dt = _rfc_dt(interval.get("startTime"))
    civ = (interval.get("civilStartTime") or {}).get("date")
    day = _date_obj(civ) or (start_dt.date() if start_dt else None)
    if day is None:
        return None

    duration = _dur_min(e.get("activeDuration"))
    if duration is None and start_dt:
        end_dt = _rfc_dt(interval.get("endTime"))
        if end_dt:
            duration = (end_dt - start_dt).total_seconds() / 60.0

    ms = e.get("metricsSummary", {}) or {}
    zones = ms.get("heartRateZoneDurations", {}) or {}
    # Google exercise zones (light/moderate/vigorous/peak) -> our z2..z5.
    z = [
        0.0,
        _dur_min(zones.get("lightTime")) or 0.0,
        _dur_min(zones.get("moderateTime")) or 0.0,
        _dur_min(zones.get("vigorousTime")) or 0.0,
        _dur_min(zones.get("peakTime")) or 0.0,
    ]
    dist_mm = _f(ms.get("distanceMillimeters"))

    return WorkoutData(
        date=day,
        type=_norm_exercise_type(e.get("exerciseType", "")),
        duration_min=round(duration or sum(z) or 0.0, 1),
        start=start_dt,
        distance_km=round(dist_mm / 1_000_000, 2) if dist_mm else None,
        avg_hr=_f(ms.get("averageHeartRateBeatsPerMinute")),
        max_hr=None,
        zone_minutes=[round(x, 1) for x in z],
        source=source,
    )
