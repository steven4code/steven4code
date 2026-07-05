import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine,
} from "recharts";
import StrainGauge from "./StrainGauge.jsx";
import { Chip } from "./ui.jsx";
import { num } from "./format.js";

const STATUS_TONE = { under: "good", optimal: "good", over: "warn" };
const STATUS_COLOR = { under: "#00a8e8", optimal: "#16ec06", over: "#ffde00" };

export default function StrainCard({ card, onOpen }) {
  if (!card || card.empty) return null;
  const color = STATUS_COLOR[card.status] || "#00a8e8";
  return (
    <div className="card clickable" onClick={onOpen}>
      <div className="card-head">
        <h2>Belastung</h2>
        <span className="open">Details →</span>
      </div>

      <div className="card-body strain-card-body">
        <StrainGauge value={card.current} max={card.scale_max} low={card.target_low} high={card.target_high} opt={card.target_opt} color={color} decimals={0} size={172} />
        <div className="metrics">
          <div className="sri-chip"><Chip tone={STATUS_TONE[card.status]}>{card.label}</Chip></div>
          <div className="metric">
            <span className="metric-label">Rest-Budget bis Obergrenze</span>
            <span className="metric-value">{num(card.remaining, 0)} <small>Punkte</small></span>
          </div>
          <div className="metric">
            <span className="metric-label">Ziel-Range (aus Erholung & Last)</span>
            <span className="metric-value">{num(card.target_low, 0)}–{num(card.target_high, 0)} <small>· opt {num(card.target_opt, 0)}</small></span>
          </div>
        </div>
      </div>

      {card.session && (
        <div className={`coach-rec tone-${card.session.tone}`}>
          <div className="cr-head">
            <span className="cr-zone">{card.session.zone}</span>
            <strong>Heute empfohlen: {card.session.headline}</strong>
          </div>
          <div className="cr-presc">{card.session.prescription}</div>
          <p className="cr-why">{card.session.rationale}</p>
          <span className="cr-source">{card.session.source}</span>
        </div>
      )}

      <div className="strain-card-chart">
        <span className="metric-label">Verlauf heute (projiziert ab {card.now_hour}:00)</span>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={card.intraday} margin={{ top: 6, right: 6, left: -22, bottom: 0 }}>
            <defs>
              <linearGradient id="scGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" tickFormatter={(h) => `${h}`} tick={{ fill: "#6b6b78", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, card.scale_max]} tick={{ fill: "#6b6b78", fontSize: 10 }} width={30} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={(h) => `${h}:00`} formatter={(v) => [Math.round(v), "Strain"]} />
            <ReferenceLine y={card.target_high} stroke="#16ec0666" strokeDasharray="3 3" />
            <ReferenceLine x={card.now_hour} stroke="#e6e9ef" strokeOpacity={0.4} />
            <Area type="monotone" dataKey="strain" stroke={color} strokeWidth={2.2} fill="url(#scGrad)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
