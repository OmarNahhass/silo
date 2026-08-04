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


def _insert_resolved(
    db_path, ticker, model_key, n, raw_prediction, actual_close, start_date="2024-01-01",
    asset_type="Stock", prior_close=None,
):
    conn = sqlite3.connect(db_path)
    dates = pd.bdate_range(start_date, periods=n)
    for d in dates:
        conn.execute(
            """
            INSERT INTO daily_predictions
                (ticker, asset_type, model_key, as_of_date, raw_prediction, predicted_at, actual_close, prior_close)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
            """,
            (ticker, asset_type, model_key, d.strftime("%Y-%m-%d"), raw_prediction, actual_close, prior_close),
        )
    conn.commit()
    conn.close()


def test_bias_correction_converges_to_known_bias(isolated_db):
    _insert_resolved(isolated_db, "TEST", "lr", n=15, raw_prediction=100.0, actual_close=103.0)

    result = prediction_history.record_and_correct(
        "TEST", "Stock", "2024-02-01", {"lr": 105.0}, pd.Series(dtype=float)
    )

    assert result["lr"]["n_samples"] == 15
    assert result["lr"]["bias"] == pytest.approx(3.0)
    assert result["lr"]["corrected"] == pytest.approx(108.0)


def test_no_correction_below_minimum_sample_size(isolated_db):
    _insert_resolved(isolated_db, "TEST", "lr", n=5, raw_prediction=100.0, actual_close=110.0)

    result = prediction_history.record_and_correct(
        "TEST", "Stock", "2024-02-01", {"lr": 105.0}, pd.Series(dtype=float)
    )

    assert result["lr"]["n_samples"] == 5
    assert result["lr"]["bias"] == 0.0
    assert result["lr"]["corrected"] == pytest.approx(105.0)


def test_migration_adds_prior_close_column_idempotently(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE daily_predictions (
            ticker TEXT NOT NULL, asset_type TEXT NOT NULL, model_key TEXT NOT NULL,
            as_of_date TEXT NOT NULL, raw_prediction REAL NOT NULL, predicted_at TEXT NOT NULL,
            actual_close REAL,
            PRIMARY KEY (ticker, asset_type, model_key, as_of_date)
        )
        """
    )
    conn.execute(
        "INSERT INTO daily_predictions VALUES ('OLD', 'Stock', 'lr', '2024-01-01', 100.0, datetime('now'), 101.0)"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(prediction_history, "DB_PATH", db_path)
    prediction_history.init_db()
    prediction_history.init_db()  # second call must not raise (already-migrated case)

    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(daily_predictions)").fetchall()}
    row = conn.execute("SELECT prior_close FROM daily_predictions WHERE ticker = 'OLD'").fetchone()
    conn.close()

    assert "prior_close" in cols
    assert row[0] is None


def test_record_and_correct_stores_prior_close_from_close_series(isolated_db):
    close = pd.Series([100.0, 102.0, 105.0], index=pd.bdate_range("2024-02-01", periods=3))

    prediction_history.record_and_correct("TEST", "Stock", "2024-02-05", {"lr": 106.0}, close)

    conn = sqlite3.connect(isolated_db)
    row = conn.execute(
        "SELECT prior_close FROM daily_predictions WHERE ticker = 'TEST' AND model_key = 'lr'"
    ).fetchone()
    conn.close()

    assert row[0] == pytest.approx(105.0)


def test_record_and_correct_with_empty_close_series_stores_null_prior_close(isolated_db):
    prediction_history.record_and_correct("TEST", "Stock", "2024-02-05", {"lr": 106.0}, pd.Series(dtype=float))

    conn = sqlite3.connect(isolated_db)
    row = conn.execute(
        "SELECT prior_close FROM daily_predictions WHERE ticker = 'TEST' AND model_key = 'lr'"
    ).fetchone()
    conn.close()

    assert row[0] is None


def test_record_prediction_upserts_a_single_row(isolated_db):
    prediction_history.record_prediction("TEST", "Stock", "ensemble", "2024-02-01", 100.0, prior_close=99.0)
    prediction_history.record_prediction("TEST", "Stock", "ensemble", "2024-02-01", 101.0, prior_close=99.5)

    conn = sqlite3.connect(isolated_db)
    rows = conn.execute(
        "SELECT raw_prediction, prior_close FROM daily_predictions WHERE ticker = 'TEST' AND model_key = 'ensemble'"
    ).fetchall()
    conn.close()

    assert rows == [(101.0, 99.5)]


def test_get_resolved_predictions_filters_correctly(isolated_db):
    _insert_resolved(isolated_db, "AAA", "lr", n=2, raw_prediction=100.0, actual_close=101.0, asset_type="Stock")
    _insert_resolved(isolated_db, "BBB", "lr", n=2, raw_prediction=50.0, actual_close=51.0, asset_type="Stock")
    _insert_resolved(isolated_db, "AAA", "rf", n=2, raw_prediction=100.0, actual_close=101.0, asset_type="Stock")
    _insert_resolved(isolated_db, "AAA", "lr", n=1, raw_prediction=100.0, actual_close=None, asset_type="Stock", start_date="2025-01-01")

    all_rows = prediction_history.get_resolved_predictions()
    assert len(all_rows) == 6  # the unresolved row is excluded

    ticker_rows = prediction_history.get_resolved_predictions(ticker="AAA", asset_type="Stock")
    assert len(ticker_rows) == 4
    assert all(r["ticker"] == "AAA" for r in ticker_rows)

    model_rows = prediction_history.get_resolved_predictions(ticker="AAA", asset_type="Stock", model_key="rf")
    assert len(model_rows) == 2
    assert all(r["model_key"] == "rf" for r in model_rows)

    since_rows = prediction_history.get_resolved_predictions(since="2024-01-02")
    assert all(r["as_of_date"] >= "2024-01-02" for r in since_rows)


def test_get_resolved_predictions_includes_legacy_rows_with_null_prior_close(isolated_db):
    _insert_resolved(isolated_db, "AAA", "lr", n=1, raw_prediction=100.0, actual_close=101.0, prior_close=None)

    rows = prediction_history.get_resolved_predictions(ticker="AAA", asset_type="Stock")

    assert len(rows) == 1
    assert rows[0]["prior_close"] is None
