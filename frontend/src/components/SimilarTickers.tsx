import type { SimilarTickerResult } from "../types";
import InfoTip from "./InfoTip";

export default function SimilarTickers({ results }: { results: SimilarTickerResult[] }) {
  if (results.length === 0) return null;

  return (
    <div className="table-wrap">
      <table className="leaderboard">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Ticker</th>
            <th>
              Similarity
              <InfoTip
                openDownward
                text="Cosine similarity between each ticker's current technical-indicator vector (recent return, moving-average ratios, RSI, MACD, volatility) and this one's -- a measure of how closely their price behavior patterns match right now, not whether the companies are actually related."
              />
            </th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={r.ticker}>
              <td>{i + 1}</td>
              <td>{r.ticker}</td>
              <td>{(r.similarity * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
