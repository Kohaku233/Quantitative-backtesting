import { useCallback, useState } from "react";

import { ApiRequestError, runBacktest } from "../lib/api";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
} from "../types/contracts";

type RunBacktestState = {
  result: BacktestRunResponse | null;
  isRunning: boolean;
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

export function useRunBacktest() {
  const [state, setState] = useState<RunBacktestState>({
    result: null,
    isRunning: false,
    error: null,
  });

  const execute = useCallback(async (payload: BacktestRunRequest) => {
    setState({ result: null, isRunning: true, error: null });

    try {
      const result = await runBacktest(payload);
      setState({ result, isRunning: false, error: null });
      return result;
    } catch (error) {
      setState({
        result: null,
        isRunning: false,
        error: toApiRequestError(error),
      });
      throw error;
    }
  }, []);

  return {
    result: state.result,
    isRunning: state.isRunning,
    error: state.error,
    runBacktest: execute,
  };
}
