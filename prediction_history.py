import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "predictions.db"
MIN_BIAS_SAMPLES = 10
BIAS_WINDOW = 30


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_predictions (
            ticker TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            model_key TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            raw_prediction REAL NOT NULL,
            predicted_at TEXT NOT NULL,
            actual_close REAL,
            PRIMARY KEY (ticker, asset_type, model_key, as_of_date)
        )
        """
    )
    conn.commit()
    conn.close()


def _resolve_pending(conn, ticker: str, asset_type: str, close: pd.Series):
    pending = conn.execute(
        "SELECT model_key, as_of_date FROM daily_predictions "
        "WHERE ticker = ? AND asset_type = ? AND actual_close IS NULL",
        (ticker, asset_type),
    ).fetchall()
    if not pending:
        return

    date_strs = [ts.strftime("%Y-%m-%d") for ts in close.index]
    pos = {d: i for i, d in enumerate(date_strs)}

    for model_key, as_of_date in pending:
        idx = pos.get(as_of_date)
        if idx is None or idx + 1 >= len(date_strs):
            continue
        actual = float(close.iloc[idx + 1])
        conn.execute(
            "UPDATE daily_predictions SET actual_close = ? "
            "WHERE ticker = ? AND asset_type = ? AND model_key = ? AND as_of_date = ?",
            (actual, ticker, asset_type, model_key, as_of_date),
        )
    conn.commit()


def record_and_correct(
    ticker: str, asset_type: str, as_of_date: str, raw_predictions: dict, close: pd.Series
) -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        _resolve_pending(conn, ticker, asset_type, close)

        for model_key, raw in raw_predictions.items():
            conn.execute(
                """
                INSERT INTO daily_predictions
                    (ticker, asset_type, model_key, as_of_date, raw_prediction, predicted_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(ticker, asset_type, model_key, as_of_date) DO UPDATE SET
                    raw_prediction = excluded.raw_prediction,
                    predicted_at = excluded.predicted_at
                """,
                (ticker, asset_type, model_key, as_of_date, raw),
            )
        conn.commit()

        results = {}
        for model_key, raw in raw_predictions.items():
            rows = conn.execute(
                "SELECT raw_prediction, actual_close FROM daily_predictions "
                "WHERE ticker = ? AND asset_type = ? AND model_key = ? AND actual_close IS NOT NULL "
                "ORDER BY as_of_date DESC LIMIT ?",
                (ticker, asset_type, model_key, BIAS_WINDOW),
            ).fetchall()
            n = len(rows)
            bias = sum(actual - pred for pred, actual in rows) / n if n >= MIN_BIAS_SAMPLES else 0.0
            results[model_key] = {"bias": bias, "corrected": raw + bias, "n_samples": n}
        return results
    finally:
        conn.close()
