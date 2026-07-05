// WHOOP-style circular stat: thick colored ring, big centered number, label.
export default function RingStat({
  label, value, max = 100, unit = "", decimals = 0,
  color = "#16ec06", sub, onOpen, size = 156, stroke = 12,
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value / max));
  const dash = c * pct;
  return (
    <button className="ringstat clickable" onClick={onOpen} type="button">
      <div className="ring-wrap" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#23232c" strokeWidth={stroke} />
          <circle
            cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color}
            strokeWidth={stroke} strokeLinecap="round"
            strokeDasharray={`${dash} ${c - dash}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: "stroke-dasharray 0.7s ease", filter: `drop-shadow(0 0 6px ${color}55)` }}
          />
        </svg>
        <div className="ring-center">
          <div className="ring-num" style={{ color }}>
            {value == null ? "–" : value.toFixed(decimals)}
            {unit ? <span className="ring-unit">{unit}</span> : null}
          </div>
        </div>
      </div>
      <div className="ringstat-label">{label}</div>
      {sub ? <div className="ringstat-sub">{sub}</div> : null}
    </button>
  );
}
