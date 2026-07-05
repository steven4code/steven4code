// Small shared UI primitives.

export function Bar({ value, max = 100, color = "#60a5fa", height = 8 }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="bar" style={{ height }}>
      <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export function Chip({ children, tone = "neutral" }) {
  return <span className={`chip ${tone}`}>{children}</span>;
}

// Small hover/focus info bubble explaining a metric.
export function InfoDot({ text }) {
  return (
    <span className="infodot" tabIndex={0} onClick={(e) => e.stopPropagation()}>
      <span className="infodot-i">i</span>
      <span className="infodot-pop">{text}</span>
    </span>
  );
}

// Inline range picker (chips) for charts.
export function RangePicker({ value, onChange, options = [7, 14, 30, 90] }) {
  return (
    <div className="range small" onClick={(e) => e.stopPropagation()}>
      {options.map((r) => (
        <button key={r} className={r === value ? "active" : ""} onClick={() => onChange(r)}>
          {r === 7 ? "Woche" : `${r}T`}
        </button>
      ))}
    </div>
  );
}

export function BackBar({ onBack, title, right }) {
  return (
    <div className="detail-bar">
      <button className="btn" onClick={onBack}>← Zurück</button>
      <h1>{title}</h1>
      <div className="detail-bar-right">{right}</div>
    </div>
  );
}

export function Kpi({ label, value, sub }) {
  return (
    <div className="kpi">
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{label}</span>
      {sub && <span className="kpi-sub">{sub}</span>}
    </div>
  );
}

export const PRIORITY_TONE = {
  high: "bad",
  medium: "warn",
  good: "good",
  info: "neutral",
};

export function Recommendation({ rec }) {
  return (
    <div className={`rec rec-${rec.priority}`}>
      <div className="rec-head">
        <span className={`rec-dot ${PRIORITY_TONE[rec.priority] || "neutral"}`} />
        <strong>{rec.title}</strong>
      </div>
      <p className="rec-detail">{rec.detail}</p>
      {rec.source && <span className="rec-source">{rec.source}</span>}
    </div>
  );
}
