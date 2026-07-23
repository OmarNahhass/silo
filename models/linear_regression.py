import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils.metrics import rmse


def perform_linear_regression(data: pd.DataFrame, test_frac: float = 0.2):
    """Predict next-day close from today's close: Close[t+1] = b0 + b1 * Close[t]."""
    close = data["Close"].dropna()

    X_all = close.values[:-1].reshape(-1, 1)
    y_all = close.values[1:]
    dates = close.index[1:]

    split = max(1, int(len(X_all) * (1 - test_frac)))

    model = LinearRegression()
    model.fit(X_all[:split], y_all[:split])

    fitted_all = model.predict(X_all)
    test_rmse = rmse(y_all[split:], fitted_all[split:]) if split < len(X_all) else float("nan")

    # Refit on the full series for the actual next-step forecast
    model.fit(X_all, y_all)
    prediction = float(model.predict(np.array([[close.values[-1]]]))[0])

    fitted = pd.Series(fitted_all, index=dates, name="Fitted")

    return {"prediction": prediction, "fitted": fitted, "rmse": test_rmse}
