import { useEffect, useState } from "react";
import { ResponsiveContainer, BarChart, Bar as RBar, Legend } from "recharts";
import { getCardioDetail } from "../api.js";
import { BackBar, BulletMeter, Kpi, Recommendation } from "./ui.jsx";
import { hm, num } from "./format.js";
import { SYSTEM, INK } from "../theme.js";
import { ChartTip, Grid, XAxisDate, YAxisNum, fmtDate } from "./chart.jsx";

const TYPE_LABEL = { run: "Lauf", padel: "Padel", soccer: "Fußball", ride: "Rad", other: "Sonst" };
const SPEC_COLS = [["run", "Lauf"], ["soccer", "Fußball"], ["padel", "Padel"], ["ride", "Rad"], ["other", "Sonst"]];
const ZLAB = ["Z1", "Z2", "Z3", "Z4", "Z5"];
const STAT_LABEL = { under: "unter Ziel", ok: "im Ziel", over: "über Ziel" };
const STAT_ICON = { under: "△", ok: "✓", over: "▲" };

export default function CardioDetail({ onBack }) {
  const [c, setC] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => { getCardioDetail().then(setC).catch((e) => setErr(e.message)); }, []);

  const bar = <BackBar onBack={onBack} title="Training" />;
  if (err) return <div className="detail">{bar}<div className="error">{err}</div></div>;
  if (!c || c.empty) return <div className="detail">{bar}<div className="loading">Lade …</div></div>;

  const cost = c.recovery_cost || {};
  const costLabel = { game: "Padel/Fußball", quality_run: "Harte Läufe", easy_run: "Lockere Läufe" };
  const m = c.model || {};

  return (
    <div className="detail">
      {bar}

      <div className="method-box">
        <b>Lauf-spezifische Systemlast.</b> Jede Zonenminute wird mit einem Modalitäts-Faktor in
        <b> Lauf-Äquivalent-Minuten</b> umgerechnet (SAID-Prinzip + Cross-Training-Transfer): Laufen = 100 %,
        Fußball stärker angerechnet als Padel (spielbasiertes Laufen; Krustrup et al.). Ziel-Mix
        <b> {m.basis}/{m.grauzone}/{m.intensiv}</b> folgt deinem Trainingsziel ({c.goal}); die <b>Grauzone ist ein
        Deckel</b>, kein Soll (Seiler). Wochensoll = chronisches Volumen mit sanfter Rampe (max. +10 %/Wo) Richtung
        Ziel-Anker ~{c.target_anchor}′. Empfehlung = größtes relatives Defizit, validiert an der Erholung — bei
        niedriger Erholung ist die Antwort immer Ruhe.
      </div>

      <h3>Systeme diese Woche — Lauf-Äquivalent vs. Zielband</h3>
      <div className="meter-list" style={{ marginTop: 0 }}>
        {(c.systems || []).map((s) => {
          const max = Math.max(s.actual_min, s.target_hi) * 1.25 || 1;
          const isCap = s.cap || s.target_lo === 0;
          const tgt = isCap ? `max. ${hm(s.target_hi)} (Deckel)` : `Ziel ${hm(s.target_lo)}–${hm(s.target_hi)}`;
          return (
            <BulletMeter
              key={s.key}
              label={`${s.label} · ${s.zones} · ${isCap ? "Deckel" : "Ziel"} ${s.target_pct}%`}
              labelDot={SYSTEM[s.key]}
              value={s.actual_min}
              valueText={hm(s.actual_min)}
              targetText={`${tgt} · ${STAT_ICON[s.status]} ${STAT_LABEL[s.status]}`}
              max={max}
              bandLo={isCap ? 0 : s.target_lo}
              bandHi={s.target_hi}
              color={SYSTEM[s.key]}
            />
          );
        })}
      </div>

      <div className="kpis">
        <Kpi label="Woche (Lauf-Äq.)" value={`${num(c.week_req_total, 0)}′`} sub={`Soll ~${num(c.target_total, 0)}′ · Anker ${num(c.target_anchor, 0)}′`} />
        <Kpi label="Spielsport-Anteil" value={`${num(c.game_share_pct, 0)}%`} sub="Padel/Fußball, anteilig" />
        <Kpi label="akut:chronisch" value={num(c.load_ratio, 2)} sub={c.load_ratio_status} />
        <Kpi label="Monotonie" value={num(c.monotony, 2)} />
        <Kpi label="VO₂max" value={num(c.vo2max, 1)} sub={c.vo2_trend == null ? "" : `${c.vo2_trend > 0 ? "+" : ""}${num(c.vo2_trend, 1)} / 6 Wo.`} />
      </div>

      <h3>Empfehlungen</h3>
      <div className="rec-list">
        {c.recommendations.map((r, i) => <Recommendation key={i} rec={r} />)}
      </div>

      <h3>Wöchentliche Lauf-Äquivalent-Last · 8 Wochen</h3>
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={c.weekly_series} margin={{ top: 8, right: 10, left: 0, bottom: 0 }} barCategoryGap="25%">
          {Grid()}
          {XAxisDate({ dataKey: "week_start" })}
          {YAxisNum({ width: 36 })}
          {ChartTip({ labelFmt: fmtDate, valueFmt: (v) => `${Math.round(v)} min` })}
          <Legend wrapperStyle={{ fontSize: 12, color: INK[2] }} />
          {/* 2px-Lücken zwischen Stapel-Segmenten übernimmt der Karten-Hintergrund via stroke */}
          <RBar dataKey="basis" name="Basis" stackId="s" fill={SYSTEM.basis} stroke="#161A21" strokeWidth={1} isAnimationActive={false} />
          <RBar dataKey="grauzone" name="Grauzone" stackId="s" fill={SYSTEM.grauzone} stroke="#161A21" strokeWidth={1} isAnimationActive={false} />
          <RBar dataKey="intensiv" name="Intensiv" stackId="s" fill={SYSTEM.intensiv} stroke="#161A21" strokeWidth={1} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>

      <h3>Run-Spezifität — Anrechnung pro Zone (% einer Lauf-Minute)</h3>
      <table className="ztable">
        <thead><tr><th>Modalität</th>{ZLAB.map((z) => <th key={z}>{z}</th>)}</tr></thead>
        <tbody>
          {SPEC_COLS.map(([key, label]) => (
            <tr key={key}>
              <td>{label}</td>
              {(c.specificity?.[key] || []).map((v, i) => <td key={i}>{Math.round(v * 100)}%</td>)}
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Erholungs-Kosten je Einheitstyp — Δ Erholung am Folgetag vs. Baseline {num(cost.baseline, 0)}</h3>
      <div className="kpis">
        {["game", "quality_run", "easy_run"].map((k) => (
          <Kpi key={k} label={costLabel[k]} value={cost[k] == null ? "–" : `${cost[k] > 0 ? "+" : ""}${num(cost[k], 1)}`} />
        ))}
      </div>

      <h3>HF-Zonen ({c.zone_method === "threshold" ? `LTHR ${c.lthr}` : `max ${c.max_hr}`})</h3>
      <table className="ztable">
        <thead><tr><th>Zone</th><th>HF-Bereich</th><th>Basis</th></tr></thead>
        <tbody>
          {c.zones.map((z) => (
            <tr key={z.zone}><td>{z.name}</td><td>{z.hr_low}–{z.hr_high} bpm</td><td>{z.basis}</td></tr>
          ))}
        </tbody>
      </table>

      <h3>Letzte Einheiten</h3>
      <table className="wtable">
        <thead><tr><th>Datum</th><th>Typ</th><th>Dauer</th><th>Ø HF</th><th>RPE</th><th>Lauf-Äq.</th><th>sRPE</th></tr></thead>
        <tbody>
          {c.recent_workouts.map((w, i) => (
            <tr key={i} className={w.quality ? "quality" : ""}>
              <td>{fmtDate(w.date)}</td>
              <td>{TYPE_LABEL[w.type] || w.type}</td>
              <td>{num(w.duration_min, 0)}′</td>
              <td>{num(w.avg_hr, 0)}</td>
              <td>{num(w.rpe, 1)}</td>
              <td>{num(w.req_total, 0)}′</td>
              <td>{w.srpe == null ? "–" : num(w.srpe, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
