"""Live intraday close prediction: fetch today's bars so far, predict the closing
price via models/intraday_regression.py, persist the prediction in a local SQLite DB,
and lazily backfill each day's actual close once it's known. No scheduler/cron --
everything resolves the next time get_live_forecast() is called.
"""

import sqlite3
import time
from pathlib import Path

from data_fetcher import fetch_data, fetch_intraday
from models.intraday_regression import predict_intraday_close

DB_PATH = Path(__file__).parent / "data" / "predictions.db"
HISTORY_CACHE_TTL = 15 * 60  # seconds
_history_cache: dict[tuple[str, str], tuple[float, object]] = {}


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS intraday_predictions (
            ticker TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            predicted_close REAL NOT NULL,
            open_price REAL NOT NULL,
            price_at_prediction REAL NOT NULL,
            predicted_at TEXT NOT NULL,
            actual_close REAL,
            PRIMARY KEY (ticker, asset_type, trade_date)
        )
        """
    )
    conn.commit()
    conn.close()


def _cached_history(ticker: str, asset_type: str):
    key = (ticker, asset_type)
    cached = _history_cache.get(key)
    now = time.time()
    if cached and now - cached[0] < HISTORY_CACHE_TTL:
        return cached[1]
    history = fetch_intraday(ticker, asset_type, period="60d", interval="5m")
    _history_cache[key] = (now, history)
    return history


def _upsert_prediction(conn, ticker, asset_type, trade_date, predicted_close, open_price, price_at_prediction):
    conn.execute(
        """
        INSERT INTO intraday_predictions
            (ticker, asset_type, trade_date, predicted_close, open_price, price_at_prediction, predicted_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(ticker, asset_type, trade_date) DO UPDATE SET
            predicted_close = excluded.predicted_close,
            open_price = excluded.open_price,
            price_at_prediction = excluded.price_at_prediction,
            predicted_at = excluded.predicted_at
        """,
        (ticker, asset_type, trade_date, predicted_close, open_price, price_at_prediction),
    )
    conn.commit()


def _backfill_actual_closes(conn, ticker, asset_type, today_trade_date):
    # Compare against the ticker's own trade_date (derived from its tz-aware bar
    # index -- ET for stocks, UTC for crypto) rather than SQLite's date('now'),
    # which is always UTC and would treat a stock's still-current session as
    # already "past" during the evening ET hours after UTC has rolled to the next day.
    pending = conn.execute(
        """
        SELECT trade_date FROM intraday_predictions
        WHERE ticker = ? AND asset_type = ? AND actual_close IS NULL
          AND trade_date < ?
        """,
        (ticker, asset_type, today_trade_date),
    ).fetchall()

    if not pending:
        return

    try:
        daily = fetch_data(ticker, asset_type=asset_type, period="1mo")
    except Exception:
        return

    close_by_date = {ts.strftime("%Y-%m-%d"): float(c) for ts, c in daily["Close"].dropna().items()}

    for (trade_date,) in pending:
        actual = close_by_date.get(trade_date)
        if actual is not None:
            conn.execute(
                "UPDATE intraday_predictions SET actual_close = ? WHERE ticker = ? AND asset_type = ? AND trade_date = ?",
                (actual, ticker, asset_type, trade_date),
            )
    conn.commit()


def get_live_forecast(ticker: str, asset_type: str) -> dict:
    ticker = ticker.strip().upper()
    today_bars = fetch_intraday(ticker, asset_type, period="1d", interval="5m")
    history_bars = _cached_history(ticker, asset_type)

    trade_date = today_bars.index[-1].strftime("%Y-%m-%d")
    open_price = float(today_bars["Open"].iloc[0])
    current_price = float(today_bars["Close"].iloc[-1])

    error = None
    predicted_close = None
    try:
        result = predict_intraday_close(today_bars, history_bars)
        predicted_close = result["prediction"]
    except Exception as e:
        error = str(e)

    conn = sqlite3.connect(DB_PATH)
    try:
        if predicted_close is not None:
            _upsert_prediction(conn, ticker, asset_type, trade_date, predicted_close, open_price, current_price)
        _backfill_actual_closes(conn, ticker, asset_type, trade_date)

        history_rows = conn.execute(
            """
            SELECT trade_date, predicted_close, price_at_prediction, actual_close
            FROM intraday_predictions
            WHERE ticker = ? AND asset_type = ?
            ORDER BY trade_date DESC LIMIT 20
            """,
            (ticker, asset_type),
        ).fetchall()
    finally:
        conn.close()

    intraday_bars = [
        {"time": ts.strftime("%Y-%m-%d %H:%M"), "price": float(row["Close"])}
        for ts, row in today_bars.iterrows()
    ]

    # naive_close is the "no change" baseline: whatever the price was at the moment
    # the prediction was made, i.e. the naive forecast that the close = current price.
    history = [
        {"trade_date": trade_date, "predicted_close": predicted, "naive_close": naive, "actual_close": actual}
        for trade_date, predicted, naive, actual in reversed(history_rows)
    ]

    resolved = [row for row in history if row["actual_close"] is not None]
    model_mae = (
        sum(abs(row["actual_close"] - row["predicted_close"]) for row in resolved) / len(resolved)
        if resolved
        else None
    )
    naive_mae = (
        sum(abs(row["actual_close"] - row["naive_close"]) for row in resolved) / len(resolved)
        if resolved
        else None
    )

    return {
        "ticker": ticker,
        "asset_type": asset_type,
        "trade_date": trade_date,
        "open_price": open_price,
        "current_price": current_price,
        "predicted_close": predicted_close,
        "error": error,
        "intraday_bars": intraday_bars,
        "history": history,
        "model_mae": model_mae,
        "naive_mae": naive_mae,
        "n_resolved": len(resolved),
    }
