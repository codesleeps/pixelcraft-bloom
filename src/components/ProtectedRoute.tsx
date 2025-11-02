import React, { useEffect } from 'react';
import { Navigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  allowedRoles?: ('admin' | 'user')[];
  redirectPath?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  allowedRoles,
  redirectPath = '/auth',
}) => {
  const { user, loading, role, session } = useAuth();
  const { toast } = useToast();
  const location = useLocation();

  // Log access attempts for security monitoring
  useEffect(() => {
    if (requireAuth && !loading) {
      if (!user) {
        console.info('Unauthorized access attempt:', location.pathname);
      } else if (allowedRoles && role && !allowedRoles.includes(role)) {
        console.warn('Insufficient permissions access attempt:', {
          path: location.pathname,
          userRole: role,
          requiredRoles: allowedRoles,
        });
      }
    }
  }, [user, role, loading, requireAuth, allowedRoles, location.pathname]);

  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Skeleton className="w-full max-w-md h-64" />
      </div>
    );
  }

  // Check authentication
  if (requireAuth && !user) {
    // Store the attempted URL for redirect after login
    sessionStorage.setItem('redirectAfterLogin', location.pathname);
    
    // Show toast notification
    toast({
      title: "Authentication Required",
      description: "Please sign in to access this page.",
      variant: "destructive",
    });
    
    return <Navigate to={redirectPath} replace state={{ from: location }} />;
  }

  // Check for session expiration
  if (requireAuth && user && !session) {
    toast({
      title: "Session Expired",
      description: "Your session has expired. Please sign in again.",
      variant: "destructive",
    });
    
    return <Navigate to={redirectPath} replace />;
  }

  // Check role-based permissions
  if (allowedRoles && role && !allowedRoles.includes(role)) {
    toast({
      title: "Access Denied",
      description: `You need ${allowedRoles.join(' or ')} permissions to access this page.`,
      variant: "destructive",
    });
    
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert className="max-w-md">
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription>
            You do not have permission to access this page. <Link to="/" className="underline">Go back home</Link>.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;