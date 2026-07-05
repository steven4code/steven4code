import Sparkline from "./Sparkline.jsx";
import { num } from "./format.js";

// Coarse general adult-male endurance bands (descriptor only, not an age/sex
// percentile). The headline insight below is derived from the personal trend +
// the user's 5-10k goal, which is the scientifically defensible signal.
const BANDS = [
  [55, "Exzellent", "#16ec06"],
  [47, "Sehr gut", "#34d399"],
  [40, "Gut", "#7dd3fc"],
  [33, "Solide", "#fbbf24"],
  [0, "Grundlegend", "#f87171"],
];
function band(v) {
  for (const [t, l, c] of BANDS) if (v >= t) return [l, c];
  return ["–", "#8a8a96"];
}

export default function Vo2Card({ extra, onOpen }) {
  const v = extra?.value;
  const series = (extra?.series || []).map((x) => x.v);
  const trend = extra?.delta;
  const [lbl, col] = v != null ? band(v) : ["–", "#8a8a96"];

  const insight =
    v == null
      ? "Noch keine VO₂max-Schätzung – nach einigen Läufen verfügbar."
      : trend != null && trend > 0.3
      ? "Steigend – deine aerobe Grundlage trägt Früchte. Kurs halten."
      : trend != null && trend < -0.3
      ? "Leicht rückläufig – mehr ruhige Z2-Grundlage und Erholung einplanen."
      : "Stabil. VO₂max ist der stärkste physiologische Prädiktor deiner 5–10 km-Zeit.";

  return (
    <div className="card clickable vo2card" onClick={onOpen}>
      <div className="card-head">
        <h2>VO₂max · Cardio-Fitness</h2>
        <span className="open">Details →</span>
      </div>
      <div className="vo2-row">
        <div className="vo2-main">
          <div className="vo2-num" style={{ color: col }}>
            {num(v, 1)}<small>ml/kg/min</small>
          </div>
          <span className="vo2-band" style={{ color: col, borderColor: `${col}55` }}>{lbl}</span>
        </div>
        <div className="vo2-spark">
          <Sparkline values={series} color={col} width={260} height={48} />
          <span className="vo2-spark-cap">{series.length}-Tage-Trend</span>
        </div>
      </div>
      <p className="vo2-insight">{insight}</p>
    </div>
  );
}
