import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from './useAuth';

// Define types for the analytics data
export interface AnalyticsData {
  totalLeads: { value: number; change: number };
  activeConversations: { value: number; change: number };
  conversionRate: { value: number; change: number };
  revenue: { value: number; change: number };
  // Add other metrics as needed
}

// Function to fetch analytics data
const fetchAnalyticsData = async (userId: string | undefined, role: string | null) => {
  if (!userId) {
    return null;
  }

  const { data, error } = await supabase.functions.invoke('get-analytics', {
    body: { userId, role },
  });

  if (error) {
    throw new Error(error.message);
  }

  return data as AnalyticsData;
};

export const useAnalytics = () => {
  const { user, role } = useAuth();
  const {
    data,
    error,
    isLoading: loading,
  } = useQuery<AnalyticsData | null>({
    queryKey: ['analytics', user?.id, role],
    queryFn: () => fetchAnalyticsData(user?.id, role),
    enabled: !!user, // Only run the query if the user is authenticated
  });

  return { data, error, loading };
};
