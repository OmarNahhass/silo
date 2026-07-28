import { BlockMath } from "react-katex";
import "katex/dist/katex.min.css";
import type { ModelMeta, ModelResult, PriceBar } from "../types";
import MetricTile from "./MetricTile";
import PredictionChart from "./PredictionChart";

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
      <PredictionChart bars={bars} result={result} />
      {meta && (
        <div className="how-it-works">
          <h5>How it works</h5>
          <BlockMath math={meta.math} />
          <p>{meta.note}</p>
        </div>
      )}
    </div>
  );
}
