'use client';

import { useCallback } from 'react';
import { ApiError, handleApiError } from '../errors';

interface UseApiErrorOptions {
  showToast?: boolean;
  reportToSentry?: boolean;
  onError?: (error: Error | ApiError) => void;
}

interface UserContext {
  userId?: string;
  userEmail?: string;
  userRole?: string;
}

export function useApiError(userContext?: UserContext) {
  const handleError = useCallback(
    (
      error: Error | ApiError,
      options?: UseApiErrorOptions
    ) => {
      const {
        showToast = true,
        reportToSentry = true,
        onError,
      } = options || {};

      // Handle the error with toast and Sentry
      handleApiError(error, {
        showToast,
        reportToSentry,
        userContext,
      });

      // Call custom error handler if provided
      if (onError) {
        onError(error);
      }
    },
    [userContext]
  );

  return { handleError };
}
