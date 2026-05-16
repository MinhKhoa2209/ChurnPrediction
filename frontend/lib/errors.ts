'use client';

import { toast } from 'sonner';

// Lazy Sentry loader to avoid SSR subscribe crashes
let _sentry: typeof import('@sentry/nextjs') | null = null;
async function getSentry() {
  if (!_sentry) {
    try {
      _sentry = await import('@sentry/nextjs');
    } catch {
      // Sentry unavailable
    }
  }
  return _sentry;
}

export enum ErrorCode {
  // Client errors (4xx)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',
  UNPROCESSABLE_ENTITY = 'UNPROCESSABLE_ENTITY',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',

  // Server errors (5xx)
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  DATABASE_ERROR = 'DATABASE_ERROR',
  STORAGE_ERROR = 'STORAGE_ERROR',
  ML_SERVICE_ERROR = 'ML_SERVICE_ERROR',
}


export interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}


export interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
    details?: ErrorDetail[];
    requestId?: string;
    timestamp: string;
  };
}


export class ApiError extends Error {
  code: ErrorCode;
  details?: ErrorDetail[];
  requestId?: string;
  timestamp: string;
  statusCode?: number;

  constructor(errorResponse: ErrorResponse['error'], statusCode?: number) {
    super(errorResponse.message);
    this.name = 'ApiError';
    this.code = errorResponse.code;
    this.details = errorResponse.details;
    this.requestId = errorResponse.requestId;
    this.timestamp = errorResponse.timestamp;
    this.statusCode = statusCode;
  }
}


const ERROR_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.VALIDATION_ERROR]: 'Please check your input and try again.',
  [ErrorCode.AUTHENTICATION_ERROR]: 'Authentication failed. Please log in again.',
  [ErrorCode.AUTHORIZATION_ERROR]: 'You do not have permission to perform this action.',
  [ErrorCode.NOT_FOUND]: 'The requested resource was not found.',
  [ErrorCode.CONFLICT]: 'This action conflicts with existing data.',
  [ErrorCode.UNPROCESSABLE_ENTITY]: 'Unable to process your request.',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'Too many requests. Please try again later.',
  [ErrorCode.INTERNAL_ERROR]: 'An unexpected error occurred. Please try again.',
  [ErrorCode.SERVICE_UNAVAILABLE]: 'Service is temporarily unavailable. Please try again later.',
  [ErrorCode.DATABASE_ERROR]: 'Database error occurred. Please try again later.',
  [ErrorCode.STORAGE_ERROR]: 'Storage error occurred. Please try again later.',
  [ErrorCode.ML_SERVICE_ERROR]: 'ML service error occurred. Please try again later.',
};


function getUserFriendlyMessage(error: ApiError): string {
  // Use specific message from backend if available
  if (error.message && error.message !== error.code) {
    return error.message;
  }

  // Fall back to generic message for error code
  return ERROR_MESSAGES[error.code] || 'An error occurred. Please try again.';
}


function formatValidationErrors(details?: ErrorDetail[]): string {
  if (!details || details.length === 0) {
    return '';
  }

  return details
    .map((detail) => {
      if (detail.field) {
        return `${detail.field}: ${detail.message}`;
      }
      return detail.message;
    })
    .join('\n');
}


export function showErrorToast(error: ApiError | Error): void {
  if (error instanceof ApiError) {
    const message = getUserFriendlyMessage(error);
    const validationErrors = formatValidationErrors(error.details);

    if (validationErrors) {
      const fullMessage = `${message}\n\n${validationErrors}${
        error.requestId ? `\n\nRequest ID: ${error.requestId}` : ''
      }`;
      toast.error(fullMessage, {
        duration: 6000,
        id: error.requestId || undefined,
      });
    } else {
      toast.error(message, {
        duration: 4000,
        id: error.requestId || undefined,
      });
    }
  } else {
    toast.error(error.message || 'An unexpected error occurred', {
      duration: 4000,
    });
  }
}


export function showSuccessToast(message: string): void {
  toast.success(message, { duration: 3000 });
}


export function showInfoToast(message: string): void {
  toast.info(message, { duration: 3000 });
}


export function showWarningToast(message: string): void {
  toast.warning(message, { duration: 4000 });
}


export async function reportErrorToSentry(
  error: Error | ApiError,
  context?: {
    userId?: string;
    userEmail?: string;
    userRole?: string;
    extra?: Record<string, any>;
  }
): Promise<void> {
  const Sentry = await getSentry();
  if (!Sentry) return;

  // Set user context if provided
  if (context?.userId || context?.userEmail) {
    Sentry.setUser({
      id: context.userId,
      email: context.userEmail,
      role: context.userRole,
    });
  }

  // Add extra context
  if (context?.extra) {
    Sentry.setContext('additional', context.extra);
  }

  // Add API error specific context
  if (error instanceof ApiError) {
    Sentry.setContext('apiError', {
      code: error.code,
      requestId: error.requestId,
      timestamp: error.timestamp,
      statusCode: error.statusCode,
      details: error.details,
    });
  }

  // Capture the error
  Sentry.captureException(error);
}

export function handleApiError(
  error: Error | ApiError,
  options?: {
    showToast?: boolean;
    reportToSentry?: boolean;
    userContext?: {
      userId?: string;
      userEmail?: string;
      userRole?: string;
    };
    extra?: Record<string, any>;
  }
): void {
  const {
    showToast = true,
    reportToSentry = true,
    userContext,
    extra,
  } = options || {};

  // Show toast notification
  if (showToast) {
    showErrorToast(error);
  }

  // Report to Sentry
  if (reportToSentry) {
    reportErrorToSentry(error, {
      ...userContext,
      extra,
    });
  }
}


export function parseApiError(response: any, statusCode?: number): ApiError {
  // Check if response has error structure
  if (response?.error) {
    return new ApiError(response.error, statusCode);
  }

  // Fallback for non-standard error responses
  return new ApiError(
    {
      code: ErrorCode.INTERNAL_ERROR,
      message: response?.message || response?.detail || 'An unexpected error occurred',
      timestamp: new Date().toISOString(),
    },
    statusCode
  );
}


export function isNetworkError(error: Error): boolean {
  return (
    error.message.includes('fetch') ||
    error.message.includes('network') ||
    error.message.includes('NetworkError') ||
    error.message.includes('Failed to fetch')
  );
}


export function isAuthenticationError(error: Error | ApiError): boolean {
  if (error instanceof ApiError) {
    return error.code === ErrorCode.AUTHENTICATION_ERROR;
  }
  return false;
}


export function isAuthorizationError(error: Error | ApiError): boolean {
  if (error instanceof ApiError) {
    return error.code === ErrorCode.AUTHORIZATION_ERROR;
  }
  return false;
}
