import type {
  AnalystTargetResponse,
  AssetType,
  ForecastResponse,
  LiveForecast,
  ModelMeta,
  SimilarTickersResponse,
  TrackRecordResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 2000;
const ATTEMPT_TIMEOUT_MS = 30000;

async function fetchWithRetry(url: string, options?: RequestInit): Promise<Response> {
  for (let attempt = 1; attempt <= RETRY_ATTEMPTS; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), ATTEMPT_TIMEOUT_MS);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } catch {
      if (attempt < RETRY_ATTEMPTS) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
      }
    } finally {
      clearTimeout(timeoutId);
    }
  }
  throw new Error(
    "Couldn't reach the server after several attempts. It may be waking up from being idle -- please try again in a moment.",
  );
}

export function warmUpBackend(): void {
  fetch(`${API_BASE}/api/models`).catch(() => {});
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getTickers(assetType: AssetType): Promise<{ tickers: string[] }> {
  return fetchWithRetry(`${API_BASE}/api/tickers/${assetType.toLowerCase()}`).then((r) =>
    handle<{ tickers: string[] }>(r),
  );
}

export function getModels(): Promise<ModelMeta[]> {
  return fetchWithRetry(`${API_BASE}/api/models`).then((r) => handle<ModelMeta[]>(r));
}

export function postForecast(
  ticker: string,
  assetType: AssetType,
  period: string,
): Promise<ForecastResponse> {
  return fetchWithRetry(`${API_BASE}/api/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, asset_type: assetType, period }),
  }).then((r) => handle<ForecastResponse>(r));
}

export function getLiveForecast(assetType: AssetType, ticker: string): Promise<LiveForecast> {
  return fetchWithRetry(`${API_BASE}/api/live/${assetType.toLowerCase()}/${ticker}`).then((r) =>
    handle<LiveForecast>(r),
  );
}

export function getAnalystTarget(assetType: AssetType, ticker: string): Promise<AnalystTargetResponse> {
  return fetchWithRetry(`${API_BASE}/api/analyst-target/${assetType.toLowerCase()}/${ticker}`).then((r) =>
    handle<AnalystTargetResponse>(r),
  );
}

export function getSimilarTickers(
  assetType: AssetType,
  ticker: string,
  topN = 10,
): Promise<SimilarTickersResponse> {
  const params = new URLSearchParams({ top_n: String(topN) });
  return fetchWithRetry(
    `${API_BASE}/api/similar-tickers/${assetType.toLowerCase()}/${ticker}?${params.toString()}`,
  ).then((r) => handle<SimilarTickersResponse>(r));
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
  return fetchWithRetry(`${API_BASE}/api/track-record${qs ? `?${qs}` : ""}`).then((r) =>
    handle<TrackRecordResponse>(r),
  );
}
