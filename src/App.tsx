import React, { useEffect, Suspense, lazy } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, useLocation } from "react-router-dom";
import * as Sentry from "@sentry/react";
import { AuthProvider } from "@/hooks/useAuth";
import ProtectedRoute from "@/components/ProtectedRoute";
import ErrorBoundary from '@/components/ErrorBoundary';

// Lazy load pages
const Index = lazy(() => import("./pages/Index"));
const Auth = lazy(() => import("./pages/Auth"));
const StrategySession = lazy(() => import("./pages/StrategySession"));
const Partnership = lazy(() => import("./pages/Partnership"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const PaymentsSuccess = lazy(() => import("./pages/PaymentsSuccess"));
const PaymentsCancel = lazy(() => import("./pages/PaymentsCancel"));

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
  </div>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 60000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
});

const SentryHashRouter = Sentry.withSentryRouting(HashRouter);
const SentryRoutes = Sentry.withSentryRouting(Routes);

const getSection = (pathname: string): string => {
  switch (pathname) {
    case '/':
      return 'home';
    case '/auth':
      return 'auth';
    case '/strategy-session':
      return 'strategy';
    case '/partnership':
      return 'partnership';
    case '/dashboard':
    case '/admin':
      return 'dashboard';
    default:
      if (pathname.startsWith('/payments')) {
        return 'payments';
      }
      return 'unknown';
  }
};

const AppContent = () => {
  const location = useLocation();

  useEffect(() => {
    const section = getSection(location.pathname);
    Sentry.setTag('app.section', section);
  }, [location.pathname]);

  return (
    <SentryRoutes>
      <Route path="/" element={<Suspense fallback={<LoadingFallback />}><Index /></Suspense>} />
      <Route path="/auth" element={<Suspense fallback={<LoadingFallback />}><Auth /></Suspense>} />
      <Route path="/strategy-session" element={<Suspense fallback={<LoadingFallback />}><StrategySession /></Suspense>} />
      <Route path="/partnership" element={<Suspense fallback={<LoadingFallback />}><Partnership /></Suspense>} />
      <Route path="/dashboard" element={<Suspense fallback={<LoadingFallback />}><ProtectedRoute allowedRoles={['admin', 'user']}><Dashboard /></ProtectedRoute></Suspense>} />
      <Route path="/admin" element={<Suspense fallback={<LoadingFallback />}><ProtectedRoute allowedRoles={['admin']}><Dashboard /></ProtectedRoute></Suspense>} />
      <Route path="/payments/success" element={<Suspense fallback={<LoadingFallback />}><PaymentsSuccess /></Suspense>} />
      <Route path="/payments/cancel" element={<Suspense fallback={<LoadingFallback />}><PaymentsCancel /></Suspense>} />
      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
      <Route path="*" element={<Suspense fallback={<LoadingFallback />}><NotFound /></Suspense>} />
    </SentryRoutes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <ErrorBoundary onError={(error, errorInfo) => { console.error('App Error:', error, errorInfo); /* Send to error tracking service */ }}>
          <SentryHashRouter>
            <AppContent />
          </SentryHashRouter>
        </ErrorBoundary>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
