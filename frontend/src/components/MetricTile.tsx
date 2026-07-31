import type { ModelResult } from "../types";

export default function MetricTile({
  result,
  lastClose,
  rank,
}: {
  result: ModelResult;
  lastClose: number;
  rank?: number;
}) {
  if (result.error || result.prediction === null) {
    return (
      <div className="metric-tile metric-tile-error">
        <div className="metric-tile-header">
          <div className="metric-label">{result.name}</div>
        </div>
        <div className="metric-category">{result.category}</div>
        <div className="metric-error">Failed: {result.error ?? "no prediction"}</div>
      </div>
    );
  }

  const delta = result.prediction - lastClose;
  const deltaPct = delta / lastClose;
  const isUp = delta >= 0;

  return (
    <div className="metric-tile">
      <div className="metric-tile-header">
        {rank !== undefined && <span className="rank-badge">#{rank}</span>}
        <div className="metric-label">{result.name}</div>
      </div>
      <div className="metric-category">{result.category}</div>
      <div className="metric-value-label">Predicted Next-Day Close</div>
      <div className="metric-value">${result.prediction.toFixed(2)}</div>
      <div className={"metric-delta " + (isUp ? "up" : "down")}>
        {isUp ? "↑" : "↓"} {delta >= 0 ? "+" : ""}
        {delta.toFixed(2)} ({deltaPct >= 0 ? "+" : ""}
        {(deltaPct * 100).toFixed(2)}%)
      </div>
      <div className="metric-rmse">
        {result.rmse !== null ? `Typical error: $${result.rmse.toFixed(2)}` : "Typical error: n/a"}
      </div>
    </div>
  );
}
