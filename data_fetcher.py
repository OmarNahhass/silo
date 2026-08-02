import time

import pandas as pd
import yfinance as yf

PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"]

_data_cache: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
DATA_CACHE_TTL = 15 * 60


def _resolve_symbol(ticker: str, asset_type: str) -> str:
    ticker = ticker.strip().upper()
    if asset_type == "Crypto" and not ticker.endswith("-USD"):
        return f"{ticker}-USD"
    return ticker


def fetch_data(ticker: str, asset_type: str = "Stock", period: str = "2y"):
    symbol = _resolve_symbol(ticker, asset_type)

    cache_key = (symbol, period)
    cached = _data_cache.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < DATA_CACHE_TTL:
        return cached[1].copy()

    data = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data found for '{symbol}'. Check the ticker symbol and try again.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.index.name = "Date"
    _data_cache[cache_key] = (now, data)
    return data.copy()


def fetch_intraday(ticker: str, asset_type: str = "Stock", period: str = "1d", interval: str = "5m"):
    symbol = _resolve_symbol(ticker, asset_type)

    data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No intraday data found for '{symbol}'.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.index.name = "Datetime"
    return data
