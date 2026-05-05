/**
 * Sentry Server Configuration
 * Error tracking for server-side errors (API routes, server components)
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
  
  integrations: [
    Sentry.httpIntegration(),
  ],
  
  // Filter out certain errors
  ignoreErrors: [
    // Network errors that are expected
    'NetworkError',
    'Failed to fetch',
  ],
  
  // Before sending events to Sentry
  beforeSend(event, hint) {
    // Don't send events in development unless explicitly enabled
    if (ENVIRONMENT === 'development' && !process.env.NEXT_PUBLIC_SENTRY_ENABLED) {
      return null;
    }
    
    return event;
  },
});
