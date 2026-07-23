import numpy as np


def rmse(y_true, y_pred):
    """Root Mean Squared Error: sqrt(mean((y_true - y_pred)^2))."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true, y_pred):
    """Mean Absolute Error: mean(|y_true - y_pred|)."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true, y_pred):
    """Mean Absolute Percentage Error: mean(|y_true - y_pred| / |y_true|) * 100."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
