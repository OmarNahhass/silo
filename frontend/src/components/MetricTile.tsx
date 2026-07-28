import type { ModelResult } from "../types";

export default function MetricTile({
  result,
  lastClose,
}: {
  result: ModelResult;
  lastClose: number;
}) {
  if (result.error || result.prediction === null) {
    return (
      <div className="metric-tile metric-tile-error">
        <div className="metric-label">{result.name}</div>
        <div className="metric-error">Failed: {result.error ?? "no prediction"}</div>
      </div>
    );
  }

  const delta = result.prediction - lastClose;
  const deltaPct = delta / lastClose;
  const isUp = delta >= 0;

  return (
    <div className="metric-tile">
      <div className="metric-label">{result.name}</div>
      <div className="metric-value">${result.prediction.toFixed(2)}</div>
      <div className={"metric-delta " + (isUp ? "up" : "down")}>
        {isUp ? "↑" : "↓"} {delta >= 0 ? "+" : ""}
        {delta.toFixed(2)} ({deltaPct >= 0 ? "+" : ""}
        {(deltaPct * 100).toFixed(2)}%)
      </div>
      <div className="metric-rmse">
        {result.rmse !== null ? `Holdout RMSE: $${result.rmse.toFixed(2)}` : "Holdout RMSE: n/a"}
      </div>
    </div>
  );
}
