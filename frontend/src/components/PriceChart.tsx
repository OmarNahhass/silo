import Plot from "react-plotly.js";
import type { PriceBar } from "../types";
import { COLORS, PLOTLY_CONFIG, PLOTLY_LAYOUT_BASE } from "../theme";

export default function PriceChart({ ticker, bars }: { ticker: string; bars: PriceBar[] }) {
  const dates = bars.map((b) => b.date);

  return (
    <Plot
      data={[
        {
          type: "candlestick",
          x: dates,
          open: bars.map((b) => b.open),
          high: bars.map((b) => b.high),
          low: bars.map((b) => b.low),
          close: bars.map((b) => b.close),
          increasing: { line: { color: COLORS.up } },
          decreasing: { line: { color: COLORS.down } },
          name: ticker,
          xaxis: "x",
          yaxis: "y",
        },
        {
          type: "bar",
          x: dates,
          y: bars.map((b) => b.volume),
          marker: {
            color: bars.map((b) => ((b.close ?? 0) >= (b.open ?? 0) ? COLORS.up : COLORS.down)),
          },
          name: "Volume",
          showlegend: false,
          xaxis: "x2",
          yaxis: "y2",
        },
      ]}
      layout={{
        ...PLOTLY_LAYOUT_BASE,
        title: { text: `${ticker} Price History` },
        margin: { ...PLOTLY_LAYOUT_BASE.margin, b: 70 },
        legend: { ...PLOTLY_LAYOUT_BASE.legend, y: -0.12 },
        grid: { rows: 2, columns: 1, subplots: [["xy"], ["x2y2"]], roworder: "top to bottom" },
        xaxis: { rangeslider: { visible: false }, domain: [0, 1], anchor: "y" },
        xaxis2: { domain: [0, 1], anchor: "y2" },
        yaxis: { title: { text: "Price (USD)" }, domain: [0.3, 1] },
        yaxis2: { title: { text: "Volume" }, domain: [0, 0.2] },
      }}
      config={PLOTLY_CONFIG}
      style={{ width: "100%", height: "480px" }}
      useResizeHandler
    />
  );
}
