"""Assemble dashboard + detail payloads from stored data."""
from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DailyMetric, Workout
from . import cardio as cardio_svc
from . import recovery as rec_svc
from . import sleep as sleep_svc
from . import strain as strain_svc
from .profile import effective_lthr, effective_resting_hr, get_profile, zone_bounds


def _load(db: Session):
    rows = list(db.scalars(select(DailyMetric).order_by(DailyMetric.date.asc())))
    workouts = list(db.scalars(select(Workout).order_by(Workout.date.asc())))
    return rows, workouts


def _parse_stages(raw):
    if not raw:
        return None
    try:
        segs = json.loads(raw)
        return segs if isinstance(segs, list) and segs else None
    except (ValueError, TypeError):
        return None


def _trend(values):
    nn = [v for v in values if v is not None]
    if not nn:
        return {"latest": None, "delta": None}
    latest = nn[-1]
    prev = nn[-2] if len(nn) > 1 else None
    return {"latest": latest, "delta": round(latest - prev, 1) if prev is not None else None}


def _compute_series(rows, workouts, profile):
    manual = profile.sleep_need_minutes if profile.sleep_need_mode == "manual" else None
    load_by_date: dict[dt.date, float] = {}
    for w in workouts:
        load_by_date[w.date] = load_by_date.get(w.date, 0.0) + cardio_svc.edwards_load(w)

    need_by_date: dict[dt.date, float] = {}
    sleep_series: list[float | None] = []
    sleep_breakdowns = []

    for idx, r in enumerate(rows):
        recent_dur = [x.sleep_minutes for x in rows[max(0, idx - 13): idx + 1] if x.sleep_minutes]
        load7 = sum(load_by_date.get(r.date - dt.timedelta(days=k), 0.0) for k in range(7))
        load_bonus = min(45.0, load7 / 25.0)
        need = sleep_svc.estimate_need(recent_dur, load_bonus, manual)
        need_by_date[r.date] = need

        sri = sleep_svc.compute_sri(rows[max(0, idx - sleep_svc.SRI_WINDOW_DAYS + 1): idx + 1])
        score, comps = sleep_svc.score_day(r, need, sri)
        sleep_series.append(score)
        sleep_breakdowns.append({"need": round(need), "score": score, "sri": sri, "components": comps})

    recovery_series = [rec_svc.compute_recovery(rows, sleep_series, i) for i in range(len(rows))]
    recovery_by_date = {rows[i].date: recovery_series[i].score for i in range(len(rows))}

    return {
        "sleep_series": sleep_series,
        "sleep_breakdowns": sleep_breakdowns,
        "need_by_date": need_by_date,
        "recovery_series": recovery_series,
        "recovery_by_date": recovery_by_date,
    }


def build_dashboard(db: Session, days: int = 30) -> dict:
    rows, workouts = _load(db)
    if not rows:
        return {"empty": True}
    profile = get_profile(db)
    resting_hr = effective_resting_hr(profile, rows)
    s = _compute_series(rows, workouts, profile)

    daily = [
        {
            "date": rows[i].date.isoformat(),
            "recovery_score": s["recovery_series"][i].score,
            "sleep_score": s["sleep_series"][i],
            "vo2max": rows[i].vo2max,
        }
        for i in range(len(rows))
    ]
    window = daily[-days:]
    last = rows[-1]
    rb = s["recovery_series"][-1]
    sb = s["sleep_breakdowns"][-1]

    recovery_card = {
        "score": rb.score,
        "label": rec_svc.label(rb.score),
        "status": rb.status,
        "flags": rb.flags,
        "components": {"hrv": rb.hrv_sub, "hr": rb.hr_sub, "sleep": rb.sleep_sub},
        "core": rb.core,
        "sleep_factor": rb.sleep_factor,
        "hrv_rmssd": rb.hrv_value,
        "rolling7_rmssd": rb.rolling7_rmssd,
        "cv7": rb.cv7,
        "within_normal": rb.within_normal,
        "hr": rb.hr_value,
        "hrv_baseline": rb.hrv_baseline,
        "hr_baseline": rb.hr_baseline,
        "trend": _trend([d["recovery_score"] for d in daily]),
        "series": [{"date": d["date"], "recovery_score": d["recovery_score"]} for d in window],
    }

    sleep_card = {
        "score": sb["score"],
        "sri": sb["sri"],
        "need_min": sb["need"],
        "minutes": last.sleep_minutes,
        "efficiency": last.sleep_efficiency,
        "deep_minutes": last.deep_minutes,
        "rem_minutes": last.rem_minutes,
        "light_minutes": last.light_minutes,
        "awake_minutes": last.awake_minutes,
        "debt_min": sleep_svc.sleep_debt(rows, s["need_by_date"]),
        "stages": _parse_stages(last.sleep_stages),
        "trend": _trend([d["sleep_score"] for d in daily]),
        "series": [{"date": d["date"], "sleep_score": d["sleep_score"]} for d in window],
    }

    cardio = cardio_svc.build_cardio(workouts, rows, profile, resting_hr, s["recovery_by_date"])
    strain = strain_svc.build_strain(
        rows, workouts, rb.score, sb["score"], cardio.get("load_ratio"),
        series_days=days, cardio_systems=cardio.get("systems"), recovery_status=rb.status,
    )

    # Sleep-stage targets, tailored to recent training load (more load -> more SWS).
    recent_strain = [p["strain"] for p in strain.get("series", [])[-3:]] if not strain.get("empty") else []
    load_factor = (sum(recent_strain) / len(recent_strain) / 100.0) if recent_strain else 0.0
    sleep_card["stage_targets"] = sleep_svc.stage_targets(sb["need"], load_factor)

    win = rows[-days:]

    def _ext(key, title, unit, attr, decimals=0, good_up=True, goal=None, insight=None):
        series = [{"date": r.date.isoformat(), "v": getattr(r, attr)} for r in win]
        vals = [x["v"] for x in series if x["v"] is not None]
        latest = vals[-1] if vals else None
        prev = vals[-2] if len(vals) > 1 else None
        delta = round(latest - prev, 1) if (latest is not None and prev is not None) else None
        return {
            "key": key, "title": title, "unit": unit, "value": latest,
            "decimals": decimals, "delta": delta, "good_up": good_up, "goal": goal,
            "series": series,
            "insight": (insight(latest, delta) if (insight and latest is not None) else ""),
        }

    extras = [
        _ext("vo2max", "VO₂max", "ml/kg/min", "vo2max", 1, True,
             insight=lambda v, d: f"Cardio-Fitness-Schätzung: {v} ml/kg/min."),
        _ext("resting_hr", "Ruhepuls", "bpm", "resting_hr", 0, False,
             insight=lambda v, d: "Niedriger ist besser – guter Erholungsmarker."),
        _ext("hrv", "HFV (RMSSD)", "ms", "hrv_rmssd", 0, True,
             insight=lambda v, d: "Höhere HFV = besser erholt."),
        _ext("steps", "Schritte", "", "steps", 0, True, goal=10000,
             insight=lambda v, d: f"{int(v):,} Schritte heute.".replace(",", ".")),
        _ext("calories", "Aktive Energie", "kcal", "active_energy_kcal", 0, True,
             insight=lambda v, d: f"{int(v)} kcal aktiv verbrannt."),
        _ext("azm", "Active Zone Min.", "min", "azm", 0, True,
             insight=lambda v, d: f"{int(v)} Minuten in höheren HF-Zonen."),
    ]

    return {
        "empty": False,
        "as_of": last.date.isoformat(),
        "recovery": recovery_card,
        "strain": strain,
        "sleep": sleep_card,
        "cardio": cardio,
        "extras": extras,
        "vo2max": next((r.vo2max for r in reversed(rows) if r.vo2max is not None), None),
    }


def build_strain_detail(db: Session, days: int = 60) -> dict:
    rows, workouts = _load(db)
    if not rows:
        return {"empty": True}
    profile = get_profile(db)
    s = _compute_series(rows, workouts, profile)
    rb = s["recovery_series"][-1]
    sb = s["sleep_breakdowns"][-1]
    resting_hr = effective_resting_hr(profile, rows)
    cardio = cardio_svc.build_cardio(workouts, rows, profile, resting_hr, s["recovery_by_date"])
    out = strain_svc.build_strain(
        rows, workouts, rb.score, sb["score"], cardio.get("load_ratio"), series_days=days,
        cardio_systems=cardio.get("systems"), recovery_status=rb.status,
    )
    out["recovery"] = rb.score
    out["sleep_score"] = sb["score"]
    out["load_ratio"] = cardio.get("load_ratio")
    return out


# --------------------------------------------------------------------------- #
# Detail views
# --------------------------------------------------------------------------- #
def build_recovery_detail(db: Session, days: int = 60) -> dict:
    rows, workouts = _load(db)
    if not rows:
        return {"empty": True}
    profile = get_profile(db)
    s = _compute_series(rows, workouts, profile)
    base = max(0, len(rows) - days)
    series = []
    for i in range(base, len(rows)):
        rb = s["recovery_series"][i]
        series.append({
            "date": rows[i].date.isoformat(),
            "recovery_score": rb.score,
            "hrv_sub": rb.hrv_sub,
            "hr_sub": rb.hr_sub,
            "sleep_sub": rb.sleep_sub,
            "rmssd": rb.hrv_value,
            "rolling7_rmssd": rb.rolling7_rmssd,
            "cv7": rb.cv7,
            "hr": rb.hr_value,
            "flags": rb.flags,
        })
    last = s["recovery_series"][-1]
    return {
        "empty": False,
        "core_weights": rec_svc.CORE_WEIGHTS,
        "baseline_days": rec_svc.BASELINE_WINDOW_DAYS,
        "method": "Autonomer Kern (lnRMSSD-dominant + HF) vs 60-Tage-Baseline ±SWC, × Schlaf-Modifikator (0,70–1,00); 7-Tage-Trend & CV; Temp/Atmung/SpO₂ als Anomalie-Flags",
        "latest": {
            "score": last.score, "core": last.core, "sleep_factor": last.sleep_factor,
            "hrv_sub": last.hrv_sub, "hr_sub": last.hr_sub,
            "sleep_sub": last.sleep_sub, "ln_rmssd": last.ln_rmssd,
            "ln_baseline": last.ln_baseline, "swc": last.swc,
            "within_normal": last.within_normal, "cv7": last.cv7, "flags": last.flags,
        },
        "series": series,
    }


def build_sleep_detail(db: Session, days: int = 60) -> dict:
    rows, workouts = _load(db)
    if not rows:
        return {"empty": True}
    profile = get_profile(db)
    s = _compute_series(rows, workouts, profile)
    base = max(0, len(rows) - days)
    series = []
    for i in range(base, len(rows)):
        r = rows[i]
        bd = s["sleep_breakdowns"][i]
        series.append({
            "date": r.date.isoformat(),
            "sleep_score": bd["score"],
            "sri": bd["sri"],
            "need_min": bd["need"],
            "minutes": r.sleep_minutes,
            "deep_minutes": r.deep_minutes,
            "rem_minutes": r.rem_minutes,
            "light_minutes": r.light_minutes,
            "awake_minutes": r.awake_minutes,
            "efficiency": r.sleep_efficiency,
            "latency_min": r.sleep_latency_min,
            "awakenings": r.awakenings,
        })
    last = s["sleep_breakdowns"][-1]
    return {
        "empty": False,
        "weights": sleep_svc.WEIGHTS,
        "latest_components": last["components"],
        "latest_sri": last["sri"],
        "latest_need": last["need"],
        "debt_min": sleep_svc.sleep_debt(rows, s["need_by_date"]),
        "series": series,
    }


def build_cardio_detail(db: Session) -> dict:
    rows, workouts = _load(db)
    if not rows:
        return {"empty": True}
    profile = get_profile(db)
    resting_hr = effective_resting_hr(profile, rows)
    s = _compute_series(rows, workouts, profile)
    cardio = cardio_svc.build_cardio(workouts, rows, profile, resting_hr, s["recovery_by_date"])
    cardio["zones"] = zone_bounds(profile, resting_hr)
    cardio["resting_hr"] = resting_hr
    cardio["max_hr"] = profile.max_hr
    cardio["lthr"] = effective_lthr(profile)
    cardio["zone_method"] = profile.zone_method
    return cardio
