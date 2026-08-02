import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from utils.metrics import rmse

MIN_HISTORY_DAYS = 10


def _day_pair(group: pd.DataFrame, now_time: pd.Timestamp):
    day = group.index[0].normalize()
    cutoff = day + (now_time - now_time.normalize())
    at_cutoff = group.loc[:cutoff]
    if at_cutoff.empty or group.index[-1] < cutoff:
        return None
    return float(at_cutoff["Close"].iloc[-1]), float(group["Open"].iloc[0]), float(group["Close"].iloc[-1])


def predict_intraday_close(today_bars: pd.DataFrame, history_bars: pd.DataFrame, test_frac: float = 0.2) -> dict:
    today_open = float(today_bars["Open"].iloc[0])
    current_price = float(today_bars["Close"].iloc[-1])
    now_time = today_bars.index[-1]
    today_date = now_time.date()

    xs, ys, day_opens = [], [], []
    for date, group in history_bars.groupby(history_bars.index.date):
        if date == today_date:
            continue
        pair = _day_pair(group, now_time)
        if pair is None:
            continue
        price_at_time, day_open, day_close = pair
        xs.append(price_at_time / day_open - 1)
        ys.append(day_close / day_open - 1)
        day_opens.append(day_open)

    if len(xs) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Not enough matching intraday history yet ({len(xs)} days, need {MIN_HISTORY_DAYS})."
        )

    X = np.array(xs).reshape(-1, 1)
    y = np.array(ys)
    day_opens = np.array(day_opens)

    split = max(1, int(len(X) * (1 - test_frac)))
    model = LinearRegression()
    model.fit(X[:split], y[:split])

    if split < len(X):
        pred_returns = model.predict(X[split:])
        pred_prices = day_opens[split:] * (1 + pred_returns)
        actual_prices = day_opens[split:] * (1 + y[split:])
        test_rmse = rmse(actual_prices, pred_prices)
    else:
        test_rmse = float("nan")

    model.fit(X, y)
    x_today = current_price / today_open - 1
    predicted_return = float(model.predict(np.array([[x_today]]))[0])
    predicted_close = today_open * (1 + predicted_return)

    return {
        "prediction": predicted_close,
        "rmse": test_rmse,
        "n_days": len(xs),
        "today_open": today_open,
        "current_price": current_price,
    }
