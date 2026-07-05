import Sparkline from "./Sparkline.jsx";
import { num } from "./format.js";

// Compact, polished tile for secondary metrics.
export default function MetricTile({ title, value, unit, decimals = 0, delta, goodUp = true, spark = [], color = "#60a5fa", onOpen }) {
  const deltaCls =
    delta == null || delta === 0
      ? "tile-delta neutral"
      : (delta > 0) === goodUp
      ? "tile-delta good"
      : "tile-delta bad";
  const deltaTxt = delta == null ? null : `${delta > 0 ? "▲" : delta < 0 ? "▼" : "▬"} ${Math.abs(delta)}`;
  return (
    <div className="tile clickable" onClick={onOpen}>
      <div className="tile-top">
        <span className="tile-title">{title}</span>
        {deltaTxt && <span className={deltaCls}>{deltaTxt}</span>}
      </div>
      <div className="tile-value">
        {value == null ? "–" : num(value, decimals)}
        {unit ? <span className="tile-unit">{unit}</span> : null}
      </div>
      <div className="tile-spark">
        <Sparkline values={spark} color={color} width={220} height={34} />
      </div>
    </div>
  );
}
