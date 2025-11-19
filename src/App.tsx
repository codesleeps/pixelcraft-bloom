import React, { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route, useLocation } from "react-router-dom";
import * as Sentry from "@sentry/react";
import { AuthProvider } from "@/hooks/useAuth";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import StrategySession from "./pages/StrategySession";
import Partnership from "./pages/Partnership";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "@/components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import ErrorBoundary from '@/components/ErrorBoundary';
import PaymentsSuccess from './pages/PaymentsSuccess';
import PaymentsCancel from './pages/PaymentsCancel';

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
      <Route path="/" element={<Index />} />
      <Route path="/auth" element={<Auth />} />
      <Route path="/strategy-session" element={<StrategySession />} />
      <Route path="/partnership" element={<Partnership />} />
      <Route path="/dashboard" element={<ProtectedRoute allowedRoles={['admin', 'user']}><Dashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><Dashboard /></ProtectedRoute>} />
      <Route path="/payments/success" element={<PaymentsSuccess />} />
      <Route path="/payments/cancel" element={<PaymentsCancel />} />
      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
      <Route path="*" element={<NotFound />} />
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
