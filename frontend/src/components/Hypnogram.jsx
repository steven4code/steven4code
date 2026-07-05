import { hm } from "./format.js";
import { STAGE as STAGE_COLOR } from "../theme.js";

// Schlafverlauf in 4 Spuren über die Nacht. Identität trägt die Spur
// (Position), Farbe verstärkt nur — deshalb ist die Palette hier auch
// mit Labels abgesichert (validiert, docs/DESIGN.md §3).
const STAGE = {
  awake: { lane: 0, color: STAGE_COLOR.awake },
  rem: { lane: 1, color: STAGE_COLOR.rem },
  light: { lane: 2, color: STAGE_COLOR.light },
  deep: { lane: 3, color: STAGE_COLOR.deep },
};
const LANE_LABELS = ["Wach", "REM", "Leicht", "Tief"];
const LANE_H = 20, GAP = 6, LANES = 4;
const H = LANES * LANE_H + (LANES - 1) * GAP;
const W = 1000;

export default function Hypnogram({ stages }) {
  if (!stages || !stages.length) return null;
  const total = stages.reduce((a, s) => a + (s.min || 0), 0) || 1;

  let x = 0;
  const rects = stages.map((s, i) => {
    const def = STAGE[s.stage] || STAGE.light;
    const w = (s.min / total) * W;
    const r = { x, y: def.lane * (LANE_H + GAP), w: Math.max(2, w), color: def.color, key: i };
    x += w;
    return r;
  });
  // Dünne Verbinder zwischen aufeinanderfolgenden Segmenten (Treppen-Optik).
  const links = [];
  for (let i = 1; i < rects.length; i++) {
    const a = rects[i - 1], b = rects[i];
    const ay = a.y + LANE_H / 2, by = b.y + LANE_H / 2;
    links.push(<line key={`l${i}`} x1={b.x} y1={ay} x2={b.x} y2={by} stroke="#2A303B" strokeWidth="2" />);
  }

  return (
    <div className="hypno">
      <div className="hypno-labels">{LANE_LABELS.map((l) => <span key={l}>{l}</span>)}</div>
      <svg className="hypno-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height: H }}>
        {[0, 1, 2, 3].map((l) => (
          <rect key={`bg${l}`} x="0" y={l * (LANE_H + GAP)} width={W} height={LANE_H} fill="#10141b" rx="4" />
        ))}
        {links}
        {rects.map((r) => (
          <rect key={r.key} x={r.x} y={r.y} width={r.w} height={LANE_H} fill={r.color} rx="4" />
        ))}
      </svg>
      <div className="hypno-foot"><span>Einschlafen</span><span>{hm(total)} im Bett</span><span>Aufwachen</span></div>
    </div>
  );
}
