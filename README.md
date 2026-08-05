# CryptoCast

CryptoCast runs 10 forecasting models -- statistical and machine learning -- plus a weighted
ensemble that combines them, on real stock and cryptocurrency price history to predict the next
trading day's closing price. It tracks live intraday predictions against what actually happens,
lets you compare two tickers side by side, and keeps an honest, ongoing record of how accurate its
own predictions have actually been.

**Live**: https://cryptocast.pages.dev
**Not financial advice** -- see the disclaimer shown on first visit.

## Features

- **Stock / Crypto forecasts** -- 10 models (Linear Regression, ARIMA, SARIMA, ETS, Prophet-style
  decomposition, Polynomial Regression, KNN, Random Forest, Gradient Boosting/XGBoost, SVR) plus an
  inverse-variance-weighted ensemble, each with its formula and a plain-English explanation.
- **Live intraday** -- predicts today's closing price from the return so far, checked against the
  naive "no change" baseline once the day resolves.
- **Compare** -- run two tickers side by side, including against Yahoo Finance analyst
  consensus targets.
- **Track Record** -- rolling accuracy (RMSE / MAE / MAPE) per model, plus a paired t-test of the
  ensemble against a naive no-change baseline, so the app's own track record is verifiable rather
  than asserted.

## Stack

- **Backend**: FastAPI (`api.py`), scikit-learn / statsmodels / XGBoost, `yfinance` for data,
  SQLite for prediction history.
- **Frontend**: React 19 + TypeScript + Vite, React Router, Plotly for charts, KaTeX for formulas.
- **Deploy**: backend on Fly.io, frontend on Cloudflare Pages, auto-deployed on push to `main` via
  GitHub Actions (`.github/workflows/deploy.yml`).

## Running locally

Backend (from the repo root):

```
uvicorn api:app --reload --port 8000
```

Frontend (from `frontend/`):

```
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000` by default (override with
`VITE_API_BASE_URL`).

## Tests

```
pytest
```

Backend tests cover the models, the ensemble, data caching, prediction history, and the track
record statistics. Frontend type-checking and linting:

```
cd frontend
npm run build   # tsc -b && vite build
npm run lint     # oxlint
```

## Project layout

```
api.py                  FastAPI app and routes
model_registry.py       The 10 models + ensemble metadata (name, formula, explanation)
models/                 One module per forecasting model
data_fetcher.py         yfinance wrapper with caching
live_forecast.py        Intraday prediction tracking (SQLite)
prediction_history.py   Daily prediction tracking + bias correction (SQLite)
track_record.py         Rolling accuracy stats + naive-baseline significance test
analyst_targets.py      Yahoo Finance analyst consensus targets
utils/                  Shared feature engineering, metrics, ticker lists
tests/                  pytest suite
frontend/               React + Vite app
```
