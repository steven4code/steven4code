import { BulletMeter, CardButton, CardHead, Chip, Recommendation } from "./ui.jsx";
import { hm } from "./format.js";
import { SYSTEM } from "../theme.js";

// Training — Woche: Systeme als Bullet-Meter gegen das persönliche Zielband
// (Lauf-Äquivalent-Minuten, polarisiertes Modell — Seiler 80/20).
function SysMeter({ s }) {
  const max = Math.max(s.actual_min, s.target_hi) * 1.25 || 1;
  const word = s.status === "ok" ? "✓ im Ziel" : s.status === "under" ? "△ unter Ziel" : "▲ über Ziel";
  return (
    <BulletMeter
      label={`${s.label} · ${s.zones}`}
      labelDot={SYSTEM[s.key]}
      value={s.actual_min}
      valueText={hm(s.actual_min)}
      targetText={`Ziel ${hm(s.target_lo)}–${hm(s.target_hi)} · ${word}`}
      max={max}
      bandLo={s.target_lo}
      bandHi={s.target_hi}
      color={SYSTEM[s.key]}
    />
  );
}

export default function CardioCard({ card, onOpen }) {
  if (!card || card.empty) {
    return (
      <CardButton onOpen={onOpen} label="Training — Details">
        <CardHead title="Training · Woche" />
        <p className="meter-note">Noch keine Trainingsdaten.</p>
      </CardButton>
    );
  }
  const top = card.recommendations && card.recommendations[0];
  const ratioWarn =
    card.load_ratio_status && card.load_ratio_status !== "ok" && card.load_ratio_status !== "unknown";
  const m = card.model || {};

  return (
    <CardButton onOpen={onOpen} label="Training — Details">
      <CardHead
        title="Training · Woche"
        right={
          <Chip tone={ratioWarn ? "warn" : "good"}>
            {ratioWarn
              ? card.load_ratio_status === "high"
                ? "▲ Last steigt schnell"
                : "▼ Last niedrig"
              : "✓ Lasttrend stabil"}
          </Chip>
        }
      />

      <span className="meter-note" style={{ display: "block", marginBottom: 4 }}>
        Lauf-spezifische Systemlast vs. Ziel ({m.basis}/{m.grauzone}/{m.intensiv} für {card.goal})
      </span>

      <div className="meter-list" style={{ marginTop: 10 }}>
        {(card.systems || []).map((s) => (
          <SysMeter key={s.key} s={s} />
        ))}
      </div>

      {top && (
        <div style={{ marginTop: 14 }}>
          <Recommendation rec={top} />
        </div>
      )}

      <p className="meter-note" style={{ marginTop: 12, marginBottom: 0 }}>
        {card.week.sessions} Einheiten · {card.week.runs} Lauf / {card.week.padel} Padel
        {card.padel_share_pct > 0 && <> · Padel-Anteil {card.padel_share_pct}% (anteilig angerechnet)</>}
      </p>
    </CardButton>
  );
}
