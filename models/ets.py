from statsmodels.tsa.holtwinters import ExponentialSmoothing

from utils.metrics import rmse
from utils.timeseries import prep_daily_close


def perform_ets_prediction(data, test_frac: float = 0.2):
    close = prep_daily_close(data)

    split = max(10, int(len(close) * (1 - test_frac)))
    train, test = close.iloc[:split], close.iloc[split:]

    if len(test) > 0:
        holdout_fit = ExponentialSmoothing(train, trend="add", seasonal=None).fit()
        holdout_forecast = holdout_fit.forecast(steps=len(test))
        test_rmse = rmse(test.values, holdout_forecast.values)
    else:
        test_rmse = float("nan")

    full_fit = ExponentialSmoothing(close, trend="add", seasonal=None).fit()
    prediction = float(full_fit.forecast(steps=1).iloc[0])
    fitted = full_fit.fittedvalues

    return {"prediction": prediction, "fitted": fitted, "rmse": test_rmse}
