import { BulletMeter, CardButton, CardHead, Chip, Recommendation } from "./ui.jsx";
import { hm } from "./format.js";
import { SYSTEM } from "../theme.js";

// Training — letzte 7 Tage: Systeme als Bullet-Meter gegen das persönliche
// Zielband (Lauf-Äquivalent-Minuten, Ziel-Mix folgt dem Trainingsziel aus den
// Einstellungen). Die Grauzone ist ein DECKEL (polarisierte Lehre): 0 min ist
// ok, nur Überschreiten wird geflaggt.
function SysMeter({ s }) {
  const max = Math.max(s.actual_min, s.target_hi) * 1.25 || 1;
  const isCap = s.cap || s.target_lo === 0;
  const word = s.status === "ok" ? "✓ im Ziel" : s.status === "under" ? "△ unter Ziel" : "▲ über Ziel";
  const tgt = isCap ? `max. ${hm(s.target_hi)}` : `Ziel ${hm(s.target_lo)}–${hm(s.target_hi)}`;
  return (
    <BulletMeter
      label={`${s.label} · ${s.zones}`}
      labelDot={SYSTEM[s.key]}
      value={s.actual_min}
      valueText={hm(s.actual_min)}
      targetText={`${tgt} · ${word}`}
      max={max}
      bandLo={isCap ? 0 : s.target_lo}
      bandHi={s.target_hi}
      color={SYSTEM[s.key]}
    />
  );
}

const RATIO_CHIP = {
  ok: ["good", "✓ Lasttrend stabil"],
  low: ["neutral", "▼ Last niedrig"],
  elevated: ["warn", "▲ Last steigt"],
  high: ["bad", "▲ Last steigt schnell"],
  unknown: ["neutral", "Lasttrend —"],
};

export default function CardioCard({ card, onOpen }) {
  if (!card || card.empty) {
    return (
      <CardButton onOpen={onOpen} label="Training — Details">
        <CardHead title="Training · Letzte 7 Tage" />
        <p className="meter-note">Noch keine Trainingsdaten.</p>
      </CardButton>
    );
  }
  const top = card.recommendations && card.recommendations[0];
  const [ratioTone, ratioText] = RATIO_CHIP[card.load_ratio_status] || RATIO_CHIP.unknown;
  const m = card.model || {};

  return (
    <CardButton onOpen={onOpen} label="Training — Details">
      <CardHead
        title="Training · Letzte 7 Tage"
        right={<Chip tone={ratioTone}>{ratioText}</Chip>}
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
        {card.week.sessions} Einheiten · {card.week.runs} Lauf / {card.week.games} Spielsport
        {card.game_share_pct > 0 && <> · Spielsport-Anteil {card.game_share_pct}% (anteilig angerechnet)</>}
      </p>
    </CardButton>
  );
}
