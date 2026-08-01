"""Runs each of the 10 forecasting models against synthetic price data so a broken
model (bad math, an exception, a NaN/negative prediction) fails CI instead of
shipping silently -- plus one hand-verifiable case: linear regression on a perfectly
linear series should recover the trend almost exactly.
"""

import numpy as np
import pandas as pd
import pytest

from model_registry import MODELS
from models.linear_regression import perform_linear_regression


def _make_synthetic_ohlcv(n: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily_returns = rng.normal(loc=0.0004, scale=0.012, size=n)
    close = 100.0 * np.exp(np.cumsum(daily_returns))
    dates = pd.bdate_range("2023-01-02", periods=n)
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.003, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.003, n)))
    volume = rng.integers(1_000_000, 5_000_000, n).astype(float)
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates
    )
    df.index.name = "Date"
    return df


def _make_linear_ohlcv(n: int = 200, start: float = 100.0, step: float = 1.0) -> pd.DataFrame:
    dates = pd.bdate_range("2023-01-02", periods=n)
    close = start + step * np.arange(n, dtype=float)
    df = pd.DataFrame(
        {"Open": close, "High": close + 0.5, "Low": close - 0.5, "Close": close,
         "Volume": np.full(n, 1_000_000.0)},
        index=dates,
    )
    df.index.name = "Date"
    return df


def test_linear_regression_recovers_slope():
    """Close[t+1] = Close[t] + 1 with zero noise -- OLS should fit this almost exactly,
    so the next-day prediction should land right on trend, not just "somewhere close"."""
    data = _make_linear_ohlcv(n=200, start=100.0, step=1.0)
    result = perform_linear_regression(data)

    expected_next = data["Close"].iloc[-1] + 1.0
    assert result["prediction"] == pytest.approx(expected_next, abs=0.05)
    assert result["rmse"] < 0.05


@pytest.mark.parametrize("spec", MODELS, ids=[m["key"] for m in MODELS])
def test_model_runs_and_returns_valid_result(spec):
    data = _make_synthetic_ohlcv()
    result = spec["run"](data)

    assert np.isfinite(result["prediction"])
    assert result["prediction"] > 0, "a price prediction should never be zero or negative"
    assert isinstance(result["fitted"], pd.Series)
    assert len(result["fitted"]) > 0

    if not pd.isna(result["rmse"]):
        assert result["rmse"] >= 0
