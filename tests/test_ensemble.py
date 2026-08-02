import pandas as pd
import pytest

from api import _compute_ensemble


def _result(key, prediction, rmse, fitted=None):
    return {
        "key": key,
        "error": None,
        "prediction": prediction,
        "rmse": rmse,
        "fitted": fitted if fitted is not None else pd.Series(dtype=float),
    }


def test_ensemble_weights_favor_the_more_accurate_model():
    raw_results = [_result("a", 100.0, 1.0), _result("b", 110.0, 2.0)]

    ensemble = _compute_ensemble(raw_results, pd.Series(dtype=float))

    inv_var_a, inv_var_b = 1 / 1.0**2, 1 / 2.0**2
    total = inv_var_a + inv_var_b
    expected_prediction = (inv_var_a / total) * 100.0 + (inv_var_b / total) * 110.0

    assert ensemble is not None
    assert ensemble["prediction"] == pytest.approx(expected_prediction)
    naive_average = (100.0 + 110.0) / 2
    assert abs(ensemble["prediction"] - 100.0) < abs(naive_average - 100.0)


def test_ensemble_is_none_with_fewer_than_two_valid_models():
    raw_results = [_result("a", 100.0, 1.0)]
    assert _compute_ensemble(raw_results, pd.Series(dtype=float)) is None


def test_ensemble_ignores_failed_or_zero_rmse_models():
    raw_results = [
        _result("a", 100.0, 1.0),
        {"key": "b", "error": "blew up", "prediction": None, "rmse": None, "fitted": pd.Series(dtype=float)},
        _result("c", 500.0, 0.0),
    ]
    ensemble = _compute_ensemble(raw_results, pd.Series(dtype=float))
    assert ensemble is None
