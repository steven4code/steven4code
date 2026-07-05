import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";
import StrainGauge from "./StrainGauge.jsx";
import { Chip } from "./ui.jsx";
import { num } from "./format.js";

const STATUS_TONE = { under: "good", optimal: "good", over: "warn" };
const STATUS_COLOR = { under: "#38bdf8", optimal: "#34d399", over: "#f59e0b" };

export default function StrainPanel({ card, onOpen }) {
  if (!card || card.empty) return null;
  const color = STATUS_COLOR[card.status] || "#f59e0b";
  return (
    <div className="card strain-panel clickable" onClick={onOpen}>
      <div className="card-head">
        <h2>Tages-Belastung · Strain</h2>
        <span className="open">Details →</span>
      </div>

      <div className="strain-body">
        <div className="strain-gauge-wrap">
          <StrainGauge value={card.current} max={card.scale_max} low={card.target_low} high={card.target_high} opt={card.target_opt} color={color} />
          <Chip tone={STATUS_TONE[card.status]}>{card.label}</Chip>
          <div className="strain-range">Ziel {num(card.target_low, 0)}–{num(card.target_high, 0)} · optimal {num(card.target_opt, 0)}</div>
        </div>

        <div className="strain-mid">
          <div className="strain-budget">
            <span className="metric-label">Rest-Budget bis Obergrenze</span>
            <span className="metric-value">{num(card.remaining, 0)} <small>Punkte</small></span>
          </div>
          {card.options.length > 0 ? (
            <div className="strain-options">
              <span className="metric-label">Heute noch möglich</span>
              <div className="opt-chips">
                {card.options.map((o) => (
                  <span key={o.zone} className="opt-chip">~{o.minutes}′ <b>{o.name.split(" ")[0]}</b></span>
                ))}
              </div>
              <span className="opt-hint">(jeweils alternativ – bis zur Obergrenze)</span>
            </div>
          ) : (
            <div className="strain-options"><span className="opt-hint">Tagesziel erreicht – Fokus auf Erholung.</span></div>
          )}
          {card.today_sessions.length > 0 && (
            <div className="strain-sessions">
              <span className="metric-label">Heute</span>
              {card.today_sessions.map((s, i) => (
                <span key={i} className="sess">{s.type === "padel" ? "Padel" : "Lauf"} {s.duration_min}′ · +{num(s.strain_contrib, 0)}</span>
              ))}
            </div>
          )}
        </div>

        <div className="strain-chart">
          <span className="metric-label">Verlauf heute (projiziert ab {card.now_hour}:00)</span>
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={card.intraday} margin={{ top: 6, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="strainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#222838" vertical={false} />
              <XAxis dataKey="hour" tickFormatter={(h) => `${h}h`} tick={{ fill: "#7b8499", fontSize: 10 }} />
              <YAxis domain={[0, card.scale_max]} tick={{ fill: "#7b8499", fontSize: 10 }} width={28} />
              <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={(h) => `${h}:00`} />
              <ReferenceLine y={card.target_high} stroke="#34d399" strokeDasharray="3 3" />
              <ReferenceLine y={card.target_low} stroke="#34d39966" strokeDasharray="3 3" />
              <ReferenceLine x={card.now_hour} stroke="#e6e9ef" strokeOpacity={0.5} />
              <Area type="monotone" dataKey="strain" stroke={color} strokeWidth={2} fill="url(#strainGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
