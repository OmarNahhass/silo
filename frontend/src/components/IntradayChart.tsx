import Plot from "react-plotly.js";
import type { LiveBar } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

export default function IntradayChart({ ticker, bars }: { ticker: string; bars: LiveBar[] }) {
  return (
    <Plot
      data={[
        {
          type: "scatter",
          mode: "lines",
          x: bars.map((b) => b.time),
          y: bars.map((b) => b.price),
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
  );
}
