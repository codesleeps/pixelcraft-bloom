import React from 'react';
import * as Sentry from '@sentry/react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

/**
 * Props for the ErrorBoundary component.
 */
interface ErrorBoundaryProps {
  /** The child components to render. */
  children: React.ReactNode;
  /** Optional custom fallback component to render on error. */
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  /** Optional callback for error reporting (e.g., to Sentry or LogRocket). */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** Optional user data for Sentry context. */
  user?: { id: string; email?: string; username?: string };
}

/**
 * State for the ErrorBoundary component.
 */
interface ErrorBoundaryState {
  /** Whether an error has occurred. */
  hasError: boolean;
  /** The error that occurred, if any. */
  error: Error | null;
}

/**
 * ErrorBoundary component that catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of the component tree that crashed.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 *
 * With custom fallback:
 * ```tsx
 * <ErrorBoundary fallback={MyFallbackComponent}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 *
 * With error reporting:
 * ```tsx
 * <ErrorBoundary onError={(error, errorInfo) => console.error(error, errorInfo)}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  /**
   * Static method to update state when an error is caught.
   * @param error The error that was thrown.
   * @returns Partial state update.
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  /**
   * Lifecycle method called after an error has been thrown by a descendant component.
   * Captures the error with Sentry and calls the optional onError callback.
   * @param error The error that was thrown.
   * @param errorInfo Information about the component stack.
   */
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Set custom context
    Sentry.setContext('error_boundary', {
      componentName: 'ErrorBoundary',
      location: window.location.href,
      props: this.props,
    });

    // Set user context if available
    if (this.props.user) {
      Sentry.setUser(this.props.user);
    }

    // Add breadcrumb
    Sentry.addBreadcrumb({
      message: 'Error boundary caught an error',
      level: 'error',
      category: 'error',
    });

    // Capture exception with React context
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
    });

    // Call onError for backward compatibility
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Method to reset the error state, allowing the component to retry rendering.
   */
  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      } else {
        return (
          <div className="flex items-center justify-center min-h-screen bg-background p-4">
            <Card className="w-full max-w-md">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-6 w-6 text-destructive" />
                  <CardTitle>Something went wrong</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  {this.state.error!.message}
                </p>
                <div className="flex flex-col space-y-2">
                  <Button
                    onClick={() => {
                      this.resetError();
                      window.location.reload();
                    }}
                  >
                    Try Again
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => (window.location.hash = '#/dashboard')}
                  >
                    Go to Dashboard
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      window.open(
                        `mailto:support@pixelcraft.com?subject=Error Report&body=${encodeURIComponent(
                          this.state.error!.message
                        )}`
                      )
                    }
                  >
                    Report Issue
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => Sentry.showReportDialog()}
                  >
                    Send Feedback
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      }
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
export { ErrorBoundary };
