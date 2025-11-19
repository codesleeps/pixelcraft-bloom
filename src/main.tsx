import * as Sentry from '@sentry/react'
import React from 'react'
import { useLocation, useNavigationType, createRoutesFromChildren, matchRoutes } from 'react-router-dom'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'development',
    release: import.meta.env.VITE_SENTRY_RELEASE,
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    integrations: [
      new Sentry.BrowserTracing({
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          React.useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
      }),
      new Sentry.Replay(),
    ],
    beforeSend: (event, hint) => {
      // Filter sensitive data from request bodies, such as passwords, tokens, API keys
      if (event.request?.data) {
        const filteredData = { ...event.request.data }
        const sensitiveKeys = ['password', 'token', 'apiKey', 'authorization']
        sensitiveKeys.forEach(key => {
          if (filteredData[key]) {
            filteredData[key] = '[FILTERED]'
          }
        })
        event.request.data = filteredData
      }
      return event
    },
    ignoreErrors: [
      'Network Error',
      'ChunkLoadError',
      'Extension context invalidated',
      'Non-Error promise rejection captured',
      'Loading chunk',
      'Script error.',
    ],
  })
  if (import.meta.env.DEV) {
    console.log('Sentry initialized successfully.')
  }
}

createRoot(document.getElementById("root")!).render(<App />);
