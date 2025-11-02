import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

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