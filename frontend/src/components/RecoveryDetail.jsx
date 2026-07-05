import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";
import { getRecoveryDetail } from "../api.js";
import { BackBar, Kpi, RangePicker } from "./ui.jsx";
import { num } from "./format.js";

const fmtDate = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };
const recColor = (s) => (s == null ? "#8a8a96" : s >= 66 ? "#16ec06" : s >= 40 ? "#ffde00" : "#ff2d55");

function insightFor(l) {
  if (l.flags && l.flags.length) return `⚠ ${l.flags.join(" · ")} – heute Erholung priorisieren.`;
  if (l.within_normal === false) return "HFV außerhalb deines Normbereichs – das Nervensystem steht unter Last.";
  if (l.score == null) return "Noch keine 60-Tage-Baseline – Score wird nach ~2 Wochen aussagekräftig.";
  if (l.score >= 66) return "Gut erholt – grünes Licht für intensive Reize (Intervalle, Tempo).";
  if (l.score >= 40) return "Moderat erholt – Qualität ok, aber heute kein Maximalreiz.";
  return "Belastet – locker bewegen oder ruhen; harte Einheiten verschieben.";
}

export default function RecoveryDetail({ onBack }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(90);
  useEffect(() => { setData(null); getRecoveryDetail(days).then(setData).catch((e) => setErr(e.message)); }, [days]);

  if (err) return <div className="detail"><BackBar onBack={onBack} title="Erholung" right={<RangePicker value={days} onChange={setDays} />} /><div className="error">{err}</div></div>;
  if (!data) return <div className="detail"><BackBar onBack={onBack} title="Erholung" right={<RangePicker value={days} onChange={setDays} />} /><div className="loading">Lade…</div></div>;
  const l = data.latest;
  const col = recColor(l.score);
  const sleepDrag = l.sleep_factor != null && l.sleep_factor < 0.92;

  return (
    <div className="detail">
      <BackBar onBack={onBack} title="Erholung – Detail" right={<RangePicker value={days} onChange={setDays} />} />

      <div className="insight-hero">
        <div className="ih-score" style={{ color: col }}>{num(l.score, 0)}<small>%</small></div>
        <div className="ih-text">
          <div className="ih-headline">{insightFor(l)}</div>
          <div className="ih-sub">
            Autonomer Kern {num(l.core, 0)} (HFV {Math.round((data.core_weights?.hrv || 0.8) * 100)}% · HF {Math.round((data.core_weights?.hr || 0.2) * 100)}%)
            {l.sleep_factor != null && <> × Schlaf-Faktor {num(l.sleep_factor, 2)}{sleepDrag && " — Schlaf bremst"}</>}
          </div>
        </div>
      </div>

      <div className="kpis">
        <Kpi label="Autonomer Kern" value={num(l.core, 0)} />
        <Kpi label="Schlaf-Faktor" value={`×${num(l.sleep_factor, 2)}`} />
        <Kpi label="HFV (lnRMSSD)" value={num(l.ln_rmssd, 2)} sub={`Baseline ${num(l.ln_baseline, 2)} ±${num(l.swc, 2)}`} />
        <Kpi label="HFV-Variabilität (CV 7T)" value={l.cv7 == null ? "–" : `${num(l.cv7, 0)}%`} sub={l.within_normal === false ? "außerhalb Norm" : "im Normbereich"} />
      </div>

      <h3>Erholung · {days === 7 ? "Woche" : `${days} Tage`}</h3>
      <ResponsiveContainer width="100%" height={230}>
        <AreaChart data={data.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#16ec06" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#16ec06" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={36} />
          <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fill: "#7b8499", fontSize: 11 }} width={34} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} formatter={(v) => [Math.round(v), "Erholung"]} />
          <ReferenceLine y={66} stroke="#16ec0655" strokeDasharray="4 4" />
          <ReferenceLine y={40} stroke="#ff2d5555" strokeDasharray="4 4" />
          <Area type="monotone" dataKey="recovery_score" stroke="#16ec06" strokeWidth={2.5} fill="url(#recGrad)" dot={false} connectNulls />
        </AreaChart>
      </ResponsiveContainer>

      <h3>HFV-Trend (7-Tage-Schnitt)</h3>
      <ResponsiveContainer width="100%" height={170}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={36} />
          <YAxis tick={{ fill: "#7b8499", fontSize: 11 }} width={30} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} formatter={(v) => [Math.round(v), "RMSSD"]} />
          <Line type="monotone" dataKey="rmssd" stroke="#3b4660" strokeWidth={1} dot={false} connectNulls />
          <Line type="monotone" dataKey="rolling7_rmssd" stroke="#16ec06" strokeWidth={2.5} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
