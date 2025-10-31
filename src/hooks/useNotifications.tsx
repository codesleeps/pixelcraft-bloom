import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { useAuth } from './useAuth';

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
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);

  const buildWebSocketUrl = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    return `${wsUrl}/api/ws/notifications?token=${session?.access_token}`;
  };

  const connect = () => {
    if (!session) return;

    if (!window.WebSocket) {
      setWsError('WebSocket not supported by this browser');
      return;
    }

    const wsUrl = buildWebSocketUrl();
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('Notifications WebSocket connected');
      setIsConnected(true);
      setWsError(null);
      reconnectAttemptsRef.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        // Ignore ping frames from server
        if (message?.type === 'ping') return;
        // Invalidate notifications query on real notification messages
        queryClient.invalidateQueries({ queryKey: ['notifications'] });
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    wsRef.current.onerror = (event) => {
      console.error('Notifications WebSocket error:', event);
      setWsError('WebSocket connection error');
    };

    wsRef.current.onclose = (event) => {
      console.log('Notifications WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      if (event.code === 1008) {
        setWsError('Authentication failed');
        return;
      }

      // Attempt reconnection if not intentional close
      if (reconnectAttemptsRef.current < 10) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      } else {
        setWsError('Max reconnection attempts reached');
      }
    };
  };

  useEffect(() => {
    if (session) {
      connect();
    }

    const handleOnline = () => {
      // Resume connection attempts when back online
      if (!isConnected && session) connect();
    };
    const handleOffline = () => {
      // Pause reconnect timers while offline
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [session, isConnected]);

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

  const { data, isLoading, error } = useQuery<NotificationListResponse>({
    queryKey: ['notifications', user?.id, options],
    queryFn,
    enabled: !!session,
    refetchInterval: 60000,
  });

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
    },
  });

  return {
    notifications: data?.notifications || [],
    unreadCount: data?.unread_count || 0,
    isLoading,
    error,
    markAsRead: markAsReadMutation.mutate,
    markAllAsRead: markAllAsReadMutation.mutate,
    isConnected,
    wsError,
  };
};