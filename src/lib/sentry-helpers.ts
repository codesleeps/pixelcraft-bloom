import * as Sentry from '@sentry/react';

// Define the User interface for type safety
interface User {
  id: string;
  email: string;
  username?: string;
  role?: string;
  // Add other non-sensitive fields as needed
}

/**
 * Safely sets the user context in Sentry, filtering out any sensitive fields.
 * If Sentry is not initialized, this function does nothing.
 * @param user - The user object or null to clear context
 */
export function setUserContext(user: User | null): void {
  try {
    if (user) {
      Sentry.setUser({
        id: user.id,
        email: user.email,
        username: user.username,
        // Add other non-sensitive fields, e.g., role: user.role
      });
    } else {
      Sentry.setUser(null);
    }
  } catch (error) {
    // Sentry not initialized or other error, silently ignore
  }
}

/**
 * Captures an API error with relevant context.
 * If Sentry is not initialized, this function does nothing.
 * @param error - The error object
 * @param endpoint - The API endpoint
 * @param method - The HTTP method
 * @param statusCode - Optional HTTP status code
 */
export function captureApiError(error: Error, endpoint: string, method: string, statusCode?: number): void {
  try {
    Sentry.captureException(error, {
      contexts: {
        api: {
          endpoint,
          method,
          statusCode,
        },
      },
    });
  } catch (err) {
    // Sentry not initialized or other error, silently ignore
  }
}

/**
 * Adds a breadcrumb for route navigation.
 * If Sentry is not initialized, this function does nothing.
 * @param from - The source route
 * @param to - The destination route
 */
export function addNavigationBreadcrumb(from: string, to: string): void {
  try {
    Sentry.addBreadcrumb({
      message: `Navigation from ${from} to ${to}`,
      category: 'navigation',
      level: 'info',
    });
  } catch (error) {
    // Sentry not initialized or other error, silently ignore
  }
}

/**
 * Measures the performance of a callback function using Sentry spans.
 * If Sentry is not initialized, the callback is executed without measurement.
 * @param name - The name of the performance measurement
 * @param callback - The function to measure
 */
export function measurePerformance(name: string, callback: () => void): void {
  try {
    Sentry.startSpan({ name, op: 'function' }, () => {
      callback();
    });
  } catch (error) {
    // Sentry not initialized or other error, execute callback without measurement
    callback();
  }
}

/**
 * Captures a form submission error with sanitized form data.
 * Sensitive fields like 'password', 'token', 'apiKey' are removed from formData.
 * If Sentry is not initialized, this function does nothing.
 * @param formName - The name of the form
 * @param error - The error object
 * @param formData - Optional form data to include (will be sanitized)
 */
export function captureFormError(formName: string, error: Error, formData?: Record<string, any>): void {
  try {
    const sensitiveKeys = ['password', 'token', 'apikey', 'secret', 'key'];
    const sanitizedFormData = formData
      ? Object.keys(formData).reduce((acc, key) => {
          if (!sensitiveKeys.includes(key.toLowerCase())) {
            acc[key] = formData[key];
          }
          return acc;
        }, {} as Record<string, any>)
      : undefined;

    Sentry.captureException(error, {
      contexts: {
        form: {
          formName,
          formData: sanitizedFormData,
        },
      },
    });
  } catch (err) {
    // Sentry not initialized or other error, silently ignore
  }
}

/**
 * Starts a manual Sentry transaction.
 * If Sentry is not initialized, this function returns null.
 * @param name - The name of the transaction
 * @param op - The operation type
 * @returns The transaction object or null if Sentry is not initialized
 */
export function startTransaction(name: string, op: string): Sentry.Transaction | null {
  try {
    return Sentry.startTransaction({ name, op });
  } catch (error) {
    // Sentry not initialized or other error, return null
    return null;
  }
}