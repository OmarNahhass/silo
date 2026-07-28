import { useForecast } from "../context/ForecastContext";
import PriceChart from "../components/PriceChart";
import MetricTile from "../components/MetricTile";
import Leaderboard from "../components/Leaderboard";

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

  const categories = [...new Set(forecast.models.map((m) => m.category))];

  return (
    <div className="page">
      <h2>
        {forecast.ticker} — {forecast.trading_days} trading days
      </h2>
      <PriceChart ticker={forecast.ticker} bars={forecast.price_history} />

      <h3>Forecasts</h3>
      <p className="muted">
        Go to <strong>{forecast.asset_type}</strong> in the sidebar to pick one model's full
        chart and math.
      </p>

      {categories.map((category) => (
        <div key={category}>
          <h4>{category} Models</h4>
          <div className="tile-grid">
            {forecast.models
              .filter((m) => m.category === category)
              .map((m) => (
                <MetricTile key={m.key} result={m} lastClose={forecast.last_close} />
              ))}
          </div>
        </div>
      ))}

      <h4>Leaderboard (ranked by holdout RMSE — lower is better)</h4>
      <Leaderboard models={forecast.models} />
    </div>
  );
}
