import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HashRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import StrategySession from "./pages/StrategySession";
import Partnership from "./pages/Partnership";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "@/components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import ErrorBoundary from '@/components/ErrorBoundary';

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

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <ErrorBoundary onError={(error, errorInfo) => { console.error('App Error:', error, errorInfo); /* Send to error tracking service */ }}>
          <HashRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/auth" element={<Auth />} />
              <Route path="/strategy-session" element={<StrategySession />} />
              <Route path="/partnership" element={<Partnership />} />
              <Route path="/dashboard" element={<ProtectedRoute allowedRoles={['admin', 'user']}><Dashboard /></ProtectedRoute>} />
              <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><Dashboard /></ProtectedRoute>} />
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </HashRouter>
        </ErrorBoundary>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
