import { renderHook, act } from '@testing-library/react-hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWebSocket } from '../useWebSocket';
import { useAuth } from '../useAuth';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock dependencies
vi.mock('../useAuth', () => ({
  useAuth: vi.fn()
}));

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: Function | null = null;
  onclose: Function | null = null;
  onmessage: Function | null = null;
  onerror: Function | null = null;
  readyState = 0;
  OPEN = 1;
  
  constructor(url: string) {
    this.url = url;
    setTimeout(() => this.onopen && this.onopen({}), 0);
  }
  
  send(data: string) {
    // Mock send
  }
  
  close() {
    if (this.onclose) this.onclose({ code: 1000 });
  }
}

// Setup global WebSocket mock
global.WebSocket = MockWebSocket as any;

describe('useWebSocket', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient();
    
    // Mock auth hook with default session
    (useAuth as any).mockReturnValue({
      session: { access_token: 'test-token' },
      user: { id: 'test-user' }
    });
    
    // Mock console methods to reduce test noise
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });
  
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  
  it('should establish connection when enabled with valid session', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useWebSocket({ endpoint: '/notifications' }),
      { wrapper }
    );
    
    await waitForNextUpdate();
    
    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionStatus).toBe('connected');
    expect(result.current.error).toBeNull();
  });
  
  it('should not connect when disabled', () => {
    const { result } = renderHook(
      () => useWebSocket({ enabled: false }),
      { wrapper }
    );
    
    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionStatus).toBe('disconnected');
  });
  
  it('should not connect without session', () => {
    (useAuth as any).mockReturnValue({ session: null });
    
    const { result } = renderHook(
      () => useWebSocket(),
      { wrapper }
    );
    
    expect(result.current.isConnected).toBe(false);
  });
  
  it('should handle reconnection', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useWebSocket(),
      { wrapper }
    );
    
    await waitForNextUpdate();
    expect(result.current.isConnected).toBe(true);
    
    // Simulate disconnect
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onclose && ws.onclose({ code: 1001 });
    });
    
    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionStatus).toBe('disconnected');
    
    // Manual reconnect
    act(() => {
      result.current.reconnect();
    });
    
    await waitForNextUpdate();
    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionStatus).toBe('connected');
  });
  
  it('should handle auth failure', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useWebSocket(),
      { wrapper }
    );
    
    await waitForNextUpdate();
    
    // Simulate auth failure
    act(() => {
      const ws = (global as any).WebSocket.mock.instances[0];
      ws.onclose && ws.onclose({ code: 1008 });
    });
    
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBe('Authentication failed');
    expect(result.current.connectionStatus).toBe('error');
  });
});