import * as Sentry from '@sentry/nextjs';
const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || 'development';
Sentry.init({
  dsn: SENTRY_DSN,
  environment: ENVIRONMENT,
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,
  debug: false,
  replaysOnErrorSampleRate: ENVIRONMENT === 'production' ? 1.0 : 0.0,
  replaysSessionSampleRate: ENVIRONMENT === 'production' ? 0.1 : 0.0,
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
    Sentry.browserTracingIntegration(),
  ],
  ignoreErrors: [
    'top.GLOBALS',
    'chrome-extension://',
    'moz-extension://',
    'NetworkError',
    'Failed to fetch',
    'Hydration failed',
    'There was an error while hydrating',
  ],
  beforeSend(event, hint) {
    if (ENVIRONMENT === 'development' && !process.env.NEXT_PUBLIC_SENTRY_ENABLED) {
      return null;
    }
    if (event.request?.url) {
      const url = event.request.url;
      if (url.includes('localhost') && ENVIRONMENT === 'production') {
        return null;
      }
    }
    return event;
  },
});
