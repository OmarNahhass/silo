import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average: SMA_t = (1/n) * sum(Close[t-n+1..t])."""
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average: EMA_t = alpha*Close_t + (1-alpha)*EMA_{t-1}, alpha = 2/(span+1)."""
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index: RSI = 100 - 100/(1 + RS), RS = avg(gain)/avg(loss) over the window."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD line = EMA_fast - EMA_slow; signal line = EMA_signal(MACD line)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer a stationary feature set from raw OHLCV data, plus the next-day
    log return as the prediction target: target_t = log(Close_{t+1} / Close_t).

    Price-scale indicators (SMA/EMA) are expressed as a ratio to the current
    close rather than raw levels, since raw price levels aren't stationary
    and would break the "similar inputs -> similar output" assumption that
    k-NN, SVR, and tree splits rely on.
    """
    close = data["Close"]
    macd_line, signal_line = macd(close)

    feat = pd.DataFrame(index=data.index)
    feat["return_1"] = close.pct_change(1)
    feat["return_5"] = close.pct_change(5)
    feat["sma_5_ratio"] = sma(close, 5) / close - 1
    feat["sma_20_ratio"] = sma(close, 20) / close - 1
    feat["ema_12_ratio"] = ema(close, 12) / close - 1
    feat["ema_26_ratio"] = ema(close, 26) / close - 1
    feat["rsi_14"] = rsi(close, 14) / 100  # scale to [0, 1]
    feat["macd_norm"] = macd_line / close
    feat["macd_signal_norm"] = signal_line / close
    feat["volatility_10"] = close.pct_change().rolling(10).std()

    target = np.log(close.shift(-1) / close)

    return feat, target
