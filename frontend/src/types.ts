export type AssetType = "Stock" | "Crypto";

export interface ModelMeta {
  key: string;
  name: string;
  category: string;
  math: string;
  note: string;
}

export interface FittedPoint {
  date: string;
  value: number | null;
}

export interface ModelResult {
  key: string;
  name: string;
  category: string;
  prediction: number | null;
  rmse: number | null;
  fitted: FittedPoint[];
  error: string | null;
}

export interface PriceBar {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface ForecastResponse {
  ticker: string;
  asset_type: AssetType;
  period: string;
  trading_days: number;
  last_close: number;
  price_history: PriceBar[];
  models: ModelResult[];
}

export interface LiveBar {
  time: string;
  price: number;
}

export interface LiveHistoryRow {
  trade_date: string;
  predicted_close: number;
  actual_close: number | null;
}

export interface LiveForecast {
  ticker: string;
  asset_type: AssetType;
  trade_date: string;
  open_price: number;
  current_price: number;
  predicted_close: number | null;
  error: string | null;
  intraday_bars: LiveBar[];
  history: LiveHistoryRow[];
}
