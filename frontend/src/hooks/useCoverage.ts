import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiRequestError, getCoverage, syncCoverage } from "../lib/api";
import type {
  CoverageStatusResponse,
  DataSyncRequest,
  DataSyncResponse,
} from "../types/contracts";

type CoverageState = {
  coverage: CoverageStatusResponse | null;
  syncResult: DataSyncResponse | null;
  isLoading: boolean;
  isSyncing: boolean;
  error: ApiRequestError | null;
};

function toApiRequestError(value: unknown): ApiRequestError {
  if (value instanceof ApiRequestError) {
    return value;
  }

  if (value && typeof value === "object" && "code" in value && "message" in value) {
    const statusValue = (value as { status?: unknown }).status;
    return new ApiRequestError({
      code: String((value as { code?: unknown }).code ?? "unknown_error"),
      message: String((value as { message?: unknown }).message ?? "Request failed."),
      status: typeof statusValue === "number" ? statusValue : 0,
      details:
        typeof (value as { details?: unknown }).details === "object" &&
        (value as { details?: unknown }).details !== null
          ? ((value as { details?: Record<string, unknown> }).details ?? {})
          : {},
    });
  }

  return new ApiRequestError({
    code: "unknown_error",
    message: value instanceof Error ? value.message : "Request failed.",
    status: 0,
    details: {},
  });
}

export function useCoverage(params: DataSyncRequest | null) {
  const [state, setState] = useState<CoverageState>({
    coverage: null,
    syncResult: null,
    isLoading: Boolean(params),
    isSyncing: false,
    error: null,
  });

  const key = useMemo(() => {
    if (!params) {
      return "";
    }

    return [
      params.strategy_id,
      params.symbol,
      params.timeframe,
      params.start,
      params.end,
    ].join("|");
  }, [params]);

  const load = useCallback(async () => {
    if (!params) {
      setState({
        coverage: null,
        syncResult: null,
        isLoading: false,
        isSyncing: false,
        error: null,
      });
      return;
    }

    setState((current) => ({ ...current, isLoading: true, error: null }));

    try {
      const coverage = await getCoverage(params);
      setState((current) => ({
        ...current,
        coverage,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isLoading: false,
        error: toApiRequestError(error),
      }));
    }
  }, [params]);

  useEffect(() => {
    void load();
  }, [key]);

  const runSync = useCallback(async () => {
    if (!params) {
      return null;
    }

    setState((current) => ({ ...current, isSyncing: true, error: null }));

    try {
      const syncResult = await syncCoverage(params);
      setState((current) => ({
        ...current,
        syncResult,
        coverage: syncResult.coverage,
        isSyncing: false,
        error: null,
      }));
      return syncResult;
    } catch (error) {
      setState((current) => ({
        ...current,
        isSyncing: false,
        error: toApiRequestError(error),
      }));
      throw error;
    }
  }, [params]);

  return {
    coverage: state.coverage,
    syncResult: state.syncResult,
    isLoading: state.isLoading,
    isSyncing: state.isSyncing,
    error: state.error,
    refetch: load,
    syncCoverage: runSync,
  };
}
