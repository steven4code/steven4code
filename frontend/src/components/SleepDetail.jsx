import { useEffect, useState } from "react";
import { ResponsiveContainer, LineChart, Line, Legend } from "recharts";
import { getSleepDetail } from "../api.js";
import { Bar, BackBar, Kpi, RangePicker } from "./ui.jsx";
import { hm, num } from "./format.js";
import { STAGE, ACCENT, SPARK, INK } from "../theme.js";
import { ChartTip, Grid, XAxisDate, YAxisNum } from "./chart.jsx";

const LABELS = {
  regularity: "Regularität (SRI)", duration: "Dauer", efficiency: "Effizienz",
  deep: "Tiefschlaf", rem: "REM", restfulness: "Ruhe (WASO)", latency: "Einschlaflatenz",
};

const LEGEND_STYLE = { fontSize: 12, color: INK[2] };

export default function SleepDetail({ onBack }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(90);
  useEffect(() => { getSleepDetail(days).then(setData).catch((e) => setErr(e.message)); }, [days]);

  const bar = <BackBar onBack={onBack} title="Schlaf" right={<RangePicker value={days} onChange={setDays} />} />;
  if (err) return <div className="detail">{bar}<div className="error">{err}</div></div>;
  if (!data) return <div className="detail">{bar}<div className="loading">Lade …</div></div>;
  const comps = data.latest_components || {};
  const score = data.series.at(-1)?.sleep_score;

  return (
    <div className="detail">
      {bar}

      <div className="insight-hero">
        <div className="ih-score" style={{ color: STAGE.rem }}>{num(score, 0)}<small>%</small></div>
        <div className="ih-text">
          <div className="ih-headline">
            {score == null ? "Noch kein Schlaf-Score." :
              score >= 80 ? "Guter Schlaf — Regularität und Dauer tragen die Erholung." :
              score >= 60 ? "Solider Schlaf mit Luft nach oben — Details unten zeigen, wo." :
              "Schlaf unter Bedarf — heute früh ins Bett zahlt direkt auf die Erholung ein."}
          </div>
          <div className="ih-sub">SRI {num(data.latest_sri, 0)} · Bedarf {hm(data.latest_need)} · Defizit (14 T) {hm(data.debt_min)}</div>
        </div>
      </div>

      <div className="method-box">
        Gewichteter Score; <b>Regularität (SRI)</b> dominiert (laut Studien stärkster Outcome-Prädiktor).
        Schlafbedarf automatisch (auf 8 h gedeckelt), Defizit über 14 Tage.
      </div>

      <div className="kpis">
        <Kpi label="Score heute" value={num(score, 0)} />
        <Kpi label="SRI" value={num(data.latest_sri, 0)} sub="Regularität" />
        <Kpi label="Bedarf" value={hm(data.latest_need)} />
        <Kpi label="Defizit (14 T)" value={hm(data.debt_min)} />
      </div>

      <h3>Komponenten heute — mit Gewichten</h3>
      <div className="comp-list">
        {Object.keys(LABELS).map((k) => (
          <div className="comp" key={k}>
            <div className="comp-top">
              <span>{LABELS[k]} <small>{Math.round((data.weights[k] || 0) * 100)}%</small></span>
              <b>{comps[k] == null ? "–" : num(comps[k], 0)}</b>
            </div>
            <Bar value={comps[k] || 0} color={STAGE.rem} />
          </div>
        ))}
      </div>

      <h3>Verlauf — Score & SRI</h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {Grid()}
          {XAxisDate()}
          {YAxisNum({ domain: [0, 100], width: 34 })}
          {ChartTip({ valueFmt: (v) => Math.round(v) })}
          <Legend wrapperStyle={LEGEND_STYLE} iconType="plainline" />
          <Line type="monotone" dataKey="sleep_score" name="Schlaf-Score" stroke={STAGE.rem} strokeWidth={2} dot={false} connectNulls  isAnimationActive={false} />
          <Line type="monotone" dataKey="sri" name="SRI" stroke={SPARK} strokeWidth={1.4} dot={false} connectNulls  isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>

      <h3>Schlafdauer & Phasen</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {Grid()}
          {XAxisDate()}
          {YAxisNum({ width: 34 })}
          {ChartTip({ valueFmt: (v) => `${Math.round(v)} min` })}
          <Legend wrapperStyle={LEGEND_STYLE} iconType="plainline" />
          <Line type="monotone" dataKey="minutes" name="Gesamt" stroke={ACCENT} strokeWidth={2} dot={false} connectNulls  isAnimationActive={false} />
          <Line type="monotone" dataKey="deep_minutes" name="Tief" stroke={STAGE.deep} strokeWidth={1.4} dot={false} connectNulls  isAnimationActive={false} />
          <Line type="monotone" dataKey="rem_minutes" name="REM" stroke={STAGE.rem} strokeWidth={1.4} dot={false} connectNulls  isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
