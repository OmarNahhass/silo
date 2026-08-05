# Class Diagram

A conceptual model of CryptoCast's domain -- the backend is implemented functionally (plain
dicts and functions, not these classes literally), but this is the shape of the data as it flows
through the system.

```mermaid
classDiagram
    class ForecastModel {
        +string key
        +string name
        +string category
        +string math
        +string note
        +run(data) Prediction
    }

    class Ensemble {
        +float[] weights
        +combine(Prediction[]) Prediction
    }

    class Prediction {
        +string key
        +string name
        +float prediction
        +float rmse
        +FittedPoint[] fitted
        +string error
    }

    class DailyPrediction {
        +string ticker
        +string asset_type
        +string model_key
        +string as_of_date
        +float raw_prediction
        +float actual_close
        +float prior_close
    }

    class TrackRecordStat {
        +string key
        +int n_samples
        +float rmse
        +float mae
        +float mape
    }

    class AnalystTarget {
        +float mean
        +float high
        +float low
        +string recommendation
        +int num_analysts
    }

    Ensemble --|> ForecastModel : is a
    ForecastModel "1" --> "*" Prediction : produces
    ForecastModel "1" --> "*" DailyPrediction : recorded as
    DailyPrediction "*" --> "1" TrackRecordStat : aggregated into
```

- **ForecastModel** -- one of the 10 models (Linear Regression, ARIMA, ... SVR); `Ensemble` is a
  special case that combines every other model's `Prediction` by inverse-variance weighting.
- **Prediction** -- what a model returns for a single forecast request: the predicted price, its
  historical RMSE, and its fitted values for charting.
- **DailyPrediction** -- the persisted row (SQLite) behind every prediction, used for both
  bias-correction and Track Record scoring once `actual_close` resolves.
- **TrackRecordStat** -- the aggregate accuracy (RMSE / MAE / MAPE) computed from many
  `DailyPrediction` rows for a given model.
- **AnalystTarget** -- the external Yahoo Finance consensus price target shown for comparison on
  the Compare page.
