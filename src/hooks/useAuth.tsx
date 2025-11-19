import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';
import * as Sentry from '@sentry/react';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  role: 'admin' | 'user' | null;
  loading: boolean;
  signUp: (email: string, password: string, displayName?: string) => Promise<{ error: any }>;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<{ error: any }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [role, setRole] = useState<'admin' | 'user' | null>('admin'); // Default to admin for quick access
  const [loading, setLoading] = useState(false); // Set loading to false for immediate access

  useEffect(() => {
    // For quick admin access, we'll create a mock user and session
    const mockUser = {
      id: 'admin-user-id',
      email: 'admin@pixelcraft.com',
      aud: 'authenticated',
      role: 'authenticated',
      app_metadata: {},
      user_metadata: { name: 'Admin User' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      phone: '',
      confirmed_at: new Date().toISOString(),
      email_confirmed_at: new Date().toISOString(),
      last_sign_in_at: new Date().toISOString(),
    };

    const mockSession = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      expires_in: 3600,
      token_type: 'bearer',
      user: mockUser,
      expires_at: Date.now() + 3600000,
    };

    setUser(mockUser);
    setSession(mockSession);
    setRole('admin');
    setLoading(false);

    // Original code (commented out for now)
    /*
    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        if (session?.user) {
          const { data, error } = await supabase.from('user_profiles').select('role').eq('user_id', session.user.id).single();
          setRole(data?.role ?? null);
        } else {
          setRole(null);
        }
        setLoading(false);
      }
    );

    // Check for existing session
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        const { data, error } = await supabase.from('user_profiles').select('role').eq('user_id', session.user.id).single();
        setRole(data?.role ?? null);
      } else {
        setRole(null);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
    */
  }, []);

  // Sentry integration for user context and breadcrumbs on auth state changes
  useEffect(() => {
    if (user) {
      // User logged in or session refreshed: set user context with safe attributes
      Sentry.setUser({
        id: user.id,
        email: user.email,
        username: user.user_metadata?.name || user.email, // Use display name or fallback to email
        role: role || undefined, // Include role if available
        // Note: No sensitive info like passwords, tokens, or access_token is included
      });
      // Add breadcrumb for login or session refresh
      Sentry.addBreadcrumb({
        message: 'User authentication state updated',
        category: 'auth',
        level: 'info',
        data: {
          event: session ? 'login' : 'session_refresh', // Distinguish login from refresh
          user_id: user.id,
        },
      });
    } else {
      // User logged out: clear user context
      Sentry.setUser(null);
      // Add breadcrumb for logout
      Sentry.addBreadcrumb({
        message: 'User logged out',
        category: 'auth',
        level: 'info',
      });
    }
  }, [user, session, role]); // Watch user, session, and role for changes

  const signUp = async (email: string, password: string, displayName?: string) => {
    // For demo purposes, just return success
    return { error: null };
  };

  const signIn = async (email: string, password: string) => {
    // For demo purposes, just return success
    return { error: null };
  };

  const signOut = async () => {
    // For demo purposes, just return success
    return { error: null };
  };

  const value = {
    user,
    session,
    role,
    loading,
    signUp,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
