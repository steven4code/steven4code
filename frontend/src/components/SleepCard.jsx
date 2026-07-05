import ScoreRing from "./ScoreRing.jsx";
import Hypnogram from "./Hypnogram.jsx";
import { Chip } from "./ui.jsx";
import { hm, num, deltaText, deltaClass } from "./format.js";

const STAGE_COLOR = { deep: "#6366f1", rem: "#a78bfa", light: "#38bdf8", awake: "#475069" };

function StageBar({ deep, rem, light, awake }) {
  const total = (deep || 0) + (rem || 0) + (light || 0) + (awake || 0);
  if (!total) return null;
  const seg = (v, cls) =>
    v ? <span className={`seg ${cls}`} style={{ width: `${(v / total) * 100}%` }} /> : null;
  return (
    <div className="stagebar">
      {seg(deep, "deep")}{seg(rem, "rem")}{seg(light, "light")}{seg(awake, "awake")}
    </div>
  );
}

// WHOOP-style stage row: actual bar + highlighted science-based target band.
function StageRow({ label, stage, actual, lo, hi, lowerIsBetter = false }) {
  const max = Math.max(actual || 0, hi || 0) * 1.3 || 1;
  const a = (actual || 0);
  const pct = (v) => `${Math.max(0, Math.min(100, (v / max) * 100))}%`;
  const inRange = lowerIsBetter ? a <= hi : a >= lo && a <= hi * 1.4;
  const below = !lowerIsBetter && a < lo;
  const tone = inRange ? "good" : below ? "warn" : lowerIsBetter ? "bad" : "neutral";
  const tgt = lowerIsBetter ? `Ziel < ${hm(hi)}` : `Ziel ${hm(lo)}–${hm(hi)}`;
  return (
    <div className="strow">
      <div className="strow-head">
        <span><i className="dot" style={{ background: STAGE_COLOR[stage] }} /> {label}</span>
        <span className="strow-val">{hm(actual)} <small>{tgt}</small></span>
      </div>
      <div className="strow-track">
        {!lowerIsBetter && lo != null && (
          <span className="strow-band" style={{ left: pct(lo), width: `calc(${pct(hi)} - ${pct(lo)})` }} />
        )}
        {lowerIsBetter && (
          <span className="strow-band ok" style={{ left: 0, width: pct(hi) }} />
        )}
        <span className="strow-fill" style={{ width: pct(a), background: STAGE_COLOR[stage] }} />
        <span className={`strow-flag ${tone}`} />
      </div>
    </div>
  );
}

export default function SleepCard({ card, onOpen }) {
  const t = card.trend || {};
  const st = card.stage_targets;
  return (
    <div className="card clickable" onClick={onOpen}>
      <div className="card-head">
        <h2>Schlaf · Phasen & Ziele</h2>
        <div className="head-right">
          <span className={deltaClass(t.delta, true)}>{deltaText(t.delta)}</span>
          <span className="open">Details →</span>
        </div>
      </div>

      <div className="card-body">
        <ScoreRing value={card.score} label="Score" />
        <div className="metrics">
          <div className="sri-chip">
            <Chip tone={card.sri >= 80 ? "good" : card.sri >= 60 ? "warn" : "bad"}>
              Regularität SRI {num(card.sri, 0)}
            </Chip>
          </div>
          <div className="metric">
            <span className="metric-label">Dauer / Bedarf</span>
            <span className="metric-value">{hm(card.minutes)} <small>/ {hm(card.need_min)}</small></span>
          </div>
          <div className="metric">
            <span className="metric-label">Effizienz · Defizit (14T)</span>
            <span className="metric-value">{num(card.efficiency, 0)}% <small>· {hm(card.debt_min)}</small></span>
          </div>
        </div>
      </div>

      {card.stages ? (
        <div className="hypno-wrap">
          <span className="metric-label">Schlafverlauf (Phasen über die Nacht)</span>
          <Hypnogram stages={card.stages} />
        </div>
      ) : (
        <div className="stagebar-wrap"><StageBar deep={card.deep_minutes} rem={card.rem_minutes} light={card.light_minutes} awake={card.awake_minutes} /></div>
      )}

      {st && (
        <div className="stagetargets">
          <StageRow label="Tiefschlaf" stage="deep" actual={card.deep_minutes} lo={st.deep.lo} hi={st.deep.hi} />
          <StageRow label="REM" stage="rem" actual={card.rem_minutes} lo={st.rem.lo} hi={st.rem.hi} />
          <StageRow label="Leichtschlaf" stage="light" actual={card.light_minutes} lo={st.light.lo} hi={st.light.hi} />
          <StageRow label="Wach (WASO)" stage="awake" actual={card.awake_minutes} hi={st.awake.hi} lowerIsBetter />
          {st.load_factor > 0.05 && (
            <span className="stagetargets-note">Tiefschlaf-Ziel an deine jüngste Trainingslast angepasst (mehr Last → mehr SWS-Bedarf).</span>
          )}
        </div>
      )}
    </div>
  );
}
