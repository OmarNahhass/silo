import type { AssetType, ForecastResponse, LiveForecast, ModelMeta } from "./types";

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
