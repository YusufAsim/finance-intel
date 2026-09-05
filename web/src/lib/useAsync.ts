/** Small data loading hook.
 *
 * Pages need the same four states everywhere: loading, error, empty and
 * loaded. Keeping that in one place stops a failed request from turning
 * into a blank screen.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "./api";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useAsync<T>(
  loader: () => Promise<T>,
  deps: unknown[] = [],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    loader()
      .then((result) => {
        if (active) setData(result);
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setData(null);
        setError(
          cause instanceof ApiError
            ? cause.message
            : "Something went wrong while loading this view.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);

  return { data, loading, error, reload };
}
