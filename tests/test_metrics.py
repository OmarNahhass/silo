import pytest

from utils.metrics import rmse, mae, mape


def test_rmse_known_values():
    assert rmse([100.0, 200.0], [98.0, 204.0]) == pytest.approx((((2**2) + (4**2)) / 2) ** 0.5)


def test_mae_known_values():
    assert mae([100.0, 200.0], [98.0, 204.0]) == pytest.approx(3.0)


def test_mape_known_values():
    assert mape([100.0, 200.0], [98.0, 204.0]) == pytest.approx(((2 / 100) + (4 / 200)) / 2 * 100)


def test_mape_ignores_zero_actuals():
    assert mape([0.0, 100.0], [5.0, 105.0]) == pytest.approx(5.0)


def test_mape_returns_none_when_all_actuals_are_zero():
    assert mape([0.0, 0.0], [1.0, 2.0]) is None
