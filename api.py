"""FastAPI backend for the CryptoCast React frontend (frontend/). Reuses the same
data-fetching and model logic as the Streamlit app (main.py) via data_fetcher.py,
model_registry.py, and utils/tickers.py -- none of that layer imports Streamlit, so
nothing here duplicates the forecasting logic, only exposes it as JSON.

Run with: uvicorn api:app --reload --port 8000
"""

import math
import warnings
warnings.filterwarnings("ignore")

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
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

live_forecast.init_db()


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

    model_results = []
    for spec in MODELS:
        try:
            result = spec["run"](data)
            model_results.append({
                "key": spec["key"],
                "name": spec["name"],
                "category": spec["category"],
                "prediction": _clean_float(result["prediction"]),
                "rmse": _clean_float(result["rmse"]),
                "fitted": _series_to_points(result["fitted"]),
                "error": None,
            })
        except Exception as e:
            model_results.append({
                "key": spec["key"],
                "name": spec["name"],
                "category": spec["category"],
                "prediction": None,
                "rmse": None,
                "fitted": [],
                "error": str(e),
            })

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
