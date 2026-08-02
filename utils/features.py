import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    close = data["Close"]
    macd_line, signal_line = macd(close)

    feat = pd.DataFrame(index=data.index)
    feat["return_1"] = close.pct_change(1)
    feat["return_5"] = close.pct_change(5)
    feat["sma_5_ratio"] = sma(close, 5) / close - 1
    feat["sma_20_ratio"] = sma(close, 20) / close - 1
    feat["ema_12_ratio"] = ema(close, 12) / close - 1
    feat["ema_26_ratio"] = ema(close, 26) / close - 1
    feat["rsi_14"] = rsi(close, 14) / 100
    feat["macd_norm"] = macd_line / close
    feat["macd_signal_norm"] = signal_line / close
    feat["volatility_10"] = close.pct_change().rolling(10).std()

    target = np.log(close.shift(-1) / close)

    return feat, target
