import { useEffect, useState } from "react";
import { getTickers, postForecast, getAnalystTarget } from "../api";
import type { AnalystTarget, AssetType, ForecastResponse, ModelResult } from "../types";
import ComparisonChart from "../components/ComparisonChart";
import AnalystComparisonChart from "../components/AnalystComparisonChart";
import SearchableSelect from "../components/SearchableSelect";
import InfoTip from "../components/InfoTip";
import { assetTypeLabel } from "../assetTypeLabel";

const PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"];

function mostAccurate(models: ModelResult[]): ModelResult | undefined {
  return [...models]
    .filter((m) => m.error === null && m.rmse !== null)
    .sort((a, b) => (a.rmse as number) - (b.rmse as number))[0];
}

interface Slot {
  assetType: AssetType;
  ticker: string;
  tickers: string[];
}

function SlotControls({
  label,
  slot,
  onChange,
}: {
  label: string;
  slot: Slot;
  onChange: (next: Slot) => void;
}) {
  return (
    <div className="asset-controls">
      <h3>{label}</h3>
      <label>
        Asset type
        <select
          value={slot.assetType}
          onChange={(e) => onChange({ ...slot, assetType: e.target.value as AssetType, ticker: "" })}
        >
          <option value="Stock">Stock</option>
          <option value="Crypto">Cryptocurrency</option>
        </select>
      </label>
      <label>
        Search or type any ticker symbol
        <SearchableSelect
          options={slot.tickers.map((t) => ({ value: t, label: t }))}
          value={slot.ticker}
          onChange={(ticker) => onChange({ ...slot, ticker: ticker.toUpperCase() })}
          placeholder={`Search ${assetTypeLabel(slot.assetType).toLowerCase()} tickers, or type any symbol...`}
          allowCreate
          ariaLabel={`Search or type any ticker symbol for ${label}`}
        />
      </label>
    </div>
  );
}

export default function ComparePage() {
  const [slotA, setSlotA] = useState<Slot>({ assetType: "Stock", ticker: "", tickers: [] });
  const [slotB, setSlotB] = useState<Slot>({ assetType: "Crypto", ticker: "", tickers: [] });
  const [period, setPeriod] = useState(PERIOD_OPTIONS[2]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forecastA, setForecastA] = useState<ForecastResponse | null>(null);
  const [forecastB, setForecastB] = useState<ForecastResponse | null>(null);
  const [targetA, setTargetA] = useState<AnalystTarget | null>(null);
  const [targetB, setTargetB] = useState<AnalystTarget | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(true);

  useEffect(() => {
    getTickers(slotA.assetType).then((r) =>
      setSlotA((s) => ({ ...s, tickers: r.tickers, ticker: s.ticker || r.tickers[0] })),
    );
  }, [slotA.assetType]);

  useEffect(() => {
    getTickers(slotB.assetType).then((r) =>
      setSlotB((s) => ({ ...s, tickers: r.tickers, ticker: s.ticker || r.tickers[0] })),
    );
  }, [slotB.assetType]);

  async function handleCompare() {
    if (!slotA.ticker.trim() || !slotB.ticker.trim()) {
      setError("Pick a ticker on both sides first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tickerA = slotA.ticker.trim().toUpperCase();
      const tickerB = slotB.ticker.trim().toUpperCase();
      const [a, b, tA, tB] = await Promise.all([
        postForecast(tickerA, slotA.assetType, period),
        postForecast(tickerB, slotB.assetType, period),
        getAnalystTarget(slotA.assetType, tickerA).catch(() => null),
        getAnalystTarget(slotB.assetType, tickerB).catch(() => null),
      ]);
      setForecastA(a);
      setForecastB(b);
      setTargetA(tA?.target ?? null);
      setTargetB(tB?.target ?? null);
      setSettingsOpen(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const bestA = forecastA ? mostAccurate(forecastA.models) : undefined;
  const bestB = forecastB ? mostAccurate(forecastB.models) : undefined;
  const pctChange = (result: ModelResult | undefined, lastClose: number | undefined) =>
    result && lastClose ? ((result.prediction as number) - lastClose) / lastClose : null;
  const pctA = bestA && forecastA ? pctChange(bestA, forecastA.last_close) : null;
  const pctB = bestB && forecastB ? pctChange(bestB, forecastB.last_close) : null;

  const modelRows =
    forecastA && forecastB
      ? forecastA.models
          .map((mA) => ({
            key: mA.key,
            name: mA.name,
            a: mA,
            b: forecastB.models.find((m) => m.key === mA.key),
          }))
          .sort((r1, r2) => {
            const avgRmse = (row: (typeof r1)) => ((row.a.rmse ?? Infinity) + (row.b?.rmse ?? Infinity)) / 2;
            return avgRmse(r1) - avgRmse(r2);
          })
      : [];

  const liveStatus = loading
    ? `Comparing ${slotA.ticker.trim().toUpperCase()} and ${slotB.ticker.trim().toUpperCase()}...`
    : error
      ? error
      : forecastA && forecastB
        ? `Comparison loaded for ${forecastA.ticker} and ${forecastB.ticker}.`
        : "";

  return (
    <div className="page">
      <div aria-live="polite" className="sr-only">
        {liveStatus}
      </div>
      <div className="asset-main-header">
        <h2>Compare Two Tickers</h2>
        {forecastA && forecastB && (
          <button className="ghost-button" onClick={() => setSettingsOpen((open) => !open)}>
            {settingsOpen ? "Hide settings" : "Change tickers"}
          </button>
        )}
      </div>
      <p className="muted">
        Run the same 10 forecasting models on two different tickersto see which one
        each model expects to have the better <strong>next trading day's closing price</strong>.
      </p>

      {settingsOpen && (
        <>
          <div className="compare-controls">
            <SlotControls label="Ticker A" slot={slotA} onChange={setSlotA} />
            <SlotControls label="Ticker B" slot={slotB} onChange={setSlotB} />
          </div>

          <div className="compare-submit">
            <label className="period-label">
              History length
              <select value={period} onChange={(e) => setPeriod(e.target.value)}>
                {PERIOD_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>

            <button className="run-button compare-button" onClick={handleCompare} disabled={loading}>
              {loading ? "Comparing..." : "Compare"}
            </button>
            {error && <p className="error-text">{error}</p>}
          </div>
        </>
      )}

      {forecastA && forecastB && (
        <>
          <div className="tile-grid compare-tile-grid">
            <div className="metric-tile">
              <div className="metric-label">{forecastA.ticker}</div>
              <div className="metric-category">Most accurate: {bestA?.name ?? "n/a"}</div>
              <div className="metric-value-label">Predicted Next-Day Close</div>
              {pctA !== null ? (
                <div className={"metric-delta " + (pctA >= 0 ? "up" : "down")}>
                  {pctA >= 0 ? "↑" : "↓"} forecasted {pctA >= 0 ? "+" : ""}
                  {(pctA * 100).toFixed(2)}%
                </div>
              ) : (
                <div className="metric-error">No confident prediction</div>
              )}
            </div>
            <div className="metric-tile">
              <div className="metric-label">{forecastB.ticker}</div>
              <div className="metric-category">Most accurate: {bestB?.name ?? "n/a"}</div>
              <div className="metric-value-label">Predicted Next-Day Close</div>
              {pctB !== null ? (
                <div className={"metric-delta " + (pctB >= 0 ? "up" : "down")}>
                  {pctB >= 0 ? "↑" : "↓"} forecasted {pctB >= 0 ? "+" : ""}
                  {(pctB * 100).toFixed(2)}%
                </div>
              ) : (
                <div className="metric-error">No confident prediction</div>
              )}
            </div>
          </div>

          {pctA !== null && pctB !== null && (
            <p className="muted">
              Based on each ticker's own most accurate model,{" "}
              <strong>{pctA > pctB ? forecastA.ticker : forecastB.ticker}</strong> is forecasted to
              outperform <strong>{pctA > pctB ? forecastB.ticker : forecastA.ticker}</strong> by{" "}
              {(Math.abs(pctA - pctB) * 100).toFixed(2)} percentage points.
            </p>
          )}

          <div className="chart-wrap">
            <ComparisonChart
              labelA={forecastA.ticker}
              barsA={forecastA.price_history}
              labelB={forecastB.ticker}
              barsB={forecastB.price_history}
            />
          </div>

          <h3>
            Model-by-model comparison
            <InfoTip text="Each model is trained separately on each ticker's own history. Typical error (RMSE) tells you how reliable that model has actually been for that specific ticker -- a model can be great for one and mediocre for the other." />
          </h3>
          <div className="table-wrap">
            <table className="leaderboard">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>{forecastA.ticker} Predicted Close</th>
                  <th>{forecastA.ticker} Typical Error</th>
                  <th>{forecastB.ticker} Predicted Close</th>
                  <th>{forecastB.ticker} Typical Error</th>
                </tr>
              </thead>
              <tbody>
                {modelRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.name}</td>
                    <td>
                      {row.a.error === null && row.a.prediction !== null
                        ? `$${row.a.prediction.toFixed(2)}`
                        : "—"}
                    </td>
                    <td>{row.a.rmse !== null ? `$${row.a.rmse.toFixed(2)}` : "—"}</td>
                    <td>
                      {row.b && row.b.error === null && row.b.prediction !== null
                        ? `$${row.b.prediction.toFixed(2)}`
                        : "—"}
                    </td>
                    <td>{row.b && row.b.rmse !== null ? `$${row.b.rmse.toFixed(2)}` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {(targetA || targetB) && (
            <>
              <h3>
                Analyst consensus
                <InfoTip text="Wall Street analysts' average 12-month price target -- a much longer horizon than the models above, which predict tomorrow's close. Shown for context, not as another next-day forecast. Crypto has no analyst-target concept, so it shows no coverage." />
              </h3>
              <div className="tile-grid compare-tile-grid">
                <div className="metric-tile">
                  <div className="metric-label">{forecastA.ticker}</div>
                  {targetA ? (
                    <>
                      <div className="metric-value-label">Mean 12-Month Target</div>
                      <div className="metric-value">${targetA.mean.toFixed(2)}</div>
                      <div className="metric-rmse">
                        Range {targetA.low !== null ? `$${targetA.low.toFixed(2)}` : "—"}
                        {" – "}
                        {targetA.high !== null ? `$${targetA.high.toFixed(2)}` : "—"}
                        {targetA.num_analysts !== null ? ` · ${targetA.num_analysts} analysts` : ""}
                        {targetA.recommendation ? ` · ${targetA.recommendation}` : ""}
                      </div>
                    </>
                  ) : (
                    <div className="metric-error">No analyst coverage</div>
                  )}
                </div>
                <div className="metric-tile">
                  <div className="metric-label">{forecastB.ticker}</div>
                  {targetB ? (
                    <>
                      <div className="metric-value-label">Mean 12-Month Target</div>
                      <div className="metric-value">${targetB.mean.toFixed(2)}</div>
                      <div className="metric-rmse">
                        Range {targetB.low !== null ? `$${targetB.low.toFixed(2)}` : "—"}
                        {" – "}
                        {targetB.high !== null ? `$${targetB.high.toFixed(2)}` : "—"}
                        {targetB.num_analysts !== null ? ` · ${targetB.num_analysts} analysts` : ""}
                        {targetB.recommendation ? ` · ${targetB.recommendation}` : ""}
                      </div>
                    </>
                  ) : (
                    <div className="metric-error">No analyst coverage</div>
                  )}
                </div>
              </div>

              <div className="analyst-chart-grid">
                {targetA && (
                  <div className="chart-wrap">
                    <AnalystComparisonChart
                      ticker={forecastA.ticker}
                      bars={forecastA.price_history}
                      prediction={bestA?.prediction ?? null}
                      target={targetA}
                    />
                  </div>
                )}
                {targetB && (
                  <div className="chart-wrap">
                    <AnalystComparisonChart
                      ticker={forecastB.ticker}
                      bars={forecastB.price_history}
                      prediction={bestB?.prediction ?? null}
                      target={targetB}
                    />
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
