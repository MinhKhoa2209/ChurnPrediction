'use client';

import { useState, useCallback } from 'react';
import { ApiError } from '../errors';
import { useApiError } from './useApiError';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error | ApiError) => void;
  showToast?: boolean;
  reportToSentry?: boolean;
}

interface UseApiState<T> {
  data: T | null;
  error: Error | ApiError | null;
  loading: boolean;
}

interface UserContext {
  userId?: string;
  userEmail?: string;
  userRole?: string;
}

export function useApi<T>(
  userContext?: UserContext
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    error: null,
    loading: false,
  });

  const { handleError } = useApiError(userContext);

  const execute = useCallback(
    async (
      apiCall: () => Promise<T>,
      options?: UseApiOptions<T>
    ): Promise<T | null> => {
      const {
        onSuccess,
        onError,
        showToast = true,
        reportToSentry = true,
      } = options || {};

      setState({ data: null, error: null, loading: true });

      try {
        const data = await apiCall();
        setState({ data, error: null, loading: false });

        if (onSuccess) {
          onSuccess(data);
        }

        return data;
      } catch (error) {
        const apiError = error instanceof ApiError ? error : new Error(String(error));
        setState({ data: null, error: apiError, loading: false });

        // Handle error with toast and Sentry
        handleError(apiError, {
          showToast,
          reportToSentry,
          onError,
        });

        return null;
      }
    },
    [handleError]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}
