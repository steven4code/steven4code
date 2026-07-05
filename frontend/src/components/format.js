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

// Renders a +/- delta with up/down arrow. `goodWhenUp` controls coloring.
export function deltaText(delta) {
  if (delta == null) return null;
  const arrow = delta > 0 ? "▲" : delta < 0 ? "▼" : "▬";
  return `${arrow} ${Math.abs(delta)}`;
}

export function deltaClass(delta, goodWhenUp = true) {
  if (delta == null || delta === 0) return "delta neutral";
  const positive = delta > 0;
  const good = goodWhenUp ? positive : !positive;
  return `delta ${good ? "good" : "bad"}`;
}
