'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useApi } from '@/lib/hooks/useApi';
import { useApiError } from '@/lib/hooks/useApiError';
import { withErrorHandling, withRetry } from '@/lib/apiInterceptor';
import { showSuccessToast, showErrorToast } from '@/lib/errors';

interface User {
  id: string;
  email: string;
  role: string;
}

export function ErrorHandlingExample() {
  const [user] = useState<User | null>(null);
  const [token] = useState<string | null>(null);

  const { data, loading, error, execute } = useApi<unknown>({
    userId: user?.id,
    userEmail: user?.email,
    userRole: user?.role,
  });

  const handleUseApiExample = async () => {
    await execute(
      () => api.get('/datasets', token || undefined),
      {
        onSuccess: (data: unknown) => {
          showSuccessToast('Data loaded successfully');
          console.log('Data:', data);
        },
        showToast: true,
        reportToSentry: true,
      }
    );
  };

  const { handleError } = useApiError({
    userId: user?.id,
    userEmail: user?.email,
    userRole: user?.role,
  });

  const handleUseApiErrorExample = async () => {
    try {
      const result = await api.get('/datasets', token || undefined);
      showSuccessToast('Data loaded successfully');
      console.log('Result:', result);
    } catch (error) {
      handleError(error as Error, {
        showToast: true,
        reportToSentry: true,
      });
    }
  };

  const handleWithErrorHandlingExample = async () => {
    const result = await withErrorHandling(
      () => api.get('/datasets', token || undefined),
      {
        showToast: true,
        reportToSentry: true,
        userContext: {
          userId: user?.id,
          userEmail: user?.email,
          userRole: user?.role,
        },
      }
    );

    if (result) {
      showSuccessToast('Data loaded successfully');
      console.log('Result:', result);
    }
  };

  const handleWithRetryExample = async () => {
    const result = await withRetry(
      () => api.get('/datasets', token || undefined),
      3,
      1000,
      {
        showToast: true,
        reportToSentry: true,
        userContext: {
          userId: user?.id,
          userEmail: user?.email,
          userRole: user?.role,
        },
      }
    );

    if (result) {
      showSuccessToast('Data loaded successfully');
      console.log('Result:', result);
    }
  };

  const handleManualExample = async () => {
    try {
      const result = await api.get('/datasets', token || undefined);
      showSuccessToast('Data loaded successfully');
      console.log('Result:', result);
    } catch (error) {
      console.error('Error:', error);
      showErrorToast(error as Error);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Error Handling Examples</h1>
      
      <div className="space-y-4">
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Example 1: useApi Hook</h2>
          <p className="text-sm text-gray-600 mb-3">
            Automatic error handling with loading states
          </p>
          <button
            onClick={handleUseApiExample}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-primary-foreground rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Fetch with useApi'}
          </button>
          {error && <p className="text-red-600 mt-2">Error occurred (check toast)</p>}
          {typeof data !== 'undefined' && data !== null ? (
            <pre className="mt-2 text-xs bg-gray-100 p-2 rounded">{JSON.stringify(data as any, null, 2)}</pre>
          ) : null}
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Example 2: useApiError Hook</h2>
          <p className="text-sm text-gray-600 mb-3">
            Manual API call with automatic error handling
          </p>
          <button
            onClick={handleUseApiErrorExample}
            className="px-4 py-2 bg-green-600 text-primary-foreground rounded hover:bg-green-700"
          >
            Fetch with useApiError
          </button>
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Example 3: withErrorHandling</h2>
          <p className="text-sm text-gray-600 mb-3">
            Wrap API call with error interceptor
          </p>
          <button
            onClick={handleWithErrorHandlingExample}
            className="px-4 py-2 bg-purple-600 text-primary-foreground rounded hover:bg-purple-700"
          >
            Fetch with withErrorHandling
          </button>
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Example 4: withRetry</h2>
          <p className="text-sm text-gray-600 mb-3">
            Automatic retry with exponential backoff
          </p>
          <button
            onClick={handleWithRetryExample}
            className="px-4 py-2 bg-orange-600 text-primary-foreground rounded hover:bg-orange-700"
          >
            Fetch with Retry
          </button>
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-2">Example 5: Manual Handling</h2>
          <p className="text-sm text-gray-600 mb-3">
            Manual error handling without automatic Sentry reporting
          </p>
          <button
            onClick={handleManualExample}
            className="px-4 py-2 bg-gray-600 text-primary-foreground rounded hover:bg-gray-700"
          >
            Fetch Manually
          </button>
        </div>
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold mb-2">Notes:</h3>
        <ul className="list-disc list-inside text-sm space-y-1">
          <li>All examples will show toast notifications on error</li>
          <li>Errors are automatically reported to Sentry (except Example 5)</li>
          <li>User context is included in Sentry reports when available</li>
          <li>Authentication errors automatically redirect to login</li>
          <li>Network errors show user-friendly messages</li>
          <li>Validation errors display field-specific messages</li>
        </ul>
      </div>
    </div>
  );
}
