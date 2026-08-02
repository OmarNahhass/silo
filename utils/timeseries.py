import pandas as pd


def prep_daily_close(data: pd.DataFrame) -> pd.Series:
    close = data["Close"].copy()
    close.index = pd.to_datetime(close.index)
    close = close.sort_index().asfreq("D").interpolate()
    return close
