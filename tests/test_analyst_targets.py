from unittest.mock import MagicMock, patch

import pytest

import analyst_targets


@pytest.fixture(autouse=True)
def clear_cache():
    analyst_targets._target_cache.clear()
    yield
    analyst_targets._target_cache.clear()


def _fake_ticker(info):
    mock = MagicMock()
    mock.info = info
    return mock


def test_crypto_never_hits_the_network():
    with patch("analyst_targets.yf.Ticker") as mock_ticker:
        result = analyst_targets.get_analyst_target("BTC", "Crypto")

    assert result is None
    mock_ticker.assert_not_called()


def test_stock_with_coverage_returns_target_fields():
    info = {
        "targetMeanPrice": 323.28,
        "targetHighPrice": 400.0,
        "targetLowPrice": 215.0,
        "targetMedianPrice": 330.0,
        "recommendationKey": "buy",
        "numberOfAnalystOpinions": 41,
    }
    with patch("analyst_targets.yf.Ticker", return_value=_fake_ticker(info)):
        result = analyst_targets.get_analyst_target("AAPL", "Stock")

    assert result == {
        "mean": 323.28,
        "high": 400.0,
        "low": 215.0,
        "median": 330.0,
        "recommendation": "buy",
        "num_analysts": 41,
    }


def test_stock_with_no_analyst_coverage_returns_none():
    with patch("analyst_targets.yf.Ticker", return_value=_fake_ticker({})):
        result = analyst_targets.get_analyst_target("TINYCAP", "Stock")

    assert result is None


def test_a_none_result_is_not_cached_and_retries_next_call():
    # A missing target could be genuine (no coverage) or a transient/incomplete
    # fetch -- either way, don't lock in a negative result for the full TTL, since
    # that would mask real data behind a one-off flaky response.
    empty = _fake_ticker({})
    covered = _fake_ticker({"targetMeanPrice": 563.05})
    with patch("analyst_targets.yf.Ticker", side_effect=[empty, covered]) as mock_ticker:
        first = analyst_targets.get_analyst_target("MSFT", "Stock")
        second = analyst_targets.get_analyst_target("MSFT", "Stock")

    assert first is None
    assert second == {
        "mean": 563.05,
        "high": None,
        "low": None,
        "median": None,
        "recommendation": None,
        "num_analysts": None,
    }
    assert mock_ticker.call_count == 2


def test_repeated_calls_hit_the_network_once():
    info = {"targetMeanPrice": 100.0}
    with patch("analyst_targets.yf.Ticker", return_value=_fake_ticker(info)) as mock_ticker:
        analyst_targets.get_analyst_target("AAPL", "Stock")
        analyst_targets.get_analyst_target("AAPL", "Stock")

    assert mock_ticker.call_count == 1
