// Tiny inline SVG sparkline from an array of numbers (nulls allowed).
export default function Sparkline({ values = [], color = "#60a5fa", width = 120, height = 38 }) {
  const nums = values.filter((v) => v != null);
  if (nums.length < 2) return <svg width={width} height={height} aria-hidden />;
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const rng = max - min || 1;
  const n = values.length;
  const pts = values
    .map((v, i) => {
      if (v == null) return null;
      const x = (i / (n - 1)) * (width - 4) + 2;
      const y = height - 3 - ((v - min) / rng) * (height - 6);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .filter(Boolean)
    .join(" ");
  return (
    <svg width={width} height={height} aria-hidden>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
