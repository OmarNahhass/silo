import { useEffect, useState } from "react";
import { getTickers, getModels, postForecast } from "../api";
import { useForecast } from "../context/ForecastContext";
import type { AssetType, ModelMeta } from "../types";
import PriceChart from "../components/PriceChart";
import ModelDetail from "../components/ModelDetail";
import SearchableSelect from "../components/SearchableSelect";

const PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"];

export default function AssetPage({ assetType }: { assetType: AssetType }) {
  const { forecast, setForecast } = useForecast();

  const [tickers, setTickers] = useState<string[]>([]);
  const [ticker, setTicker] = useState("");
  const [period, setPeriod] = useState(PERIOD_OPTIONS[2]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [models, setModels] = useState<ModelMeta[]>([]);
  const [selectedKey, setSelectedKey] = useState<string>("");
  const [sortByAccuracy, setSortByAccuracy] = useState(false);

  useEffect(() => {
    getTickers(assetType).then((r) => {
      setTickers(r.tickers);
      setTicker((current) => current || r.tickers[0]);
    });
  }, [assetType]);

  useEffect(() => {
    getModels().then(setModels);
  }, []);

  const matchingForecast = forecast && forecast.asset_type === assetType ? forecast : null;

  useEffect(() => {
    if (matchingForecast && !selectedKey) {
      setSelectedKey(matchingForecast.models[0]?.key ?? "");
    }
  }, [matchingForecast, selectedKey]);

  async function handleRunForecast() {
    if (!ticker.trim()) {
      setError("Enter a ticker symbol first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await postForecast(ticker.trim().toUpperCase(), assetType, period);
      setForecast(result);
      setSelectedKey(result.models[0]?.key ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const orderedModels = matchingForecast
    ? [...matchingForecast.models].sort((a, b) => {
        if (!sortByAccuracy) return 0;
        const ra = a.rmse ?? Infinity;
        const rb = b.rmse ?? Infinity;
        return ra - rb;
      })
    : [];

  const selectedResult = matchingForecast?.models.find((m) => m.key === selectedKey);
  const selectedMeta = models.find((m) => m.key === selectedKey);

  return (
    <div className="page asset-layout">
      <aside className="asset-controls">
        <h3>{assetType} Settings</h3>
        <label>
          Search ticker symbol
          <SearchableSelect
            options={tickers.map((t) => ({ value: t, label: t }))}
            value={ticker}
            onChange={setTicker}
            placeholder={`Search ${assetType.toLowerCase()} tickers...`}
          />
        </label>
        <label>
          History length
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            {PERIOD_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <button className="run-button" onClick={handleRunForecast} disabled={loading}>
          {loading ? "Running..." : "Run Forecast"}
        </button>
        {error && <p className="error-text">{error}</p>}
      </aside>

      <div className="asset-main">
        <h2>{assetType} Forecasts</h2>

        {!matchingForecast ? (
          <p className="hint-banner">
            Search a {assetType.toLowerCase()} ticker in the sidebar, then click{" "}
            <strong>Run Forecast</strong>.
          </p>
        ) : (
          <>
            <h3>
              {matchingForecast.ticker} — {matchingForecast.trading_days} trading days
            </h3>
            <PriceChart ticker={matchingForecast.ticker} bars={matchingForecast.price_history} />

            <h3>Select a forecasting model</h3>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={sortByAccuracy}
                onChange={(e) => setSortByAccuracy(e.target.checked)}
              />
              Sort by most accurate (lowest holdout RMSE first)
            </label>
            <label>
              Forecasting model
              <SearchableSelect
                options={orderedModels.map((m) => ({
                  value: m.key,
                  label:
                    m.name +
                    (m.rmse !== null ? ` — RMSE $${m.rmse.toFixed(2)}` : m.error ? " (failed)" : ""),
                }))}
                value={selectedKey}
                onChange={setSelectedKey}
                placeholder="Search models..."
              />
            </label>

            {selectedResult && (
              <ModelDetail
                result={selectedResult}
                meta={selectedMeta}
                bars={matchingForecast.price_history}
                lastClose={matchingForecast.last_close}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
