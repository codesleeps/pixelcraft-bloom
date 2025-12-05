import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { useWebSocket } from './useWebSocket';

export interface Notification {
  id: string;
  notification_type: string;
  severity: string;
  title: string;
  message: string;
  action_url?: string;
  metadata: Record<string, any>;
  read_at?: string;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

// Helper function for authenticated fetch (supports RequestInit)
const fetchWithAuth = async (url: string, token: string, init?: RequestInit) => {
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const headers: HeadersInit = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    ...(init?.headers || {}),
  };
  const response = await fetch(`${apiBaseUrl}${url}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

export const useNotifications = (options?: { unread_only?: boolean; notification_type?: string; limit?: number }) => {
  const { unread_only = false, notification_type, limit = 50 } = options || {};
  const { session, user } = useAuth();
  const queryClient = useQueryClient();
  const [lastNotification, setLastNotification] = useState<Notification | null>(null);

  // Use the enhanced WebSocket hook for notifications channel
  const {
    isConnected,
    error: wsError,
    connectionStatus
  } = useWebSocket({
    enabled: !!session,
    heartbeatInterval: 30000,
    maxReconnectAttempts: 15,
    endpoint: '/notifications',
    onMessage: (data) => {
      try {
        // Handle notification-specific events
        if (data.event_type === 'notification_created') {
          // Update the notification cache
          queryClient.invalidateQueries({ queryKey: ['notifications'] });

          // Store the latest notification for UI updates
          if (data.notification) {
            setLastNotification(data.notification);

            // Persist unread count in localStorage for session persistence
            const currentUnreadCount = parseInt(localStorage.getItem('unreadNotificationCount') || '0', 10);
            localStorage.setItem('unreadNotificationCount', (currentUnreadCount + 1).toString());
          }
        }
      } catch (err) {
        console.error('Failed to process notification message:', err);
      }
    }
  });

  const queryFn = async (): Promise<NotificationListResponse> => {
    if (!session?.access_token) {
      throw new Error('No access token');
    }

    const params = new URLSearchParams({
      limit: limit.toString(),
      unread_only: unread_only.toString(),
    });
    if (notification_type) {
      params.append('notification_type', notification_type);
    }

    return fetchWithAuth(`/api/notifications?${params.toString()}`, session.access_token);
  };

  const { data, isLoading, error, refetch } = useQuery<NotificationListResponse>({
    queryKey: ['notifications', user?.id, options],
    queryFn,
    enabled: !!session,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  useEffect(() => {
    if (data) {
      // Update the persisted unread count
      localStorage.setItem('unreadNotificationCount', data.unread_count.toString());
    }
  }, [data]);

  const markAsReadMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      if (!session?.access_token) {
        throw new Error('No access token');
      }
      return fetchWithAuth('/api/notifications/mark-read', session.access_token, {
        method: 'POST',
        body: JSON.stringify({ notification_ids: ids }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: async () => {
      if (!session?.access_token) {
        throw new Error('No access token');
      }
      return fetchWithAuth('/api/notifications/mark-all-read', session.access_token, {
        method: 'POST',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      // Reset the persisted unread count
      localStorage.setItem('unreadNotificationCount', '0');
    },
  });

  // Get persisted unread count from localStorage if data is not yet loaded
  const getUnreadCount = () => {
    if (data?.unread_count !== undefined) {
      return data.unread_count;
    }

    // Fall back to localStorage if query hasn't loaded yet
    return parseInt(localStorage.getItem('unreadNotificationCount') || '0', 10);
  };

  return {
    notifications: data?.notifications || [],
    unreadCount: getUnreadCount(),
    isLoading,
    error,
    markAsRead: markAsReadMutation.mutate,
    markAllAsRead: markAllAsReadMutation.mutate,
    isConnected,
    wsError,
    connectionStatus,
    lastNotification,
    refetchNotifications: refetch
  };
};