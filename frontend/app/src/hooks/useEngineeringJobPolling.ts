import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export const ENGINEERING_JOB_TYPES = [
  "st_generation",
  "st_verification",
  "io_mapping",
  "runtime_validation",
  "simulation_validation",
] as const;

export const ENGINEERING_JOB_STATES = [
  "queued",
  "pending",
  "running",
  "succeeded",
  "failed",
  "cancelled",
  "unknown",
] as const;

export const ENGINEERING_JOB_TERMINAL_STATES = ["succeeded", "failed", "cancelled"] as const;

export type EngineeringJobType = (typeof ENGINEERING_JOB_TYPES)[number];
export type EngineeringJobState = (typeof ENGINEERING_JOB_STATES)[number];

export type EngineeringJobStatusResponse<TResult = unknown> = {
  job_id: string;
  project_id: string;
  job_type: EngineeringJobType;
  status: EngineeringJobState | string;
  progress?: number | null;
  message?: string | null;
  updated_at?: string | null;
  result?: TResult | null;
  error?: string | null;
};

export type PollingError = {
  message: string;
  cause?: unknown;
  retryCount: number;
};

export type UseEngineeringJobPollingOptions<TResponse> = {
  enabled?: boolean;
  immediate?: boolean;
  intervalMs?: number;
  maxPollAttempts?: number;
  maxRetries?: number;
  backoffBaseMs?: number;
  backoffMaxMs?: number;
  backoffJitterRatio?: number;
  fetchStatus: (signal: AbortSignal) => Promise<TResponse>;
  getState?: (response: TResponse) => string | null | undefined;
  isTerminal?: (response: TResponse) => boolean;
  isSuccess?: (response: TResponse) => boolean;
  onUpdate?: (response: TResponse) => void;
  onSuccess?: (response: TResponse) => void;
  onTerminal?: (response: TResponse) => void;
  onError?: (error: PollingError) => void;
  onCancel?: () => void;
};

export type UseEngineeringJobPollingResult<TResponse> = {
  data: TResponse | null;
  error: PollingError | null;
  isPolling: boolean;
  isCancelled: boolean;
  pollCount: number;
  retryCount: number;
  lastState: string | null;
  isTerminal: boolean;
  isSuccess: boolean;
  start: () => void;
  cancel: () => void;
  reset: () => void;
};

export const isEngineeringJobTerminalState = (state: string | null | undefined): boolean => {
  if (!state) {
    return false;
  }
  return ENGINEERING_JOB_TERMINAL_STATES.includes(state as (typeof ENGINEERING_JOB_TERMINAL_STATES)[number]);
};

export const defaultBackoffDelay = (
  retryCount: number,
  baseMs: number,
  maxMs: number,
  jitterRatio: number
): number => {
  const exponent = Math.max(0, retryCount - 1);
  const exponentialDelay = Math.min(maxMs, baseMs * 2 ** exponent);
  const jitterSpread = exponentialDelay * Math.max(0, jitterRatio);
  const jitterOffset = jitterSpread > 0 ? (Math.random() * jitterSpread * 2 - jitterSpread) : 0;
  const delayWithJitter = Math.round(exponentialDelay + jitterOffset);
  return Math.max(0, Math.min(maxMs, delayWithJitter));
};

const defaultGetState = <TResponse,>(response: TResponse): string | null => {
  if (typeof response !== "object" || response === null) {
    return null;
  }

  const maybeRecord = response as Record<string, unknown>;
  const maybeState = maybeRecord.status;
  return typeof maybeState === "string" ? maybeState : null;
};

export function useEngineeringJobPolling<TResponse>(
  options: UseEngineeringJobPollingOptions<TResponse>
): UseEngineeringJobPollingResult<TResponse> {
  const {
    enabled = true,
    immediate = true,
    intervalMs = 3000,
    maxPollAttempts = Number.POSITIVE_INFINITY,
    maxRetries = 5,
    backoffBaseMs = 1000,
    backoffMaxMs = 30000,
    backoffJitterRatio = 0.2,
    fetchStatus,
    getState = defaultGetState,
    isTerminal,
    isSuccess,
    onUpdate,
    onSuccess,
    onTerminal,
    onError,
    onCancel,
  } = options;

  const [data, setData] = useState<TResponse | null>(null);
  const [error, setError] = useState<PollingError | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [isCancelled, setIsCancelled] = useState<boolean>(false);
  const [pollCount, setPollCount] = useState<number>(0);
  const [retryCount, setRetryCount] = useState<number>(0);
  const [lastState, setLastState] = useState<string | null>(null);

  const timeoutRef = useRef<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const unmountedRef = useRef<boolean>(false);
  const pollCountRef = useRef<number>(0);
  const retryCountRef = useRef<number>(0);
  const cancelledRef = useRef<boolean>(false);

  const clearTimer = useCallback((): void => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const cancelCurrentRequest = useCallback((): void => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const stopPolling = useCallback((): void => {
    clearTimer();
    cancelCurrentRequest();
    setIsPolling(false);
  }, [cancelCurrentRequest, clearTimer]);

  const resolveTerminal = useCallback(
    (response: TResponse): { terminal: boolean; success: boolean; state: string | null } => {
      const state = getState(response) ?? null;
      const terminal = isTerminal ? isTerminal(response) : isEngineeringJobTerminalState(state);
      const successState = state === "succeeded";
      const success = isSuccess ? isSuccess(response) : successState;
      return { terminal, success, state };
    },
    [getState, isSuccess, isTerminal]
  );

  const scheduleNextPoll = useCallback(
    (delayMs: number, runner: () => Promise<void>): void => {
      clearTimer();
      timeoutRef.current = window.setTimeout(() => {
        void runner();
      }, delayMs);
    },
    [clearTimer]
  );

  const poll = useCallback(async (): Promise<void> => {
    if (unmountedRef.current || cancelledRef.current) {
      return;
    }

    if (pollCountRef.current >= maxPollAttempts) {
      stopPolling();
      return;
    }

    cancelCurrentRequest();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetchStatus(controller.signal);
      if (unmountedRef.current || cancelledRef.current) {
        return;
      }

      pollCountRef.current += 1;
      setPollCount(pollCountRef.current);
      retryCountRef.current = 0;
      setRetryCount(0);
      setError(null);
      setData(response);
      onUpdate?.(response);

      const resolution = resolveTerminal(response);
      setLastState(resolution.state);

      if (resolution.terminal) {
        stopPolling();
        onTerminal?.(response);
        if (resolution.success) {
          onSuccess?.(response);
        }
        return;
      }

      scheduleNextPoll(intervalMs, poll);
    } catch (cause) {
      if (unmountedRef.current || cancelledRef.current) {
        return;
      }
      if (controller.signal.aborted) {
        return;
      }

      retryCountRef.current += 1;
      setRetryCount(retryCountRef.current);

      const pollingError: PollingError = {
        message: "Engineering status polling failed",
        cause,
        retryCount: retryCountRef.current,
      };
      setError(pollingError);
      onError?.(pollingError);

      if (retryCountRef.current > maxRetries) {
        stopPolling();
        return;
      }

      const retryDelay = defaultBackoffDelay(retryCountRef.current, backoffBaseMs, backoffMaxMs, backoffJitterRatio);
      scheduleNextPoll(retryDelay, poll);
    }
  }, [
    backoffBaseMs,
    backoffJitterRatio,
    backoffMaxMs,
    cancelCurrentRequest,
    fetchStatus,
    intervalMs,
    maxPollAttempts,
    maxRetries,
    onError,
    onSuccess,
    onTerminal,
    onUpdate,
    resolveTerminal,
    scheduleNextPoll,
    stopPolling,
  ]);

  const start = useCallback((): void => {
    if (!enabled) {
      return;
    }
    cancelledRef.current = false;
    setIsCancelled(false);
    setIsPolling(true);
    setError(null);
    void poll();
  }, [enabled, poll]);

  const cancel = useCallback((): void => {
    cancelledRef.current = true;
    setIsCancelled(true);
    stopPolling();
    onCancel?.();
  }, [onCancel, stopPolling]);

  const reset = useCallback((): void => {
    cancelledRef.current = false;
    pollCountRef.current = 0;
    retryCountRef.current = 0;
    setData(null);
    setError(null);
    setIsCancelled(false);
    setPollCount(0);
    setRetryCount(0);
    setLastState(null);
  }, []);

  useEffect(() => {
    if (!enabled || !immediate) {
      return;
    }
    start();
    return () => {
      cancel();
    };
  }, [cancel, enabled, immediate, start]);

  useEffect(() => {
    return () => {
      unmountedRef.current = true;
      stopPolling();
    };
  }, [stopPolling]);

  return useMemo(
    () => ({
      data,
      error,
      isPolling,
      isCancelled,
      pollCount,
      retryCount,
      lastState,
      isTerminal: isEngineeringJobTerminalState(lastState),
      isSuccess: lastState === "succeeded",
      start,
      cancel,
      reset,
    }),
    [cancel, data, error, isCancelled, isPolling, lastState, pollCount, reset, retryCount, start]
  );
}
