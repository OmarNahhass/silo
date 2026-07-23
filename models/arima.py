import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from utils.metrics import rmse

ORDER = (5, 1, 0)  # (p, d, q): 5 autoregressive lags, 1st difference, no MA terms


def _prep(data: pd.DataFrame) -> pd.Series:
    close = data["Close"].copy()
    close.index = pd.to_datetime(close.index)
    close = close.sort_index().asfreq("D").interpolate()
    return close


def perform_arima_prediction(data: pd.DataFrame, test_frac: float = 0.2):
    """ARIMA(p,d,q): forecast the differenced, autoregressive series ORDER steps back."""
    close = _prep(data)

    split = max(10, int(len(close) * (1 - test_frac)))
    train, test = close.iloc[:split], close.iloc[split:]

    if len(test) > 0:
        holdout_fit = ARIMA(train, order=ORDER).fit()
        holdout_forecast = holdout_fit.forecast(steps=len(test))
        test_rmse = rmse(test.values, holdout_forecast.values)
    else:
        test_rmse = float("nan")

    full_fit = ARIMA(close, order=ORDER).fit()
    prediction = float(full_fit.forecast(steps=1).iloc[0])
    # The first `d` fitted values are placeholder 0s from differencing warm-up; drop them.
    fitted = full_fit.fittedvalues.iloc[ORDER[1]:]

    return {"prediction": prediction, "fitted": fitted, "rmse": test_rmse}
