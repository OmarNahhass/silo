# Forecast Request Sequence

What happens when a user clicks "Run Forecast" on the Stock, Crypto, or Compare page.

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as POST /api/forecast
    participant YF as yfinance
    participant Models as 10 models<br/>(ThreadPoolExecutor)
    participant Hist as prediction_history.py
    participant DB as SQLite

    User->>FE: Click "Run Forecast"
    FE->>API: {ticker, asset_type, period}
    API->>YF: fetch_data(ticker)
    YF-->>API: OHLCV price history
    API->>Models: run all 10 models in parallel
    Models-->>API: prediction + RMSE per model
    API->>Hist: record_and_correct(raw predictions)
    Hist->>DB: upsert predictions, backfill prior day's actual_close
    Hist-->>API: rolling bias correction per model
    API->>API: apply corrections, compute ensemble<br/>(inverse-variance weighted average)
    API->>Hist: record_prediction("ensemble", ...)
    Hist->>DB: upsert ensemble row (tracking only)
    API-->>FE: models[] + ensemble + price history
    FE-->>User: renders chart, ranked tiles, leaderboard
```

The ensemble's own prediction is tracked separately from the 10 individual models specifically so
its accuracy can be measured later -- see [Track Record](track-record-sequence.md).
