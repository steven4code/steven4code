import { BulletMeter, CardButton, CardHead } from "./ui.jsx";
import { num } from "./format.js";
import { strainColor } from "../theme.js";

// Coach — genau EINE Empfehlung pro Tag (Hick's Law) + Belastungs-Budget
// als Bullet-Meter mit Zielband (Few) statt Rundinstrument.
export default function CoachCard({ strain, onOpen }) {
  if (!strain || strain.empty) return null;
  const s = strain.session;
  const color = strainColor(strain.status);
  const statusWord =
    strain.status === "over"
      ? "über Ziel"
      : strain.status === "optimal"
      ? "im Zielband"
      : `${num(strain.remaining, 0)} Punkte Budget`;

  return (
    <CardButton onOpen={onOpen} className={`coach tone-${s?.tone || "good"}`} label="Coach — Belastungsdetails">
      <CardHead title="Coach · Heute" />

      {s && (
        <>
          <div className="coach-head">
            <span className="coach-zone">{s.zone}</span>
            <strong>{s.headline}</strong>
          </div>
          <p className="coach-presc">{s.prescription}</p>
          <p className="coach-why">{s.rationale}</p>
          <span className="coach-src">{s.source}</span>
        </>
      )}

      <div style={{ marginTop: 16 }}>
        <BulletMeter
          label="Tages-Belastung"
          value={strain.current}
          valueText={`${num(strain.current, 0)} / ${num(strain.scale_max, 0)}`}
          targetText={statusWord}
          max={strain.scale_max || 100}
          bandLo={strain.target_low}
          bandHi={strain.target_high}
          mark={strain.target_opt}
          color={color}
          note={`Zielband ${num(strain.target_low, 0)}–${num(strain.target_high, 0)} aus Erholung, Schlaf und chronischer Last · Marker = Optimum`}
        />
      </div>

      {strain.options?.length > 0 && (
        <div className="coach-alt">
          <span className="coach-alt-cap">Alternativ passt heute noch:</span>
          <div className="opt-chips">
            {strain.options.map((o) => (
              <span key={o.zone} className="opt-chip">
                ~{o.minutes}′ <b>{o.name}</b>
              </span>
            ))}
          </div>
        </div>
      )}
    </CardButton>
  );
}
