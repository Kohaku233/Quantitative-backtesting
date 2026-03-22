import { useCallback, useEffect, useState } from "react";

import { getStrategies, ApiRequestError } from "../lib/api";
import type {
  StrategyMetadata,
  DiscoveryWarning,
} from "../types/contracts";

type StrategiesState = {
  strategies: StrategyMetadata[];
  discoveryWarnings: DiscoveryWarning[];
  isLoading: boolean;
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

export function useStrategies() {
  const [state, setState] = useState<StrategiesState>({
    strategies: [],
    discoveryWarnings: [],
    isLoading: true,
    error: null,
  });

  const load = useCallback(async () => {
    setState((current) => ({ ...current, isLoading: true, error: null }));

    try {
      const response = await getStrategies();
      setState({
        strategies: response.strategies,
        discoveryWarnings: response.discovery_warnings,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        isLoading: false,
        error: toApiRequestError(error),
      }));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    strategies: state.strategies,
    discoveryWarnings: state.discoveryWarnings,
    isLoading: state.isLoading,
    error: state.error,
    refetch: load,
  };
}
