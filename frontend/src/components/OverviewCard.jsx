import Sparkline from "./Sparkline.jsx";

// One Bevel-style row: title, big value, one-line insight, sparkline, tap arrow.
export default function OverviewCard({
  title,
  value,
  unit,
  sub,
  spark = [],
  color = "#60a5fa",
  accent,
  delta,
  goodUp = true,
  onOpen,
}) {
  const deltaCls =
    delta == null || delta === 0
      ? "ov-delta neutral"
      : (delta > 0) === goodUp
      ? "ov-delta good"
      : "ov-delta bad";
  const deltaTxt =
    delta == null ? null : `${delta > 0 ? "▲" : delta < 0 ? "▼" : "▬"} ${Math.abs(delta)}`;

  return (
    <div className="ovcard clickable" onClick={onOpen}>
      <div className="ov-left">
        <div className="ov-title">{title}</div>
        <div className="ov-value" style={accent ? { color: accent } : undefined}>
          {value}
          {unit ? <span className="ov-unit">{unit}</span> : null}
        </div>
        {sub ? <div className="ov-sub">{sub}</div> : null}
      </div>
      <div className="ov-right">
        <Sparkline values={spark} color={color} />
        {deltaTxt ? <span className={deltaCls}>{deltaTxt}</span> : null}
      </div>
      <span className="ov-arrow">›</span>
    </div>
  );
}
