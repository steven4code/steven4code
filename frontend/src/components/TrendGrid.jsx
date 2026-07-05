import Sparkline from "./Sparkline.jsx";
import { Chip } from "./ui.jsx";
import { num, int, deltaText, deltaClass } from "./format.js";

// Trends: Stat-Tiles nach Kontrakt (Label · Wert · Delta vs. Vortag ·
// Sparkline in EINER De-Emphasis-Farbe — Identität steckt im Label,
// Richtung im Delta; Tufte-Sparklines leben von Zurückhaltung).

// Grobe Ausdauer-Bänder (nur Deskriptor, kein Alters-/Geschlechts-Perzentil).
const VO2_BANDS = [
  [55, "Exzellent"],
  [47, "Sehr gut"],
  [40, "Gut"],
  [33, "Solide"],
  [0, "Grundlegend"],
];
const vo2Band = (v) => VO2_BANDS.find(([t]) => v >= t)?.[1] ?? "–";

function Tile({ extra, onOpen }) {
  const e = extra;
  const isInt = e.decimals === 0;
  const val = e.value == null ? "–" : isInt ? int(e.value) : num(e.value, e.decimals);
  const series = (e.series || []).map((x) => x.v);
  // Delta zuerst auf Anzeige-Präzision runden — was als „0" erscheint,
  // darf nicht als Anstieg/Abfall gefärbt sein.
  const d = e.delta == null ? null : Number(e.delta.toFixed(e.decimals));
  const deltaStr =
    d == null ? null : isInt ? `${d > 0 ? "▲" : d < 0 ? "▼" : "±"} ${int(Math.abs(d))}` : deltaText(d, e.decimals);
  return (
    <button type="button" className="tile" onClick={() => onOpen(e)} aria-label={`${e.title} — Details`}>
      <div className="tile-top">
        <span className="tile-title">{e.title}</span>
        {deltaStr != null && (
          <span className={`tile-delta ${deltaClass(d, e.good_up).replace("delta ", "")}`}>
            {deltaStr}
          </span>
        )}
      </div>
      <div className="tile-value">
        {val}
        {e.unit && <small>{e.unit}</small>}
      </div>
      {e.key === "vo2max" && e.value != null && (
        <span className="tile-band">
          <Chip tone="neutral">{vo2Band(e.value)}</Chip>
        </span>
      )}
      <div className="tile-spark">
        <Sparkline values={series} width={200} height={30} />
      </div>
    </button>
  );
}

export default function TrendGrid({ extras, onOpen }) {
  if (!extras || !extras.length) return null;
  return (
    <>
      <h2 className="section-label">Trends</h2>
      <div className="tilegrid">
        {extras.map((e) => (
          <Tile key={e.key} extra={e} onOpen={onOpen} />
        ))}
      </div>
    </>
  );
}
