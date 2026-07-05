import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, ReferenceLine,
} from "recharts";
import { getStrainDetail } from "../api.js";
import { BackBar, BulletMeter, Kpi, RangePicker } from "./ui.jsx";
import { num } from "./format.js";
import { strainColor, STATUS, CHART } from "../theme.js";
import { AreaGradient, ChartTip, Grid, XAxisDate, XAxisHour, YAxisNum } from "./chart.jsx";

export default function StrainDetail({ onBack }) {
  const [c, setC] = useState(null);
  const [err, setErr] = useState(null);
  const [days, setDays] = useState(60);
  useEffect(() => { getStrainDetail(days).then(setC).catch((e) => setErr(e.message)); }, [days]);

  const bar = <BackBar onBack={onBack} title="Belastung" right={<RangePicker value={days} onChange={setDays} />} />;
  if (err) return <div className="detail">{bar}<div className="error">{err}</div></div>;
  if (!c || c.empty) return <div className="detail">{bar}<div className="loading">Lade …</div></div>;

  const col = strainColor(c.status);
  const insight =
    c.status === "over"
      ? "Tagesziel erreicht — weitere harte Reize erhöhen jetzt das Überlastungsrisiko. Fokus auf Erholung."
      : c.status === "optimal"
      ? "Im optimalen Belastungsfenster für deine heutige Erholung — gut dosiert."
      : `Noch Raum: ${num(c.remaining, 0)} Punkte bis zur Obergrenze. Heute ist ein weiterer Reiz gut vertretbar.`;

  return (
    <div className="detail">
      {bar}

      <div className="insight-hero">
        <div className="ih-score" style={{ color: col }}>{num(c.current, 0)}<small>/{num(c.scale_max, 0)}</small></div>
        <div className="ih-text">
          <div className="ih-headline">{insight}</div>
          <div className="ih-sub">
            Ziel {num(c.target_low, 0)}–{num(c.target_high, 0)} (optimal {num(c.target_opt, 0)}) ·
            projiziert ganzer Tag {num(c.projected_full_day, 0)}
          </div>
        </div>
      </div>

      <BulletMeter
        value={c.current}
        max={c.scale_max || 100}
        bandLo={c.target_low}
        bandHi={c.target_high}
        mark={c.target_opt}
        color={col}
        note={`Zielband aus Erholung + Schlaf + chronischer Last (ACWR) · Marker = Optimum`}
      />

      <div className="method-box" style={{ marginTop: 14 }}>
        <b>Strain 0–100</b>, personalisiert-logarithmisch (jeder Punkt oben ist schwerer): kardiovaskuläre Last
        per <b>Banister-TRIMP</b> aus HF-Zonenzeit (Training + Ganztags-Last) — Ruhe-/Sitzzeit zählt ~0, daher
        morgens niedrig. Die Skala ist auf deine eigene 60-Tage-Lastverteilung geeicht. Ziel-Range aus
        <b> Erholung + Schlaf + chronischer Last (ACWR)</b> — erholt = mehr erlaubt, steigende Wochenlast senkt die
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
          <div className="opt-chips">
            {c.options.map((o) => <span key={o.zone} className="opt-chip">~{o.minutes}′ <b>{o.name}</b></span>)}
          </div>
        </>
      )}

      <h3>Verlauf heute — Akkumulation, projiziert ab {c.now_hour}:00</h3>
      <ResponsiveContainer width="100%" height={230}>
        <AreaChart data={c.intraday} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {AreaGradient({ id: "strainDetailGrad", color: col })}
          {Grid()}
          {XAxisHour({ tickFormatter: (h) => `${h}h` })}
          {YAxisNum({ domain: [0, c.scale_max], width: 30 })}
          {ChartTip({ labelFmt: (h) => `${h}:00 Uhr`, valueFmt: (v) => Math.round(v) })}
          <ReferenceLine y={c.target_high} stroke={STATUS.good} strokeOpacity={0.5} strokeDasharray="4 4" />
          <ReferenceLine y={c.target_low} stroke={STATUS.good} strokeOpacity={0.25} strokeDasharray="4 4" />
          <ReferenceLine x={c.now_hour} stroke={CHART.refline} />
          <Area type="monotone" dataKey="strain" name="Belastung" stroke={col} strokeWidth={2} fill="url(#strainDetailGrad)" dot={false}  isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>

      <h3>Tägliche Belastung · {days === 7 ? "Woche" : `${days} Tage`}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={c.series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          {Grid()}
          {XAxisDate()}
          {YAxisNum({ domain: [0, c.scale_max], width: 30 })}
          {ChartTip({ valueFmt: (v) => Math.round(v) })}
          <ReferenceLine y={c.target_opt} stroke={STATUS.good} strokeOpacity={0.5} strokeDasharray="4 4" />
          <Line type="monotone" dataKey="strain" name="Belastung" stroke={col} strokeWidth={2} dot={false}  isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
