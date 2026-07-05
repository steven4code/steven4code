"""Sleep need, sleep score and Sleep Regularity Index (SRI).

Gold-standard refinement: sleep *regularity* is a stronger predictor of health
outcomes than duration, so the SRI is the heaviest-weighted component and a
headline metric. Need is capped at 8h; cumulative debt is secondary.

SRI (Phillips et al.): probability that sleep/wake state is the same at two time
points 24h apart, scaled so 0.5 -> 0 and 1.0 -> 100.
"""
from __future__ import annotations

# Component weights (sum 1.0). Regularity (SRI) dominates.
WEIGHTS = {
    "regularity": 0.30,
    "duration": 0.22,
    "efficiency": 0.12,
    "deep": 0.10,
    "rem": 0.10,
    "restfulness": 0.10,
    "latency": 0.06,
}

DEBT_WINDOW_DAYS = 14
SRI_WINDOW_DAYS = 14
NEED_FLOOR_MIN = 420  # 7h
NEED_CEIL_MIN = 480   # 8h cap (gold-standard choice: regularity > duration debt)
EPOCH_MIN = 30


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def estimate_need(recent_durations, load_bonus_min=0.0, manual_minutes=None):
    if manual_minutes:
        return float(manual_minutes)
    if not recent_durations:
        return 480.0
    base = _percentile(recent_durations, 0.90)
    return _clamp(base + load_bonus_min, NEED_FLOOR_MIN, NEED_CEIL_MIN)


# --- Sleep Regularity Index ------------------------------------------------- #
def _asleep(row, clock_min) -> bool | None:
    if row.sleep_onset_min is None or not row.sleep_minutes:
        return None
    start = (21 * 60 + row.sleep_onset_min) % 1440
    end = (start + row.sleep_minutes) % 1440
    if start <= end:
        return start <= clock_min < end
    return clock_min >= start or clock_min < end


def compute_sri(window_rows) -> float | None:
    usable = [r for r in window_rows if r.sleep_onset_min is not None and r.sleep_minutes]
    if len(usable) < 2:
        return None
    matches = total = 0
    for a, b in zip(usable, usable[1:]):
        for c in range(0, 1440, EPOCH_MIN):
            sa, sb = _asleep(a, c), _asleep(b, c)
            if sa is None or sb is None:
                continue
            matches += 1 if sa == sb else 0
            total += 1
    if total == 0:
        return None
    frac = matches / total
    return round(_clamp((2 * frac - 1) * 100, 0, 100), 1)


# --- Component scores ------------------------------------------------------- #
def _score_duration(minutes, need):
    if not minutes:
        return None
    ratio = minutes / need
    score = _clamp((ratio - 0.5) / 0.5, 0, 1) * 100
    if ratio > 1.15:
        score -= min(15, (ratio - 1.15) * 100)
    return _clamp(score, 0, 100)


def _score_efficiency(eff):
    if eff is None:
        return None
    return _clamp((eff - 60) / 25, 0, 1) * 100


def _score_range(value, total, lo_frac, hi_frac):
    if not value or not total:
        return None
    frac = value / total
    if lo_frac <= frac <= hi_frac:
        return 100.0
    if frac < lo_frac:
        return _clamp(frac / lo_frac, 0, 1) * 100
    return _clamp(1 - (frac - hi_frac) / hi_frac, 0, 1) * 100


def _score_latency(lat):
    if lat is None:
        return None
    return 100.0 if lat <= 20 else _clamp(1 - (lat - 20) / 55, 0, 1) * 100


def _score_restfulness(awakenings, awake_min, total):
    if total is None:
        return None
    pen = (awakenings or 0) * 6 + (awake_min or 0) / total * 100
    return _clamp(100 - pen, 0, 100)


def score_day(row, need, sri):
    total = row.sleep_minutes
    comps = {
        "regularity": sri,
        "duration": _score_duration(total, need),
        "efficiency": _score_efficiency(row.sleep_efficiency),
        "deep": _score_range(row.deep_minutes, total, 0.13, 0.23),
        "rem": _score_range(row.rem_minutes, total, 0.20, 0.25),
        "restfulness": _score_restfulness(row.awakenings, row.awake_minutes, total),
        "latency": _score_latency(row.sleep_latency_min),
    }
    present = {k: v for k, v in comps.items() if v is not None}
    if not present:
        return None, comps
    wsum = sum(WEIGHTS[k] for k in present)
    score = sum(present[k] * WEIGHTS[k] for k in present) / wsum
    return round(score, 1), comps


def stage_targets(need_min, load_factor=0.0):
    """Per-stage target ranges (minutes), tailored to recent training load.

    Evidence base:
    - Deep / SWS ~13-23% of sleep and rises with physical training load
      (slow-wave rebound after exercise: Driver & Taylor 2000; Shapiro 1981).
      So the deep band shifts UP with recent load (load_factor 0..1).
    - REM ~20-25% (relatively stable, duration-sensitive).
    - Light (N1+N2) ~45-57% (the remainder).
    - WASO/Wach kept low (<~8% of the night).
    """
    lf = _clamp(load_factor, 0.0, 1.0)
    deep_lo = 0.13 + 0.03 * lf
    deep_hi = 0.20 + 0.04 * lf
    return {
        "need_min": round(need_min),
        "load_factor": round(lf, 2),
        "deep": {"lo": round(need_min * deep_lo), "hi": round(need_min * deep_hi)},
        "rem": {"lo": round(need_min * 0.20), "hi": round(need_min * 0.25)},
        "light": {"lo": round(need_min * 0.45), "hi": round(need_min * 0.57)},
        "awake": {"hi": round(need_min * 0.08)},
    }


def sleep_debt(rows, need_by_date) -> float:
    debt = 0.0
    for r in rows[-DEBT_WINDOW_DAYS:]:
        if r.sleep_minutes is None:
            continue
        need = need_by_date.get(r.date, 480.0)
        debt += max(0.0, need - r.sleep_minutes)
    return round(debt, 0)
