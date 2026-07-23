import numpy as np
import pandas as pd
from sklearn.base import clone

from utils.features import build_features
from utils.metrics import rmse


def fit_return_based_model(estimator, data: pd.DataFrame, test_frac: float = 0.2):
    """
    Shared train/evaluate/forecast pipeline for any scikit-learn-compatible
    regressor. The estimator learns to predict the next-day *log return*
    from engineered technical-indicator features (see utils/features.py),
    since log returns are approximately stationary while raw price levels
    are not -- a model trained directly on price levels would just memorize
    the price range it was trained on and fail to extrapolate.

    Predicted prices are reconstructed one step at a time via
    Close_{t+1} = Close_t * exp(predicted_log_return), never chained
    forward, so forecast error doesn't compound across days.
    """
    close = data["Close"]
    feat, target = build_features(data)
    feat = feat.dropna()

    train_data = feat.join(target.rename("target")).dropna()
    X_all = train_data.drop(columns="target")
    y_all = train_data["target"]

    split = max(10, int(len(X_all) * (1 - test_frac)))
    X_train, y_train = X_all.iloc[:split], y_all.iloc[:split]
    X_test = X_all.iloc[split:]

    if len(X_test) > 0:
        holdout_model = clone(estimator).fit(X_train, y_train)
        pred_returns = holdout_model.predict(X_test)
        prev_close = close.loc[X_test.index].values
        pred_price = prev_close * np.exp(pred_returns)
        actual_price = close.shift(-1).loc[X_test.index].values
        test_rmse = rmse(actual_price, pred_price)
    else:
        test_rmse = float("nan")

    full_model = clone(estimator).fit(X_all, y_all)

    fitted_returns = full_model.predict(X_all)
    fitted_price = pd.Series(close.loc[X_all.index].values * np.exp(fitted_returns), index=X_all.index)

    next_return = full_model.predict(feat.iloc[[-1]])[0]
    prediction = float(close.iloc[-1] * np.exp(next_return))

    return {"prediction": prediction, "fitted": fitted_price, "rmse": test_rmse}
