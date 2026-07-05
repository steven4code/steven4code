import Hypnogram from "./Hypnogram.jsx";
import { BulletMeter, CardButton, CardHead, Chip } from "./ui.jsx";
import { hm, num, deltaText, deltaClass } from "./format.js";
import { STAGE } from "../theme.js";

// Phasen-Ziel als Bullet-Meter: Ist-Balken + wissenschaftliches Zielband
// (SWS-Rebound nach Last: Driver & Taylor 2000 — Bänder kommen aus sleep.py).
function StageMeter({ label, stage, actual, lo, hi, lowerIsBetter = false }) {
  const max = Math.max(actual || 0, hi || 0) * 1.3 || 1;
  const a = actual || 0;
  const inRange = lowerIsBetter ? a <= hi : a >= lo;
  const tgt = lowerIsBetter ? `Ziel < ${hm(hi)}` : `Ziel ${hm(lo)}–${hm(hi)}`;
  return (
    <BulletMeter
      label={label}
      labelDot={STAGE[stage]}
      value={a}
      valueText={hm(actual)}
      targetText={`${tgt} · ${inRange ? "✓ erfüllt" : lowerIsBetter ? "△ drüber" : "△ drunter"}`}
      max={max}
      bandLo={lowerIsBetter ? 0 : lo}
      bandHi={hi}
      color={STAGE[stage]}
    />
  );
}

export default function SleepCard({ card, onOpen }) {
  const t = card.trend || {};
  const st = card.stage_targets;
  const sriTone = card.sri >= 80 ? "good" : card.sri >= 60 ? "warn" : "bad";
  const debtBig = card.debt_min != null && card.debt_min > 90;

  return (
    <CardButton onOpen={onOpen} label="Schlaf — Details">
      <CardHead
        title="Schlaf · Letzte Nacht"
        right={<span className={deltaClass(t.delta, true)}>{deltaText(t.delta)}</span>}
      />

      <div className="stats-row">
        <div className="stat">
          <span className="stat-label">Dauer / Bedarf</span>
          <span className="stat-value">
            {hm(card.minutes)} <small>/ {hm(card.need_min)}</small>
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Effizienz</span>
          <span className="stat-value">{num(card.efficiency, 0)}%</span>
        </div>
        <div className="stat">
          <span className="stat-label">Defizit (14 T)</span>
          <span className="stat-value">{hm(card.debt_min)}</span>
          {debtBig && <span className="stat-sub">baut sich über Tage ab</span>}
        </div>
        <div className="stat">
          <span className="stat-label">Regularität</span>
          <span className="stat-value">
            <Chip tone={sriTone}>SRI {num(card.sri, 0)}</Chip>
          </span>
        </div>
      </div>

      {card.stages && (
        <div className="hypno-wrap">
          <span className="hypno-cap">Schlafverlauf — Phasen über die Nacht</span>
          <Hypnogram stages={card.stages} />
        </div>
      )}

      {st && (
        <div className="meter-list">
          <StageMeter label="Tiefschlaf" stage="deep" actual={card.deep_minutes} lo={st.deep.lo} hi={st.deep.hi} />
          <StageMeter label="REM" stage="rem" actual={card.rem_minutes} lo={st.rem.lo} hi={st.rem.hi} />
          <StageMeter label="Leichtschlaf" stage="light" actual={card.light_minutes} lo={st.light.lo} hi={st.light.hi} />
          <StageMeter label="Wach (WASO)" stage="awake" actual={card.awake_minutes} hi={st.awake.hi} lowerIsBetter />
          {st.load_factor > 0.05 && (
            <span className="meter-list-note">
              Tiefschlaf-Ziel an die jüngste Trainingslast angepasst (mehr Last → mehr SWS-Bedarf).
            </span>
          )}
        </div>
      )}
    </CardButton>
  );
}
