import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';

interface TimeSeriesDataPoint {
  date: Date;
  value: number;
  label?: string;
}

interface ServiceRecommendation {
  service_name: string;
  total_recommendations: number;
  accepted_count: number;
  acceptance_rate: number;
  avg_confidence: number;
}

interface AgentPerformance {
  agent_type: string;
  total_actions: number;
  success_rate: number;
  avg_execution_time: number;
  error_rate: number;
}

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const fetchWithAuth = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP error! status: ${res.status}`);
  }
  return res.json();
};

export const useLeadTrends = (timeRange: { start_date: string; end_date: string }, aggregation: 'daily' | 'weekly') => {
  const { session } = useAuth();
  const { data, isLoading, error } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['leadTrends', timeRange, aggregation],
    queryFn: async () => {
      const url = `${apiBaseUrl}/api/analytics/leads/trends?start_date=${timeRange.start_date}&end_date=${timeRange.end_date}&aggregation=${aggregation}`;
      const response = await fetchWithAuth(url, session!.access_token);
      return response.data.map((point: any) => ({
        ...point,
        date: new Date(point.date),
      }));
    },
    enabled: !!session,
  });
  return { data, isLoading, error };
};

export const useConversationTrends = (timeRange: { start_date: string; end_date: string }, aggregation: 'daily' | 'weekly', filters?: { status?: string; channel?: string }) => {
  const { session } = useAuth();
  const queryParams = new URLSearchParams({
    start_date: timeRange.start_date,
    end_date: timeRange.end_date,
    aggregation,
    ...(filters?.status && { status: filters.status }),
    ...(filters?.channel && { channel: filters.channel }),
  });
  const url = `${apiBaseUrl}/api/analytics/conversations/trends?${queryParams}`;
  const { data, isLoading, error } = useQuery<TimeSeriesDataPoint[]>({
    queryKey: ['conversationTrends', timeRange, aggregation, filters],
    queryFn: async () => {
      const response = await fetchWithAuth(url, session!.access_token);
      return response.data.map((point: any) => ({
        ...point,
        date: new Date(point.date),
      }));
    },
    enabled: !!session,
  });
  return { data, isLoading, error };
};

export const useServiceRecommendations = () => {
  const { session } = useAuth();
  const { data, isLoading, error } = useQuery<ServiceRecommendation[]>({
    queryKey: ['serviceRecommendations'],
    queryFn: () => fetchWithAuth(`${apiBaseUrl}/api/analytics/services/recommendations`, session!.access_token),
    enabled: !!session,
  });
  return { data, isLoading, error };
};

export const useAgentPerformance = (timeRange: { start_date: string; end_date: string }) => {
  const { session, role } = useAuth();
  const { data, isLoading, error } = useQuery<AgentPerformance[]>({
    queryKey: ['agentPerformance', timeRange],
    queryFn: () => fetchWithAuth(`${apiBaseUrl}/api/analytics/agents/summary?start_date=${timeRange.start_date}&end_date=${timeRange.end_date}`, session!.access_token),
    enabled: !!session && role === 'admin',
  });
  return { data, isLoading, error };
};