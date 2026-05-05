"use client";

/**
 * Degraded Mode Banner Component
 * 
 * Displays a warning banner when the backend is operating in degraded mode
 * or when the frontend cannot reach the backend.
 * 

import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, X } from "lucide-react";

interface DegradedModeBannerProps {
  /**
   * Whether the backend is in degraded mode (cache unavailable)
   */
  degradedMode?: boolean;
  
  /**
   * Whether the backend is completely unreachable
   */
  backendUnreachable?: boolean;
  
  /**
   * Callback when user dismisses the banner
   */
  onDismiss?: () => void;
  
  /**
   * Callback when user clicks retry/refresh
   */
  onRetry?: () => void;
}

export function DegradedModeBanner({
  degradedMode = false,
  backendUnreachable = false,
  onDismiss,
  onRetry,
}: DegradedModeBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Reset dismissed state when mode changes
  useEffect(() => {
    setDismissed(false);
  }, [degradedMode, backendUnreachable]);

  // Don't show banner if dismissed or no issues
  if (dismissed || (!degradedMode && !backendUnreachable)) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await onRetry?.();
    } finally {
      // Keep spinner for at least 500ms for better UX
      setTimeout(() => setIsRetrying(false), 500);
    }
  };

  // Determine banner content based on issue type
  const isUnreachable = backendUnreachable;
  const bgColor = isUnreachable ? "bg-red-50 dark:bg-red-950" : "bg-yellow-50 dark:bg-yellow-950";
  const borderColor = isUnreachable ? "border-red-200 dark:border-red-800" : "border-yellow-200 dark:border-yellow-800";
  const textColor = isUnreachable ? "text-red-900 dark:text-red-100" : "text-yellow-900 dark:text-yellow-100";
  const iconColor = isUnreachable ? "text-red-600 dark:text-red-400" : "text-yellow-600 dark:text-yellow-400";

  const title = isUnreachable
    ? "Backend Unreachable"
    : "System Operating in Degraded Mode";

  const message = isUnreachable
    ? "Cannot connect to the backend server. You are viewing cached data. Some features may be unavailable."
    : "The caching service is currently unavailable. The system is operating with reduced performance but all features remain functional.";

  return (
    <div
      className={`${bgColor} ${borderColor} border-b px-4 py-3 shadow-sm`}
      role="alert"
      aria-live="polite"
    >
      <div className="mx-auto max-w-7xl">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <AlertTriangle
            className={`${iconColor} mt-0.5 h-5 w-5 flex-shrink-0`}
            aria-hidden="true"
          />

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className={`${textColor} text-sm font-semibold`}>
              {title}
            </h3>
            <p className={`${textColor} mt-1 text-sm opacity-90`}>
              {message}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Retry button */}
            {onRetry && (
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className={`${textColor} inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed`}
                aria-label="Retry connection"
              >
                <RefreshCw
                  className={`h-4 w-4 ${isRetrying ? "animate-spin" : ""}`}
                  aria-hidden="true"
                />
                <span>{isRetrying ? "Retrying..." : "Retry"}</span>
              </button>
            )}

            {/* Dismiss button */}
            {onDismiss && (
              <button
                onClick={handleDismiss}
                className={`${textColor} rounded-md p-1.5 transition-colors hover:bg-black/5 dark:hover:bg-white/10`}
                aria-label="Dismiss banner"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to detect degraded mode from API responses
 * 
 * Monitors API response headers for X-Degraded-Mode header
export function useDegradedMode() {
  const [degradedMode, setDegradedMode] = useState(false);
  const [backendUnreachable, setBackendUnreachable] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  /**
   * Check response headers for degraded mode indicator
   */
  const checkResponse = (response: Response) => {
    const isDegraded = response.headers.get("X-Degraded-Mode") === "true";
    setDegradedMode(isDegraded);
    setBackendUnreachable(false);
    setLastChecked(new Date());
  };

  /**
   * Mark backend as unreachable (network error)
   */
  const markUnreachable = () => {
    setBackendUnreachable(true);
    setDegradedMode(false);
    setLastChecked(new Date());
  };

  /**
   * Clear all error states
   */
  const clearErrors = () => {
    setDegradedMode(false);
    setBackendUnreachable(false);
    setLastChecked(new Date());
  };

  return {
    degradedMode,
    backendUnreachable,
    lastChecked,
    checkResponse,
    markUnreachable,
    clearErrors,
  };
}
