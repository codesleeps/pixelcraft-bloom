import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';

interface UseWebSocketOptions {
  enabled?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { enabled = true } = options;
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildWebSocketUrl = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    return `${wsUrl}/api/ws/analytics?token=${session?.access_token}`;
  };

  const connect = () => {
    if (!session || !enabled) return;

    if (!window.WebSocket) {
      setError('WebSocket not supported by this browser');
      return;
    }

    const wsUrl = buildWebSocketUrl();
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { event_type } = message;

        switch (event_type) {
          case 'lead_created':
          case 'lead_analyzed':
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
            queryClient.invalidateQueries({ queryKey: ['leadTrends'] });
            break;
          case 'message_created':
          case 'conversation_deleted':
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
            queryClient.invalidateQueries({ queryKey: ['conversationTrends'] });
            break;
          case 'subscription_created':
          case 'subscription_updated':
            queryClient.invalidateQueries({ queryKey: ['analytics'] });
            queryClient.invalidateQueries({ queryKey: ['subscriptionTrends'] });
            queryClient.invalidateQueries({ queryKey: ['revenueByPackage'] });
            break;
          default:
            console.log('Unknown event type:', event_type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    wsRef.current.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
    };

    wsRef.current.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);

      if (event.code === 1008) {
        setError('Authentication failed');
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
        setError('Max reconnection attempts reached');
      }
    };
  };

  useEffect(() => {
    if (session && enabled) {
      connect();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [session, enabled]);

  return { isConnected, error };
};