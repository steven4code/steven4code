// Geteilte UI-Primitives des Designsystems (docs/DESIGN.md).

// Karte, die eine Detailansicht öffnet: echter Button (Tastatur + Fokus).
export function CardButton({ onOpen, className = "", children, label }) {
  return (
    <button
      type="button"
      className={`card card-btn ${className}`}
      onClick={onOpen}
      aria-label={label}
    >
      {children}
    </button>
  );
}

export function CardHead({ title, right }) {
  return (
    <div className="card-head">
      <h2 className="card-title">{title}</h2>
      <div className="card-head-right">
        {right}
        <span className="open-hint" aria-hidden>
          Details →
        </span>
      </div>
    </div>
  );
}

export function Bar({ value, max = 100, color = "var(--accent)", height = 6 }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="bar" style={{ height }}>
      <div className="bar-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

// Status-Chip: Bedeutung immer über Text/Icon, Farbe nur Verstärkung.
export function Chip({ children, tone = "neutral" }) {
  return <span className={`chip ${tone}`}>{children}</span>;
}

// Bullet-Meter (Zielband-Motiv): Ist-Balken + hinterlegtes Band + Marker.
// Position statt Winkel (Cleveland & McGill 1984); Form nach Few's Bullet Graph.
export function BulletMeter({
  label,
  labelDot,
  value,
  valueText,
  targetText,
  max,
  bandLo,
  bandHi,
  mark,
  color = "var(--accent)",
  note,
}) {
  const m = Math.max(max || 0, 1);
  const pct = (v) => `${Math.max(0, Math.min(100, ((v || 0) / m) * 100))}%`;
  return (
    <div className="meter">
      {(label || valueText) && (
        <div className="meter-head">
          <span className="mh-label">
            {labelDot && <i className="dot" style={{ background: labelDot }} />}
            {label}
          </span>
          <span className="mh-val">
            {valueText} {targetText && <small>{targetText}</small>}
          </span>
        </div>
      )}
      <div className="meter-track">
        {bandLo != null && bandHi != null && (
          <span
            className="meter-band"
            style={{ left: pct(bandLo), width: `calc(${pct(bandHi)} - ${pct(bandLo)})` }}
          />
        )}
        <span className="meter-fill" style={{ width: pct(value), background: color }} />
        {mark != null && <span className="meter-mark" style={{ left: pct(mark) }} />}
      </div>
      {note && <span className="meter-note">{note}</span>}
    </div>
  );
}

// Info-Bubble mit Metrik-Erklärung.
export function InfoDot({ text }) {
  return (
    <span className="infodot" tabIndex={0} onClick={(e) => e.stopPropagation()}>
      <span className="infodot-i">i</span>
      <span className="infodot-pop">{text}</span>
    </span>
  );
}

// Zeitraum-Filter: EIN Band pro View, scoped alles darunter.
export function RangePicker({ value, onChange, options = [7, 14, 30, 90] }) {
  return (
    <div className="range" role="group" aria-label="Zeitraum" onClick={(e) => e.stopPropagation()}>
      {options.map((r) => (
        <button
          key={r}
          type="button"
          className={r === value ? "active" : ""}
          aria-pressed={r === value}
          onClick={() => onChange(r)}
        >
          {r === 7 ? "Woche" : `${r}T`}
        </button>
      ))}
    </div>
  );
}

export function BackBar({ onBack, title, right }) {
  return (
    <div className="detail-bar">
      <button type="button" className="btn" onClick={onBack}>
        ← Zurück
      </button>
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

const PRIORITY_ICON = { high: "⚑", medium: "△", good: "✓", info: "·" };

export function Recommendation({ rec }) {
  const tone = PRIORITY_TONE[rec.priority] || "neutral";
  return (
    <div className="rec">
      <div className="rec-head">
        <Chip tone={tone}>{PRIORITY_ICON[rec.priority] || "·"}</Chip>
        <strong>{rec.title}</strong>
      </div>
      <p className="rec-detail">{rec.detail}</p>
      {rec.source && <span className="rec-source">{rec.source}</span>}
    </div>
  );
}
