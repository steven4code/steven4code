import ScoreRing from "./ScoreRing.jsx";
import TrendChart from "./TrendChart.jsx";
import { num, deltaText, deltaClass } from "./format.js";

export default function RecoveryCard({ card, series }) {
  const t = card.trend || {};
  return (
    <div className="card span-2">
      <div className="card-head">
        <h2>Erholung</h2>
        <span className={deltaClass(t.delta, true)}>{deltaText(t.delta)}</span>
      </div>
      <div className="card-body recovery-body">
        <ScoreRing value={card.score} label={card.label} />
        <div className="metrics">
          <div className="metric">
            <span className="metric-label">HRV (RMSSD)</span>
            <span className="metric-value">
              {num(card.hrv_rmssd, 1)} <small>ms</small>
            </span>
            <span className="metric-sub">
              Baseline {num(card.hrv_baseline, 1)} · z {num(card.hrv_z, 2)}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Ruhepuls</span>
            <span className="metric-value">
              {num(card.resting_hr, 1)} <small>bpm</small>
            </span>
            <span className="metric-sub">
              Baseline {num(card.rhr_baseline, 1)} · z {num(card.rhr_z, 2)}
            </span>
          </div>
        </div>
      </div>
      {card.status === "insufficient_data" && (
        <p className="hint">Noch zu wenige Tage für eine stabile Baseline.</p>
      )}
      <TrendChart data={series} dataKey="recovery_score" color="#34d399" domain={[0, 100]} />
    </div>
  );
}
