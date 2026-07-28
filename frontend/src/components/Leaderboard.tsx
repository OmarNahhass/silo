import type { ModelResult } from "../types";

export default function Leaderboard({ models }: { models: ModelResult[] }) {
  const ranked = models
    .filter((m) => m.error === null && m.rmse !== null)
    .slice()
    .sort((a, b) => (a.rmse as number) - (b.rmse as number));

  return (
    <div className="table-wrap">
      <table className="leaderboard">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Category</th>
            <th>Prediction</th>
            <th>Holdout RMSE</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((m, i) => (
            <tr key={m.key}>
              <td>{i + 1}</td>
              <td>{m.name}</td>
              <td>{m.category}</td>
              <td>${m.prediction?.toFixed(2)}</td>
              <td>${m.rmse?.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
