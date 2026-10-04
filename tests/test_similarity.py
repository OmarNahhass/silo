from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

import similarity

FEATURE_COLUMNS = [
    "return_1", "return_5", "sma_5_ratio", "sma_20_ratio",
    "ema_12_ratio", "ema_26_ratio", "rsi_14", "macd_norm",
    "macd_signal_norm", "volatility_10",
]


@pytest.fixture(autouse=True)
def clear_cache():
    similarity._universe_cache.clear()
    yield
    similarity._universe_cache.clear()


def _price_series(prices, start="2024-01-01"):
    dates = pd.bdate_range(start, periods=len(prices))
    return pd.DataFrame({"Close": prices}, index=dates)


def _trend_prices(n, start=100.0, step=0.01):
    return [start * (1 + step) ** i for i in range(n)]


def _flat_prices(n, level=100.0):
    return [level] * n


def _choppy_prices(n, start=100.0, seed=0):
    rng = np.random.default_rng(seed)
    prices = [start]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + rng.uniform(-0.05, 0.05)))
    return prices


def _vec(values):
    return pd.Series(values, index=FEATURE_COLUMNS)


def test_scaled_identical_pattern_ranks_most_similar(monkeypatch):
    n = 60
    query_prices = _trend_prices(n, start=100.0)
    scaled_prices = [p * 0.1 for p in query_prices]  # same shape, different price level

    fake_data = {
        "QRY": _price_series(query_prices),
        "SIM": _price_series(scaled_prices),
        "FLAT": _price_series(_flat_prices(n, level=50.0)),
        "VOL": _price_series(_choppy_prices(n, start=200.0, seed=1)),
    }

    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["QRY", "SIM", "FLAT", "VOL"])
    monkeypatch.setattr(similarity, "fetch_data", lambda ticker, asset_type, period: fake_data[ticker].copy())

    results = similarity.get_similar_tickers("QRY", "Stock", top_n=3)

    assert results[0]["ticker"] == "SIM"
    assert results[0]["similarity"] == pytest.approx(1.0, abs=1e-6)
    assert "QRY" not in [r["ticker"] for r in results]


def test_universe_ticker_with_insufficient_data_is_skipped(monkeypatch):
    n = 60
    fake_data = {
        "QRY": _price_series(_trend_prices(n)),
        "GOOD": _price_series(_trend_prices(n, start=50.0, step=0.015)),
        "SHORT": _price_series(_trend_prices(5)),  # too short for ema_26/macd to produce a non-NaN row
    }

    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["QRY", "GOOD", "SHORT"])
    monkeypatch.setattr(similarity, "fetch_data", lambda ticker, asset_type, period: fake_data[ticker].copy())

    results = similarity.get_similar_tickers("QRY", "Stock", top_n=5)

    tickers = [r["ticker"] for r in results]
    assert "SHORT" not in tickers
    assert "GOOD" in tickers


def test_query_ticker_with_no_data_raises(monkeypatch):
    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["AAA"])

    def fake_fetch_data(ticker, asset_type, period):
        if ticker == "NODATA":
            raise ValueError("No data found")
        return _price_series(_trend_prices(60))

    monkeypatch.setattr(similarity, "fetch_data", fake_fetch_data)

    with pytest.raises(ValueError):
        similarity.get_similar_tickers("NODATA", "Stock")


def test_universe_matrix_is_cached_within_ttl(monkeypatch):
    n = 60
    fake_data = {
        "AAA": _price_series(_trend_prices(n, start=50.0)),
        "BBB": _price_series(_choppy_prices(n, start=75.0, seed=2)),
    }
    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["AAA", "BBB"])
    monkeypatch.setattr(similarity, "fetch_data", lambda ticker, asset_type, period: fake_data[ticker].copy())

    with patch("similarity._build_universe_matrix", wraps=similarity._build_universe_matrix) as spy:
        similarity.get_similar_tickers("AAA", "Stock")
        similarity.get_similar_tickers("BBB", "Stock")
        assert spy.call_count == 1


def test_universe_matrix_rebuilds_after_ttl_expires(monkeypatch):
    n = 60
    fake_data = {
        "AAA": _price_series(_trend_prices(n, start=50.0)),
        "BBB": _price_series(_choppy_prices(n, start=75.0, seed=2)),
    }
    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["AAA", "BBB"])
    monkeypatch.setattr(similarity, "fetch_data", lambda ticker, asset_type, period: fake_data[ticker].copy())

    with patch("similarity._build_universe_matrix", wraps=similarity._build_universe_matrix) as spy:
        similarity.get_similar_tickers("AAA", "Stock")

        cache_key = ("Stock", "6mo")
        timestamp, matrix = similarity._universe_cache[cache_key]
        similarity._universe_cache[cache_key] = (timestamp - similarity.VECTOR_CACHE_TTL - 1, matrix)

        similarity.get_similar_tickers("BBB", "Stock")
        assert spy.call_count == 2


def test_standardization_prevents_one_large_scale_feature_from_dominating(monkeypatch):
    # Query and candidate B share a big raw value in volatility_10 (the last column) but are
    # unrelated everywhere else. Candidate A matches the query's shape on every other dimension
    # but differs sharply on volatility_10. Without standardizing first, the huge raw magnitude
    # of volatility_10 would make B look far more "similar" than A, even though A is the true
    # shape match.
    query = _vec([0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.5, 0.01, 0.01, 10.0])
    candidate_a = _vec([0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.5, 0.01, 0.01, 0.1])
    candidate_b = _vec([0.9, -0.8, 0.7, -0.6, 0.5, -0.4, 0.05, -0.3, 0.2, 9.5])

    vectors = {"QRY": query, "A": candidate_a, "B": candidate_b}

    monkeypatch.setattr(similarity, "_current_feature_vector", lambda ticker, asset_type, period: vectors[ticker])
    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: ["A", "B"])

    results = similarity.get_similar_tickers("QRY", "Stock", top_n=2)
    ranked = [r["ticker"] for r in results]

    assert ranked[0] == "A"


def test_top_n_is_respected_and_capped(monkeypatch):
    n = 60
    tickers = [f"T{i}" for i in range(8)]
    fake_data = {
        t: _price_series(_trend_prices(n, start=50.0 + i, step=0.005 + i * 0.001))
        for i, t in enumerate(tickers)
    }
    fake_data["QRY"] = _price_series(_trend_prices(n, start=100.0))

    monkeypatch.setattr(similarity, "_get_ticker_universe", lambda asset_type: tickers)
    monkeypatch.setattr(similarity, "fetch_data", lambda ticker, asset_type, period: fake_data[ticker].copy())

    results = similarity.get_similar_tickers("QRY", "Stock", top_n=3)
    assert len(results) == 3

    results_capped = similarity.get_similar_tickers("QRY", "Stock", top_n=999)
    assert len(results_capped) <= similarity.TOP_N_MAX
    assert len(results_capped) <= len(tickers)
