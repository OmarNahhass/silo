import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from data_fetcher import fetch_data
from utils.features import build_features
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS

TOP_N_DEFAULT = 10
TOP_N_MAX = 25
VECTOR_CACHE_TTL = 15 * 60
SIMILARITY_MAX_WORKERS = 4

_universe_cache: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
_similarity_executor = ThreadPoolExecutor(max_workers=SIMILARITY_MAX_WORKERS)


def _get_ticker_universe(asset_type: str) -> list[str]:
    return STOCK_TICKERS if asset_type == "Stock" else CRYPTO_TICKERS


def _current_feature_vector(ticker: str, asset_type: str, period: str) -> pd.Series | None:
    try:
        data = fetch_data(ticker, asset_type=asset_type, period=period)
        feat, _ = build_features(data)
        feat = feat.dropna()
        if feat.empty:
            return None
        return feat.iloc[-1]
    except Exception:
        return None


def _build_universe_matrix(asset_type: str, period: str) -> pd.DataFrame:
    tickers = _get_ticker_universe(asset_type)

    def _fetch_one(t: str):
        return t, _current_feature_vector(t, asset_type, period)

    results = list(_similarity_executor.map(_fetch_one, tickers))
    rows = {t: vec for t, vec in results if vec is not None}
    return pd.DataFrame.from_dict(rows, orient="index")


def _get_universe_matrix(asset_type: str, period: str) -> pd.DataFrame:
    cache_key = (asset_type, period)
    cached = _universe_cache.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < VECTOR_CACHE_TTL:
        return cached[1]
    matrix = _build_universe_matrix(asset_type, period)
    _universe_cache[cache_key] = (now, matrix)
    return matrix


def _rank_by_similarity(query_vec: pd.Series, universe: pd.DataFrame) -> list[tuple[str, float]]:
    if universe.empty:
        return []

    combined = pd.concat([universe, query_vec.to_frame().T])
    scaled = StandardScaler().fit_transform(combined.values)

    universe_scaled = scaled[:-1]
    query_scaled = scaled[-1:]

    sims = cosine_similarity(query_scaled, universe_scaled)[0]
    return sorted(zip(universe.index, sims), key=lambda pair: pair[1], reverse=True)


def get_similar_tickers(
    ticker: str, asset_type: str, period: str = "6mo", top_n: int = TOP_N_DEFAULT
) -> list[dict]:
    ticker = ticker.strip().upper()
    top_n = max(1, min(top_n, TOP_N_MAX))

    query_vec = _current_feature_vector(ticker, asset_type, period)
    if query_vec is None:
        raise ValueError(f"Not enough data for '{ticker}' to compute similarity.")

    universe = _get_universe_matrix(asset_type, period)
    universe = universe.drop(index=ticker, errors="ignore")

    ranked = _rank_by_similarity(query_vec, universe)[:top_n]
    return [{"ticker": t, "similarity": float(s)} for t, s in ranked]
