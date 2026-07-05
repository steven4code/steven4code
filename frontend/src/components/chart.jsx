// Einheitliches Chart-Chrome (docs/DESIGN.md §5): ein Grid, eine Achse,
// ein Tooltip — statt per Chart kopierter Styles.
//
// WICHTIG: Recharts erkennt Kinder über ihren Element-Typ. Wrapper-
// Komponenten (<Grid/>) würden ignoriert — deshalb sind das hier
// FACTORIES, die echte Recharts-Elemente zurückgeben. Verwendung im JSX
// als Aufruf: {Grid()} · {XAxisDate()} · {YAxisNum({ domain: [0, 100] })}.
import { XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { CHART, INK } from "../theme.js";

export const fmtDate = (d) => {
  const x = new Date(d);
  return `${x.getDate()}.${x.getMonth() + 1}.`;
};

const AXIS_TICK = { fill: CHART.axis, fontSize: 11 };

// Haarlinien-Grid, nur horizontal, durchgezogen (gestrichelt ist für
// Ziel-Referenzlinien reserviert).
export const Grid = () => <CartesianGrid stroke={CHART.grid} vertical={false} />;

export const XAxisDate = (props = {}) => (
  <XAxis
    dataKey="date"
    tickFormatter={fmtDate}
    tick={AXIS_TICK}
    minTickGap={32}
    axisLine={false}
    tickLine={false}
    {...props}
  />
);

export const XAxisHour = (props = {}) => (
  <XAxis
    dataKey="hour"
    tickFormatter={(h) => `${h}`}
    tick={AXIS_TICK}
    axisLine={false}
    tickLine={false}
    {...props}
  />
);

export const YAxisNum = (props = {}) => (
  <YAxis tick={AXIS_TICK} width={36} axisLine={false} tickLine={false} {...props} />
);

// Ein Tooltip für alles: Wert zuerst (fett), Serienname sekundär,
// Serien-Key als kurzer Farbstrich.
function TooltipBody({ active, payload, label, labelFmt, valueFmt }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      style={{
        background: "#10131a",
        border: `1px solid rgba(255,255,255,0.13)`,
        borderRadius: 8,
        padding: "8px 11px",
        fontSize: 12,
        color: INK[2],
        boxShadow: "0 8px 24px rgba(0,0,0,.55)",
      }}
    >
      <div style={{ color: INK[3], fontSize: 11, marginBottom: 4 }}>
        {labelFmt ? labelFmt(label) : label}
      </div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 7, padding: "1px 0" }}>
          <span style={{ width: 10, height: 2.5, borderRadius: 2, background: p.color || p.stroke }} />
          <b style={{ color: INK[1], fontWeight: 650 }}>
            {valueFmt ? valueFmt(p.value, p.dataKey) : Math.round(p.value * 10) / 10}
          </b>
          <span>{p.name}</span>
        </div>
      ))}
    </div>
  );
}

export const ChartTip = ({ labelFmt = fmtDate, valueFmt } = {}) => (
  <Tooltip
    cursor={{ stroke: CHART.refline, strokeWidth: 1 }}
    content={<TooltipBody labelFmt={labelFmt} valueFmt={valueFmt} />}
  />
);

// Verlaufs-Füllung (~10 % Deckkraft als Wash) für Flächencharts.
export const AreaGradient = ({ id, color }) => (
  <defs>
    <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor={color} stopOpacity={0.22} />
      <stop offset="100%" stopColor={color} stopOpacity={0} />
    </linearGradient>
  </defs>
);
