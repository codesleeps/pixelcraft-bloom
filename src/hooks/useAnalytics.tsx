import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';

// This hook fetches analytics data and automatically updates when real-time events are received via WebSocket (see useWebSocket hook)
// The WebSocket connection invalidates the React Query cache, triggering automatic refetches

// Define types for the analytics data
export interface AnalyticsData {
  total_leads: { value: number; change: number };
  qualified_leads: { value: number; change: number };
  conversion_rate: { value: number; change: number };
  avg_lead_score: { value: number; change: number };
  total_conversations: { value: number; change: number };
  active_conversations: { value: number; change: number };
  completed_conversations: { value: number; change: number };
  avg_messages_per_conversation: { value: number; change: number };
  mrr: { value: number; change: number };
  arr: { value: number; change: number };
  total_revenue: { value: number; change: number };
  active_subscriptions: { value: number; change: number };
  cancelled_subscriptions: { value: number; change: number };
  churn_rate: { value: number; change: number };
}

// Helper function to calculate percentage change
const calculatePercentageChange = (current: number, previous: number): number => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

// Helper function to get time ranges
const getTimeRanges = (periodDays: number = 30) => {
  const now = new Date();
  const currentEnd = now.toISOString();
  const currentStart = new Date(now.getTime() - periodDays * 24 * 60 * 60 * 1000).toISOString();
  const previousEnd = currentStart;
  const previousStart = new Date(now.getTime() - 2 * periodDays * 24 * 60 * 60 * 1000).toISOString();
  return {
    current: { start_date: currentStart, end_date: currentEnd },
    previous: { start_date: previousStart, end_date: previousEnd },
  };
};

// Helper function for safe numeric parsing
const safeParseFloat = (value: any, defaultValue: number = 0): number => {
  return value != null ? parseFloat(value) : defaultValue;
};

// Helper function to get recovery suggestions based on error type
const getRecoverySuggestion = (errorType: string): string => {
  switch (errorType) {
    case 'Authentication error':
      return 'Please sign in again.';
    case 'Network error':
      return 'Please check your internet connection.';
    case 'Timeout error':
      return 'The request took too long. Please try again.';
    case 'Rate limit exceeded':
      return 'Too many requests. Please wait a moment.';
    case 'Permission denied':
    case 'Resource not found':
    case 'CORS error':
    case 'Data parsing error':
    default:
      return 'Please try again later.';
  }
};

// Function to fetch analytics data
const fetchAnalyticsData = async (token: string | undefined, timeRange: ReturnType<typeof getTimeRanges>) => {
  if (!token) {
    return null;
  }

  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const endpoints = ['/api/analytics/leads/summary', '/api/analytics/conversations/summary', '/api/analytics/revenue/summary'];

  const fetchPromises = endpoints.flatMap(endpoint => [
    fetch(`${apiBaseUrl}${endpoint}?start_date=${timeRange.current.start_date}&end_date=${timeRange.current.end_date}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }),
    fetch(`${apiBaseUrl}${endpoint}?start_date=${timeRange.previous.start_date}&end_date=${timeRange.previous.end_date}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }),
  ]);

  try {
    const responses = await Promise.all(fetchPromises);
    const data = await Promise.all(responses.map(async (res, index) => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status} for ${endpoints[Math.floor(index / 2)]}`);
      }
      return res.json();
    }));

    // Parse data: data[0] = current leads, data[1] = previous leads, data[2] = current conv, etc.
    const [currentLeads, previousLeads, currentConv, previousConv, currentRev, previousRev] = data;

    return {
      total_leads: { value: currentLeads.total_leads, change: calculatePercentageChange(currentLeads.total_leads, previousLeads.total_leads) },
      qualified_leads: { value: currentLeads.qualified_leads, change: calculatePercentageChange(currentLeads.qualified_leads, previousLeads.qualified_leads) },
      conversion_rate: { value: currentLeads.conversion_rate, change: calculatePercentageChange(currentLeads.conversion_rate, previousLeads.conversion_rate) },
      avg_lead_score: { value: currentLeads.avg_lead_score, change: calculatePercentageChange(currentLeads.avg_lead_score, previousLeads.avg_lead_score) },
      total_conversations: { value: currentConv.total_conversations, change: calculatePercentageChange(currentConv.total_conversations, previousConv.total_conversations) },
      active_conversations: { value: currentConv.active_conversations, change: calculatePercentageChange(currentConv.active_conversations, previousConv.active_conversations) },
      completed_conversations: { value: currentConv.completed_conversations, change: calculatePercentageChange(currentConv.completed_conversations, previousConv.completed_conversations) },
      avg_messages_per_conversation: { value: currentConv.avg_messages_per_conversation, change: calculatePercentageChange(currentConv.avg_messages_per_conversation, previousConv.avg_messages_per_conversation) },
      mrr: { value: safeParseFloat(currentRev.mrr), change: calculatePercentageChange(safeParseFloat(currentRev.mrr), safeParseFloat(previousRev.mrr)) },
      arr: { value: safeParseFloat(currentRev.arr), change: calculatePercentageChange(safeParseFloat(currentRev.arr), safeParseFloat(previousRev.arr)) },
      total_revenue: { value: safeParseFloat(currentRev.total_revenue), change: calculatePercentageChange(safeParseFloat(currentRev.total_revenue), safeParseFloat(previousRev.total_revenue)) },
      active_subscriptions: { value: safeParseFloat(currentRev.active_subscriptions), change: calculatePercentageChange(safeParseFloat(currentRev.active_subscriptions), safeParseFloat(previousRev.active_subscriptions)) },
      cancelled_subscriptions: { value: safeParseFloat(currentRev.cancelled_subscriptions), change: calculatePercentageChange(safeParseFloat(currentRev.cancelled_subscriptions), safeParseFloat(previousRev.cancelled_subscriptions)) },
      churn_rate: { value: safeParseFloat(currentRev.churn_rate), change: calculatePercentageChange(safeParseFloat(currentRev.churn_rate), safeParseFloat(previousRev.churn_rate)) },
    } as AnalyticsData;
  } catch (error) {
    let errorType = 'Unknown error';
    let endpointContext = '';
    if (error instanceof Error) {
      if (error.message.includes('HTTP error! status: 401')) {
        errorType = 'Authentication error';
      } else if (error.message.includes('HTTP error! status: 403')) {
        errorType = 'Permission denied';
      } else if (error.message.includes('HTTP error! status: 404')) {
        errorType = 'Resource not found';
      } else if (error.message.includes('HTTP error! status: 429')) {
        errorType = 'Rate limit exceeded';
      } else if (error.message.includes('HTTP error! status:')) {
        errorType = 'Network error';
        const match = error.message.match(/for (\/api\/analytics\/[^)]+)/);
        endpointContext = match ? ` on endpoint ${match[1]}` : '';
      } else if (error.message.includes('timeout')) {
        errorType = 'Timeout error';
      } else if (error.message.includes('CORS')) {
        errorType = 'CORS error';
      } else {
        errorType = 'Data parsing error';
      }
    }
    throw new Error(`Failed to fetch analytics data (${errorType}${endpointContext}): ${error instanceof Error ? error.message : 'Unknown error'}. ${getRecoverySuggestion(errorType)}`);
  }
};

export const useAnalytics = () => {
  const { user, role, session } = useAuth();
  const timeRange = getTimeRanges(); // Default 30 days; can be customized if needed
  const {
    data,
    error,
    isLoading: loading,
  } = useQuery<AnalyticsData | null>({
    queryKey: ['analytics', user?.id, role, timeRange],
    queryFn: () => fetchAnalyticsData(session?.access_token, timeRange),
    enabled: !!user && !!session, // Only run if user is authenticated and session exists
    retry: 3, // Use React Query's built-in retry for transient errors
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
    refetchInterval: 60000, // Refresh every 60 seconds as fallback when WebSocket is disconnected
  });

  return { data, error, loading };
};
