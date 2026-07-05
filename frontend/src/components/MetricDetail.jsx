import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { BackBar, Kpi } from "./ui.jsx";
import { num } from "./format.js";

const fmtDate = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };

// Generic detail for the simple metric cards (uses the series already loaded).
export default function MetricDetail({ extra, onBack }) {
  if (!extra) return <div className="detail"><BackBar onBack={onBack} title="Metrik" /></div>;
  const data = (extra.series || []).map((s) => ({ date: s.date, v: s.v }));
  const vals = data.map((d) => d.v).filter((v) => v != null);
  const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  const min = vals.length ? Math.min(...vals) : null;
  const max = vals.length ? Math.max(...vals) : null;
  const dec = extra.decimals ?? 0;

  return (
    <div className="detail">
      <BackBar onBack={onBack} title={extra.title} />
      {extra.insight ? <div className="method-box">{extra.insight}</div> : null}
      <div className="kpis">
        <Kpi label="Aktuell" value={`${num(extra.value, dec)} ${extra.unit}`} />
        <Kpi label="Ø (Zeitraum)" value={num(avg, dec)} />
        <Kpi label="Min" value={num(min, dec)} />
        <Kpi label="Max" value={num(max, dec)} />
        {extra.goal ? <Kpi label="Ziel" value={num(extra.goal, 0)} /> : null}
      </div>
      <h3>Verlauf</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 10, left: -6, bottom: 0 }}>
          <defs>
            <linearGradient id="mdg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="date" tickFormatter={fmtDate} tick={{ fill: "#7b8499", fontSize: 11 }} minTickGap={28} />
          <YAxis tick={{ fill: "#7b8499", fontSize: 11 }} width={44} domain={["auto", "auto"]} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtDate} />
          <Area type="monotone" dataKey="v" stroke="#60a5fa" strokeWidth={2.5} fill="url(#mdg)" connectNulls dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
