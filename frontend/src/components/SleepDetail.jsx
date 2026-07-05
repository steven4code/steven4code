import { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";
import { getSleepDetail } from "../api.js";
import { Bar, BackBar, Kpi, RangePicker } from "./ui.jsx";
import { hm, num } from "./format.js";

const fmtDate = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };

const LABELS = {
  regularity: "Regularität (SRI)", duration: "Dauer", efficiency: "Effizienz",
  deep: "Tiefschlaf", rem: "REM", restfulness: "Ruhe (WASO)", latency: "Einschlaflatenz",
};

export default function SleepDetail({ onBack }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(90);
  useEffect(() => { setData(null); getSleepDetail(days).then(setData).catch((e) => setErr(e.message)); }, [days]);

  if (err) return <div className="detail"><BackBar onBack={onBack} title="Schlaf" right={<RangePicker value={days} onChange={setDays} />} /><div className="error">{err}</div></div>;
  if (!data) return <div className="detail"><BackBar onBack={onBack} title="Schlaf" right={<RangePicker value={days} onChange={setDays} />} /><div className="loading">Lade…</div></div>;
  const comps = data.latest_components || {};

  return (
    <div className="detail">
      <BackBar onBack={onBack} title="Schlaf – Detail" right={<RangePicker value={days} onChange={setDays} />} />
      <div className="method-box">
        Gewichteter Score; <b>Regularität (SRI)</b> dominiert (laut Studien stärkster Outcome-Prädiktor).
        Schlafbedarf automatisch (auf 8 h gedeckelt), Defizit über 14 Tage.
      </div>

      <div className="kpis">
        <Kpi label="Score heute" value={num(data.series.at(-1)?.sleep_score, 0)} />
        <Kpi label="SRI" value={num(data.latest_sri, 0)} sub="Regularität" />
        <Kpi label="Bedarf" value={hm(data.latest_need)} />
        <Kpi label="Defizit (14T)" value={hm(data.debt_min)} />
      </div>

      <h3>Komponenten heute (mit Gewichten)</h3>
      <div className="comp-list">
        {Object.keys(LABELS).map((k) => (
          <div className="comp" key={k}>
            <div className="comp-top">
              <span>{LABELS[k]} <small>{Math.round((data.weights[k] || 0) * 100)}%</small></span>
              <span>{comps[k] == null ? "–" : num(comps[k], 0)}</span>
            </div>
            <Bar value={comps[k] || 0} color="#a78bfa" />
          </div>
        ))}
      </div>

      <h3>Verlauf: Score & SRI</h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: -8, bottom: 0 }}>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={30} />
          <YAxis domain={[0, 100]} tick={{ fill: "#7b8499", fontSize: 11 }} width={34} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="sleep_score" name="Schlaf-Score" stroke="#a78bfa" strokeWidth={2.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="sri" name="SRI" stroke="#f0abfc" strokeWidth={1.4} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>

      <h3>Schlafdauer & Phasen</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: -8, bottom: 0 }}>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={30} />
          <YAxis tick={{ fill: "#7b8499", fontSize: 11 }} width={34} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="minutes" name="Gesamt (min)" stroke="#60a5fa" strokeWidth={2} dot={false} connectNulls />
          <Line type="monotone" dataKey="deep_minutes" name="Tief" stroke="#4f46e5" strokeWidth={1.2} dot={false} connectNulls />
          <Line type="monotone" dataKey="rem_minutes" name="REM" stroke="#a78bfa" strokeWidth={1.2} dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
