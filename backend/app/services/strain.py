"""Daily strain (cardiovascular load) — 0-100, gold-standard rebuild.

Load metric: Banister TRIMP (the physiologically grounded internal-load standard)
— duration weighted by heart-rate reserve (HRr) with an EXPONENTIAL intensity
factor. Crucially, at rest HRr ~ 0, so resting/sedentary time contributes ~0
strain (this fixes the previous "21 in the morning" bug, where resting minutes
were counted as zone 1).

Scale: personalized logarithmic mapping
    strain = 100 * (1 - exp(-TRIMP / tau))
with tau derived from the user's own 60-day load distribution (their ~90th
percentile day maps to ~85), so strain is relative to personal fitness (like
WHOOP), bounded 0-100, and progressively harder to increase near the top.

Inputs:
- Daily: time in each of the 5 HR zones (all-day, real `time-in-heart-rate-zone`
  or, as fallback, the day's workouts). Per-zone TRIMP/min uses the zone's
  representative HRr midpoint.
- Today's live curve: per-hour zone-minutes from the intraday minute-HR stream.

Refs: Banister TRIMP & Edwards zone-TRIMP (interchangeable, r~0.89); WHOOP strain
methodology (personalized HR zones, logarithmic).
"""
from __future__ import annotations

import datetime as dt
import json
import math

STRAIN_MAX = 100.0
# Banister intensity factor f(HRr) = HRr * a * e^(b*HRr) (male coefficients).
_A, _B = 0.64, 1.92
# Representative heart-rate-reserve midpoint per zone (Z1..Z5).
ZONE_HRR_MID = [0.45, 0.55, 0.65, 0.78, 0.92]
ZONE_TRIMP_MIN = [hrr * _A * math.exp(_B * hrr) for hrr in ZONE_HRR_MID]

BASELINE_DAYS = 60
TRIMP_REF_FLOOR = 120.0       # min personal reference (new users)
TARGET_PCT = 0.85             # 90th-percentile day -> ~85 strain
WAKE_HOUR, SLEEP_HOUR = 6, 23


def _zone_trimp(z) -> float:
    return sum((z[i] or 0) * ZONE_TRIMP_MIN[i] for i in range(5))


def _workout_zone_trimp(w) -> float:
    return _zone_trimp([w.z1_min, w.z2_min, w.z3_min, w.z4_min, w.z5_min])


def _all_day_zones(row):
    z = [row.hr_z1_min, row.hr_z2_min, row.hr_z3_min, row.hr_z4_min, row.hr_z5_min]
    return z if any(v is not None for v in z) else None


def _day_trimp(row, workouts_today) -> float:
    z = _all_day_zones(row)
    if z is not None:
        return _zone_trimp(z)
    return sum(_workout_zone_trimp(w) for w in workouts_today)


def _percentile(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _personal_tau(daily_trimps) -> float:
    vals = [t for t in daily_trimps if t > 0]
    ref = max(TRIMP_REF_FLOOR, _percentile(vals, 0.90)) if vals else TRIMP_REF_FLOOR
    return ref / (-math.log(1 - TARGET_PCT))  # ref / 1.897


def trimp_to_strain(t, tau):
    return STRAIN_MAX * (1 - math.exp(-max(0.0, t) / tau))


def strain_to_trimp(s, tau):
    s = min(s, STRAIN_MAX - 0.5)
    return -tau * math.log(1 - s / STRAIN_MAX)


def _target_range(recovery, sleep_score, load_ratio):
    rec = recovery if recovery is not None else 50
    opt = 35 + (rec / 100) * 45  # rec 0 -> 35, rec 100 -> 80
    if sleep_score is not None:
        opt += (sleep_score - 70) / 100 * 8
    low, high = opt - 12, opt + 10
    if load_ratio is not None:
        if load_ratio > 1.3:
            high -= 10
        elif load_ratio < 0.8:
            high += 6
    low = max(0.0, min(STRAIN_MAX, low))
    high = max(low + 3, min(STRAIN_MAX, high))
    return round(low), round(max(low, min(high, opt))), round(high)


def _options(current_trimp, high_strain, tau):
    delta = max(0.0, strain_to_trimp(high_strain, tau) - current_trimp)
    return [
        {"zone": zi + 1, "name": name, "minutes": round(delta / ZONE_TRIMP_MIN[zi])}
        for zi, name in ((1, "Z2 Aerob"), (2, "Z3 Tempo"), (3, "Z4 Schwelle"))
    ]


def _session_advice(rem_trimp, remaining_pts, status, recovery, rec_status, systems):
    """A sport-coach-style, structured session prescription coupled to recovery,
    cardio-load deficits and the remaining strain budget — not just raw minutes."""
    def zmin(zi):
        return rem_trimp / ZONE_TRIMP_MIN[zi] if rem_trimp > 0 else 0.0

    rec = recovery
    budget_txt = f"Rest-Budget {round(remaining_pts)}"
    low_rec = (rec is not None and rec < 40) or rec_status == "anomaly"

    if status == "over" or low_rec or rem_trimp < 8:
        why = []
        if rec is not None and rec < 40:
            why.append(f"Erholung niedrig ({round(rec)})")
        elif rec_status == "anomaly":
            why.append("Anomalie-Flag aktiv")
        if status == "over":
            why.append("Tagesbudget ausgeschöpft")
        return {
            "headline": "Regeneration", "zone": "Z1", "tone": "warn",
            "prescription": "Ruhetag oder 20–30 min sehr locker (Zone 1)",
            "rationale": (" · ".join(why) or "wenig Budget heute")
            + " → heute kein harter Reiz; die Anpassung passiert in der Erholung.",
            "source": "Erholungs- & belastungsgekoppelt",
        }

    sys = {s["key"]: s for s in (systems or [])}
    intens_under = sys.get("intensiv", {}).get("status") == "under"
    basis_under = sys.get("basis", {}).get("status") == "under"
    moderate = rec is not None and rec < 60

    if moderate or not intens_under:
        mins = int(min(75, max(30, zmin(1) * 0.8)))
        why = [f"Erholung moderat ({round(rec)})"] if moderate else []
        why.append("Basis-System unter Ziel" if basis_under else "Intensiv-Ziel erfüllt – Basis pflegen")
        return {
            "headline": "Ruhiger Grundlagenlauf", "zone": "Z2", "tone": "good",
            "prescription": f"{mins} min locker in Zone 2 (Gespräch durchgehend möglich)",
            "rationale": " · ".join(why) + f" → aerobe Grundlage statt Intensität. {budget_txt}.",
            "source": "polarisiert + erholungsvalidiert",
        }

    # Recovery is good and the intensive system lags → structured quality.
    z5b, z4b = zmin(4), zmin(3)
    if z5b >= 12:
        n = max(3, min(6, round(min(z5b, 24) / 4)))
        return {
            "headline": "VO₂max-Intervalle", "zone": "Z5", "tone": "good",
            "prescription": f"{n}×4 min @ ~90–95% HFmax · 3 min Trabpause",
            "rationale": f"Erholung grün ({round(rec)}) und Intensiv-System unter Ziel → "
                         f"ein VO₂max-Reiz bringt für 5–10 km jetzt am meisten. {budget_txt}.",
            "source": "4×4-min-HIIT-Evidenz · erholungsvalidiert",
        }
    if z4b >= 18:
        total = int(min(40, z4b))
        struct = (f"2×{total // 2} min Zone 4 (10-km-Tempo) · 3 min Trab"
                  if total >= 30 else f"{total} min Zone 4 (Schwelle) am Stück")
        return {
            "headline": "Schwellen-Intervalle", "zone": "Z4", "tone": "good",
            "prescription": struct,
            "rationale": f"Erholung gut ({round(rec)}), Budget reicht für Schwellenarbeit → "
                         f"hebt die Laktatschwelle und damit dein 5–10 km-Tempo. {budget_txt}.",
            "source": "Schwellen-Evidenz · erholungsvalidiert",
        }
    n = max(4, min(10, round(z5b))) if z5b >= 4 else 6
    return {
        "headline": "Kurze, scharfe Reize", "zone": "Z5", "tone": "good",
        "prescription": f"{n}×1 min Zone 5 · 1 min Trab (am Ende eines lockeren Laufs)",
        "rationale": f"Erholung gut ({round(rec)}), aber Restbudget klein → kurze VO₂max-Reize "
                     f"ohne Überlastung. {budget_txt}.",
        "source": "erholungs- & belastungsgekoppelt",
    }


def build_strain(rows, workouts, recovery, sleep_score, load_ratio, series_days=30,
                 cardio_systems=None, recovery_status=None) -> dict:
    if not rows:
        return {"empty": True}
    today_row = rows[-1]
    today = today_row.date
    today_workouts = [w for w in workouts if w.date == today]

    by_date = {}
    for w in workouts:
        by_date.setdefault(w.date, []).append(w)

    daily_trimp = [_day_trimp(r, by_date.get(r.date, [])) for r in rows]
    tau = _personal_tau(daily_trimp[-BASELINE_DAYS:])

    now_hour = max(WAKE_HOUR, min(SLEEP_HOUR, dt.datetime.now().hour))

    intr = None
    if today_row.intraday_zones:
        try:
            intr = json.loads(today_row.intraday_zones)
        except (ValueError, TypeError):
            intr = None

    curve = []
    current_trimp = 0.0
    if intr:
        cum = 0.0
        for h in range(0, 24):
            cum += _zone_trimp(intr[h]) if h < len(intr) else 0.0
            if WAKE_HOUR <= h <= SLEEP_HOUR:
                curve.append({"hour": h, "strain": round(trimp_to_strain(cum, tau)), "projected": h > now_hour})
            if h <= now_hour:
                current_trimp = cum
    else:
        # No intraday: ramp the full-day trimp linearly across waking hours.
        full = _day_trimp(today_row, today_workouts)
        span = SLEEP_HOUR - WAKE_HOUR
        for h in range(WAKE_HOUR, SLEEP_HOUR + 1):
            frac = (h - WAKE_HOUR) / span
            t = full * frac
            curve.append({"hour": h, "strain": round(trimp_to_strain(t, tau)), "projected": h > now_hour})
            if h <= now_hour:
                current_trimp = t

    current = round(trimp_to_strain(current_trimp, tau))
    projected_full = round(trimp_to_strain(_day_trimp(today_row, today_workouts), tau))

    low, opt, high = _target_range(recovery, sleep_score, load_ratio)
    remaining = max(0, high - current)
    if current < low:
        status, lbl = "under", "Raum für Training"
    elif current <= high:
        status, lbl = "optimal", "Im optimalen Bereich"
    else:
        status, lbl = "over", "Genug für heute"

    series = [
        {"date": r.date.isoformat(), "strain": round(trimp_to_strain(t, tau))}
        for r, t in zip(rows, daily_trimp)
    ][-series_days:]

    rem_trimp = max(0.0, strain_to_trimp(high, tau) - current_trimp)
    session = _session_advice(rem_trimp, remaining, status, recovery, recovery_status, cardio_systems)

    return {
        "empty": False,
        "scale_max": STRAIN_MAX,
        "current": current,
        "projected_full_day": projected_full,
        "now_hour": now_hour,
        "data_source": "intraday" if intr else "estimated",
        "target_low": low,
        "target_opt": opt,
        "target_high": high,
        "remaining": remaining,
        "status": status,
        "label": lbl,
        "session": session,
        "options": _options(current_trimp, high, tau) if status != "over" else [],
        "intraday": curve,
        "series": series,
        "today_sessions": [
            {"type": w.type, "duration_min": round(w.duration_min),
             "strain_contrib": round(trimp_to_strain(_workout_zone_trimp(w), tau))}
            for w in today_workouts
        ],
    }
