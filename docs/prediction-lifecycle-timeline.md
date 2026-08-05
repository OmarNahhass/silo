# Prediction Lifecycle Timeline

The life of a single prediction, from the moment it's made to the moment it counts toward Track
Record -- no scheduler involved, every step is a side effect of a real API request.

```mermaid
timeline
    title Lifecycle of a Single Prediction
    section Day 1 — Prediction made
        POST /api/forecast is called : model predicts next close : row inserted with actual_close = NULL : prior_close set to today's close
    section Day 2 — Same ticker forecasted again
        _resolve_pending() runs automatically : actual_close backfilled from day 2's price data : prediction is now "resolved"
    section Anytime after — Track Record queried
        get_resolved_predictions() includes the row : RMSE / MAE / MAPE computed for its model : ensemble rows feed the naive-baseline significance test
```

Nothing is scored until it resolves, and nothing is discarded -- a prediction sits as "pending"
for as long as it takes before that ticker is forecasted again, which is also what backfills its
`actual_close`.
