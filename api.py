"""FastAPI backend for the CryptoCast React frontend (frontend/). Reuses the same
data-fetching and model logic as the Streamlit app (main.py) via data_fetcher.py,
model_registry.py, and utils/tickers.py -- none of that layer imports Streamlit, so
nothing here duplicates the forecasting logic, only exposes it as JSON.

Run with: uvicorn api:app --reload --port 8000
"""

import os

# Must run before numpy/statsmodels/sklearn/xgboost are imported anywhere (including
# transitively via data_fetcher below) -- each of those libraries otherwise spins up
# its own BLAS thread pool sized to all CPU cores. The API runs all 10 models
# concurrently in a thread pool (see _model_executor below), and two concurrent
# /api/forecast requests (e.g. the Compare page) run 20 of those threads at once --
# without this cap, every one of those threads also tries to grab every core for its
# own matrix math, and the resulting oversubscription made two concurrent forecasts
# take ~20s instead of the ~6s they take once each thread is limited to one core.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import math
import warnings
warnings.filterwarnings("ignore")

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_fetcher import fetch_data, PERIOD_OPTIONS
from model_registry import MODELS
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS
import live_forecast

app = FastAPI(title="CryptoCast API")

app.add_middleware(
    CORSMiddleware,
    # Vite's dev port drifts (5173, 5174, ...) whenever the default is already taken,
    # so match any localhost port instead of hardcoding one.
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

live_forecast.init_db()

# The 10 models are independent of each other, and the slow ones (SARIMA's iterative MLE
# fit, Random Forest/XGBoost's tree ensembles) do their real work in C/Fortran code that
# releases the GIL -- so running them in a thread pool gives real wall-clock speedup
# instead of the ~10s+ you get from running all 10 one after another.
_model_executor = ThreadPoolExecutor(max_workers=len(MODELS))


def _clean_float(value):
    """NaN isn't valid JSON -- convert to None so the frontend gets a clean null."""
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _series_to_points(series):
    return [{"date": ts.strftime("%Y-%m-%d"), "value": _clean_float(val)} for ts, val in series.items()]


class ForecastRequest(BaseModel):
    ticker: str
    asset_type: str  # "Stock" or "Crypto"
    period: str = PERIOD_OPTIONS[2]


@app.get("/api/tickers/{asset_type}")
def get_tickers(asset_type: str):
    if asset_type.lower() == "stock":
        return {"tickers": STOCK_TICKERS}
    if asset_type.lower() == "crypto":
        return {"tickers": CRYPTO_TICKERS}
    raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")


@app.get("/api/models")
def get_models():
    return [
        {"key": spec["key"], "name": spec["name"], "category": spec["category"],
         "math": spec["math"], "note": spec["note"]}
        for spec in MODELS
    ]


@app.post("/api/forecast")
def post_forecast(req: ForecastRequest):
    if not req.ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker is required.")

    try:
        data = fetch_data(req.ticker, asset_type=req.asset_type, period=req.period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't fetch data for {req.ticker}: {e}")

    close = data["Close"].dropna()

    def _run_one(spec):
        try:
            result = spec["run"](data)
            return {
                "key": spec["key"],
                "name": spec["name"],
                "category": spec["category"],
                "prediction": _clean_float(result["prediction"]),
                "rmse": _clean_float(result["rmse"]),
                "fitted": _series_to_points(result["fitted"]),
                "error": None,
            }
        except Exception as e:
            return {
                "key": spec["key"],
                "name": spec["name"],
                "category": spec["category"],
                "prediction": None,
                "rmse": None,
                "fitted": [],
                "error": str(e),
            }

    # map() preserves MODELS order in the results even though execution is concurrent.
    model_results = list(_model_executor.map(_run_one, MODELS))

    price_history = [
        {
            "date": ts.strftime("%Y-%m-%d"),
            "open": _clean_float(row["Open"]),
            "high": _clean_float(row["High"]),
            "low": _clean_float(row["Low"]),
            "close": _clean_float(row["Close"]),
            "volume": _clean_float(row["Volume"]),
        }
        for ts, row in data.iterrows()
    ]

    return {
        "ticker": req.ticker.strip().upper(),
        "asset_type": req.asset_type,
        "period": req.period,
        "trading_days": len(data),
        "last_close": _clean_float(close.iloc[-1]),
        "price_history": price_history,
        "models": model_results,
    }


@app.get("/api/live/{asset_type}/{ticker}")
def get_live(asset_type: str, ticker: str):
    if asset_type.lower() not in ("stock", "crypto"):
        raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")
    asset_type = "Stock" if asset_type.lower() == "stock" else "Crypto"

    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker is required.")

    try:
        return live_forecast.get_live_forecast(ticker, asset_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't fetch live data for {ticker}: {e}")
