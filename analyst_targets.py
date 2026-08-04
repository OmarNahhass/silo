import time

import yfinance as yf

_target_cache: dict[str, tuple[float, dict | None]] = {}
TARGET_CACHE_TTL = 60 * 60


def get_analyst_target(ticker: str, asset_type: str) -> dict | None:
    if asset_type == "Crypto":
        return None

    symbol = ticker.strip().upper()

    cached = _target_cache.get(symbol)
    now = time.time()
    if cached and now - cached[0] < TARGET_CACHE_TTL:
        return cached[1]

    info = yf.Ticker(symbol).info
    mean = info.get("targetMeanPrice")

    if mean is None:
        return None

    result = {
        "mean": float(mean),
        "high": float(info["targetHighPrice"]) if info.get("targetHighPrice") is not None else None,
        "low": float(info["targetLowPrice"]) if info.get("targetLowPrice") is not None else None,
        "median": float(info["targetMedianPrice"]) if info.get("targetMedianPrice") is not None else None,
        "recommendation": info.get("recommendationKey"),
        "num_analysts": info.get("numberOfAnalystOpinions"),
    }
    _target_cache[symbol] = (now, result)
    return result
