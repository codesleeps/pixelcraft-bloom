import { vi } from 'vitest';

// Create a mock query builder that supports chaining
const createMockQueryBuilder = () => ({
  insert: vi.fn(() => Promise.resolve({ error: null })),
  select: vi.fn(() => createMockQueryBuilder()),
  eq: vi.fn(() => createMockQueryBuilder()),
  order: vi.fn(() => Promise.resolve({ data: [], error: null })),
  single: vi.fn(() => Promise.resolve({ data: null, error: null })),
});

// Mock Supabase client
export const mockSupabase = {
  from: vi.fn(() => createMockQueryBuilder()),
};