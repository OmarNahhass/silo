import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils.metrics import rmse
from utils.timeseries import prep_daily_close

N_CHANGEPOINTS = 10
FOURIER_ORDER = 3
SEASONAL_PERIOD = 7.0


def _design_matrix(t: np.ndarray, changepoints: np.ndarray) -> np.ndarray:
    cols = [t]
    for cp in changepoints:
        cols.append(np.clip(t - cp, 0, None))
    for n in range(1, FOURIER_ORDER + 1):
        cols.append(np.sin(2 * np.pi * n * t / SEASONAL_PERIOD))
        cols.append(np.cos(2 * np.pi * n * t / SEASONAL_PERIOD))
    return np.column_stack(cols)


def perform_prophet_style_prediction(data, test_frac: float = 0.2):
    close = prep_daily_close(data)
    n = len(close)
    t_full = np.arange(n, dtype=float)

    changepoint_end = t_full[int(n * 0.8)]
    changepoints = np.linspace(0, changepoint_end, N_CHANGEPOINTS + 2)[1:-1]

    X_full = _design_matrix(t_full, changepoints)
    y_full = close.values

    split = max(30, int(n * (1 - test_frac)))
    X_train, y_train = X_full[:split], y_full[:split]
    X_test, y_test = X_full[split:], y_full[split:]

    if len(X_test) > 0:
        holdout_model = LinearRegression().fit(X_train, y_train)
        test_rmse = rmse(y_test, holdout_model.predict(X_test))
    else:
        test_rmse = float("nan")

    full_model = LinearRegression().fit(X_full, y_full)
    fitted = pd.Series(full_model.predict(X_full), index=close.index)

    next_t = np.array([n], dtype=float)
    prediction = float(full_model.predict(_design_matrix(next_t, changepoints))[0])

    return {"prediction": prediction, "fitted": fitted, "rmse": test_rmse}
