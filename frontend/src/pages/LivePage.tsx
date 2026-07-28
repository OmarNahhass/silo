import { useEffect, useState } from "react";
import { getTickers, getLiveForecast } from "../api";
import type { AssetType, LiveForecast } from "../types";
import IntradayChart from "../components/IntradayChart";
import SearchableSelect from "../components/SearchableSelect";

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

  // Auto-refresh whichever ticker is currently tracked, every 60s, while this page is mounted.
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
              <option value="Crypto">Crypto</option>
            </select>
          </label>
          <label>
            Search ticker symbol
            <SearchableSelect
              options={tickers.map((t) => ({ value: t, label: t }))}
              value={ticker}
              onChange={setTicker}
              placeholder={`Search ${assetType.toLowerCase()} tickers...`}
            />
          </label>
          <button className="run-button" onClick={() => track(ticker)} disabled={loading}>
            {loading ? "Loading..." : "Track"}
          </button>
          {error && <p className="error-text">{error}</p>}
        </aside>

        <div className="asset-main">
          {!live ? (
            <p className="hint-banner">
              Search a ticker and click <strong>Track</strong> to see today's live price and
              predicted close.
            </p>
          ) : (
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
                    <div className="metric-label">Predicted Close</div>
                    <div className="metric-value">${live.predicted_close.toFixed(2)}</div>
                    {delta !== null && (
                      <div className={"metric-delta " + (delta >= 0 ? "up" : "down")}>
                        {delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(2)} from current
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="metric-tile metric-tile-error">
                    <div className="metric-label">Predicted Close</div>
                    <div className="metric-error">{live.error ?? "Unavailable"}</div>
                  </div>
                )}
              </div>

              <div className="chart-wrap">
                <IntradayChart ticker={live.ticker} bars={live.intraday_bars} />
              </div>

              <h3>Predicted vs. Actual</h3>
              <div className="table-wrap">
                <table className="leaderboard">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Predicted Close</th>
                      <th>Actual Close</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {live.history.map((row) => {
                      const err = row.actual_close !== null ? row.actual_close - row.predicted_close : null;
                      return (
                        <tr key={row.trade_date}>
                          <td>{row.trade_date}</td>
                          <td>${row.predicted_close.toFixed(2)}</td>
                          <td>{row.actual_close !== null ? `$${row.actual_close.toFixed(2)}` : "—"}</td>
                          <td>
                            {err !== null
                              ? `${err >= 0 ? "+" : ""}${err.toFixed(2)} (${((err / row.predicted_close) * 100).toFixed(2)}%)`
                              : "—"}
                          </td>
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
