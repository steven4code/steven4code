// Circular SVG gauge for a 0-100 score.
export default function ScoreRing({ value, max = 100, size = 132, label }) {
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value / max));
  const dash = c * pct;

  const color =
    value == null
      ? "#3a4256"
      : value >= 66
      ? "#34d399"
      : value >= 40
      ? "#fbbf24"
      : "#f87171";

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#222838"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div className="ring-center">
        <div className="ring-value">{value == null ? "–" : Math.round(value)}</div>
        {label && <div className="ring-label">{label}</div>}
      </div>
    </div>
  );
}
