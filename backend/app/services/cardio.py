"""Cardio Load — run-specific training-system distribution (gold-standard).

What it answers: *which endurance systems have I loaded this week, how does that
compare to the ideal mix for fast 5-10 km, and what should I do next?*

Key ideas (all evidence-based):
1. RUN-SPECIFIC load. Adaptations are specific (SAID principle). Central/aerobic
   adaptations transfer moderately across modalities; running economy & vVO2max
   are gait-specific and barely transfer. So every zone-minute is multiplied by a
   modality x zone "specificity" factor -> RUN-EQUIVALENT minutes. Running = 100%;
   padel counts only partially, and less in the race-pace zones (Tanaka 1994
   cross-training review; Burnley & Jones intensity domains).
2. THREE systems (from the chosen Z1-2 / Z3 / Z4-5 grouping):
   - Aerobe Basis (Z1-2): mitochondria, capillaries, stroke volume.
   - Grauzone (Z3): tempo / sub-threshold.
   - Intensiv (Z4-5): threshold + VO2max — the 5-10 km ceiling.
3. TARGET = a quality-heavy distribution (70/10/20) of the athlete's sustainable
   weekly run-equivalent volume (chronic load -> safe progression). VO2max trend
   informs the recommendation.
4. The biggest *relative* deficit drives the recommendation, validated against how
   recovery actually responds to each session type, and against the run-specificity
   of recent intensity (a padel-heavy week still lacks a real running stimulus).
"""
from __future__ import annotations

import datetime as dt
import statistics

# Target distribution (user-selected: quality-heavy). Fractions sum to 1.
MODEL = {"basis": 0.70, "grauzone": 0.10, "intensiv": 0.20}

# Modality x zone run-specificity (fraction of each zone-minute that counts as a
# run-equivalent training stimulus). Run = 1.0 everywhere (the goal modality).
SPECIFICITY = {
    "run": [1.00, 1.00, 1.00, 1.00, 1.00],
    "ride": [0.65, 0.70, 0.60, 0.45, 0.40],
    "padel": [0.50, 0.55, 0.45, 0.30, 0.25],
    "other": [0.55, 0.60, 0.50, 0.35, 0.30],
}

ZONE_WEIGHTS = [1, 2, 3, 4, 5]
MIN_WEEK_TARGET = 90.0  # floor for a sensible weekly run-equivalent target (min)

GOAL_TARGETS = {  # legacy polarization context (kept for the detail view)
    "run_5_10k": {"low": 80, "grey": 5, "high": 15},
    "general": {"low": 70, "grey": 20, "high": 10},
}


# --------------------------------------------------------------------------- #
# Load primitives
# --------------------------------------------------------------------------- #
def edwards_load(w) -> float:
    z = [w.z1_min, w.z2_min, w.z3_min, w.z4_min, w.z5_min]
    return sum((z[i] or 0) * ZONE_WEIGHTS[i] for i in range(5))


def srpe(w):
    return round(w.rpe * w.duration_min, 0) if w.rpe else None


def _spec(wtype):
    return SPECIFICITY.get(wtype, SPECIFICITY["other"])


def _req_zones(w):
    """Run-equivalent minutes per zone for one workout."""
    z = [w.z1_min, w.z2_min, w.z3_min, w.z4_min, w.z5_min]
    sp = _spec(w.type)
    return [(z[i] or 0.0) * sp[i] for i in range(5)]


def _req_total(w):
    return sum(_req_zones(w))


def _systems_req(workouts):
    agg = [0.0] * 5
    padel_req = 0.0
    total = 0.0
    for w in workouts:
        rz = _req_zones(w)
        for i in range(5):
            agg[i] += rz[i]
        s = sum(rz)
        total += s
        if w.type == "padel":
            padel_req += s
    return {
        "zones": agg,
        "basis": agg[0] + agg[1],
        "grauzone": agg[2],
        "intensiv": agg[3] + agg[4],
        "z4": agg[3],
        "z5": agg[4],
        "total": total,
        "padel_req": padel_req,
    }


def _in_range(workouts, start, end):
    return [w for w in workouts if start <= w.date <= end]


def _is_quality_run(w) -> bool:
    return w.type == "run" and ((w.z4_min or 0) + (w.z5_min or 0)) >= 6


def _ewma(daily, n):
    lam = 2 / (n + 1)
    val = 0.0
    for load in daily:
        val = load * lam + val * (1 - lam)
    return val


def _sys_target(total, frac):
    mid = total * frac
    return {"lo": round(mid * 0.85), "hi": round(mid * 1.2), "mid": round(mid)}


def _status(actual, tgt):
    if actual < tgt["lo"]:
        return "under"
    if actual > tgt["hi"]:
        return "over"
    return "ok"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def build_cardio(workouts, rows, profile, resting_hr, recovery_by_date) -> dict:
    if not rows:
        return {"empty": True}
    today = rows[-1].date

    # Daily run-equivalent minutes -> acute (7d) / chronic (28d) weekly volume.
    req_by_date: dict[dt.date, float] = {}
    edw_by_date: dict[dt.date, float] = {}
    for w in workouts:
        req_by_date[w.date] = req_by_date.get(w.date, 0.0) + _req_total(w)
        edw_by_date[w.date] = edw_by_date.get(w.date, 0.0) + edwards_load(w)
    daily_req = [req_by_date.get(r.date, 0.0) for r in rows]
    daily_edw = [edw_by_date.get(r.date, 0.0) for r in rows]

    chronic_weekly = statistics.fmean(daily_req[-28:]) * 7 if len(daily_req) >= 1 else 0.0
    acute_weekly = sum(daily_req[-7:])
    ratio = round(_ewma(daily_edw, 7) / _ewma(daily_edw, 28), 2) if _ewma(daily_edw, 28) else None

    # Safe progressive overload: nudge the target up only when ramp is gentle.
    target_total = max(MIN_WEEK_TARGET, chronic_weekly)
    if ratio is not None and ratio < 1.2:
        target_total *= 1.05

    wk = _in_range(workouts, today - dt.timedelta(days=6), today)
    sysreq = _systems_req(wk)

    systems = []
    for key, label, zones in (
        ("basis", "Aerobe Basis", "Z1–Z2"),
        ("grauzone", "Grauzone / Tempo", "Z3"),
        ("intensiv", "Intensiv (Schwelle + VO₂max)", "Z4–Z5"),
    ):
        tgt = _sys_target(target_total, MODEL[key])
        actual = round(sysreq[key])
        systems.append({
            "key": key, "label": label, "zones": zones,
            "actual_min": actual, "target_lo": tgt["lo"], "target_hi": tgt["hi"],
            "target_mid": tgt["mid"], "target_pct": round(MODEL[key] * 100),
            "pct_of_target": round(actual / tgt["mid"] * 100) if tgt["mid"] else None,
            "status": _status(actual, tgt),
        })

    padel_share = round(sysreq["padel_req"] / sysreq["total"] * 100) if sysreq["total"] else 0

    last7 = daily_edw[-7:]
    monotony = (
        round(statistics.fmean(last7) / statistics.pstdev(last7), 2)
        if len(last7) >= 2 and statistics.pstdev(last7) > 0 else None
    )

    vo2_series = [r.vo2max for r in rows[-42:] if r.vo2max is not None]
    vo2_trend = (round(vo2_series[-1] - vo2_series[0], 1)
                 if len(vo2_series) >= 2 else None)
    latest_vo2 = vo2_series[-1] if vo2_series else None
    recovery_today = recovery_by_date.get(today)
    cost = _recovery_cost(workouts, recovery_by_date, today)

    recs = _recommendations(systems, sysreq, padel_share, ratio, monotony,
                            cost, vo2_trend, recovery_today, wk)

    week = {
        "volume_min": round(sum(w.duration_min for w in wk), 0),
        "distance_km": round(sum(w.distance_km or 0 for w in wk), 1),
        "sessions": len(wk), "runs": sum(1 for w in wk if w.type == "run"),
        "padel": sum(1 for w in wk if w.type == "padel"),
        "req_total": round(sysreq["total"]),
        "edwards_load": round(sum(edwards_load(w) for w in wk), 0),
        "srpe_load": round(sum(srpe(w) or 0 for w in wk), 0),
    }

    return {
        "empty": False,
        "as_of": today.isoformat(),
        "goal": "Schnelle 5–10 km",
        "model": {k: round(v * 100) for k, v in MODEL.items()},
        "systems": systems,
        "week_req_total": round(acute_weekly),
        "target_total": round(target_total),
        "padel_share_pct": padel_share,
        "specificity": SPECIFICITY,
        "week": week,
        "load_ratio": ratio,
        "load_ratio_status": _ratio_status(ratio),
        "monotony": monotony,
        "vo2max": latest_vo2,
        "vo2_trend": vo2_trend,
        "recovery_cost": cost,
        "weekly_series": _weekly_series(workouts, today, weeks=8),
        "recommendations": recs,
        "recent_workouts": _recent_workouts(workouts, today, days=21),
        "distribution_28d": _distribution(_in_range(workouts, today - dt.timedelta(days=27), today)),
        "target": GOAL_TARGETS["run_5_10k"],
    }


def _ratio_status(ratio):
    if ratio is None:
        return "unknown"
    if ratio > 1.5:
        return "high"
    if ratio < 0.8:
        return "low"
    return "ok"


def _recommendations(systems, sysreq, padel_share, ratio, monotony, cost,
                     vo2_trend, recovery_today, week_workouts):
    recs = []
    by_key = {s["key"]: s for s in systems}
    basis, grau, intens = by_key["basis"], by_key["grauzone"], by_key["intensiv"]
    rec_ok = recovery_today is None or recovery_today >= 50

    if sysreq["total"] <= 0:
        return [{"priority": "info", "title": "Noch keine Trainingsdaten",
                 "detail": "Nach den ersten synchronisierten Einheiten erscheinen hier Empfehlungen.",
                 "source": ""}]

    # 1. Base-neglect guard (quality-heavy plans tend to skimp on Z2).
    if basis["target_mid"] and basis["actual_min"] < 0.6 * basis["target_mid"]:
        deficit = round(basis["target_mid"] - basis["actual_min"])
        recs.append({
            "priority": "high", "title": "Aerobe Basis vernachlässigt",
            "detail": f"Nur {basis['actual_min']} von ~{basis['target_mid']} min lockerer Z1–Z2-Last. "
                      f"Plane ~{deficit} min ruhigen Z2-Lauf – ohne Basis stagnieren 5–10 km trotz Intensität.",
            "source": "Basis-Schutz · polarisiert/pyramidal-Evidenz",
        })

    # 2. Recovery does not keep up with a session type.
    worst = min([(v, k) for k, v in cost.items() if k != "baseline" and v is not None], default=None)
    if worst is not None and worst[0] <= -6:
        nice = {"padel": "Padel", "quality_run": "harte Läufe", "easy_run": "Läufe"}[worst[1]]
        recs.append({
            "priority": "high", "title": "Erholung kommt nicht hinterher",
            "detail": f"Nach {nice} liegt deine Erholung am Folgetag im Schnitt {abs(worst[0])} Punkte unter Baseline. "
                      "Hart nur bei grüner Erholung, sonst Z2/Ruhe.",
            "source": "Erholungs-validiert (HFV-gesteuert)",
        })

    # 3. Load ramping too fast.
    if ratio is not None and ratio > 1.5:
        recs.append({
            "priority": "high", "title": "Belastung steigt zu schnell",
            "detail": f"Akut:chronisch bei {ratio}. Anstieg drosseln, eine ruhigere Woche einplanen.",
            "source": "EWMA-Lastanstieg",
        })

    # 4. Biggest relative deficit -> concrete next session.
    deficits = []
    for s in (basis, grau, intens):
        if s["target_mid"] and s["actual_min"] < s["target_lo"]:
            deficits.append(((s["target_mid"] - s["actual_min"]) / s["target_mid"], s))
    deficits.sort(reverse=True)
    if deficits:
        _, s = deficits[0]
        need = round(s["target_mid"] - s["actual_min"])
        if s["key"] == "basis" and not any(r["title"] == "Aerobe Basis vernachlässigt" for r in recs):
            recs.append({"priority": "medium", "title": "Mehr aerobe Grundlage",
                         "detail": f"~{need} min ruhiger Z2-Lauf fehlen diese Woche für deinen Mix.",
                         "source": "Ziel-Mix 70/10/20"})
        elif s["key"] == "intensiv":
            if rec_ok:
                vo2_note = " Dein VO₂max-Trend ist rückläufig – Zeit für scharfe Reize." if (vo2_trend is not None and vo2_trend < -0.3) else ""
                recs.append({"priority": "medium", "title": "VO₂max-Reiz setzen",
                             "detail": f"Intensiv-System unter Ziel. 1× strukturierte Intervalle "
                                       f"(z.B. 4×4 min @ ~90–95% HFmax) – maximiert Zeit nahe VO₂max.{vo2_note}",
                             "source": "4×4-min-HIIT-Evidenz"})
            else:
                recs.append({"priority": "medium", "title": "Intensität verschieben",
                             "detail": "Intensiv-System unter Ziel, aber Erholung niedrig. Erst regenerieren, "
                                       "harte Reize bei grüner Erholung nachholen.",
                             "source": "Erholungs-validiert"})
        elif s["key"] == "grauzone":
            recs.append({"priority": "low", "title": "Etwas Tempo (Z3) ergänzen",
                         "detail": f"~{need} min Tempo/Schwellen-Anteil fehlen – z.B. ein zügiger Dauerlauf.",
                         "source": "Ziel-Mix 70/10/20"})

    # 5. Run-specificity gap: intensity came mostly from padel.
    if padel_share >= 35 and intens["status"] != "over":
        recs.append({
            "priority": "medium", "title": "Lauf-spezifische Intensität fehlt",
            "detail": f"~{padel_share}% deiner Wochenlast stammt aus Padel (nur teilweise lauf-spezifisch). "
                      "Für 5–10 km braucht es einen echten Lauf-Intensitätsreiz (Intervalle/Tempo).",
            "source": "Spezifität (SAID) · Padel anteilig angerechnet",
        })

    # 6. Monotony.
    if monotony is not None and monotony > 2.0:
        recs.append({"priority": "low", "title": "Mehr Variation / Ruhetage",
                     "detail": f"Hohe Monotonie ({monotony}). Harte und leichte Tage klarer trennen.",
                     "source": "Foster Monotonie/Strain"})

    if not recs:
        recs.append({"priority": "good", "title": "Mix passt",
                     "detail": "Systeme, Last und Erholung sind stimmig verteilt. Umfang behutsam steigern.",
                     "source": ""})

    order = {"high": 0, "medium": 1, "low": 2, "good": 3, "info": 4}
    recs.sort(key=lambda r: order.get(r["priority"], 9))
    return recs[:4]


def _distribution(workouts):
    z = [0.0] * 5
    for w in workouts:
        for i, m in enumerate([w.z1_min, w.z2_min, w.z3_min, w.z4_min, w.z5_min]):
            z[i] += m or 0.0
    total = sum(z)
    if total <= 0:
        return None
    return {
        "zone_minutes": [round(x, 1) for x in z], "total_min": round(total, 1),
        "low": round((z[0] + z[1]) / total * 100, 1),
        "grey": round(z[2] / total * 100, 1),
        "high": round((z[3] + z[4]) / total * 100, 1),
    }


def _recovery_cost(workouts, recovery_by_date, today):
    recent = [v for d, v in recovery_by_date.items()
              if v is not None and d >= today - dt.timedelta(days=28)]
    baseline = statistics.fmean(recent) if recent else None
    buckets = {"padel": [], "quality_run": [], "easy_run": []}
    if baseline is not None:
        for w in workouts:
            nxt = recovery_by_date.get(w.date + dt.timedelta(days=1))
            if nxt is None:
                continue
            delta = nxt - baseline
            if w.type == "padel":
                buckets["padel"].append(delta)
            elif _is_quality_run(w):
                buckets["quality_run"].append(delta)
            elif w.type == "run":
                buckets["easy_run"].append(delta)
    out = {k: round(statistics.fmean(v), 1) if v else None for k, v in buckets.items()}
    out["baseline"] = round(baseline, 1) if baseline is not None else None
    return out


def _weekly_series(workouts, today, weeks=8):
    series = []
    monday = today - dt.timedelta(days=today.weekday())
    for i in range(weeks - 1, -1, -1):
        ws = monday - dt.timedelta(days=7 * i)
        we = ws + dt.timedelta(days=6)
        wk = _in_range(workouts, ws, we)
        sysreq = _systems_req(wk)
        series.append({
            "week_start": ws.isoformat(),
            "req_total": round(sysreq["total"]),
            "basis": round(sysreq["basis"]),
            "grauzone": round(sysreq["grauzone"]),
            "intensiv": round(sysreq["intensiv"]),
            "volume_min": round(sum(w.duration_min for w in wk), 0),
        })
    return series


def _recent_workouts(workouts, today, days=21):
    out = []
    for w in sorted(_in_range(workouts, today - dt.timedelta(days=days), today),
                    key=lambda x: x.date, reverse=True):
        out.append({
            "date": w.date.isoformat(), "type": w.type,
            "duration_min": round(w.duration_min, 0), "distance_km": w.distance_km,
            "avg_hr": w.avg_hr, "rpe": w.rpe,
            "zone_minutes": [w.z1_min, w.z2_min, w.z3_min, w.z4_min, w.z5_min],
            "req_total": round(_req_total(w)),
            "edwards_load": round(edwards_load(w), 0), "srpe": srpe(w),
            "quality": _is_quality_run(w),
        })
    return out
