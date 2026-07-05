// Instrument-Ring: Status auf einen Blick, Präzision trägt die Zahl im
// Zentrum (Winkel ist ein grober Kanal — Cleveland & McGill 1984).
// Track = abgedunkelte Stufe derselben Farbe (Meter-Regel), kein Glow.
export default function ScoreRing({
  value,
  max = 100,
  size = 64,
  stroke = 7,
  color = "var(--accent)",
  text,
  textSize,
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value / max));
  const dash = c * pct;
  return (
    <div className="ring-wrap" style={{ width: size, height: size }}>
      <svg width={size} height={size} aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeOpacity={0.16}
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
          style={{ transition: "stroke-dasharray 0.6s ease-out" }}
        />
      </svg>
      {text !== undefined && (
        <div className="ring-center">
          <div className="ring-num" style={{ fontSize: textSize || size * 0.3 }}>
            {text}
          </div>
        </div>
      )}
    </div>
  );
}
