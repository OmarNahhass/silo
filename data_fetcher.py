import time

import pandas as pd
import yfinance as yf

PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"]

# Repeated /api/forecast calls for the same ticker+period within a short window
# (re-running a forecast, the Compare page hitting the same ticker twice, etc.) used
# to re-download the full history from Yahoo every single time. Same pattern as
# live_forecast.py's history cache: a short in-process TTL, keyed by the resolved
# symbol + period since different periods return different amounts of data.
_data_cache: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
DATA_CACHE_TTL = 15 * 60  # seconds


def _resolve_symbol(ticker: str, asset_type: str) -> str:
    """Map a user-entered ticker to the symbol yfinance expects."""
    ticker = ticker.strip().upper()
    if asset_type == "Crypto" and not ticker.endswith("-USD"):
        return f"{ticker}-USD"
    return ticker


def fetch_data(ticker: str, asset_type: str = "Stock", period: str = "2y"):
    """Fetch daily OHLCV history for a stock or crypto ticker via yfinance, cached
    briefly so repeated requests for the same ticker/period don't hit the network
    (or Yahoo's rate limits) every single time.
    """
    symbol = _resolve_symbol(ticker, asset_type)

    cache_key = (symbol, period)
    cached = _data_cache.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < DATA_CACHE_TTL:
        return cached[1].copy()

    data = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data found for '{symbol}'. Check the ticker symbol and try again.")

    # yfinance can return MultiIndex columns (Price, Ticker) for some requests
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.index.name = "Date"
    _data_cache[cache_key] = (now, data)
    return data.copy()


def fetch_intraday(ticker: str, asset_type: str = "Stock", period: str = "1d", interval: str = "5m"):
    """Fetch intraday OHLCV bars (tz-aware index: exchange tz for stocks, UTC for crypto)."""
    symbol = _resolve_symbol(ticker, asset_type)

    data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No intraday data found for '{symbol}'.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.index.name = "Datetime"
    return data
