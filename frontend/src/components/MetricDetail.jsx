import { ResponsiveContainer, AreaChart, Area, ReferenceLine } from "recharts";
import { BackBar, Kpi } from "./ui.jsx";
import { num, int } from "./format.js";
import { ACCENT, STATUS } from "../theme.js";
import { AreaGradient, ChartTip, Grid, XAxisDate, YAxisNum } from "./chart.jsx";

// Generische Detailansicht für die Trend-Tiles (nutzt die geladene Serie).
export default function MetricDetail({ extra, onBack }) {
  if (!extra) return <div className="detail"><BackBar onBack={onBack} title="Metrik" /></div>;
  const data = (extra.series || []).map((s) => ({ date: s.date, v: s.v }));
  const vals = data.map((d) => d.v).filter((v) => v != null);
  const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  const min = vals.length ? Math.min(...vals) : null;
  const max = vals.length ? Math.max(...vals) : null;
  const dec = extra.decimals ?? 0;
  const fmt = (v) => (dec === 0 ? int(v) : num(v, dec));

  return (
    <div className="detail">
      <BackBar onBack={onBack} title={extra.title} />
      {extra.insight ? <div className="method-box">{extra.insight}</div> : null}
      <div className="kpis">
        <Kpi label="Aktuell" value={`${fmt(extra.value)} ${extra.unit}`} />
        <Kpi label="Ø (Zeitraum)" value={fmt(avg)} />
        <Kpi label="Min" value={fmt(min)} />
        <Kpi label="Max" value={fmt(max)} />
        {extra.goal ? <Kpi label="Ziel" value={int(extra.goal)} /> : null}
      </div>
      <h3>Verlauf</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {AreaGradient({ id: "metricGrad", color: ACCENT })}
          {Grid()}
          {XAxisDate({ minTickGap: 28 })}
          {YAxisNum({ width: 46, domain: ["auto", "auto"] })}
          {ChartTip({ valueFmt: (v) => fmt(v) })}
          {extra.goal && <ReferenceLine y={extra.goal} stroke={STATUS.good} strokeOpacity={0.5} strokeDasharray="4 4" />}
          <Area type="monotone" dataKey="v" name={extra.title} stroke={ACCENT} strokeWidth={2} fill="url(#metricGrad)" connectNulls dot={false}  isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
