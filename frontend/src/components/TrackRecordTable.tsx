import type { TrackRecordModelStat } from "../types";
import InfoTip from "./InfoTip";

export default function TrackRecordTable({ models }: { models: TrackRecordModelStat[] }) {
  const ranked = models.slice().sort((a, b) => a.rmse - b.rmse);

  return (
    <div className="table-wrap">
      <table className="leaderboard">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Category</th>
            <th>Samples</th>
            <th>
              RMSE
              <InfoTip openDownward text="Root mean squared error across every resolved prediction in scope. Lower is better." />
            </th>
            <th>
              MAE
              <InfoTip openDownward text="Mean absolute error -- the average size of the miss, in dollars, treating every miss equally (unlike RMSE, which punishes big misses more)." />
            </th>
            <th>
              MAPE
              <InfoTip openDownward text="Mean absolute percentage error -- the average miss as a percentage of price, which makes it comparable across tickers at very different price levels." />
            </th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((m, i) => (
            <tr key={m.key}>
              <td>{i + 1}</td>
              <td>{m.name}</td>
              <td>{m.category}</td>
              <td>{m.n_samples}</td>
              <td>${m.rmse.toFixed(2)}</td>
              <td>${m.mae.toFixed(2)}</td>
              <td>{m.mape !== null ? `${m.mape.toFixed(2)}%` : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
