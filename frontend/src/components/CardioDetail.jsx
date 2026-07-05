import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar as RBar, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { getCardioDetail } from "../api.js";
import { BackBar, Kpi, Recommendation } from "./ui.jsx";
import { hm, num } from "./format.js";

const fmtWeek = (d) => { const x = new Date(d); return `${x.getDate()}.${x.getMonth() + 1}.`; };
const TYPE_LABEL = { run: "Lauf", padel: "Padel", ride: "Rad", other: "Sonst" };
const SPEC_COLS = [["run", "Lauf"], ["padel", "Padel"], ["ride", "Rad"], ["other", "Sonst"]];
const ZLAB = ["Z1", "Z2", "Z3", "Z4", "Z5"];
const SYS_COLOR = { basis: "#16ec06", grauzone: "#ffde00", intensiv: "#ff2d55" };
const STAT_LABEL = { under: "unter Ziel", ok: "im Ziel", over: "über Ziel" };

export default function CardioDetail({ onBack }) {
  const [c, setC] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => { getCardioDetail().then(setC).catch((e) => setErr(e.message)); }, []);

  if (err) return <div className="detail"><BackBar onBack={onBack} title="Cardio Load" /><div className="error">{err}</div></div>;
  if (!c || c.empty) return <div className="detail"><BackBar onBack={onBack} title="Cardio Load" /><div className="loading">Lade…</div></div>;

  const cost = c.recovery_cost || {};
  const costLabel = { padel: "Padel", quality_run: "Harte Läufe", easy_run: "Lockere Läufe" };
  const m = c.model || {};

  return (
    <div className="detail">
      <BackBar onBack={onBack} title="Cardio Load – Detail" />
      <div className="method-box">
        <b>Lauf-spezifische Systemlast.</b> Jede Zonenminute wird mit einem Modalitäts-Faktor in
        <b> Lauf-Äquivalent-Minuten</b> umgerechnet (SAID-Prinzip + Cross-Training-Transfer): Laufen = 100 %,
        Padel anteilig – zentral/aerob mäßig, renntempo-spezifisch kaum. Ziel-Mix <b>{m.basis}/{m.grauzone}/{m.intensiv}</b>
        {" "}(qualitätslastig) deines tragbaren Wochenvolumens. Empfehlung = größtes relatives Defizit, validiert an der Erholung.
      </div>

      <h3>Systeme diese Woche (Lauf-Äquivalent) vs. Ziel</h3>
      <div className="systable">
        {(c.systems || []).map((s) => {
          const max = Math.max(s.actual_min, s.target_hi) * 1.25 || 1;
          const pct = (v) => `${Math.max(0, Math.min(100, (v / max) * 100))}%`;
          const tone = s.status === "ok" ? "good" : s.status === "under" ? "warn" : "neutral";
          return (
            <div className="strow" key={s.key}>
              <div className="strow-head">
                <span><i className="dot" style={{ background: SYS_COLOR[s.key] }} /> {s.label} <small>{s.zones} · Ziel {s.target_pct}%</small></span>
                <span className="strow-val">{hm(s.actual_min)} <small>Ziel {hm(s.target_lo)}–{hm(s.target_hi)} · {STAT_LABEL[s.status]}</small></span>
              </div>
              <div className="strow-track">
                <span className="strow-band" style={{ left: pct(s.target_lo), width: `calc(${pct(s.target_hi)} - ${pct(s.target_lo)})` }} />
                <span className="strow-fill" style={{ width: pct(s.actual_min), background: SYS_COLOR[s.key] }} />
                <span className={`strow-flag ${tone}`} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="kpis">
        <Kpi label="Woche (Lauf-Äq.)" value={`${num(c.week_req_total, 0)}′`} sub={`Ziel ~${num(c.target_total, 0)}′`} />
        <Kpi label="Padel-Anteil" value={`${num(c.padel_share_pct, 0)}%`} sub="anteilig angerechnet" />
        <Kpi label="akut:chronisch" value={num(c.load_ratio, 2)} sub={c.load_ratio_status} />
        <Kpi label="Monotonie" value={num(c.monotony, 2)} />
        <Kpi label="VO₂max" value={num(c.vo2max, 1)} sub={c.vo2_trend == null ? "" : `${c.vo2_trend > 0 ? "+" : ""}${num(c.vo2_trend, 1)} / 6 Wo.`} />
      </div>

      <h3>Empfehlungen</h3>
      <div className="rec-list">
        {c.recommendations.map((r, i) => <Recommendation key={i} rec={r} />)}
      </div>

      <h3>Run-Spezifität: Anrechnung pro Zone (% einer Lauf-Minute)</h3>
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

      <h3>Erholungs-Kosten je Einheitstyp (Δ Erholung am Folgetag vs. Baseline {num(cost.baseline, 0)})</h3>
      <div className="kpis">
        {["padel", "quality_run", "easy_run"].map((k) => (
          <Kpi key={k} label={costLabel[k]} value={cost[k] == null ? "–" : `${cost[k] > 0 ? "+" : ""}${num(cost[k], 1)}`} />
        ))}
      </div>

      <h3>Wöchentliche Lauf-Äquivalent-Last (8 Wochen)</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={c.weekly_series} margin={{ top: 8, right: 10, left: -8, bottom: 0 }}>
          <CartesianGrid stroke="#222838" vertical={false} />
          <XAxis dataKey="week_start" tickFormatter={fmtWeek} tick={{ fill: "#7b8499", fontSize: 11 }} />
          <YAxis tick={{ fill: "#7b8499", fontSize: 11 }} width={36} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #2a3142", borderRadius: 8 }} labelFormatter={fmtWeek} />
          <RBar dataKey="basis" stackId="s" fill="#16ec06" isAnimationActive={false} />
          <RBar dataKey="grauzone" stackId="s" fill="#ffde00" isAnimationActive={false} />
          <RBar dataKey="intensiv" stackId="s" fill="#ff2d55" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>

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
              <td>{fmtWeek(w.date)}</td>
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
