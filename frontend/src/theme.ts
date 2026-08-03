export const COLORS = {
  actual: "#d4d4d4",
  fit: "#6366f1",
  forecast: "#fbbf24",
  up: "#22c55e",
  down: "#ef4444",
  compareA: "#6366f1",
  compareB: "#38bdf8",
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
  paper_bgcolor: "#0a0a0b",
  plot_bgcolor: "#0a0a0b",
  font: { color: "#f4f4f5", family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  margin: { l: 50, r: 10, t: 50, b: 40 },
  dragmode: "pan" as const,
  hovermode: "x unified" as const,
  legend: { orientation: "h" as const, yanchor: "top" as const, y: -0.18, xanchor: "center" as const, x: 0.5 },
};
