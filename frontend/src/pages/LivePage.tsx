import { useEffect, useState } from "react";
import { getTickers, getLiveForecast } from "../api";
import type { AssetType, LiveForecast } from "../types";
import IntradayChart from "../components/IntradayChart";
import SearchableSelect from "../components/SearchableSelect";
import InfoTip from "../components/InfoTip";
import { assetTypeLabel } from "../assetTypeLabel";

const REFRESH_INTERVAL_MS = 60_000;

export default function LivePage() {
  const [assetType, setAssetType] = useState<AssetType>("Stock");
  const [tickers, setTickers] = useState<string[]>([]);
  const [ticker, setTicker] = useState("");
  const [live, setLive] = useState<LiveForecast | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTicker("");
    getTickers(assetType).then((r) => setTickers(r.tickers));
  }, [assetType]);

  async function track(t: string) {
    if (!t.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getLiveForecast(assetType, t.trim().toUpperCase());
      setLive(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!live) return;
    const id = setInterval(() => {
      getLiveForecast(live.asset_type, live.ticker)
        .then(setLive)
        .catch(() => {});
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [live?.ticker, live?.asset_type]);

  const delta = live && live.predicted_close !== null ? live.predicted_close - live.current_price : null;

  return (
    <div className="page">
      <h2>Live Intraday Forecast</h2>
      <p className="muted">
        Predicts today's closing price from the return so far, using the historical relationship
        between partial-day and full-day returns. Data is delayed ~15-20 minutes (free Yahoo
        Finance feed).
      </p>

      <div className="asset-layout">
        <aside className="asset-controls">
          <h3>Track a ticker</h3>
          <label>
            Asset type
            <select value={assetType} onChange={(e) => setAssetType(e.target.value as AssetType)}>
              <option value="Stock">Stock</option>
              <option value="Crypto">Cryptocurrency</option>
            </select>
          </label>
          <label>
            Search or type any ticker symbol
            <SearchableSelect
              options={tickers.map((t) => ({ value: t, label: t }))}
              value={ticker}
              onChange={(t) => setTicker(t.toUpperCase())}
              placeholder={`Search ${assetTypeLabel(assetType).toLowerCase()} tickers, or type any symbol...`}
              allowCreate
              ariaLabel="Search or type any ticker symbol"
            />
          </label>
          <button className="run-button" onClick={() => track(ticker)} disabled={loading}>
            {loading ? "Loading..." : "Track"}
          </button>
          {error && <p className="error-text">{error}</p>}
        </aside>

        <div className="asset-main">
          {live && (
            <>
              <h3>
                {live.ticker} — {live.trade_date}
              </h3>

              <div className="tile-grid">
                <div className="metric-tile">
                  <div className="metric-label">Today's Open</div>
                  <div className="metric-value">${live.open_price.toFixed(2)}</div>
                </div>
                <div className="metric-tile">
                  <div className="metric-label">Current Price</div>
                  <div className="metric-value">${live.current_price.toFixed(2)}</div>
                </div>
                {live.predicted_close !== null ? (
                  <div className="metric-tile">
                    <div className="metric-label">Today's Predicted Close</div>
                    <div className="metric-value">${live.predicted_close.toFixed(2)}</div>
                    {delta !== null &&
                      (Math.abs(delta) < 0.005 ? (
                        <div className="metric-delta">No change from current</div>
                      ) : (
                        <div className={"metric-delta " + (delta >= 0 ? "up" : "down")}>
                          {delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(2)} from current
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="metric-tile metric-tile-error">
                    <div className="metric-label">Today's Predicted Close</div>
                    <div className="metric-error">{live.error ?? "Unavailable"}</div>
                  </div>
                )}
              </div>

              <div className="chart-wrap">
                <IntradayChart ticker={live.ticker} bars={live.intraday_bars} />
              </div>

              <h3>
                Predicted vs. Actual
                <InfoTip text="Once a tracked day ends, its real closing price gets filled in here automatically, so you can see how close the prediction actually was." />
              </h3>

              {live.n_resolved > 0 && live.model_mae !== null && live.naive_mae !== null && (
                <p className={"muted"}>
                  Over the last {live.n_resolved} resolved day{live.n_resolved === 1 ? "" : "s"}: the
                  model was off by <strong>${live.model_mae.toFixed(2)}</strong> on average, vs.{" "}
                  <strong>${live.naive_mae.toFixed(2)}</strong> for just assuming the price wouldn't
                  move at all —{" "}
                  {live.model_mae < live.naive_mae
                    ? `beating that baseline by $${(live.naive_mae - live.model_mae).toFixed(2)}.`
                    : live.model_mae > live.naive_mae
                      ? `currently worse than doing nothing.`
                      : "tied with doing nothing."}
                </p>
              )}

              <div className="table-wrap">
                <table className="leaderboard">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Predicted</th>
                      <th>
                        Naive (No Change)
                        <InfoTip
                          openDownward
                          text="The simplest possible guess: assume the price stays exactly where it was when the prediction was made. If the model can't beat this, it isn't adding any value."
                        />
                      </th>
                      <th>Actual Close</th>
                      <th>Model Error</th>
                      <th>Naive Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {live.history.map((row) => {
                      const modelErr = row.actual_close !== null ? row.actual_close - row.predicted_close : null;
                      const naiveErr = row.actual_close !== null ? row.actual_close - row.naive_close : null;
                      return (
                        <tr key={row.trade_date}>
                          <td>{row.trade_date}</td>
                          <td>${row.predicted_close.toFixed(2)}</td>
                          <td>${row.naive_close.toFixed(2)}</td>
                          <td>{row.actual_close !== null ? `$${row.actual_close.toFixed(2)}` : "—"}</td>
                          <td>{modelErr !== null ? `${modelErr >= 0 ? "+" : ""}${modelErr.toFixed(2)}` : "—"}</td>
                          <td>{naiveErr !== null ? `${naiveErr >= 0 ? "+" : ""}${naiveErr.toFixed(2)}` : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
