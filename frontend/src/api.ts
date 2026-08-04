import type {
  AnalystTargetResponse,
  AssetType,
  ForecastResponse,
  LiveForecast,
  ModelMeta,
  TrackRecordResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getTickers(assetType: AssetType): Promise<{ tickers: string[] }> {
  return fetch(`${API_BASE}/api/tickers/${assetType.toLowerCase()}`).then((r) =>
    handle<{ tickers: string[] }>(r),
  );
}

export function getModels(): Promise<ModelMeta[]> {
  return fetch(`${API_BASE}/api/models`).then((r) => handle<ModelMeta[]>(r));
}

export function postForecast(
  ticker: string,
  assetType: AssetType,
  period: string,
): Promise<ForecastResponse> {
  return fetch(`${API_BASE}/api/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, asset_type: assetType, period }),
  }).then((r) => handle<ForecastResponse>(r));
}

export function getLiveForecast(assetType: AssetType, ticker: string): Promise<LiveForecast> {
  return fetch(`${API_BASE}/api/live/${assetType.toLowerCase()}/${ticker}`).then((r) =>
    handle<LiveForecast>(r),
  );
}

export function getAnalystTarget(assetType: AssetType, ticker: string): Promise<AnalystTargetResponse> {
  return fetch(`${API_BASE}/api/analyst-target/${assetType.toLowerCase()}/${ticker}`).then((r) =>
    handle<AnalystTargetResponse>(r),
  );
}

export function getTrackRecord(
  assetType?: AssetType,
  ticker?: string,
  since?: string,
): Promise<TrackRecordResponse> {
  const params = new URLSearchParams();
  if (assetType) params.set("asset_type", assetType.toLowerCase());
  if (ticker) params.set("ticker", ticker);
  if (since) params.set("since", since);
  const qs = params.toString();
  return fetch(`${API_BASE}/api/track-record${qs ? `?${qs}` : ""}`).then((r) =>
    handle<TrackRecordResponse>(r),
  );
}
