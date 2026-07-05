import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";
import { getStrainDetail } from "../api.js";
import { BackBar, Kpi, RangePicker } from "./ui.jsx";
import { num } from "./format.js";

const fmtDate = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };

export default function StrainDetail({ onBack }) {
  const [c, setC] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(60);
  useEffect(() => { setC(null); getStrainDetail(days).then(setC).catch((e) => setErr(e.message)); }, [days]);

  if (err) return <div className="detail"><BackBar onBack={onBack} title="Belastung" right={<RangePicker value={days} onChange={setDays} />} /><div className="error">{err}</div></div>;
  if (!c || c.empty) return <div className="detail"><BackBar onBack={onBack} title="Belastung" right={<RangePicker value={days} onChange={setDays} />} /><div className="loading">Lade…</div></div>;

  const insight =
    c.status === "over"
      ? "Tagesziel erreicht – weitere harte Reize erhöhen jetzt das Überlastungsrisiko. Fokus auf Erholung."
      : c.status === "optimal"
      ? "Im optimalen Belastungsfenster für deine heutige Erholung – gut dosiert."
      : `Noch Raum: ${num(c.remaining, 0)} Punkte bis zur Obergrenze. Heute ist ein weiterer Reiz gut vertretbar.`;

  return (
    <div className="detail">
      <BackBar onBack={onBack} title="Tages-Belastung – Detail" right={<RangePicker value={days} onChange={setDays} />} />

      <div className="insight-hero">
        <div className="ih-score" style={{ color: "#00a8e8" }}>{num(c.current, 0)}<small>/100</small></div>
        <div className="ih-text">
          <div className="ih-headline">{insight}</div>
          <div className="ih-sub">Ziel {num(c.target_low, 0)}–{num(c.target_high, 0)} (optimal {num(c.target_opt, 0)}) · projiziert ganzer Tag {num(c.projected_full_day, 0)}</div>
        </div>
      </div>

      <div className="method-box">
        <b>Strain 0–100</b>, personalisiert-logarithmisch (jeder Punkt oben ist schwerer): kardiovaskuläre Last
        per <b>Banister-TRIMP</b> aus HF-Zonenzeit (Training + Ganztags-Last) – Ruhe-/Sitzzeit zählt ~0, daher
        morgens niedrig. Die Skala ist auf deine eigene 60-Tage-Lastverteilung geeicht. Ziel-Range aus
        <b> Erholung + Schlaf + chronischer Last (ACWR)</b> – erholt = mehr erlaubt, steigende Wochenlast senkt die
        Obergrenze. Rest-Budget → konkrete Zonen-Optionen.
      </div>

      <div className="kpis">
        <Kpi label="Aktuell" value={num(c.current, 0)} sub={c.label} />
        <Kpi label="Ziel-Range" value={`${num(c.target_low, 0)}–${num(c.target_high, 0)}`} sub={`optimal ${num(c.target_opt, 0)}`} />
        <Kpi label="Rest-Budget" value={num(c.remaining, 0)} />
        <Kpi label="Projiziert (ganzer Tag)" value={num(c.projected_full_day, 0)} />
        <Kpi label="Erholung" value={num(c.recovery, 0)} />
        <Kpi label="akut:chronisch" value={num(c.load_ratio, 2)} />
      </div>

      {c.options.length > 0 && (
        <>
          <h3>Heute noch möglich (jeweils alternativ)</h3>
          <div className="opt-chips big">
            {c.options.map((o) => <span key={o.zone} className="opt-chip">~{o.minutes}′ <b>{o.name}</b></span>)}
          </div>
        </>
      )}

      <h3>Verlauf heute (Akkumulation, projiziert ab {c.now_hour}:00)</h3>
      <ResponsiveContainer width="100%" height={230}>
        <AreaChart data={c.intraday} margin={{ top: 8, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="sd" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="hour" tickFormatter={(h) => `${h}h`} tick={{ fill: "#7b8499", fontSize: 11 }} />
          <YAxis domain={[0, c.scale_max]} tick={{ fill: "#7b8499", fontSize: 11 }} width={30} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={(h) => `${h}:00`} />
          <ReferenceLine y={c.target_high} stroke="#34d399" strokeDasharray="3 3" label={{ value: "Obergrenze", fill: "#34d399", fontSize: 10 }} />
          <ReferenceLine y={c.target_low} stroke="#34d39966" strokeDasharray="3 3" />
          <ReferenceLine x={c.now_hour} stroke="#e6e9ef" strokeOpacity={0.5} />
          <Area type="monotone" dataKey="strain" stroke="#f59e0b" strokeWidth={2.5} fill="url(#sd)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>

      <h3>Tägliche Belastung ({days === 7 ? "Woche" : `${days} Tage`})</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={c.series} margin={{ top: 8, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={30} />
          <YAxis domain={[0, c.scale_max]} tick={{ fill: "#7b8499", fontSize: 11 }} width={30} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} />
          <ReferenceLine y={c.target_opt} stroke="#34d39988" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="strain" stroke="#f59e0b" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
