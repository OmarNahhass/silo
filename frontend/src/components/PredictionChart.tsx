import Plot from "../plotly";
import type { PriceBar, ModelResult } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

function nextDate(lastDate: string, prevDate: string): string {
  const last = new Date(lastDate).getTime();
  const prev = new Date(prevDate).getTime();
  return new Date(last + (last - prev)).toISOString().slice(0, 10);
}

export default function PredictionChart({
  bars,
  result,
}: {
  bars: PriceBar[];
  result: ModelResult;
}) {
  const actualDates = bars.map((b) => b.date);
  const actualValues = bars.map((b) => b.close);
  const fittedDates = result.fitted.map((p) => p.date);
  const fittedValues = result.fitted.map((p) => p.value);

  const forecastDate =
    bars.length >= 2 ? nextDate(bars[bars.length - 1].date, bars[bars.length - 2].date) : "";

  const lastActual = actualValues[actualValues.length - 1];
  const chartLabel =
    `${result.name} chart: actual close vs. fitted values` +
    (lastActual !== null && lastActual !== undefined ? `, last actual close $${lastActual.toFixed(2)}` : "") +
    (result.prediction !== null ? `, predicting $${result.prediction.toFixed(2)} for the next trading day` : "") +
    ".";

  return (
    <div role="img" aria-label={chartLabel}>
      <Plot
        data={[
          {
            type: "scatter",
            mode: "lines",
            x: actualDates,
            y: actualValues,
            line: { color: COLORS.actual, width: 2 },
            name: "Actual Close",
          },
          {
            type: "scatter",
            mode: "lines",
            x: fittedDates,
            y: fittedValues,
            line: { color: COLORS.fit, width: 2, dash: "dash" },
            name: `${result.name} Fit`,
          },
          {
            type: "scatter",
            mode: "markers",
            x: [forecastDate],
            y: [result.prediction],
            marker: { color: COLORS.forecast, size: 12, symbol: "diamond", line: { color: "white", width: 1 } },
            name: "Predicted Next-Day Close",
          },
        ]}
        layout={{
          ...PLOTLY_LAYOUT_BASE,
          title: { text: `${result.name}: Actual vs. Fitted vs. Predicted Next-Day Close` },
          yaxis: { title: { text: "Price (USD)" } },
        }}
        config={PLOTLY_CONFIG}
        style={{ width: "100%", height: "420px" }}
        useResizeHandler
      />
    </div>
  );
}
