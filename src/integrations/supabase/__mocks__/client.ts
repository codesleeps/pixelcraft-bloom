import { mockSupabase } from '@/test/mocks/supabase';

// Re-export the mock supabase client in the same shape as the real module
export const supabase = mockSupabase;
export default { supabase };
