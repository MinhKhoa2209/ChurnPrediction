import { handleApiError, ApiError, isAuthenticationError } from './errors';
import { useDegradedModeStore } from './store/degradedModeStore';

interface InterceptorOptions {
  showToast?: boolean;
  reportToSentry?: boolean;
  userContext?: {
    userId?: string;
    userEmail?: string;
    userRole?: string;
  };
  onAuthError?: () => void;
  cacheKey?: string;
}

export async function withErrorHandling<T>(
  apiCall: () => Promise<T>,
  options?: InterceptorOptions
): Promise<T | null> {
  const {
    showToast = true,
    reportToSentry = true,
    userContext,
    onAuthError,
    cacheKey,
  } = options || {};

  const store = useDegradedModeStore.getState();

  try {
    const response = await apiCall();

    // Check if response is a fetch Response object
    if (response && typeof response === 'object' && 'headers' in response) {
      const fetchResponse = response as unknown as Response;
      
      // Check for degraded mode header (Requirement 30.2)
      const isDegraded = fetchResponse.headers.get('X-Degraded-Mode') === 'true';
      store.setDegradedMode(isDegraded);
      
      // Mark as connected if we got a response
      if (!store.backendUnreachable) {
        store.markConnected();
      }
      
      // Cache successful responses if cache key provided (Requirement 30.4)
      if (cacheKey && response) {
        store.cacheData(cacheKey, response);
      }
    }

    return response;
  } catch (error) {
    // Check if this is a network error (backend unreachable)
    const isNetworkError = 
      error instanceof TypeError ||
      (error instanceof Error && error.message.includes('fetch')) ||
      (error instanceof Error && error.message.includes('network'));

    if (isNetworkError) {
      // Backend is unreachable - try to return cached data (Requirement 30.4)
      store.setBackendUnreachable(true);
      
      if (cacheKey) {
        const cachedData = store.getCachedData(cacheKey);
        if (cachedData) {
          console.log(`Using cached data for ${cacheKey} (backend unreachable)`);
          return cachedData;
        }
      }
    }

    const apiError = error instanceof ApiError ? error : new Error(String(error));

    // Handle authentication errors specially
    if (isAuthenticationError(apiError)) {
      if (onAuthError) {
        onAuthError();
      } else {
        // Default: redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }

    // Handle the error with toast and Sentry
    handleApiError(apiError, {
      showToast,
      reportToSentry,
      userContext,
    });

    return null;
  }
}

/**
 * Creates an API interceptor with pre-configured options
 * Useful for creating a consistent error handling pattern across the app
 * 
 * @param defaultOptions - Default options for all intercepted calls
 * @returns Function to wrap API calls
 */
export function createApiInterceptor(defaultOptions?: InterceptorOptions) {
  return async function <T>(
    apiCall: () => Promise<T>,
    options?: InterceptorOptions
  ): Promise<T | null> {
    return withErrorHandling(apiCall, {
      ...defaultOptions,
      ...options,
    });
  };
}

/**
 * Retry an API call with exponential backoff
 * Requirement 20.4: Retry failed requests with exponential backoff
 * 
 * @param apiCall - The API call function to execute
 * @param maxRetries - Maximum number of retries (default: 3)
 * @param baseDelay - Base delay in milliseconds (default: 1000)
 * @param options - Interceptor options
 * @returns Promise with the API response or null on error
 */
export async function withRetry<T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
  options?: InterceptorOptions
): Promise<T | null> {
  let lastError: Error | ApiError | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error instanceof ApiError ? error : new Error(String(error));

      // Don't retry on authentication or authorization errors
      if (
        lastError instanceof ApiError &&
        (isAuthenticationError(lastError) || lastError.code === 'AUTHORIZATION_ERROR')
      ) {
        break;
      }

      // Don't retry on validation errors
      if (lastError instanceof ApiError && lastError.code === 'VALIDATION_ERROR') {
        break;
      }

      // If this is the last attempt, break
      if (attempt === maxRetries) {
        break;
      }

      // Calculate exponential backoff delay
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  // Handle the final error
  if (lastError) {
    handleApiError(lastError, options);
  }

  return null;
}

/**
 * Auto-reconnect to backend when unreachable
 * Requirement 30.6: Automatically reconnect and refresh when backend recovers
 * 
 * @param healthCheckFn - Function to check backend health
 * @param onReconnect - Callback when reconnection succeeds
 * @returns Cleanup function to stop reconnection attempts
 */
export function startAutoReconnect(
  healthCheckFn: () => Promise<boolean>,
  onReconnect?: () => void
): () => void {
  const store = useDegradedModeStore.getState();
  let timeoutId: NodeJS.Timeout | null = null;
  let stopped = false;

  const attemptReconnect = async () => {
    if (stopped) return;

    const { reconnectAttempts, backendUnreachable } = useDegradedModeStore.getState();

    // Stop if backend is reachable or max attempts exceeded
    if (!backendUnreachable || reconnectAttempts >= 5) {
      return;
    }

    store.startReconnect();

    try {
      const isHealthy = await healthCheckFn();
      
      if (isHealthy) {
        // Reconnection successful
        store.completeReconnect(true);
        console.log('Backend reconnected successfully');
        
        // Call reconnect callback to refresh data
        if (onReconnect) {
          onReconnect();
        }
        
        return; // Stop reconnection attempts
      } else {
        // Health check failed, schedule next attempt
        store.completeReconnect(false);
        scheduleNextAttempt();
      }
    } catch (error) {
      // Reconnection failed, schedule next attempt
      store.completeReconnect(false);
      scheduleNextAttempt();
    }
  };

  const scheduleNextAttempt = () => {
    if (stopped) return;

    const { reconnectAttempts } = useDegradedModeStore.getState();
    
    // Calculate exponential backoff delay
    const delay = Math.min(
      2000 * Math.pow(2, reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    console.log(`Scheduling reconnection attempt in ${delay}ms`);
    
    timeoutId = setTimeout(attemptReconnect, delay);
  };

  // Start first attempt
  scheduleNextAttempt();

  // Return cleanup function
  return () => {
    stopped = true;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
}
