import type { ModelMeta, ModelResult, PriceBar } from "../types";
import MetricTile from "./MetricTile";
import PredictionChart from "./PredictionChart";
import Math from "./Math";

export default function ModelDetail({
  result,
  meta,
  bars,
  lastClose,
}: {
  result: ModelResult;
  meta: ModelMeta | undefined;
  bars: PriceBar[];
  lastClose: number;
}) {
  if (result.error || result.prediction === null) {
    return (
      <div className="model-detail">
        <p className="error-text">
          {result.name} failed to run: {result.error ?? "unknown error"}
        </p>
      </div>
    );
  }

  return (
    <div className="model-detail">
      <MetricTile result={result} lastClose={lastClose} />
      <div className="chart-wrap">
        <PredictionChart bars={bars} result={result} />
      </div>
      {meta && (
        <div className="how-it-works">
          <h5>How it works</h5>
          <Math tex={meta.math} />
          <p>{meta.note}</p>
        </div>
      )}
    </div>
  );
}
