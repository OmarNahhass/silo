import Plot from "../plotly";
import type { LiveBar } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

export default function IntradayChart({ ticker, bars }: { ticker: string; bars: LiveBar[] }) {
  const prices = bars.map((b) => b.price);
  const rangeText = prices.length
    ? `, ranging from $${Math.min(...prices).toFixed(2)} to $${Math.max(...prices).toFixed(2)}`
    : "";
  const chartLabel = `${ticker} intraday price chart for today${rangeText}.`;

  return (
    <div role="img" aria-label={chartLabel}>
      <Plot
        data={[
          {
            type: "scatter",
            mode: "lines",
            x: bars.map((b) => b.time),
            y: prices,
            line: { color: COLORS.actual, width: 2 },
            name: ticker,
          },
        ]}
        layout={{
          ...PLOTLY_LAYOUT_BASE,
          title: { text: `${ticker} — Today So Far` },
          yaxis: { title: { text: "Price (USD)" } },
        }}
        config={PLOTLY_CONFIG}
        style={{ width: "100%", height: "380px" }}
        useResizeHandler
      />
    </div>
  );
}
