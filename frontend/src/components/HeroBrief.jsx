import ScoreRing from "./ScoreRing.jsx";
import { Chip } from "./ui.jsx";
import { hm, num, longDate } from "./format.js";
import { scoreColor, strainColor } from "../theme.js";

// Tagesbriefing — die Signatur des Designs: das Verdikt (Satz) kommt vor
// der Zahl (Klartext schlägt Rohwerte, NN/g); darunter die Instrumenten-
// Trias als Beleg. Reihenfolge = Entscheidungshierarchie (docs/DESIGN.md §2).

function verdict(rec, sleep, strain) {
  if (!rec) return { line: "Daten werden geladen …" };
  if (rec.flags && rec.flags.length)
    return {
      line: (
        <>
          <b>Achtung:</b> {rec.flags[0]} — heute Erholung priorisieren.
        </>
      ),
    };
  if (rec.score == null)
    return { line: <>Baseline wird aufgebaut — nach ~2 Wochen voll aussagekräftig.</> };

  const sleepShort =
    sleep?.minutes != null && sleep?.need_min != null && sleep.minutes < sleep.need_min - 60;
  const over = strain?.status === "over";

  if (rec.score >= 66)
    return {
      line: over ? (
        <>
          <b>Gut erholt</b> — aber das Tagesbudget ist bereits erreicht. Der Reiz ist gesetzt,
          jetzt zählt die Erholung.
        </>
      ) : (
        <>
          <b>Gut erholt</b> — grünes Licht für intensive Reize wie Intervalle oder Tempo.
        </>
      ),
    };
  if (rec.score >= 40)
    return {
      line: sleepShort ? (
        <>
          <b>Moderat erholt</b> — der Schlaf war zu kurz. Qualität ist ok, heute kein Maximalreiz.
        </>
      ) : (
        <>
          <b>Moderat erholt</b> — Qualität ist ok, aber heute kein Maximalreiz.
        </>
      ),
    };
  return {
    line: (
      <>
        <b>Belastet</b> — locker bewegen oder ruhen; harte Einheiten verschieben.
      </>
    ),
  };
}

// Zahl wohnt IM Ring (keine Dopplung daneben); Label + Kontextzeile daneben.
function TrioItem({ label, ring, sub, onOpen }) {
  return (
    <button type="button" className="trio-item" onClick={onOpen} aria-label={`${label} — Details`}>
      {ring}
      <span className="trio-meta">
        <span className="trio-label">{label}</span>
        <span className="trio-sub">{sub}</span>
      </span>
    </button>
  );
}

export default function HeroBrief({ asOf, recovery, strain, sleep, onOpen }) {
  const v = verdict(recovery, sleep, strain);
  const recCol = scoreColor(recovery?.score);
  const slpCol = scoreColor(sleep?.score);
  const strCol = strainColor(strain?.status);

  return (
    <section className="card brief" aria-label="Tagesbriefing">
      <p className="brief-date">{longDate(asOf)} · Tagesbriefing</p>
      <p className="brief-verdict">{v.line}</p>

      {recovery?.flags?.length > 0 && (
        <div className="brief-flags">
          {recovery.flags.map((f) => (
            <Chip key={f} tone="bad">⚠ {f}</Chip>
          ))}
        </div>
      )}

      <div className="brief-trio">
        <TrioItem
          label="Erholung"
          ring={
            <ScoreRing
              value={recovery?.score}
              color={recCol}
              size={68}
              text={recovery?.score == null ? "–" : `${Math.round(recovery.score)}%`}
              textSize={17}
            />
          }
          sub={`HFV ${num(recovery?.hrv_rmssd, 0)} · Puls ${num(recovery?.hr, 0)}`}
          onOpen={() => onOpen("recovery")}
        />
        <TrioItem
          label="Belastung"
          ring={
            <ScoreRing
              value={strain?.current}
              max={strain?.scale_max || 100}
              color={strCol}
              size={68}
              text={strain?.current == null ? "–" : Math.round(strain.current)}
              textSize={17}
            />
          }
          sub={`Ziel ${num(strain?.target_low, 0)}–${num(strain?.target_high, 0)}`}
          onOpen={() => onOpen("strain")}
        />
        <TrioItem
          label="Schlaf"
          ring={
            <ScoreRing
              value={sleep?.score}
              color={slpCol}
              size={68}
              text={sleep?.score == null ? "–" : `${Math.round(sleep.score)}%`}
              textSize={17}
            />
          }
          sub={`${hm(sleep?.minutes)} / ${hm(sleep?.need_min)}`}
          onOpen={() => onOpen("sleep")}
        />
      </div>
    </section>
  );
}
