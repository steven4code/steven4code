import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

function fmtDate(d) {
  const date = new Date(d);
  return `${date.getDate()}.${date.getMonth() + 1}.`;
}

const fmtTick = (v) =>
  typeof v === "number" ? (Number.isInteger(v) ? `${v}` : v.toFixed(1)) : v;

export default function TrendChart({ data, dataKey, color = "#60a5fa", domain }) {
  const id = `grad-${dataKey}`;
  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data} margin={{ top: 6, right: 8, left: -6, bottom: 0 }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#222838" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={fmtDate}
          tick={{ fill: "#7b8499", fontSize: 11 }}
          minTickGap={28}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={domain || ["auto", "auto"]}
          tick={{ fill: "#7b8499", fontSize: 11 }}
          tickFormatter={fmtTick}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <Tooltip
          contentStyle={{
            background: "#161b27",
            border: "1px solid #2a3142",
            borderRadius: 8,
            color: "#e6e9ef",
          }}
          labelFormatter={fmtDate}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#${id})`}
          connectNulls
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
