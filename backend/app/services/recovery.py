"""Recovery score — autonomic core × sleep modifier (gold-standard-aligned).

Rationale (see literature review): there is no validated fixed weighting for a
composite recovery score, and naively adding correlated signals (HRV, HR, sleep)
double-counts the same overnight state. So we:

  1. Build an AUTONOMIC CORE from HRV (dominant) and resting/sleeping HR
     (a minor confirmer, since it is largely redundant with HRV). Both are
     judged against a personal 60-day baseline via lnRMSSD / z-scores.
  2. Apply SLEEP as a MODIFIER (multiplicative factor 0.70–1.00), not an additive
     term — a poor night caps your readiness instead of being averaged in.
  3. Surface a 7-day rolling lnRMSSD mean + coefficient of variation (CV) as the
     trend/early-warning context (reactive daily value + stable trend = hybrid).
  4. Skin-temp / respiratory-rate / SpO2 anomalies cap the score (illness/strain).

HRV index: lnRMSSD (Plews et al. 2013). Baseline ± SWC (0.5·SD) for meaningful
change (Buchheit 2014). RMSSD daily / weekly mean / weekly CV per the 2025
Sensors review.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

BASELINE_WINDOW_DAYS = 60
MIN_BASELINE_DAYS = 14
ROLLING_DAYS = 7
SCORE_SLOPE = 20.0
SWC_FACTOR = 0.5

# Autonomic core: HRV dominant, HR a minor confirmer (largely redundant w/ HRV).
CORE_WEIGHTS = {"hrv": 0.80, "hr": 0.20}
# Sleep modifier: factor 1.0 at/above SLEEP_ANCHOR, down to SLEEP_MOD_MIN at 0.
SLEEP_MOD_MIN = 0.70
SLEEP_ANCHOR = 85.0

# Anomaly thresholds
TEMP_ABS_FLAG = 0.6
RESP_SD_FLAG = 2.0
SPO2_ABS_FLAG = 92.0
ANOMALY_CAP = 50.0


@dataclass
class RecoveryBreakdown:
    score: float | None
    core: float | None = None
    sleep_factor: float | None = None
    hrv_sub: float | None = None
    hr_sub: float | None = None
    sleep_sub: float | None = None
    hrv_z: float | None = None
    hr_z: float | None = None
    ln_rmssd: float | None = None
    ln_baseline: float | None = None
    swc: float | None = None
    within_normal: bool | None = None
    rolling7_rmssd: float | None = None
    cv7: float | None = None
    hrv_value: float | None = None
    hr_value: float | None = None
    hrv_baseline: float | None = None
    hr_baseline: float | None = None
    flags: list[str] = field(default_factory=list)
    status: str = "ok"


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _stats(sample):
    if len(sample) < 2:
        return (sample[0] if sample else None), None
    return statistics.fmean(sample), statistics.pstdev(sample)


def _sleep_factor(sleep_sub):
    if sleep_sub is None:
        return 1.0  # no sleep data -> no modifier
    return _clamp(SLEEP_MOD_MIN + (1 - SLEEP_MOD_MIN) * (sleep_sub / SLEEP_ANCHOR),
                  SLEEP_MOD_MIN, 1.0)


def compute_recovery(rows, sleep_series, idx) -> RecoveryBreakdown:
    lo = max(0, idx - BASELINE_WINDOW_DAYS)
    base_rows = rows[lo:idx]
    today = rows[idx]

    # ---- HRV (lnRMSSD vs 60-day baseline) --------------------------------- #
    ln_today = math.log(today.hrv_rmssd) if today.hrv_rmssd else None
    ln_base = [math.log(r.hrv_rmssd) for r in base_rows if r.hrv_rmssd]
    hrv_sub = hrv_z = ln_mean = swc = within = None
    if ln_today is not None and len(ln_base) >= MIN_BASELINE_DAYS:
        ln_mean, ln_sd = _stats(ln_base)
        swc = SWC_FACTOR * ln_sd if ln_sd else 0.0
        if ln_sd:
            hrv_z = (ln_today - ln_mean) / ln_sd
            hrv_sub = _clamp(50 + SCORE_SLOPE * hrv_z, 0, 100)
            within = abs(ln_today - ln_mean) <= swc

    recent = [r.hrv_rmssd for r in rows[max(0, idx - ROLLING_DAYS + 1): idx + 1] if r.hrv_rmssd]
    rolling7 = round(statistics.fmean(recent), 1) if recent else None
    cv7 = (round(statistics.pstdev(recent) / statistics.fmean(recent) * 100, 1)
           if len(recent) >= 3 and statistics.fmean(recent) > 0 else None)

    # ---- (sleeping) resting HR -------------------------------------------- #
    hr_val = today.sleeping_hr if today.sleeping_hr is not None else today.resting_hr
    hr_base = [(r.sleeping_hr if r.sleeping_hr is not None else r.resting_hr) for r in base_rows]
    hr_base = [v for v in hr_base if v is not None]
    hr_sub = hr_z = hr_mean = None
    if hr_val is not None and len(hr_base) >= MIN_BASELINE_DAYS:
        hr_mean, hr_sd = _stats(hr_base)
        if hr_sd:
            hr_z = (hr_val - hr_mean) / hr_sd
            hr_sub = _clamp(50 - SCORE_SLOPE * hr_z, 0, 100)  # lower HR = better

    # ---- autonomic core (HRV dominant + HR confirmer) --------------------- #
    parts = []
    if hrv_sub is not None:
        parts.append(("hrv", hrv_sub))
    if hr_sub is not None:
        parts.append(("hr", hr_sub))
    core = None
    if parts:
        wsum = sum(CORE_WEIGHTS[k] for k, _ in parts)
        core = sum(v * CORE_WEIGHTS[k] for k, v in parts) / wsum

    # ---- sleep modifier ---------------------------------------------------- #
    sleep_sub = sleep_series[idx]
    factor = _sleep_factor(sleep_sub)

    if core is None:
        score, status = None, "insufficient_data"
    else:
        score = core * factor
        status = "ok"

    flags = _anomaly_flags(today, base_rows)
    if flags and score is not None:
        score = min(score, ANOMALY_CAP)
        status = "anomaly"

    return RecoveryBreakdown(
        score=round(score, 1) if score is not None else None,
        core=round(core, 1) if core is not None else None,
        sleep_factor=round(factor, 2),
        hrv_sub=round(hrv_sub, 1) if hrv_sub is not None else None,
        hr_sub=round(hr_sub, 1) if hr_sub is not None else None,
        sleep_sub=round(sleep_sub, 1) if sleep_sub is not None else None,
        hrv_z=round(hrv_z, 2) if hrv_z is not None else None,
        hr_z=round(hr_z, 2) if hr_z is not None else None,
        ln_rmssd=round(ln_today, 3) if ln_today is not None else None,
        ln_baseline=round(ln_mean, 3) if ln_mean is not None else None,
        swc=round(swc, 3) if swc is not None else None,
        within_normal=within,
        rolling7_rmssd=rolling7,
        cv7=cv7,
        hrv_value=today.hrv_rmssd,
        hr_value=hr_val,
        hrv_baseline=round(math.exp(ln_mean), 1) if ln_mean is not None else None,
        hr_baseline=round(hr_mean, 1) if hr_mean is not None else None,
        flags=flags,
        status=status,
    )


def _anomaly_flags(today, base_rows) -> list[str]:
    flags = []
    if today.skin_temp_dev is not None and abs(today.skin_temp_dev) >= TEMP_ABS_FLAG:
        flags.append(f"Hauttemperatur {today.skin_temp_dev:+.1f}°C abweichend")
    if today.respiratory_rate is not None:
        rr_base = [r.respiratory_rate for r in base_rows if r.respiratory_rate]
        if len(rr_base) >= MIN_BASELINE_DAYS:
            m, sd = _stats(rr_base)
            if sd and today.respiratory_rate > m + RESP_SD_FLAG * sd:
                flags.append(f"Atemfrequenz erhöht ({today.respiratory_rate:.1f}/min)")
    if today.spo2 is not None and today.spo2 < SPO2_ABS_FLAG:
        flags.append(f"SpO₂ niedrig ({today.spo2:.0f}%)")
    return flags


def label(score: float | None) -> str:
    if score is None:
        return "Noch keine Baseline"
    if score >= 66:
        return "Gut erholt"
    if score >= 40:
        return "Moderat"
    return "Belastet"
