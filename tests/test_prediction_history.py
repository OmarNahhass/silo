"""prediction_history.record_and_correct: verifies the bias math against a synthetic,
isolated SQLite DB (never touches the real data/predictions.db)."""

import sqlite3

import pandas as pd
import pytest

import prediction_history


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_predictions.db"
    monkeypatch.setattr(prediction_history, "DB_PATH", db_path)
    prediction_history.init_db()
    return db_path


def _insert_resolved(db_path, ticker, model_key, n, raw_prediction, actual_close, start_date="2024-01-01"):
    conn = sqlite3.connect(db_path)
    dates = pd.bdate_range(start_date, periods=n)
    for d in dates:
        conn.execute(
            """
            INSERT INTO daily_predictions
                (ticker, asset_type, model_key, as_of_date, raw_prediction, predicted_at, actual_close)
            VALUES (?, 'Stock', ?, ?, ?, datetime('now'), ?)
            """,
            (ticker, model_key, d.strftime("%Y-%m-%d"), raw_prediction, actual_close),
        )
    conn.commit()
    conn.close()


def test_bias_correction_converges_to_known_bias(isolated_db):
    # Model has consistently predicted $3.00 too low across 15 resolved days --
    # record_and_correct should learn that exact bias and apply it going forward.
    _insert_resolved(isolated_db, "TEST", "lr", n=15, raw_prediction=100.0, actual_close=103.0)

    result = prediction_history.record_and_correct(
        "TEST", "Stock", "2024-02-01", {"lr": 105.0}, pd.Series(dtype=float)
    )

    assert result["lr"]["n_samples"] == 15
    assert result["lr"]["bias"] == pytest.approx(3.0)
    assert result["lr"]["corrected"] == pytest.approx(108.0)


def test_no_correction_below_minimum_sample_size(isolated_db):
    # Only 5 resolved days -- fewer than MIN_BIAS_SAMPLES -- so correction should stay off.
    _insert_resolved(isolated_db, "TEST", "lr", n=5, raw_prediction=100.0, actual_close=110.0)

    result = prediction_history.record_and_correct(
        "TEST", "Stock", "2024-02-01", {"lr": 105.0}, pd.Series(dtype=float)
    )

    assert result["lr"]["n_samples"] == 5
    assert result["lr"]["bias"] == 0.0
    assert result["lr"]["corrected"] == pytest.approx(105.0)
