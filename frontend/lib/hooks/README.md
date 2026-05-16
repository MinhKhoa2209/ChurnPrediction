# Error Handling Hooks

This directory contains custom React hooks for handling API errors with automatic toast notifications and Sentry reporting.

## Requirements

- **Requirement 20.2**: Report errors to Sentry with user context
- **Requirement 20.4**: Display user-friendly error messages in toast notifications

## Available Hooks

### `useApiError`

A hook for handling API errors consistently across the application.

```typescript
import { useApiError } from '@/lib/hooks/useApiError';

function MyComponent() {
  const { handleError } = useApiError({
    userId: user?.id,
    userEmail: user?.email,
    userRole: user?.role,
  });

  const handleSubmit = async () => {
    try {
      await api.post('/endpoint', data, token);
    } catch (error) {
      handleError(error, {
        showToast: true,
        reportToSentry: true,
      });
    }
  };
}
```

### `useApi`

A hook for making API calls with automatic error handling and loading states.

```typescript
import { useApi } from '@/lib/hooks/useApi';

function MyComponent() {
  const { data, loading, error, execute } = useApi({
    userId: user?.id,
    userEmail: user?.email,
    userRole: user?.role,
  });

  const fetchData = async () => {
    await execute(
      () => api.get('/endpoint', token),
      {
        onSuccess: (data) => {
          console.log('Success:', data);
        },
        showToast: true,
        reportToSentry: true,
      }
    );
  };

  return (
    <div>
      {loading && <p>Loading...</p>}
      {error && <p>Error occurred</p>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
      <button onClick={fetchData}>Fetch Data</button>
    </div>
  );
}
```

## API Interceptor

For more advanced use cases, you can use the API interceptor directly:

```typescript
import { withErrorHandling, withRetry } from '@/lib/apiInterceptor';

// Simple error handling
const data = await withErrorHandling(
  () => api.get('/endpoint', token),
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

// With retry logic
const data = await withRetry(
  () => api.get('/endpoint', token),
  3, // max retries
  1000, // base delay in ms
  {
    showToast: true,
    reportToSentry: true,
  }
);
```

## Error Boundary

All components are wrapped in an ErrorBoundary that catches React errors:

```typescript
import { ErrorBoundary, withErrorBoundary } from '@/components/ErrorBoundary';

// Wrap a component
function MyComponent() {
  return (
    <ErrorBoundary>
      <ChildComponent />
    </ErrorBoundary>
  );
}

// Or use HOC
const SafeComponent = withErrorBoundary(MyComponent);
```

## Toast Notifications

Toast notifications are automatically shown for errors. You can also show success messages:

```typescript
import { showSuccessToast, showErrorToast, showInfoToast, showWarningToast } from '@/lib/errors';

// Success
showSuccessToast('Operation completed successfully');

// Error
showErrorToast(new Error('Something went wrong'));

// Info
showInfoToast('This is an informational message');

// Warning
showWarningToast('This is a warning message');
```

## Sentry Integration

Errors are automatically reported to Sentry with user context. The Sentry configuration is in:
- `sentry.client.config.ts` - Client-side errors
- `sentry.server.config.ts` - Server-side errors

To set user context manually:

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.setUser({
  id: user.id,
  email: user.email,
  role: user.role,
});
```

## Best Practices

1. **Always provide user context** when available for better error tracking
2. **Use `useApi` hook** for simple API calls with loading states
3. **Use `withErrorHandling`** for more control over error handling
4. **Use `withRetry`** for operations that should be retried on failure
5. **Don't retry** authentication, authorization, or validation errors
6. **Show toasts** for user-facing errors, but not for background operations
7. **Report to Sentry** for all unexpected errors, but not for expected validation errors
