import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";
import { InfoDot } from "./ui.jsx";
import { num, deltaText, deltaClass } from "./format.js";

const fmtDate = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };
const recColor = (s) => (s == null ? "#3a3a44" : s >= 66 ? "#16ec06" : s >= 40 ? "#ffde00" : "#ff2d55");

const INFO = {
  hrv: "Herzfrequenzvariabilität (RMSSD) aus dem Nachtschlaf – Aktivität deines Erholungsnervs (Parasympathikus). Höher = besser erholt. Gemessen über die Schlagintervalle im Schlaf; bewertet als ln(RMSSD)-Z-Wert gegen deinen persönlichen 60-Tage-Schnitt (±SWC).",
  hr: "Niedrigster Ruhepuls im Schlaf. Sinkt mit Fitness und guter Erholung, steigt bei Stress, hoher Last oder Krankheit. Verglichen mit deinem 60-Tage-Schnitt (Z-Wert).",
  core: "Autonomer Kern (0–100): kombiniert HFV (80 %) und Ruhe-HF (20 %) relativ zu deiner Baseline. Bildet den Kern der Erholung – der finale Score = Kern × Schlaf-Modifikator (0,70–1,00).",
};

function insightFor(c) {
  if (c.flags && c.flags.length) return `⚠ ${c.flags[0]} – heute Erholung priorisieren.`;
  if (c.within_normal === false) return "HFV außerhalb deines Normbereichs – das Nervensystem steht unter Last.";
  if (c.score == null) return "Baseline wird aufgebaut – nach ~2 Wochen voll aussagekräftig.";
  if (c.score >= 66) return "Gut erholt – grünes Licht für intensive Reize (Intervalle, Tempo).";
  if (c.score >= 40) return "Moderat erholt – Qualität ok, aber heute kein Maximalreiz.";
  return "Belastet – locker bewegen oder ruhen; harte Einheiten verschieben.";
}

function Ring({ value, color, size = 168, stroke = 14 }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = value == null ? 0 : Math.max(0, Math.min(1, value / 100));
  const dash = c * pct;
  return (
    <div className="rh-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#23232c" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`} transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.7s ease", filter: `drop-shadow(0 0 7px ${color}55)` }}
        />
      </svg>
      <div className="ring-center">
        <div className="rh-num" style={{ color }}>{value == null ? "–" : Math.round(value)}<span className="rh-unit">%</span></div>
      </div>
    </div>
  );
}

function Stat({ label, info, value, baseline, delta, goodUp = true }) {
  return (
    <div className="rh-stat">
      <span className="rh-stat-label">{label} <InfoDot text={info} /></span>
      <span className="rh-stat-value">{value}</span>
      <span className="rh-stat-sub">
        {baseline != null && <>Ø {baseline} </>}
        {delta != null && <span className={deltaClass(delta, goodUp)}>{deltaText(delta)}</span>}
      </span>
    </div>
  );
}

export default function RecoveryHero({ card, onOpen }) {
  if (!card) return null;
  const col = recColor(card.score);
  const t = card.trend || {};
  const hrvDelta = (card.hrv_rmssd != null && card.hrv_baseline != null) ? Math.round((card.hrv_rmssd - card.hrv_baseline) * 10) / 10 : null;
  const hrDelta = (card.hr != null && card.hr_baseline != null) ? Math.round((card.hr - card.hr_baseline) * 10) / 10 : null;

  return (
    <div className="card clickable rec-hero" onClick={onOpen}>
      <div className="card-head">
        <h2>Erholung</h2>
        <div className="head-right">
          <span className={deltaClass(t.delta, true)}>{deltaText(t.delta)}</span>
          <span className="open">Details →</span>
        </div>
      </div>

      <div className="rh-grid">
        <div className="rh-left">
          <Ring value={card.score} color={col} />
          <div className="rh-label" style={{ color: col }}>{card.label}</div>
        </div>

        <div className="rh-mid">
          <p className="rh-insight">{insightFor(card)}</p>
          <div className="rh-stats three">
            <Stat label="HFV (RMSSD)" info={INFO.hrv} value={`${num(card.hrv_rmssd, 0)} ms`} baseline={card.hrv_baseline != null ? `${num(card.hrv_baseline, 0)} ms` : null} delta={hrvDelta} goodUp />
            <Stat label="Ruhepuls" info={INFO.hr} value={`${num(card.hr, 0)} bpm`} baseline={card.hr_baseline != null ? `${num(card.hr_baseline, 0)} bpm` : null} delta={hrDelta} goodUp={false} />
            <Stat label="Autonomer Kern" info={INFO.core} value={num(card.core, 0)} baseline={null} delta={null} />
          </div>
        </div>

        <div className="rh-trend">
          <span className="rh-trend-cap">Verlauf</span>
          <ResponsiveContainer width="100%" height={156}>
            <AreaChart data={card.series} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="rhGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={col} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={col} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1d1d24" vertical={false} />
              <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 10 }} minTickGap={30} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fill: "#7b8499", fontSize: 10 }} width={34} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} formatter={(v) => [Math.round(v), "Erholung"]} />
              <ReferenceLine y={66} stroke="#16ec0644" strokeDasharray="4 4" />
              <ReferenceLine y={40} stroke="#ff2d5544" strokeDasharray="4 4" />
              <Area type="monotone" dataKey="recovery_score" stroke={col} strokeWidth={2.5} fill="url(#rhGrad)" dot={false} connectNulls />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
