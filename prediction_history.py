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
    cols = {row[1] for row in conn.execute("PRAGMA table_info(daily_predictions)").fetchall()}
    if "prior_close" not in cols:
        conn.execute("ALTER TABLE daily_predictions ADD COLUMN prior_close REAL")
    conn.commit()
    conn.close()


def _upsert_row(conn, ticker, asset_type, model_key, as_of_date, raw_prediction, prior_close):
    conn.execute(
        """
        INSERT INTO daily_predictions
            (ticker, asset_type, model_key, as_of_date, raw_prediction, predicted_at, prior_close)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
        ON CONFLICT(ticker, asset_type, model_key, as_of_date) DO UPDATE SET
            raw_prediction = excluded.raw_prediction,
            predicted_at = excluded.predicted_at,
            prior_close = excluded.prior_close
        """,
        (ticker, asset_type, model_key, as_of_date, raw_prediction, prior_close),
    )


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
    prior_close = float(close.iloc[-1]) if len(close) else None
    conn = sqlite3.connect(DB_PATH)
    try:
        _resolve_pending(conn, ticker, asset_type, close)

        for model_key, raw in raw_predictions.items():
            _upsert_row(conn, ticker, asset_type, model_key, as_of_date, raw, prior_close)
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


def record_prediction(
    ticker: str, asset_type: str, model_key: str, as_of_date: str, raw_prediction: float, prior_close: float | None = None
) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        _upsert_row(conn, ticker, asset_type, model_key, as_of_date, raw_prediction, prior_close)
        conn.commit()
    finally:
        conn.close()


def get_resolved_predictions(
    ticker: str | None = None,
    asset_type: str | None = None,
    model_key: str | None = None,
    since: str | None = None,
) -> list[dict]:
    clauses = ["actual_close IS NOT NULL"]
    params: list = []
    if ticker is not None:
        clauses.append("ticker = ?")
        params.append(ticker)
    if asset_type is not None:
        clauses.append("asset_type = ?")
        params.append(asset_type)
    if model_key is not None:
        clauses.append("model_key = ?")
        params.append(model_key)
    if since is not None:
        clauses.append("as_of_date >= ?")
        params.append(since)

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT ticker, asset_type, model_key, as_of_date, raw_prediction, actual_close, prior_close "
            f"FROM daily_predictions WHERE {' AND '.join(clauses)} ORDER BY as_of_date",
            params,
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "ticker": r[0],
            "asset_type": r[1],
            "model_key": r[2],
            "as_of_date": r[3],
            "raw_prediction": r[4],
            "actual_close": r[5],
            "prior_close": r[6],
        }
        for r in rows
    ]
