// Semicircular 0-max gauge with a highlighted target band.
function pt(cx, cy, r, deg) {
  const rad = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}
function arc(cx, cy, r, a1, a2) {
  const [x1, y1] = pt(cx, cy, r, a1);
  const [x2, y2] = pt(cx, cy, r, a2);
  const large = a2 - a1 > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
}
const ang = (v, max) => 180 + (Math.max(0, Math.min(max, v)) / max) * 180;

export default function StrainGauge({ value, max = 21, low, high, opt, size = 220, color = "#f59e0b", decimals = 1 }) {
  const cx = size / 2;
  const cy = size / 2 + 6;
  const r = size / 2 - 16;
  const stroke = 14;
  return (
    <div className="gauge" style={{ width: size, height: size / 2 + 30 }}>
      <svg width={size} height={size / 2 + 30}>
        <path d={arc(cx, cy, r, 180, 360)} fill="none" stroke="#222838" strokeWidth={stroke} strokeLinecap="round" />
        {low != null && high != null && (
          <path d={arc(cx, cy, r, ang(low, max), ang(high, max))} fill="none" stroke="#34d39955" strokeWidth={stroke} strokeLinecap="butt" />
        )}
        <path
          d={arc(cx, cy, r, 180, ang(value, max))}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          style={{ transition: "all 0.7s ease" }}
        />
        {opt != null && (() => {
          const [mx, my] = pt(cx, cy, r, ang(opt, max));
          const [ix, iy] = pt(cx, cy, r - stroke, ang(opt, max));
          return <line x1={ix} y1={iy} x2={mx} y2={my} stroke="#e6e9ef" strokeWidth={2} />;
        })()}
      </svg>
      <div className="gauge-center">
        <div className="gauge-value">{value == null ? "–" : value.toFixed(decimals)}</div>
        <div className="gauge-max">/ {max}</div>
      </div>
    </div>
  );
}
