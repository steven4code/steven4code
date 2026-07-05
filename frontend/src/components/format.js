export function hm(minutes) {
  if (minutes == null) return "–";
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return `${h}h ${m}m`;
}

export function num(value, digits = 0) {
  if (value == null) return "–";
  return value.toFixed(digits);
}

// 9007 -> "9.007" (de-DE Tausenderpunkt)
export function int(value) {
  if (value == null) return "–";
  return Math.round(value).toLocaleString("de-DE");
}

// Delta mit Pfeil — Richtung immer als Zeichen UND Farbe (nie Farbe allein).
export function deltaText(delta, digits = 0) {
  if (delta == null) return null;
  const arrow = delta > 0 ? "▲" : delta < 0 ? "▼" : "—";
  return `${arrow} ${Math.abs(delta).toFixed(digits)}`;
}

export function deltaClass(delta, goodWhenUp = true) {
  if (delta == null || delta === 0) return "delta neutral";
  const positive = delta > 0;
  const good = goodWhenUp ? positive : !positive;
  return `delta ${good ? "good" : "bad"}`;
}

// "2026-07-05" -> "Samstag · 5. Juli"
export function longDate(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T12:00:00`);
  const wd = d.toLocaleDateString("de-DE", { weekday: "long" });
  const dm = d.toLocaleDateString("de-DE", { day: "numeric", month: "long" });
  return `${wd} · ${dm}`;
}
