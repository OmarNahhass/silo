import { useEffect, useState } from "react";
import { getTickers, getTrackRecord } from "../api";
import { useSlowLoadingHint } from "../hooks/useSlowLoadingHint";
import type { AssetType, TrackRecordResponse } from "../types";
import SearchableSelect from "../components/SearchableSelect";
import TrackRecordTable from "../components/TrackRecordTable";
import InfoTip from "../components/InfoTip";

type AssetTypeFilter = "All" | AssetType;

const PERIOD_OPTIONS = [
  { label: "All time", days: null },
  { label: "Last 90 days", days: 90 },
  { label: "Last 30 days", days: 30 },
];

function sinceFor(days: number | null): string | undefined {
  if (days === null) return undefined;
  return new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);
}

export default function TrackRecordPage() {
  const [assetTypeFilter, setAssetTypeFilter] = useState<AssetTypeFilter>("All");
  const [stockTickers, setStockTickers] = useState<string[]>([]);
  const [cryptoTickers, setCryptoTickers] = useState<string[]>([]);
  const [ticker, setTicker] = useState("");
  const [periodDays, setPeriodDays] = useState<number | null>(null);
  const [data, setData] = useState<TrackRecordResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(true);
  const showSlowHint = useSlowLoadingHint(loading);
  const [tickersError, setTickersError] = useState(false);

  function loadTickers() {
    setTickersError(false);
    Promise.all([getTickers("Stock"), getTickers("Crypto")])
      .then(([stock, crypto]) => {
        setStockTickers(stock.tickers);
        setCryptoTickers(crypto.tickers);
      })
      .catch(() => setTickersError(true));
  }

  useEffect(loadTickers, []);

  const tickerAssetType: Record<string, AssetType> = {};
  stockTickers.forEach((t) => (tickerAssetType[t] = "Stock"));
  cryptoTickers.forEach((t) => (tickerAssetType[t] = "Crypto"));

  const tickerOptions =
    assetTypeFilter === "All"
      ? [...stockTickers, ...cryptoTickers]
      : assetTypeFilter === "Stock"
        ? stockTickers
        : cryptoTickers;

  async function handleViewTrackRecord() {
    const effectiveAssetType: AssetType | undefined =
      assetTypeFilter === "All" ? (ticker ? tickerAssetType[ticker] : undefined) : assetTypeFilter;

    setLoading(true);
    setError(null);
    try {
      const result = await getTrackRecord(effectiveAssetType, ticker || undefined, sinceFor(periodDays));
      setData(result);
      setSettingsOpen(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const test = data?.ensemble_vs_naive_test ?? null;
  const naive = data?.naive_baseline ?? null;
  const ensembleStat = data?.per_model.find((m) => m.key === "ensemble") ?? null;

  const liveStatus = loading
    ? showSlowHint
      ? "Still working -- the server may be waking up from being idle, this can take up to about 30 seconds."
      : "Loading track record..."
    : error
      ? error
      : data
        ? `Track record loaded, ${data.per_model.length} model${data.per_model.length === 1 ? "" : "s"}.`
        : "";

  return (
    <div className="page asset-layout">
      <div aria-live="polite" className="sr-only">
        {liveStatus}
      </div>
      <div className="asset-main-header">
        <h2>Track Record</h2>
        {data && (
          <button className="ghost-button" onClick={() => setSettingsOpen((open) => !open)}>
            {settingsOpen ? "Hide filters" : "Change filters"}
          </button>
        )}
      </div>
      <p className="muted">
        Every forecast this app has ever made gets checked against what actually happened the
        next trading day. This is that.
      </p>

      {settingsOpen && (
        <aside className="asset-controls">
          <h3>Filter</h3>
          <label>
            Asset type
            <select
              value={assetTypeFilter}
              onChange={(e) => {
                setAssetTypeFilter(e.target.value as AssetTypeFilter);
                setTicker("");
              }}
            >
              <option value="All">All</option>
              <option value="Stock">Stock</option>
              <option value="Crypto">Cryptocurrency</option>
            </select>
          </label>
          <label>
            Search or type any ticker symbol
            <SearchableSelect
              options={[
                { value: "", label: "All tickers" },
                ...tickerOptions.map((t) => ({ value: t, label: t })),
              ]}
              value={ticker}
              onChange={setTicker}
              placeholder="Search tickers..."
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
            Window
            <select
              value={periodDays ?? ""}
              onChange={(e) => setPeriodDays(e.target.value === "" ? null : Number(e.target.value))}
            >
              {PERIOD_OPTIONS.map((p) => (
                <option key={p.label} value={p.days ?? ""}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <button className="run-button" onClick={handleViewTrackRecord} disabled={loading}>
            {loading ? "Loading..." : "View Track Record"}
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

      {data && (
        <div className="asset-main">
          <h3>
            Ensemble vs. naive baseline
            <InfoTip text="The naive baseline is the simplest possible forecast: assume tomorrow's close equals today's. If the ensemble can't reliably beat that, it isn't adding value." />
          </h3>

          {test ? (
            <p className="muted">{test.verdict}</p>
          ) : naive && ensembleStat ? (
            <p className="muted">
              {ensembleStat.n_samples} resolved prediction{ensembleStat.n_samples === 1 ? "" : "s"} so
              far — not enough yet for a statistically meaningful test (need at least 20).
            </p>
          ) : (
            <p className="muted">
              No resolved ensemble history in this scope yet. Predictions get checked against
              reality the day after they're made, so come back once a few forecasts have had
              time to resolve.
            </p>
          )}

          {naive && ensembleStat && (
            <div className="tile-grid">
              <div className="metric-tile">
                <div className="metric-label">Ensemble — typical error</div>
                <div className="metric-value">${ensembleStat.mae.toFixed(2)}</div>
                <div className="metric-rmse">{ensembleStat.n_samples} samples</div>
              </div>
              <div className="metric-tile">
                <div className="metric-label">Naive baseline — typical error</div>
                <div className="metric-value">${naive.mae.toFixed(2)}</div>
                <div className="metric-rmse">{naive.n_samples} samples</div>
              </div>
            </div>
          )}

          <h3>Per-model accuracy</h3>
          {data.per_model.length > 0 ? (
            <TrackRecordTable models={data.per_model} />
          ) : (
            <p className="muted">No resolved predictions in this scope yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
