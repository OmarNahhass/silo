import Plot from "../plotly";
import type { AnalystTarget, PriceBar } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function AnalystComparisonChart({
  ticker,
  bars,
  prediction,
  target,
}: {
  ticker: string;
  bars: PriceBar[];
  prediction: number | null;
  target: AnalystTarget;
}) {
  const dates = bars.map((b) => b.date);
  const values = bars.map((b) => b.close);
  const lastDate = dates[dates.length - 1];
  const nextDayDate = lastDate ? addDays(lastDate, 1) : "";
  const targetDate = lastDate ? addDays(lastDate, 365) : "";

  return (
    <Plot
      data={[
        {
          type: "scatter",
          mode: "lines",
          x: dates,
          y: values,
          line: { color: COLORS.actual, width: 2 },
          name: "Actual Close",
        },
        ...(prediction !== null
          ? [
              {
                type: "scatter" as const,
                mode: "markers" as const,
                x: [nextDayDate],
                y: [prediction],
                marker: { color: COLORS.forecast, size: 12, symbol: "diamond", line: { color: "white", width: 1 } },
                name: "Our Next-Day Prediction",
              },
            ]
          : []),
        {
          type: "scatter",
          mode: "markers",
          x: [targetDate],
          y: [target.mean],
          error_y: {
            type: "data",
            symmetric: false,
            array: [target.high !== null ? target.high - target.mean : 0],
            arrayminus: [target.low !== null ? target.mean - target.low : 0],
            color: COLORS.compareB,
            thickness: 2,
            width: 6,
          },
          marker: { color: COLORS.compareB, size: 10 },
          name: "Analyst 12-Month Target",
        },
      ]}
      layout={{
        ...PLOTLY_LAYOUT_BASE,
        title: { text: `${ticker}: Price, Our Prediction & Analyst Target` },
        yaxis: { title: { text: "Price (USD)" } },
      }}
      config={PLOTLY_CONFIG}
      style={{ width: "100%", height: "380px" }}
      useResizeHandler
    />
  );
}
