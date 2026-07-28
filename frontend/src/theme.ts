// Mirrors utils/plotting.py's palette and Plotly config, so charts here match the
// Streamlit app's baseline until this gets restyled.
export const COLORS = {
  actual: "#d4d4d4", // neutral light gray
  fit: "#f97316", // orange accent
  forecast: "#fbbf24", // amber
  up: "#22c55e",
  down: "#ef4444",
};

export const PLOTLY_CONFIG = {
  scrollZoom: true,
  displaylogo: false,
  modeBarButtonsToRemove: [
    "zoom2d",
    "zoomIn2d",
    "zoomOut2d",
    "autoScale2d",
    "lasso2d",
    "select2d",
  ] as const,
};

export const PLOTLY_LAYOUT_BASE = {
  paper_bgcolor: "#1a1a1a",
  plot_bgcolor: "#1a1a1a",
  font: { color: "#e5e5e5", family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  margin: { l: 50, r: 10, t: 50, b: 40 },
  dragmode: "pan" as const,
  hovermode: "x unified" as const,
  // Legend sits below the plot rather than stacked above the title -- at the top,
  // the legend (y=1.02, just above the axes) and the title (rendered in the same
  // ~40px top margin band) had nowhere to fit without overlapping each other.
  legend: { orientation: "h" as const, yanchor: "top" as const, y: -0.18, xanchor: "center" as const, x: 0.5 },
};
