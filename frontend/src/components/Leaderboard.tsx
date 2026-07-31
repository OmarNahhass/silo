import type { ModelResult } from "../types";
import InfoTip from "./InfoTip";

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
            <th>Predicted Next-Day Close</th>
            <th>
              Typical Error
              <InfoTip text="On past data the model didn't train on, its predictions were off by about this much on average. Lower is better. (Technically: RMSE, root mean squared error.)" />
            </th>
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
