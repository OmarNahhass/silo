import { useForecast } from "../context/ForecastContext";
import PriceChart from "../components/PriceChart";
import MetricTile from "../components/MetricTile";
import Leaderboard from "../components/Leaderboard";
import InfoTip from "../components/InfoTip";

export default function Overview() {
  const { forecast } = useForecast();

  if (!forecast) {
    return (
      <div className="page">
        <p className="hint-banner">
          Pick <strong>Stock</strong> or <strong>Crypto</strong> in the sidebar to search a
          ticker and run a forecast.
        </p>
      </div>
    );
  }

  // Ranked by accuracy (lowest holdout RMSE first) rather than grouped by category --
  // the point is that anyone unfamiliar with these models can tell at a glance which
  // one to trust most for this specific ticker. Models that failed to run sort last.
  // Includes the Ensemble (weighted average of the other 10) as just another entry --
  // it usually ranks #1 since combining models tends to cancel out individual mistakes.
  const ranked = [...forecast.models]
    .filter((m) => m.error === null && m.rmse !== null)
    .sort((a, b) => (a.rmse as number) - (b.rmse as number));
  const failed = forecast.models.filter((m) => m.error !== null || m.rmse === null);

  return (
    <div className="page">
      <h2>
        {forecast.ticker} — {forecast.trading_days} trading days
      </h2>
      <div className="chart-wrap">
        <PriceChart ticker={forecast.ticker} bars={forecast.price_history} />
      </div>

      <h3>Forecasts — ranked by accuracy</h3>
      <p className="muted">
        #1 is the model that was most accurate when tested against recent past data for{" "}
        {forecast.ticker} specifically — not just guessed to be best. That's often{" "}
        <strong>Ensemble (Weighted Average)</strong>, which combines all 10 individual models
        into one prediction rather than betting on a single one. Go to{" "}
        <strong>{forecast.asset_type}</strong> in the sidebar to pick one model's full chart and
        the math behind it.
      </p>

      <div className="tile-grid">
        {ranked.map((m, i) => (
          <MetricTile key={m.key} result={m} lastClose={forecast.last_close} rank={i + 1} />
        ))}
        {failed.map((m) => (
          <MetricTile key={m.key} result={m} lastClose={forecast.last_close} />
        ))}
      </div>

      <h4>
        Leaderboard — most accurate first
        <InfoTip text="Ranked by typical error (RMSE) on data each model didn't train on. Lower error means its past predictions were, on average, closer to what actually happened." />
      </h4>
      <Leaderboard models={forecast.models} />
    </div>
  );
}
