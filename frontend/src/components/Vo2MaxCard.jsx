import TrendChart from "./TrendChart.jsx";
import { num, deltaText, deltaClass } from "./format.js";

export default function Vo2MaxCard({ card, series }) {
  const t = card.trend || {};
  return (
    <div className="card span-2">
      <div className="card-head">
        <h2>VO₂max</h2>
        <span className={deltaClass(t.delta, true)}>{deltaText(t.delta)}</span>
      </div>
      <div className="card-body vo2-body">
        <div className="vo2-value">
          {num(card.value, 1)}
          <small>ml/kg/min</small>
        </div>
        <div className="vo2-label">{card.label}</div>
      </div>
      <TrendChart data={series} dataKey="vo2max" color="#60a5fa" />
    </div>
  );
}
