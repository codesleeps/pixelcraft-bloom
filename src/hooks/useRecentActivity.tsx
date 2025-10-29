import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { supabase } from '@/integrations/supabase/client';

// Define the ActivityItem interface with discriminated union
export interface ActivityItem {
  type: 'conversation' | 'appointment';
  id: string;
  created_at: string;
  status: string;
  channel?: string; // For conversations
  appointment_type?: string; // For appointments
  data: any; // Full data object
}

// Helper function for authenticated fetch
const fetchWithAuth = async (url: string, token: string) => {
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${apiBaseUrl}${url}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

export const useRecentActivity = (limit: number = 10) => {
  const { user, role, session } = useAuth();

  const queryFn = async (): Promise<ActivityItem[]> => {
    if (!user || !session?.access_token || role !== 'user') {
      return [];
    }

    const userId = user.id;

    // Fetch conversations and appointments in parallel
    const [conversationsResponse, appointmentsResponse] = await Promise.all([
      fetchWithAuth(`/api/analytics/conversations/list?limit=${limit}&sort_by=created_at&sort_order=desc`, session.access_token),
      supabase.from('appointments').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(limit),
    ]);

    // Process conversations
    const conversations: ActivityItem[] = conversationsResponse.items.map((conv: any) => ({
      type: 'conversation' as const,
      id: conv.id,
      created_at: conv.created_at,
      status: conv.status,
      channel: conv.channel,
      data: conv,
    }));

    // Process appointments
    const appointments: ActivityItem[] = appointmentsResponse.data.map((appt: any) => ({
      type: 'appointment' as const,
      id: appt.id,
      created_at: appt.created_at,
      status: appt.status,
      appointment_type: appt.appointment_type,
      data: appt,
    }));

    // Combine and sort by created_at descending
    const combined = [...conversations, ...appointments].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    return combined;
  };

  const { data, isLoading, error } = useQuery<ActivityItem[]>({
    queryKey: ['recentActivity', user?.id, limit],
    queryFn,
    enabled: !!user && role === 'user' && !!session,
  });

  return { data: data || [], isLoading, error };
};