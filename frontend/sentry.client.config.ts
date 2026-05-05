/**
 * Sentry Client Configuration
 * Error tracking for client-side errors
 * Requirement 20.2: Report errors to Sentry with user context
 */

import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || 'development';

Sentry.init({
  dsn: SENTRY_DSN,
  
  // Environment
  environment: ENVIRONMENT,
  
  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,
  
  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,
  
  // Replay configuration
  replaysOnErrorSampleRate: ENVIRONMENT === 'production' ? 1.0 : 0.0,
  replaysSessionSampleRate: ENVIRONMENT === 'production' ? 0.1 : 0.0,
  
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
    Sentry.browserTracingIntegration(),
  ],
  
  // Filter out certain errors
  ignoreErrors: [
    // Browser extensions
    'top.GLOBALS',
    'chrome-extension://',
    'moz-extension://',
    // Network errors that are expected
    'NetworkError',
    'Failed to fetch',
    // React hydration errors (usually not critical)
    'Hydration failed',
    'There was an error while hydrating',
  ],
  
  // Before sending events to Sentry
  beforeSend(event, hint) {
    // Don't send events in development unless explicitly enabled
    if (ENVIRONMENT === 'development' && !process.env.NEXT_PUBLIC_SENTRY_ENABLED) {
      return null;
    }
    
    // Filter out certain URLs
    if (event.request?.url) {
      const url = event.request.url;
      if (url.includes('localhost') && ENVIRONMENT === 'production') {
        return null;
      }
    }
    
    return event;
  },
});
