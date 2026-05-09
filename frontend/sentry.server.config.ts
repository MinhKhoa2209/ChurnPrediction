import * as Sentry from '@sentry/nextjs';
const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || 'development';
Sentry.init({
  dsn: SENTRY_DSN,
  environment: ENVIRONMENT,
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,
  debug: false,
  integrations: [
    Sentry.httpIntegration(),
  ],
  ignoreErrors: [
    'NetworkError',
    'Failed to fetch',
  ],
  beforeSend(event, hint) {
    if (ENVIRONMENT === 'development' && !process.env.NEXT_PUBLIC_SENTRY_ENABLED) {
      return null;
    }
    return event;
  },
});
