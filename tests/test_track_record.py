import sqlite3

import pandas as pd
import pytest

import prediction_history
import track_record


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_predictions.db"
    monkeypatch.setattr(prediction_history, "DB_PATH", db_path)
    prediction_history.init_db()
    return db_path


def _insert(db_path, ticker, model_key, as_of_date, raw_prediction, actual_close, prior_close=None, asset_type="Stock"):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO daily_predictions
            (ticker, asset_type, model_key, as_of_date, raw_prediction, predicted_at, actual_close, prior_close)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
        """,
        (ticker, asset_type, model_key, as_of_date, raw_prediction, actual_close, prior_close),
    )
    conn.commit()
    conn.close()


def test_per_model_rmse_and_mae_from_known_constant_error(isolated_db):
    dates = pd.bdate_range("2024-01-01", periods=10)
    for d in dates:
        _insert(isolated_db, "AAA", "lr", d.strftime("%Y-%m-%d"), raw_prediction=98.0, actual_close=100.0)

    result = track_record.get_track_record(ticker="AAA", asset_type="Stock")

    lr_stats = next(m for m in result["per_model"] if m["key"] == "lr")
    assert lr_stats["n_samples"] == 10
    assert lr_stats["rmse"] == pytest.approx(2.0)
    assert lr_stats["mae"] == pytest.approx(2.0)
    assert lr_stats["mape"] == pytest.approx(2.0)


def test_mape_guards_against_zero_actual_close(isolated_db):
    _insert(isolated_db, "AAA", "lr", "2024-01-01", raw_prediction=1.0, actual_close=0.0)

    result = track_record.get_track_record(ticker="AAA", asset_type="Stock")

    lr_stats = next(m for m in result["per_model"] if m["key"] == "lr")
    assert lr_stats["mape"] is None
    assert lr_stats["rmse"] == pytest.approx(1.0)


def test_ensemble_vs_naive_paired_ttest_detects_real_improvement(isolated_db):
    dates = pd.bdate_range("2024-01-01", periods=30)
    for i, d in enumerate(dates):
        actual = 100.0 + i
        prior = actual - 1.0  # naive baseline always off by 1.0
        jitter = 0.1 if i % 2 == 0 else -0.1
        ensemble_pred = actual - 0.2 + jitter  # ensemble consistently off by ~0.2, less than naive's 1.0
        _insert(
            isolated_db, "AAA", "ensemble", d.strftime("%Y-%m-%d"),
            raw_prediction=ensemble_pred, actual_close=actual, prior_close=prior,
        )

    result = track_record.get_track_record(ticker="AAA", asset_type="Stock")

    assert result["naive_baseline"]["n_samples"] == 30
    test = result["ensemble_vs_naive_test"]
    assert test is not None
    assert test["p_value"] < 0.05
    assert test["t_statistic"] < 0
    assert "significantly lower" in test["verdict"]


def test_insufficient_samples_returns_no_test(isolated_db):
    dates = pd.bdate_range("2024-01-01", periods=5)
    for d in dates:
        _insert(
            isolated_db, "AAA", "ensemble", d.strftime("%Y-%m-%d"),
            raw_prediction=99.0, actual_close=100.0, prior_close=98.0,
        )

    result = track_record.get_track_record(ticker="AAA", asset_type="Stock")

    assert result["naive_baseline"]["n_samples"] == 5
    assert result["ensemble_vs_naive_test"] is None


def test_empty_scope_returns_graceful_response(isolated_db):
    result = track_record.get_track_record(ticker="NOPE", asset_type="Stock")

    assert result["per_model"] == []
    assert result["naive_baseline"] is None
    assert result["ensemble_vs_naive_test"] is None
