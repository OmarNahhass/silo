# Backend Module Dependencies

```mermaid
flowchart TD
    api["api.py<br/>(FastAPI routes)"]
    data_fetcher["data_fetcher.py"]
    model_registry["model_registry.py"]
    prediction_history["prediction_history.py"]
    track_record["track_record.py"]
    live_forecast["live_forecast.py"]
    analyst_targets["analyst_targets.py"]
    models["models/*.py<br/>(10 forecasting models)"]
    utils_metrics["utils/metrics.py"]
    utils_features["utils/features.py"]
    utils_tickers["utils/tickers.py"]

    api --> data_fetcher
    api --> model_registry
    api --> prediction_history
    api --> track_record
    api --> live_forecast
    api --> analyst_targets
    api --> utils_tickers

    model_registry --> models
    models --> utils_features

    track_record --> prediction_history
    track_record --> model_registry
    track_record --> utils_metrics

    live_forecast --> data_fetcher
```

Each model in `models/` exposes a single `perform_*` function returning a prediction, its RMSE,
and its fitted values; `model_registry.py` is the single source of truth for the 10 models' keys,
names, formulas, and explanations, shared by every endpoint that needs them.
