from statsmodels.tsa.statespace.sarimax import SARIMAX

from utils.metrics import rmse
from utils.timeseries import prep_daily_close

ORDER = (2, 1, 2)
SEASONAL_ORDER = (1, 1, 1, 7)


def perform_sarima_prediction(data, test_frac: float = 0.2):
    close = prep_daily_close(data)

    split = max(30, int(len(close) * (1 - test_frac)))
    train, test = close.iloc[:split], close.iloc[split:]

    if len(test) > 0:
        holdout_fit = SARIMAX(
            train, order=ORDER, seasonal_order=SEASONAL_ORDER,
            enforce_stationarity=False, enforce_invertibility=False,
        ).fit(disp=False)
        holdout_forecast = holdout_fit.forecast(steps=len(test))
        test_rmse = rmse(test.values, holdout_forecast.values)
    else:
        test_rmse = float("nan")

    full_fit = SARIMAX(
        close, order=ORDER, seasonal_order=SEASONAL_ORDER,
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False)
    prediction = float(full_fit.forecast(steps=1).iloc[0])
    warmup = ORDER[1] + SEASONAL_ORDER[1] * SEASONAL_ORDER[3]
    fitted = full_fit.fittedvalues.iloc[warmup:]

    return {"prediction": prediction, "fitted": fitted, "rmse": test_rmse}
