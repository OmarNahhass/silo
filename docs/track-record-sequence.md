# Track Record: Prediction Resolution & Scoring

Every prediction is written the moment it's made, then resolved the next time that ticker is
forecasted on a later trading day -- no scheduler required.

```mermaid
sequenceDiagram
    actor User
    participant D1 as POST /api/forecast (day 1)
    participant DB as SQLite daily_predictions
    participant D2 as POST /api/forecast (day 2, same ticker)
    participant TR as GET /api/track-record
    participant FE as Frontend

    D1->>DB: INSERT prediction for as_of_date=day1<br/>(actual_close = NULL, prior_close = day1's close)

    Note over D2,DB: Some time later...
    D2->>DB: _resolve_pending()<br/>backfills day1's actual_close using day2's price data

    FE->>TR: GET /api/track-record?ticker=...
    TR->>DB: get_resolved_predictions()<br/>(WHERE actual_close IS NOT NULL)
    DB-->>TR: rows with prediction + actual outcome
    TR->>TR: per model: RMSE / MAE / MAPE
    TR->>TR: ensemble rows only: paired t-test vs.<br/>naive "no change" baseline (prior_close)
    TR-->>FE: per-model stats + significance verdict
    FE-->>User: ranked accuracy table + plain-language verdict
```

The naive baseline for a given day is simply "the price won't move" -- the closing price at
prediction time. The paired t-test (`scipy.stats.ttest_1samp` on the per-day difference in
absolute error) answers a concrete question: does the ensemble's error actually differ from the
naive baseline's, with at least 20 resolved days before the test is considered meaningful.
