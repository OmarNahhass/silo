import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import math
import warnings
warnings.filterwarnings("ignore")

from concurrent.futures import ThreadPoolExecutor

import time
from collections import defaultdict

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data_fetcher import fetch_data, PERIOD_OPTIONS
from model_registry import MODELS, ENSEMBLE_META
from utils.metrics import rmse
from utils.tickers import STOCK_TICKERS, CRYPTO_TICKERS
import live_forecast
import prediction_history
import track_record
from analyst_targets import get_analyst_target

app = FastAPI(title="Silo API")

_allowed_origins = os.environ.get("ALLOWED_ORIGINS")
if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _allowed_origins.split(",")],
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_methods=["*"],
        allow_headers=["*"],
    )

live_forecast.init_db()
prediction_history.init_db()

_model_executor = ThreadPoolExecutor(max_workers=4)

_request_log: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20


def _client_ip(request: Request) -> str:
    return (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def rate_limit(request: Request):
    ip = _client_ip(request)
    now = time.time()
    recent = [t for t in _request_log[ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests -- please slow down and try again shortly.")
    recent.append(now)
    _request_log[ip] = recent


def _clean_float(value):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _series_to_points(series):
    return [{"date": ts.strftime("%Y-%m-%d"), "value": _clean_float(val)} for ts, val in series.items()]


class ForecastRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    asset_type: str
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
def post_forecast(req: ForecastRequest, _: None = Depends(rate_limit)):
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

    raw_results = list(_model_executor.map(_run_one, MODELS))

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
        try:
            prediction_history.record_prediction(
                ticker, req.asset_type, "ensemble", as_of_date, ensemble["prediction"], float(close.iloc[-1])
            )
        except Exception:
            pass

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
def get_live(
    asset_type: str,
    ticker: str = Path(..., min_length=1, max_length=20),
    _: None = Depends(rate_limit),
):
    if asset_type.lower() not in ("stock", "crypto"):
        raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")
    asset_type = "Stock" if asset_type.lower() == "stock" else "Crypto"

    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker is required.")

    try:
        return live_forecast.get_live_forecast(ticker, asset_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't fetch live data for {ticker}: {e}")


@app.get("/api/analyst-target/{asset_type}/{ticker}")
def get_analyst_target_endpoint(
    asset_type: str,
    ticker: str = Path(..., min_length=1, max_length=20),
    _: None = Depends(rate_limit),
):
    if asset_type.lower() not in ("stock", "crypto"):
        raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")
    asset_type = "Stock" if asset_type.lower() == "stock" else "Crypto"

    if not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker is required.")

    try:
        target = get_analyst_target(ticker, asset_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't fetch analyst data for {ticker}: {e}")

    return {"ticker": ticker.strip().upper(), "asset_type": asset_type, "target": target}


@app.get("/api/track-record")
def get_track_record_endpoint(asset_type: str | None = None, ticker: str | None = None, since: str | None = None):
    if ticker and not asset_type:
        raise HTTPException(status_code=400, detail="asset_type is required when ticker is given.")
    if asset_type is not None:
        if asset_type.lower() not in ("stock", "crypto"):
            raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")
        asset_type = "Stock" if asset_type.lower() == "stock" else "Crypto"
    ticker = ticker.strip().upper() if ticker else None

    try:
        return track_record.get_track_record(ticker=ticker, asset_type=asset_type, since=since)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Couldn't compute track record: {e}")
