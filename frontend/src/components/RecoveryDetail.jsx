import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, ReferenceLine,
} from "recharts";
import { getRecoveryDetail } from "../api.js";
import { BackBar, Kpi, RangePicker } from "./ui.jsx";
import { num } from "./format.js";
import { scoreColor, STATUS, SPARK } from "../theme.js";
import { AreaGradient, ChartTip, Grid, XAxisDate, YAxisNum } from "./chart.jsx";

function insightFor(l) {
  if (l.flags && l.flags.length) return `Achtung: ${l.flags.join(" · ")} — heute Erholung priorisieren.`;
  if (l.within_normal === false) return "HFV außerhalb deines Normbereichs — das Nervensystem steht unter Last.";
  if (l.score == null) return "Noch keine 60-Tage-Baseline — Score wird nach ~2 Wochen aussagekräftig.";
  if (l.score >= 66) return "Gut erholt — grünes Licht für intensive Reize (Intervalle, Tempo).";
  if (l.score >= 40) return "Moderat erholt — Qualität ok, aber heute kein Maximalreiz.";
  return "Belastet — locker bewegen oder ruhen; harte Einheiten verschieben.";
}

export default function RecoveryDetail({ onBack }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(90);
  useEffect(() => { getRecoveryDetail(days).then(setData).catch((e) => setErr(e.message)); }, [days]);

  const bar = <BackBar onBack={onBack} title="Erholung" right={<RangePicker value={days} onChange={setDays} />} />;
  if (err) return <div className="detail">{bar}<div className="error">{err}</div></div>;
  if (!data) return <div className="detail">{bar}<div className="loading">Lade …</div></div>;
  const l = data.latest;
  const col = scoreColor(l.score);
  const sleepDrag = l.sleep_factor != null && l.sleep_factor < 0.92;

  return (
    <div className="detail">
      {bar}

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

      <div className="method-box">
        {data.method}
      </div>

      <div className="kpis">
        <Kpi label="Autonomer Kern" value={num(l.core, 0)} />
        <Kpi label="Schlaf-Faktor" value={`×${num(l.sleep_factor, 2)}`} />
        <Kpi label="HFV (lnRMSSD)" value={num(l.ln_rmssd, 2)} sub={`Baseline ${num(l.ln_baseline, 2)} ±${num(l.swc, 2)}`} />
        <Kpi label="HFV-Variabilität (CV 7T)" value={l.cv7 == null ? "–" : `${num(l.cv7, 0)}%`} sub={l.within_normal === false ? "außerhalb Norm" : "im Normbereich"} />
      </div>

      <h3>Erholung · {days === 7 ? "Woche" : `${days} Tage`}</h3>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {AreaGradient({ id: "recGrad", color: col })}
          {Grid()}
          {XAxisDate()}
          {YAxisNum({ domain: [0, 100], ticks: [0, 25, 50, 75, 100], width: 34 })}
          {ChartTip({ valueFmt: (v) => Math.round(v) })}
          <ReferenceLine y={66} stroke={STATUS.good} strokeOpacity={0.4} strokeDasharray="4 4" />
          <ReferenceLine y={40} stroke={STATUS.bad} strokeOpacity={0.4} strokeDasharray="4 4" />
          <Area type="monotone" dataKey="recovery_score" name="Erholung" stroke={col} strokeWidth={2} fill="url(#recGrad)" dot={false} connectNulls  isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>

      <h3>HFV-Trend — Tageswert & 7-Tage-Schnitt</h3>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {Grid()}
          {XAxisDate()}
          {YAxisNum({ width: 34 })}
          {ChartTip({ valueFmt: (v) => Math.round(v) })}
          <Line type="monotone" dataKey="rmssd" name="RMSSD (Tag)" stroke={SPARK} strokeWidth={1.2} dot={false} connectNulls  isAnimationActive={false} />
          <Line type="monotone" dataKey="rolling7_rmssd" name="RMSSD (7T-Schnitt)" stroke={col} strokeWidth={2} dot={false} connectNulls  isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
