"""data_fetcher.fetch_data's TTL cache -- mocks yfinance entirely, no network calls."""

from unittest.mock import patch

import pandas as pd
import pytest

import data_fetcher


def _fake_yf_response():
    return pd.DataFrame(
        {"Open": [100.0], "High": [101.0], "Low": [99.0], "Close": [100.5], "Volume": [1_000_000]},
        index=pd.DatetimeIndex(["2024-01-01"], name="Date"),
    )


@pytest.fixture(autouse=True)
def clear_cache():
    data_fetcher._data_cache.clear()
    yield
    data_fetcher._data_cache.clear()


def test_repeated_calls_hit_the_network_once():
    with patch("data_fetcher.yf.download", return_value=_fake_yf_response()) as mock_download:
        data_fetcher.fetch_data("AAPL", asset_type="Stock", period="2y")
        data_fetcher.fetch_data("AAPL", asset_type="Stock", period="2y")

    assert mock_download.call_count == 1


def test_different_period_is_a_cache_miss():
    with patch("data_fetcher.yf.download", return_value=_fake_yf_response()) as mock_download:
        data_fetcher.fetch_data("AAPL", asset_type="Stock", period="2y")
        data_fetcher.fetch_data("AAPL", asset_type="Stock", period="5y")

    assert mock_download.call_count == 2


def test_cached_result_is_an_independent_copy():
    # Callers mutating their own copy shouldn't corrupt what the next caller gets back.
    with patch("data_fetcher.yf.download", return_value=_fake_yf_response()):
        first = data_fetcher.fetch_data("AAPL", asset_type="Stock", period="2y")
        first.loc[first.index[0], "Close"] = 999.0
        second = data_fetcher.fetch_data("AAPL", asset_type="Stock", period="2y")

    assert second["Close"].iloc[0] != 999.0
