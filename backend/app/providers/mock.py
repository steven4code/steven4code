"""Mock provider: realistic daily metrics + training sessions, no credentials.

The data is deterministic per-date (seeded by the date) so the dashboard is
stable across reloads but has natural variation. Crucially, recovery inputs
(HRV / resting HR / sleep) respond to recent training load, so the
recovery-validated training logic has something meaningful to react to.

The synthetic athlete trains 6x/week and is intentionally intensity-heavy with
two padel sessions (lots of Z3/Z4 "grey zone"), which is exactly the pattern the
cardio engine should flag for a 5-10k goal.
"""
from __future__ import annotations

import datetime as dt
import math
import random

from .base import DailyMetricData, WorkoutData

# Karvonen zone bounds assume the default profile (max 190, rest 50). The mock
# emits zone minutes directly so they line up with that default.
ZONE_WEIGHTS = [1, 2, 3, 4, 5]

# Weekly template: weekday -> (type, duration, [z1..z5] minutes)
_TEMPLATE = {
    0: ("rest", 0, [0, 0, 0, 0, 0]),
    1: ("run_intervals", 55, [10, 15, 8, 15, 7]),   # VO2max 4x4
    2: ("padel", 75, [5, 25, 30, 13, 2]),
    3: ("run_easy", 45, [12, 28, 5, 0, 0]),
    4: ("run_tempo", 50, [8, 14, 18, 10, 0]),
    5: ("padel", 80, [5, 26, 32, 15, 2]),
    6: ("run_long", 80, [16, 54, 10, 0, 0]),
}


class MockProvider:
    name = "mock"

    def is_authenticated(self) -> bool:
        return True

    def _rng(self, key: str, day: dt.date) -> random.Random:
        # Stable across processes (Python's hash() is salted per run).
        offset = {"day": 11, "wk": 23, "rpe": 37}.get(key, 7)
        return random.Random(day.toordinal() * 101 + offset)

    # -- workouts ----------------------------------------------------------- #
    def _template_for(self, day: dt.date):
        kind, dur, zones = _TEMPLATE[day.weekday()]
        if kind == "rest" or dur == 0:
            return None
        rng = self._rng("wk", day)
        # +/- 15% session-to-session variation.
        scale = rng.uniform(0.85, 1.15)
        zmin = [round(z * scale, 1) for z in zones]
        duration = round(sum(zmin), 1)
        wtype = "padel" if kind == "padel" else "run"
        return kind, wtype, duration, zmin

    def _workout_for(self, day: dt.date) -> WorkoutData | None:
        t = self._template_for(day)
        if t is None:
            return None
        kind, wtype, duration, zmin = t
        total = sum(zmin) or 1
        # Weighted-average HR per zone midpoint (max 190 / rest 50 Karvonen).
        zone_mid_hr = [127, 141, 155, 169, 183]
        avg_hr = round(sum(zmin[i] * zone_mid_hr[i] for i in range(5)) / total)
        max_hr = round(min(190, avg_hr + 12 + (8 if zmin[4] > 0 else 0)))
        distance = None
        if wtype == "run":
            # ~ pace by intensity: easier mix -> ~6:00/km, harder -> faster.
            avg_pace = 6.4 - (avg_hr - 140) * 0.02
            distance = round(duration / max(4.0, avg_pace), 1)
        start = dt.datetime.combine(day, dt.time(18, 30))
        rng = self._rng("rpe", day)
        rpe_map = {
            "run_easy": 3.5,
            "run_long": 5.0,
            "run_tempo": 6.5,
            "run_intervals": 8.5,
            "padel": 7.5,  # high perceived load despite moderate mean HR
        }
        rpe = round(rpe_map.get(kind, 5) + rng.uniform(-0.5, 0.5), 1)
        return WorkoutData(
            date=day,
            type=wtype,
            duration_min=duration,
            external_id=f"mock-{day.isoformat()}-{kind}",
            start=start,
            distance_km=distance,
            avg_hr=avg_hr,
            max_hr=max_hr,
            rpe=rpe,
            zone_minutes=zmin,
            source="mock",
        )

    def _day_load(self, day: dt.date) -> float:
        """Crude internal load for a day's session (0 on rest days)."""
        w = self._workout_for(day)
        if w is None:
            return 0.0
        return sum(w.zone_minutes[i] * ZONE_WEIGHTS[i] for i in range(5)) / 60.0

    def _hypnogram(self, deep, rem, light, awake, rng) -> list:
        """Build a realistic ordered hypnogram summing ~to the stage totals.

        Deep (SWS) is front-loaded, REM back-loaded, light fills the cycles, with
        a few brief awakenings between cycles — the textbook nightly architecture.
        """
        total = deep + rem + light
        if total <= 0:
            return []
        n = max(3, min(6, round(total / 95)))
        w_deep = [max(0.05, 1.0 - (i / (n - 1)) * 1.25) for i in range(n)]
        w_rem = [0.15 + (i / (n - 1)) for i in range(n)]
        sd, sr = sum(w_deep), sum(w_rem)
        deep_parts = [deep * w / sd for w in w_deep]
        rem_parts = [rem * w / sr for w in w_rem]
        light_parts = [light / n] * n
        awake_each = awake / max(1, n - 1)

        segs = []

        def add(stage, mins):
            if mins >= 1:
                segs.append({"stage": stage, "min": round(mins, 1)})

        for i in range(n):
            if i > 0:
                add("awake", awake_each * rng.uniform(0.6, 1.4))
            add("light", light_parts[i] * 0.45)
            add("deep", deep_parts[i])
            add("light", light_parts[i] * 0.55)
            add("rem", rem_parts[i])
        return segs

    # -- daily metrics ------------------------------------------------------ #
    def _day(self, day: dt.date) -> DailyMetricData:
        rng = self._rng("day", day)
        t = day.toordinal()
        drift = math.sin(t / 40.0)
        weekend = day.weekday() >= 5

        # Fatigue from the previous 1-2 days suppresses HRV and lifts resting HR.
        load = 0.6 * self._day_load(day - dt.timedelta(days=1)) + 0.3 * self._day_load(
            day - dt.timedelta(days=2)
        )

        hrv = 58 + 7 * drift - 2.4 * load + (3 if weekend else 0) + rng.uniform(-6, 6)
        hrv = round(max(20.0, hrv), 1)

        resting_hr = 50 - 2.5 * drift + 1.1 * load + rng.uniform(-2.5, 2.5)
        resting_hr = round(max(40.0, resting_hr), 1)
        sleeping_hr = round(max(38.0, resting_hr - rng.uniform(1, 3)), 1)

        # Deterministic 3-day "illness" block every 47 days to demo anomaly flags.
        ill = (t % 47) in (0, 1, 2)
        resp_rate = round(14.5 + 0.2 * load + (2.2 if ill else 0) + rng.uniform(-0.6, 0.6), 1)
        spo2 = round(rng.uniform(92.0, 94.0) if ill else rng.uniform(95.5, 99.0), 1)
        skin_temp_dev = round(
            (1.0 + rng.uniform(-0.1, 0.3)) if ill else rng.uniform(-0.25, 0.25), 2
        )
        if ill:  # illness suppresses HRV / raises resting HR too
            hrv = round(max(20.0, hrv - 8), 1)
            resting_hr = round(resting_hr + 4, 1)

        vo2max = round(49.0 + 1.5 * math.sin(t / 130.0) + rng.uniform(-0.3, 0.3), 1)

        # Sleep: a bit shorter / worse after hard days; longer on weekends.
        sleep_minutes = (
            455 + (35 if weekend else 0) - 6 * load + rng.uniform(-35, 35)
        )
        sleep_minutes = round(max(240.0, sleep_minutes))
        efficiency = round(min(97.0, 90 - 0.6 * load + rng.uniform(-5, 5)), 1)
        deep = round(sleep_minutes * rng.uniform(0.13, 0.20))
        rem = round(sleep_minutes * rng.uniform(0.18, 0.25))
        awake = round(sleep_minutes * rng.uniform(0.03, 0.08))
        light = max(0, sleep_minutes - deep - rem - awake)
        latency = round(max(2.0, 12 + 1.5 * load + rng.uniform(-6, 8)), 1)
        awakenings = max(0, round(2 + 0.3 * load + rng.uniform(-1.5, 1.5)))
        # Minutes after 21:00 that sleep began (~22:30 +/- with noise).
        onset = round(90 + (25 if weekend else 0) + rng.uniform(-25, 35))

        # All-day load: everyday low-zone time + the day's workout zones.
        # NOTE: this is genuine *in-zone* time (HR above the Z1 lower bound from
        # walking/stairs/chores) — sedentary/resting minutes are NOT counted, so
        # a true rest day stays low. Kept small & realistic to avoid the old
        # "strain saturates in the morning" bug.
        w = self._workout_for(day)
        wz = w.zone_minutes if w else [0.0] * 5
        everyday = [rng.uniform(15, 30), rng.uniform(5, 14), rng.uniform(0, 3), 0, 0]
        hr_zone = [round(everyday[i] + wz[i], 1) for i in range(5)]
        steps = round(rng.uniform(7000, 13000) + (2500 if w and w.type == "run" else 0))
        distance = round(steps * 0.00072 + (w.distance_km if (w and w.distance_km) else 0), 1)
        energy = round(rng.uniform(380, 620) + sum(wz) * 4)
        azm = round(wz[2] + 2 * (wz[3] + wz[4]) + rng.uniform(5, 20))

        return DailyMetricData(
            date=day,
            hrv_rmssd=hrv,
            resting_hr=resting_hr,
            sleeping_hr=sleeping_hr,
            respiratory_rate=resp_rate,
            spo2=spo2,
            skin_temp_dev=skin_temp_dev,
            vo2max=vo2max,
            steps=steps,
            distance_km=distance,
            active_energy_kcal=energy,
            azm=azm,
            hr_zone_minutes=hr_zone,
            sleep_minutes=float(sleep_minutes),
            sleep_efficiency=efficiency,
            deep_minutes=float(deep),
            rem_minutes=float(rem),
            light_minutes=float(light),
            awake_minutes=float(awake),
            sleep_latency_min=latency,
            awakenings=awakenings,
            sleep_onset_min=float(onset),
            sleep_score=None,
            sleep_stages=self._hypnogram(deep, rem, light, awake, rng),
            source="mock",
        )

    # -- provider API ------------------------------------------------------- #
    def _intraday_for(self, day: dt.date) -> list[list[float]]:
        rng = self._rng("intra", day)
        buckets = [[0.0] * 5 for _ in range(24)]
        for h in range(7, 23):  # everyday low-zone in-zone activity while awake
            buckets[h][0] += round(rng.uniform(0.8, 2.0), 1)
            buckets[h][1] += round(rng.uniform(0, 1.0), 1)
        w = self._workout_for(day)
        if w:
            sh = w.start.hour if w.start else 18
            for i in range(5):
                buckets[sh][i] += w.zone_minutes[i]
        return [[round(x, 1) for x in b] for b in buckets]

    def fetch_daily_metrics(
        self, start: dt.date, end: dt.date
    ) -> list[DailyMetricData]:
        days, cur = [], start
        while cur <= end:
            days.append(self._day(cur))
            cur += dt.timedelta(days=1)
        if days:  # attach an intraday curve for "today" (the last day)
            days[-1].intraday_zones = self._intraday_for(end)
        return days

    def fetch_workouts(self, start: dt.date, end: dt.date) -> list[WorkoutData]:
        out, cur = [], start
        while cur <= end:
            w = self._workout_for(cur)
            if w is not None:
                out.append(w)
            cur += dt.timedelta(days=1)
        return out
