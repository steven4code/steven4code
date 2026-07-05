import { ResponsiveContainer, AreaChart, Area, ReferenceLine } from "recharts";
import { CardButton, CardHead, Chip } from "./ui.jsx";
import { num } from "./format.js";
import { strainColor, strainTone, STATUS, CHART } from "../theme.js";
import { AreaGradient, ChartTip, Grid, XAxisHour, YAxisNum } from "./chart.jsx";

// Tages-Belastung: Akkumulation über den Tag gegen das Zielband.
// (Das Budget-Meter und die Empfehlung wohnen in der Coach-Karte.)
export default function StrainCard({ card, onOpen }) {
  if (!card || card.empty) return null;
  const color = strainColor(card.status);

  return (
    <CardButton onOpen={onOpen} label="Belastung — Details">
      <CardHead
        title="Belastung · Tagesverlauf"
        right={<Chip tone={strainTone(card.status)}>{card.label}</Chip>}
      />

      <ResponsiveContainer width="100%" height={150}>
        <AreaChart data={card.intraday} margin={{ top: 6, right: 6, left: 0, bottom: 0 }}>
          {AreaGradient({ id: "strainDayGrad", color: color })}
          {Grid()}
          {XAxisHour()}
          {YAxisNum({ domain: [0, card.scale_max], width: 30 })}
          {ChartTip({ labelFmt: (h) => `${h}:00 Uhr`, valueFmt: (v) => Math.round(v) })}
          <ReferenceLine y={card.target_high} stroke={STATUS.good} strokeOpacity={0.5} strokeDasharray="4 4" />
          <ReferenceLine y={card.target_low} stroke={STATUS.good} strokeOpacity={0.25} strokeDasharray="4 4" />
          <ReferenceLine x={card.now_hour} stroke={CHART.refline} />
          <Area
            type="monotone"
            dataKey="strain"
            name="Belastung"
            stroke={color}
            strokeWidth={2}
            fill="url(#strainDayGrad)"
            dot={false}
           isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
      <span className="meter-note">
        Gestrichelt = Zielband {num(card.target_low, 0)}–{num(card.target_high, 0)} · senkrecht = jetzt
        ({card.now_hour}:00), danach Projektion
      </span>
    </CardButton>
  );
}
