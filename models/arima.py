from statsmodels.tsa.arima.model import ARIMA

from utils.metrics import rmse
from utils.timeseries import prep_daily_close

ORDER = (5, 1, 0)  # (p, d, q): 5 autoregressive lags, 1st difference, no MA terms


def perform_arima_prediction(data, test_frac: float = 0.2):
    """ARIMA(p,d,q): forecast the differenced, autoregressive series ORDER steps back."""
    close = prep_daily_close(data)

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
