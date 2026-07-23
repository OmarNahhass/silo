import pandas as pd
import yfinance as yf

PERIOD_OPTIONS = ["6mo", "1y", "2y", "5y", "max"]


def _resolve_symbol(ticker: str, asset_type: str) -> str:
    """Map a user-entered ticker to the symbol yfinance expects."""
    ticker = ticker.strip().upper()
    if asset_type == "Crypto" and not ticker.endswith("-USD"):
        return f"{ticker}-USD"
    return ticker


def fetch_data(ticker: str, asset_type: str = "Stock", period: str = "2y"):
    """Fetch daily OHLCV history for a stock or crypto ticker via yfinance."""
    symbol = _resolve_symbol(ticker, asset_type)

    data = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data found for '{symbol}'. Check the ticker symbol and try again.")

    # yfinance can return MultiIndex columns (Price, Ticker) for some requests
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.index.name = "Date"
    return data
