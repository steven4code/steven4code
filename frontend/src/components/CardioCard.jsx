import { Recommendation } from "./ui.jsx";
import { hm, num } from "./format.js";

const SYS_COLOR = { basis: "#16ec06", grauzone: "#ffde00", intensiv: "#ff2d55" };

function SysRow({ s }) {
  const color = SYS_COLOR[s.key];
  const max = Math.max(s.actual_min, s.target_hi) * 1.25 || 1;
  const pct = (v) => `${Math.max(0, Math.min(100, (v / max) * 100))}%`;
  const tone = s.status === "ok" ? "good" : s.status === "under" ? "warn" : "neutral";
  return (
    <div className="strow">
      <div className="strow-head">
        <span><i className="dot" style={{ background: color }} /> {s.label} <small>{s.zones}</small></span>
        <span className="strow-val">{hm(s.actual_min)} <small>Ziel {hm(s.target_lo)}–{hm(s.target_hi)}</small></span>
      </div>
      <div className="strow-track">
        <span className="strow-band" style={{ left: pct(s.target_lo), width: `calc(${pct(s.target_hi)} - ${pct(s.target_lo)})` }} />
        <span className="strow-fill" style={{ width: pct(s.actual_min), background: color }} />
        <span className={`strow-flag ${tone}`} />
      </div>
    </div>
  );
}

export default function CardioCard({ card, onOpen }) {
  if (!card || card.empty) {
    return (
      <div className="card clickable" onClick={onOpen}>
        <div className="card-head"><h2>Cardio Load · Trainingsverteilung</h2><span className="open">Details →</span></div>
        <p className="hint">Noch keine Trainingsdaten.</p>
      </div>
    );
  }
  const top = card.recommendations && card.recommendations[0];
  const ratioWarn = card.load_ratio_status && card.load_ratio_status !== "ok" && card.load_ratio_status !== "unknown";
  const m = card.model || {};

  return (
    <div className="card clickable cardio-card" onClick={onOpen}>
      <div className="card-head">
        <h2>Cardio Load · Trainingsverteilung</h2>
        <span className="open">Details →</span>
      </div>

      <span className="cardio-cap">
        Lauf-spezifische Systemlast · diese Woche vs. Ziel ({m.basis}/{m.grauzone}/{m.intensiv} für {card.goal})
      </span>

      <div className="stagetargets">
        {(card.systems || []).map((s) => <SysRow key={s.key} s={s} />)}
      </div>

      {top && <div className="cardio-rec"><Recommendation rec={top} /></div>}

      <div className="cardio-foot">
        <span>
          {card.week.sessions} Einh. · {card.week.runs} Lauf / {card.week.padel} Padel
          {card.padel_share_pct > 0 && <> · Padel-Anteil {card.padel_share_pct}% <small>(anteilig angerechnet)</small></>}
        </span>
        <span className={`load-pill ${ratioWarn ? "warn" : "ok"}`}>
          Lasttrend {ratioWarn ? (card.load_ratio_status === "high" ? "steigt schnell ↑" : "niedrig ↓") : "stabil"}
        </span>
      </div>
    </div>
  );
}
