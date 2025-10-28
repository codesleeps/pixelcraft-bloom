import { vi } from 'vitest';
import type { User, Session } from '@supabase/supabase-js';

const mockUser: User = {
  id: 'mock-user-id',
  email: 'mock@example.com',
  aud: 'authenticated',
  role: 'authenticated',
  app_metadata: {},
  user_metadata: {},
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  phone: '',
  confirmed_at: new Date().toISOString(),
  email_confirmed_at: new Date().toISOString(),
  last_sign_in_at: new Date().toISOString(),
};

const mockSession: Session = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  expires_in: 3600,
  token_type: 'bearer',
  user: mockUser,
  expires_at: Date.now() + 3600000,
};

export const mockUseAuth = () => ({
  user: null,
  session: null,
  loading: false,
  signUp: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
});

export const mockAuthenticatedUser = () => ({
  user: mockUser,
  session: mockSession,
  loading: false,
  signUp: vi.fn(),
  signIn: vi.fn(),
  signOut: vi.fn(),
});

export const mockUnauthenticatedUser = () => mockUseAuth();