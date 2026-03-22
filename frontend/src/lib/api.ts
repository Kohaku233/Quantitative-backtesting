import {
  type ApiErrorEnvelope,
  AppApiError,
  type BacktestRunRequest,
  type BacktestRunResponse,
  type CoverageStatusResponse,
  type DataSyncRequest,
  type DataSyncResponse,
  type JsonRecord,
  type StrategiesResponse,
} from "../types/contracts";

async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text.length > 0 ? text : undefined;
}

function isErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const error = (value as { error?: unknown }).error;
  if (typeof error !== "object" || error === null) {
    return false;
  }

  const candidate = error as {
    code?: unknown;
    message?: unknown;
    details?: unknown;
  };

  return (
    typeof candidate.code === "string" &&
    typeof candidate.message === "string" &&
    typeof candidate.details === "object" &&
    candidate.details !== null
  );
}

function normalizeDetails(value: unknown): JsonRecord {
  if (typeof value === "object" && value !== null) {
    return value as JsonRecord;
  }

  if (typeof value === "string") {
    return { message: value };
  }

  return {};
}

export class ApiRequestError extends AppApiError {
  constructor({
    code,
    message,
    status,
    details,
  }: {
    code: string;
    message: string;
    status: number;
    details?: JsonRecord;
  }) {
    super({ code, message, status, details });
    this.name = "ApiRequestError";
  }
}

export async function fetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  let response: Response;

  try {
    response = await fetch(input, {
      ...init,
      headers,
    });
  } catch (cause) {
    throw new ApiRequestError({
      code: "network_error",
      message: cause instanceof Error ? cause.message : "Network request failed.",
      status: 0,
      details: { cause: String(cause) },
    });
  }

  const body = await readBody(response);

  if (!response.ok) {
    if (isErrorEnvelope(body)) {
      throw new ApiRequestError({
        code: body.error.code,
        message: body.error.message,
        status: response.status,
        details: body.error.details,
      });
    }

    throw new ApiRequestError({
      code: "http_error",
      message: response.statusText || "Request failed.",
      status: response.status,
      details: normalizeDetails(body),
    });
  }

  return body as T;
}

export function getStrategies(): Promise<StrategiesResponse> {
  return fetchJson<StrategiesResponse>("/api/strategies");
}

export function getCoverage(
  params: DataSyncRequest,
): Promise<CoverageStatusResponse> {
  const searchParams = new URLSearchParams({
    strategy_id: params.strategy_id,
    symbol: params.symbol,
    timeframe: params.timeframe,
    start: params.start,
    end: params.end,
  });

  return fetchJson<CoverageStatusResponse>(`/api/data/status?${searchParams.toString()}`);
}

export function syncCoverage(
  payload: DataSyncRequest,
): Promise<DataSyncResponse> {
  return fetchJson<DataSyncResponse>("/api/data/sync", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function runBacktest(
  payload: BacktestRunRequest,
): Promise<BacktestRunResponse> {
  return fetchJson<BacktestRunResponse>("/api/backtests/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
