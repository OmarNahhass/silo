import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTickers, getModels, postForecast, getTrackRecord, getSimilarTickers } from "../api";
import { useForecast } from "../context/ForecastContext";
import { useSlowLoadingHint } from "../hooks/useSlowLoadingHint";
import type { AssetType, ModelMeta, ModelResult, TrackRecordResponse, SimilarTickersResponse } from "../types";
import PriceChart from "../components/PriceChart";
import ModelDetail from "../components/ModelDetail";
import SearchableSelect from "../components/SearchableSelect";
import InfoTip from "../components/InfoTip";
import MetricTile from "../components/MetricTile";
import Leaderboard from "../components/Leaderboard";
import SimilarTickers from "../components/SimilarTickers";
import { assetTypeLabel } from "../assetTypeLabel";

const PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"];

function mostAccurate(models: ModelResult[]): ModelResult | undefined {
  return [...models]
    .filter((m) => m.error === null && m.rmse !== null)
    .sort((a, b) => (a.rmse as number) - (b.rmse as number))[0];
}

export default function AssetPage({ assetType }: { assetType: AssetType }) {
  const { forecast, setForecast } = useForecast();

  const [tickers, setTickers] = useState<string[]>([]);
  const [ticker, setTicker] = useState("");
  const [period, setPeriod] = useState(PERIOD_OPTIONS[2]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(true);

  const [models, setModels] = useState<ModelMeta[]>([]);
  const [selectedKey, setSelectedKey] = useState<string>("");
  const [sortByAccuracy, setSortByAccuracy] = useState(true);
  const [trackRecord, setTrackRecord] = useState<TrackRecordResponse | null>(null);
  const [tickersError, setTickersError] = useState(false);
  const [similarTickers, setSimilarTickers] = useState<SimilarTickersResponse | null>(null);
  const [similarError, setSimilarError] = useState(false);
  const [similarLoading, setSimilarLoading] = useState(false);
  const showSlowHint = useSlowLoadingHint(loading);
  const showSimilarSlowHint = useSlowLoadingHint(similarLoading);

  function loadTickers() {
    setTickersError(false);
    getTickers(assetType)
      .then((r) => {
        setTickers(r.tickers);
        setTicker((current) => current || r.tickers[0]);
      })
      .catch(() => setTickersError(true));
  }

  useEffect(loadTickers, [assetType]);

  useEffect(() => {
    getModels().then(setModels);
  }, []);

  const matchingForecast = forecast && forecast.asset_type === assetType ? forecast : null;

  useEffect(() => {
    if (!matchingForecast) {
      setTrackRecord(null);
      return;
    }
    getTrackRecord(assetType, matchingForecast.ticker)
      .then(setTrackRecord)
      .catch(() => setTrackRecord(null));
  }, [assetType, matchingForecast]);

  function loadSimilarTickers() {
    if (!matchingForecast) {
      setSimilarTickers(null);
      setSimilarError(false);
      return;
    }
    setSimilarLoading(true);
    setSimilarError(false);
    getSimilarTickers(assetType, matchingForecast.ticker)
      .then((r) => setSimilarTickers(r))
      .catch(() => setSimilarError(true))
      .finally(() => setSimilarLoading(false));
  }

  useEffect(loadSimilarTickers, [assetType, matchingForecast]);

  useEffect(() => {
    if (matchingForecast && !selectedKey) {
      const best = mostAccurate(matchingForecast.models);
      setSelectedKey(best?.key ?? matchingForecast.models[0]?.key ?? "");
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
      const best = mostAccurate(result.models);
      setSelectedKey(best?.key ?? result.models[0]?.key ?? "");
      setSettingsOpen(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
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

  const ranked = matchingForecast
    ? [...matchingForecast.models]
        .filter((m) => m.error === null && m.rmse !== null)
        .sort((a, b) => (a.rmse as number) - (b.rmse as number))
    : [];
  const failed = matchingForecast ? matchingForecast.models.filter((m) => m.error !== null || m.rmse === null) : [];

  const selectedResult = matchingForecast?.models.find((m) => m.key === selectedKey);
  const selectedMeta = models.find((m) => m.key === selectedKey);

  const liveStatus = loading
    ? showSlowHint
      ? "Still working -- the server may be waking up from being idle, this can take up to about 30 seconds."
      : `Running forecast for ${ticker.trim().toUpperCase()}...`
    : error
      ? error
      : matchingForecast
        ? `Forecast loaded for ${matchingForecast.ticker}. Top model: ${ranked[0]?.name ?? "none"}.`
        : "";

  return (
    <div className="page asset-layout">
      <div aria-live="polite" className="sr-only">
        {liveStatus}
      </div>
      <div className="asset-main-header">
        <h2>{assetTypeLabel(assetType)} Forecasts</h2>
        {matchingForecast && (
          <button className="ghost-button" onClick={() => setSettingsOpen((open) => !open)}>
            {settingsOpen ? "Hide settings" : "Change ticker"}
          </button>
        )}
      </div>
      <p className="muted">
        Runs 10 different forecasting models on a ticker's price history to predict its{" "}
        <strong>next trading day's closing price</strong>, and shows which ones have actually
        been most accurate for it.
      </p>

      {settingsOpen && (
        <aside className="asset-controls">
          <h3>{assetTypeLabel(assetType)} Settings</h3>
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
            {tickersError && (
              <span className="error-text">
                Couldn't load the ticker list -- you can still type a symbol directly, or{" "}
                <button type="button" className="link-button" onClick={loadTickers}>
                  try again
                </button>
                .
              </span>
            )}
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
          {showSlowHint && (
            <p className="muted">
              Still working -- the server may be waking up from being idle, this can take up to
              about 30 seconds.
            </p>
          )}
          {error && <p className="error-text">{error}</p>}
        </aside>
      )}

      {matchingForecast && (
        <div className="asset-main">
          <h3>
            {matchingForecast.ticker} — {matchingForecast.trading_days} trading days
          </h3>
          {(() => {
            const ensembleStat = trackRecord?.per_model.find((m) => m.key === "ensemble");
            const naive = trackRecord?.naive_baseline;
            if (!ensembleStat || !naive || ensembleStat.n_samples === 0) return null;
            return (
              <p className="muted">
                Ensemble's typical error over its last {ensembleStat.n_samples} tracked day
                {ensembleStat.n_samples === 1 ? "" : "s"} for {matchingForecast.ticker}: $
                {ensembleStat.mae.toFixed(2)} (vs ${naive.mae.toFixed(2)} assuming no change). See the{" "}
                <Link to="/track-record">full track record</Link>.
              </p>
            );
          })()}

          <h4>
            Similar Tickers
            <InfoTip text="Other tickers whose current technical-indicator pattern (momentum, trend, volatility) most closely resembles this one, ranked by cosine similarity. This is about recent price behavior, not whether the companies are actually related." />
          </h4>
          {similarLoading && !similarTickers && (
            <p className="muted">
              Finding similar tickers...
              {showSimilarSlowHint && (
                <>
                  {" "}
                  Still working -- this can take longer the first time, up to about 30 seconds.
                </>
              )}
            </p>
          )}
          {similarError && (
            <p className="error-text">
              Couldn't load similar tickers.{" "}
              <button type="button" className="link-button" onClick={loadSimilarTickers}>
                try again
              </button>
              .
            </p>
          )}
          {similarTickers && <SimilarTickers results={similarTickers.results} />}

          <div className="chart-wrap">
            <PriceChart ticker={matchingForecast.ticker} bars={matchingForecast.price_history} />
          </div>

          <h3>Forecasts — ranked by accuracy</h3>
          <p className="muted">
            #1 is the model that was most accurate when tested against recent past data for{" "}
            {matchingForecast.ticker} specifically — not just guessed to be best. That's often{" "}
            <strong>Ensemble (Weighted Average)</strong>, which combines all 10 individual models
            into one prediction rather than betting on a single one.
          </p>
          <div className="tile-grid">
            {ranked.map((m, i) => (
              <MetricTile key={m.key} result={m} lastClose={matchingForecast.last_close} rank={i + 1} />
            ))}
            {failed.map((m) => (
              <MetricTile key={m.key} result={m} lastClose={matchingForecast.last_close} />
            ))}
          </div>

          <h4>
            Leaderboard — most accurate first
            <InfoTip text="Ranked by typical error (RMSE) on data each model didn't train on. Lower error means its past predictions were, on average, closer to what actually happened." />
          </h4>
          <Leaderboard models={matchingForecast.models} />

          <h3>
            Select a forecasting model
            <InfoTip text="Each model uses a different approach to guess tomorrow's price. None are perfect -- comparing several is how you tell a lucky guess from a genuinely useful one." />
          </h3>
          <p className="muted">
            Don't want to pick just one? <strong>Ensemble (Weighted Average)</strong> combines
            all 10 into a single prediction, weighted by how accurate each has actually been for
            this ticker. It's usually the single most accurate option here -- look for it in the
            list below.
          </p>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={sortByAccuracy}
              onChange={(e) => setSortByAccuracy(e.target.checked)}
            />
            Sort by accuracy (most accurate first)
          </label>
          <label>
            Forecasting model
            <SearchableSelect
              options={orderedModels.map((m, i) => ({
                value: m.key,
                label:
                  (sortByAccuracy && m.rmse !== null ? `#${i + 1} ` : "") +
                  m.name +
                  (m.rmse !== null ? ` — avg error $${m.rmse.toFixed(2)}` : m.error ? " (failed)" : ""),
              }))}
              value={selectedKey}
              onChange={setSelectedKey}
              placeholder="Search models..."
              ariaLabel="Forecasting model"
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
        </div>
      )}
    </div>
  );
}
