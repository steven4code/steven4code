import { SPARK } from "../theme.js";

// Wortgroße Trendlinie (Tufte). Standardfarbe: De-Emphasis-Blaugrau —
// Identität steckt im Tile-Label, Richtung im Delta. Endpunkt markiert.
export default function Sparkline({ values = [], color = SPARK, width = 120, height = 30 }) {
  const nums = values.filter((v) => v != null);
  if (nums.length < 2) return <svg width={width} height={height} aria-hidden />;
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const rng = max - min || 1;
  const n = values.length;
  const pts = [];
  let last = null;
  values.forEach((v, i) => {
    if (v == null) return;
    const x = (i / (n - 1)) * (width - 8) + 4;
    const y = height - 4 - ((v - min) / rng) * (height - 8);
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
    last = [x, y];
  });
  return (
    <svg width={width} height={height} aria-hidden>
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {last && <circle cx={last[0]} cy={last[1]} r="2.6" fill={color} stroke="#161A21" strokeWidth="1.5" />}
    </svg>
  );
}
