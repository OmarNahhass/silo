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
  naive_close: number;
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
  model_mae: number | null;
  naive_mae: number | null;
  n_resolved: number;
}

export interface AnalystTarget {
  mean: number;
  high: number | null;
  low: number | null;
  median: number | null;
  recommendation: string | null;
  num_analysts: number | null;
}

export interface AnalystTargetResponse {
  ticker: string;
  asset_type: AssetType;
  target: AnalystTarget | null;
}

export interface TrackRecordModelStat {
  key: string;
  name: string;
  category: string;
  n_samples: number;
  rmse: number;
  mae: number;
  mape: number | null;
}

export interface NaiveBaselineStat {
  n_samples: number;
  rmse: number;
  mae: number;
}

export interface EnsembleVsNaiveTest {
  n_samples: number;
  mean_abs_error_diff: number;
  t_statistic: number;
  p_value: number;
  significant_at_0_05: boolean;
  verdict: string;
}

export interface TrackRecordResponse {
  scope: { ticker: string | null; asset_type: AssetType | null; since: string | null };
  per_model: TrackRecordModelStat[];
  naive_baseline: NaiveBaselineStat | null;
  ensemble_vs_naive_test: EnsembleVsNaiveTest | null;
}

export interface SimilarTickerResult {
  ticker: string;
  similarity: number;
}

export interface SimilarTickersResponse {
  ticker: string;
  asset_type: AssetType;
  results: SimilarTickerResult[];
}
