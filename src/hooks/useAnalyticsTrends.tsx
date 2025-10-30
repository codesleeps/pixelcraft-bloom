import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';

// These hooks fetch trend data and automatically update when real-time events are received via WebSocket
// Cache invalidation is handled by the useWebSocket hook, which triggers automatic refetches

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

interface SubscriptionTrendPoint {
  period: Date;
  new_subscriptions: number;
  cancelled_subscriptions: number;
  net_change: number;
  cumulative_active: number;
}

interface RevenueByPackage {
  package_id: string;
  package_name: string;
  subscription_count: number;
  total_revenue: number;
  avg_revenue_per_subscription: number;
}

interface CustomerLTV {
  user_id: string;
  total_spent: number;
  subscription_count: number;
  avg_subscription_value: number;
  lifetime_months: number;
  estimated_ltv: number;
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
    refetchInterval: 120000,
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
    refetchInterval: 120000,
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

export const useSubscriptionTrends = (timeRange: { start_date: string; end_date: string }, aggregation: 'daily' | 'weekly') => {
  const { session } = useAuth();
  const { data, isLoading, error } = useQuery<SubscriptionTrendPoint[]>({
    queryKey: ['subscriptionTrends', timeRange, aggregation],
    queryFn: async () => {
      const url = `${apiBaseUrl}/api/analytics/revenue/subscription-trends?start_date=${timeRange.start_date}&end_date=${timeRange.end_date}&aggregation=${aggregation}`;
      const response = await fetchWithAuth(url, session!.access_token);
      return response.data.map((point: any) => ({
        ...point,
        period: new Date(point.period),
      }));
    },
    enabled: !!session,
    refetchInterval: 120000,
  });
  return { data, isLoading, error };
};

export const useRevenueByPackage = (timeRange: { start_date: string; end_date: string }) => {
  const { session } = useAuth();
  const { data, isLoading, error } = useQuery<RevenueByPackage[]>({
    queryKey: ['revenueByPackage', timeRange],
    queryFn: async () => {
      const url = `${apiBaseUrl}/api/analytics/revenue/by-package?start_date=${timeRange.start_date}&end_date=${timeRange.end_date}`;
      const response = await fetchWithAuth(url, session!.access_token);
      return response.map((item: any) => ({
        ...item,
        total_revenue: parseFloat(item.total_revenue),
        avg_revenue_per_subscription: parseFloat(item.avg_revenue_per_subscription),
      }));
    },
    enabled: !!session,
  });
  return { data, isLoading, error };
};

export const useCustomerLTV = (pagination?: { limit: number; offset: number }) => {
  const { session } = useAuth();
  const params = { limit: 50, offset: 0, ...pagination };
  const { data, isLoading, error } = useQuery<CustomerLTV[]>({
    queryKey: ['customerLTV', params],
    queryFn: async () => {
      const url = `${apiBaseUrl}/api/analytics/revenue/customer-ltv?limit=${params.limit}&offset=${params.offset}`;
      const response = await fetchWithAuth(url, session!.access_token);
      return response.map((item: any) => ({
        ...item,
        total_spent: parseFloat(item.total_spent),
        avg_subscription_value: parseFloat(item.avg_subscription_value),
        estimated_ltv: parseFloat(item.estimated_ltv),
      }));
    },
    enabled: !!session,
  });
  return { data, isLoading, error };
};
