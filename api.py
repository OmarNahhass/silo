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

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_fetcher import fetch_data, PERIOD_OPTIONS
from model_registry import MODELS, ENSEMBLE_META
from utils.metrics import rmse
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS
import live_forecast
import prediction_history

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
prediction_history.init_db()

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
    ] + [{k: ENSEMBLE_META[k] for k in ("key", "name", "category", "math", "note")}]


def _compute_ensemble(raw_results: list[dict], close: pd.Series) -> dict | None:
    """Inverse-variance-weighted average of every model that actually produced a
    usable prediction: weight_i proportional to 1/RMSE_i^2, so more-reliable models
    (for this specific ticker) get more say. Also reconstructs the ensemble's own
    fitted series (weighted average of each contributing model's fitted values, on
    the dates they all share) and scores it on the same trailing-20% holdout window
    every individual model uses, so its RMSE is measured the same way, not estimated.
    """
    valid = [
        r for r in raw_results
        if r["error"] is None and r["prediction"] is not None
        and r["rmse"] is not None and r["rmse"] > 0 and math.isfinite(r["rmse"])
    ]
    if len(valid) < 2:
        return None

    inv_var = {r["key"]: 1.0 / (r["rmse"] ** 2) for r in valid}
    total = sum(inv_var.values())
    weights = {k: v / total for k, v in inv_var.items()}

    prediction = sum(weights[r["key"]] * r["prediction"] for r in valid)

    fitted_by_key = {r["key"]: r["fitted"] for r in valid}
    combined = pd.concat(fitted_by_key, axis=1, join="inner").dropna()

    ensemble_rmse = float("nan")
    ensemble_fitted = pd.Series(dtype=float)
    if len(combined) >= 10:
        w_vec = pd.Series({k: weights[k] for k in combined.columns})
        ensemble_fitted = combined.mul(w_vec, axis=1).sum(axis=1)
        split = max(1, int(len(ensemble_fitted) * 0.8))
        holdout_idx = ensemble_fitted.index[split:].intersection(close.index)
        if len(holdout_idx) > 0:
            ensemble_rmse = rmse(close.loc[holdout_idx].values, ensemble_fitted.loc[holdout_idx].values)

    return {
        "key": ENSEMBLE_META["key"],
        "name": ENSEMBLE_META["name"],
        "category": ENSEMBLE_META["category"],
        "prediction": prediction,
        "rmse": ensemble_rmse,
        "fitted": ensemble_fitted,
        "error": None,
    }


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
                "prediction": result["prediction"],
                "rmse": result["rmse"],
                "fitted": result["fitted"],
                "error": None,
            }
        except Exception as e:
            return {
                "key": spec["key"],
                "name": spec["name"],
                "category": spec["category"],
                "prediction": None,
                "rmse": None,
                "fitted": pd.Series(dtype=float),
                "error": str(e),
            }

    # map() preserves MODELS order in the results even though execution is concurrent.
    # Kept as raw pandas objects (not yet JSON-serialized) so the ensemble below can
    # reconstruct a weighted-average fitted series and score its own holdout RMSE the
    # same way each individual model does.
    raw_results = list(_model_executor.map(_run_one, MODELS))

    # Bias-correct each model's point prediction using its own tracked history of real
    # predictions vs. what actually happened (prediction_history.py) -- e.g. if Random
    # Forest has quietly run $0.40 too high on average over its last 30 resolved AAPL
    # predictions, shift today's prediction down by $0.40. Only the point "prediction"
    # is corrected, not "fitted"/"rmse" (those describe the historical backtest, a
    # separate, unrelated notion of accuracy from this ticker's live track record).
    ticker = req.ticker.strip().upper()
    as_of_date = close.index[-1].strftime("%Y-%m-%d")
    raw_predictions = {
        r["key"]: r["prediction"] for r in raw_results if r["error"] is None and r["prediction"] is not None
    }
    corrections = prediction_history.record_and_correct(ticker, req.asset_type, as_of_date, raw_predictions, close)
    for r in raw_results:
        info = corrections.get(r["key"])
        if info is not None:
            r["prediction"] = info["corrected"]
            r["bias"] = info["bias"]
            r["bias_n_samples"] = info["n_samples"]

    ensemble = _compute_ensemble(raw_results, close)
    if ensemble is not None:
        raw_results.append(ensemble)

    model_results = [
        {
            "key": r["key"],
            "name": r["name"],
            "category": r["category"],
            "prediction": _clean_float(r["prediction"]),
            "rmse": _clean_float(r["rmse"]),
            "fitted": _series_to_points(r["fitted"]),
            "error": r["error"],
            "bias": _clean_float(r.get("bias")),
            "bias_n_samples": r.get("bias_n_samples", 0),
        }
        for r in raw_results
    ]

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
        "ticker": ticker,
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
