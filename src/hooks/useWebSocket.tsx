import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';

/**
 * useWebSocket
 *
 * Establishes an authenticated WebSocket connection to the analytics channel and
 * automatically reconnects with exponential backoff.
 *
 * Parameters:
 * - options.enabled?: boolean (default: true)
 *   When false, the hook will not attempt to connect.
 * - options.heartbeatInterval?: number (default: 30000)
 *   Interval in ms to send heartbeat pings to keep connection alive.
 * - options.maxReconnectAttempts?: number (default: 15)
 *   Maximum number of reconnection attempts before giving up.
 * - options.initialBackoffDelay?: number (default: 1000)
 *   Initial delay in ms before first reconnection attempt.
 * - options.maxBackoffDelay?: number (default: 30000)
 *   Maximum delay in ms between reconnection attempts.
 *
 * Returns:
 * - isConnected: boolean
 *   True when the socket is currently open.
 * - error: string | null
 *   Last connection error (auth failure, unsupported, max retries, etc.).
 * - reconnect: () => void
 *   Function to manually trigger reconnection.
 * - connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error'
 *   Current connection status.
 *
 * Authentication:
 * - Uses the current Supabase session access_token via useAuth().
 * - Token is appended as a query parameter (token=JWT) when building the WS URL.
 *
 * Reconnection behavior:
 * - Exponential backoff starting at initialBackoffDelay, capped at maxBackoffDelay.
 * - Stops retrying after receiving policy close code 1008 (auth failure) or after maxReconnectAttempts.
 * - Automatically reconnects when network comes back online.
 */
interface UseWebSocketOptions {
  enabled?: boolean;
  heartbeatInterval?: number;
  maxReconnectAttempts?: number;
  initialBackoffDelay?: number;
  maxBackoffDelay?: number;
  endpoint?: string;
}

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    enabled = true,
    heartbeatInterval = 30000,
    maxReconnectAttempts = 15,
    initialBackoffDelay = 1000,
    maxBackoffDelay = 30000,
    endpoint = '/analytics'
  } = options;
  
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const intentionalCloseRef = useRef(false);
  
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');

  const buildWebSocketUrl = useCallback(() => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws');
    // Ensure token is properly passed as expected by backend auth
    if (!session?.access_token) {
      throw new Error('No access token available for WebSocket connection');
    }
    return `${wsUrl}/api/ws${endpoint}?token=${encodeURIComponent(session.access_token)}`;
  }, [session, endpoint]);

  const sendHeartbeat = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      } catch (err) {
        console.error('Failed to send heartbeat:', err);
      }
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, heartbeatInterval);
  }, [heartbeatInterval, sendHeartbeat]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const cleanupConnection = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopHeartbeat();
  }, [stopHeartbeat]);

  const connect = useCallback(() => {
    if (!session?.access_token || !enabled) {
      setConnectionStatus('disconnected');
      return;
    }

    // Clean up any existing connection
    cleanupConnection();
    
    if (!window.WebSocket) {
      setError('WebSocket not supported by this browser');
      setConnectionStatus('error');
      return;
    }

    setConnectionStatus('connecting');
    intentionalCloseRef.current = false;
    
    try {
      const wsUrl = buildWebSocketUrl();
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log(`WebSocket connected to ${endpoint}`);
        setIsConnected(true);
        setError(null);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          // Handle heartbeat response
          if (message?.type === 'pong') {
            return;
          }
          
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
            case 'notification_created':
              queryClient.invalidateQueries({ queryKey: ['notifications'] });
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
        setConnectionStatus('error');
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        stopHeartbeat();
        
        // Don't attempt to reconnect if this was an intentional close
        if (intentionalCloseRef.current) {
          setConnectionStatus('disconnected');
          return;
        }

        if (event.code === 1008) {
          setError('Authentication failed');
          setConnectionStatus('error');
          return;
        }

        // Attempt reconnection if not intentional close
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            initialBackoffDelay * Math.pow(2, reconnectAttemptsRef.current),
            maxBackoffDelay
          );
          
          setConnectionStatus('connecting');
          reconnectAttemptsRef.current += 1;
          
          console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          setError('Max reconnection attempts reached');
          setConnectionStatus('error');
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
      setConnectionStatus('error');
    }
  }, [session, enabled, buildWebSocketUrl, startHeartbeat, stopHeartbeat, cleanupConnection,
    initialBackoffDelay,
    maxBackoffDelay,
    maxReconnectAttempts,
    queryClient,
    endpoint
  ]);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    cleanupConnection();
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, [cleanupConnection]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    setError(null);
    connect();
  }, [connect]);

  useEffect(() => {
    if (session?.access_token && enabled) {
      connect();
    } else if (!session?.access_token && wsRef.current) {
      disconnect();
    }

    const handleOnline = () => {
      console.log('Network back online, attempting to reconnect WebSocket');
      if (!isConnected && session?.access_token && enabled) {
        reconnect();
      }
    };
    
    const handleOffline = () => {
      console.log('Network offline, pausing WebSocket reconnection');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      setConnectionStatus('disconnected');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      disconnect();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [session, enabled, connect, disconnect, reconnect, isConnected]);

  return { 
    isConnected, 
    error, 
    reconnect,
    connectionStatus,
    disconnect
  };
};