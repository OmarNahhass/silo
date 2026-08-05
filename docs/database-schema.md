# Database Schema

Two SQLite tables, both append/upsert-only with no scheduled jobs -- every write happens as a
side effect of a real API request.

```mermaid
erDiagram
    daily_predictions {
        text ticker PK
        text asset_type PK
        text model_key PK
        text as_of_date PK
        real raw_prediction
        text predicted_at
        real actual_close "NULL until resolved"
        real prior_close "naive-baseline input"
    }

    intraday_predictions {
        text ticker PK
        text asset_type PK
        text trade_date PK
        real predicted_close
        real open_price
        real price_at_prediction
        text predicted_at
        real actual_close "NULL until resolved"
    }
```

`daily_predictions` holds one row per (ticker, asset type, model, date) -- including a synthetic
`model_key = "ensemble"` row -- and backs both the rolling bias-correction shown live in the
Forecast pages and the [Track Record](track-record-sequence.md) statistics.

`intraday_predictions` is the same idea at intraday granularity for the Live page: one row per
(ticker, asset type, trade date), resolved once the trading day ends.
