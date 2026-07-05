import { useEffect, useState } from "react";
import { getProfile, updateProfile } from "../api.js";
import { BackBar } from "./ui.jsx";

const GOALS = [
  ["run_5_10k", "5–10 km (polarisiert)"],
  ["pyramidal", "Pyramidal"],
  ["general", "Allgemeine Fitness"],
  ["competition", "Wettkampf Ausdauer"],
];

export default function Settings({ onBack, onSaved }) {
  const [p, setP] = useState(null);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => { getProfile().then(setP).catch((e) => setErr(e.message)); }, []);

  if (err) return <div className="detail"><BackBar onBack={onBack} title="Einstellungen" /><div className="error">{err}</div></div>;
  if (!p) return <div className="detail"><BackBar onBack={onBack} title="Einstellungen" /><div className="loading">Lade…</div></div>;

  const set = (k, v) => setP({ ...p, [k]: v });
  const numOrNull = (v) => (v === "" || v == null ? null : Number(v));

  const save = async () => {
    setMsg(null); setErr(null);
    try {
      await updateProfile({
        max_hr: numOrNull(p.max_hr),
        lthr: numOrNull(p.lthr),
        zone_method: p.zone_method,
        resting_hr_override: numOrNull(p.resting_hr_override),
        training_goal: p.training_goal,
        sleep_need_mode: p.sleep_need_mode,
        sleep_need_minutes: p.sleep_need_mode === "manual" ? numOrNull(p.sleep_need_minutes) : null,
      });
      setMsg("Gespeichert.");
      onSaved && onSaved();
    } catch (e) { setErr(e.message); }
  };

  return (
    <div className="detail">
      <BackBar onBack={onBack} title="Einstellungen" />
      <div className="settings">
        <Field label="Maximale HF (bpm)">
          <input type="number" value={p.max_hr ?? ""} onChange={(e) => set("max_hr", e.target.value)} />
        </Field>
        <Field label={`Schwellen-HF / LTHR (leer = auto ≈ ${p.lthr_effective})`}>
          <input type="number" value={p.lthr ?? ""} onChange={(e) => set("lthr", e.target.value)} placeholder={`${p.lthr_effective}`} />
        </Field>
        <Field label="Zonen-Methode">
          <select value={p.zone_method} onChange={(e) => set("zone_method", e.target.value)}>
            <option value="threshold">Schwellen-basiert (LTHR)</option>
            <option value="karvonen">Karvonen (%HFR)</option>
          </select>
        </Field>
        <Field label={`Ruhe-HF Override (leer = auto ≈ ${p.resting_hr_effective})`}>
          <input type="number" value={p.resting_hr_override ?? ""} onChange={(e) => set("resting_hr_override", e.target.value)} placeholder={`${p.resting_hr_effective}`} />
        </Field>
        <Field label="Trainingsziel">
          <select value={p.training_goal} onChange={(e) => set("training_goal", e.target.value)}>
            {GOALS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>
        <Field label="Schlafbedarf">
          <select value={p.sleep_need_mode} onChange={(e) => set("sleep_need_mode", e.target.value)}>
            <option value="auto">Automatisch</option>
            <option value="manual">Manuell</option>
          </select>
        </Field>
        {p.sleep_need_mode === "manual" && (
          <Field label="Schlafbedarf (Minuten)">
            <input type="number" value={p.sleep_need_minutes ?? ""} onChange={(e) => set("sleep_need_minutes", e.target.value)} placeholder="480" />
          </Field>
        )}
        <div className="settings-actions">
          <button className="btn primary" onClick={save}>Speichern</button>
          {msg && <span className="ok-msg">{msg}</span>}
          {err && <span className="err-msg">{err}</span>}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
