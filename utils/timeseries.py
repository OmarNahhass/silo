import pandas as pd


def prep_daily_close(data: pd.DataFrame) -> pd.Series:
    """Close price reindexed to a continuous daily calendar frequency (weekends
    linearly interpolated), which classical time-series models (ARIMA/SARIMA/ETS)
    need since they assume evenly spaced observations."""
    close = data["Close"].copy()
    close.index = pd.to_datetime(close.index)
    close = close.sort_index().asfreq("D").interpolate()
    return close
