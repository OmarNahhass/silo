import numpy as np
import pandas as pd
from sklearn.base import clone

from utils.features import build_features
from utils.metrics import rmse


def fit_return_based_model(estimator, data: pd.DataFrame, test_frac: float = 0.2):
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
