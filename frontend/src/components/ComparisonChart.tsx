import Plot from "../plotly";
import type { PriceBar } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

function toPctChange(bars: PriceBar[]): number[] {
  const base = bars.find((b) => b.close !== null)?.close;
  if (!base) return bars.map(() => 0);
  return bars.map((b) => (b.close !== null ? ((b.close - base) / base) * 100 : 0));
}

export default function ComparisonChart({
  labelA,
  barsA,
  labelB,
  barsB,
}: {
  labelA: string;
  barsA: PriceBar[];
  labelB: string;
  barsB: PriceBar[];
}) {
  return (
    <Plot
      data={[
        {
          type: "scatter",
          mode: "lines",
          x: barsA.map((b) => b.date),
          y: toPctChange(barsA),
          line: { color: COLORS.compareA, width: 2 },
          name: labelA,
        },
        {
          type: "scatter",
          mode: "lines",
          x: barsB.map((b) => b.date),
          y: toPctChange(barsB),
          line: { color: COLORS.compareB, width: 2 },
          name: labelB,
        },
      ]}
      layout={{
        ...PLOTLY_LAYOUT_BASE,
        title: { text: `${labelA} vs. ${labelB} — % change over the period` },
        yaxis: { title: { text: "% change" }, ticksuffix: "%" },
      }}
      config={PLOTLY_CONFIG}
      style={{ width: "100%", height: "420px" }}
      useResizeHandler
    />
  );
}
