import { renderHook, act } from '@testing-library/react-hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useNotifications } from '../useNotifications';
import { useAuth } from '../useAuth';
import { useWebSocket } from '../useWebSocket';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock dependencies
vi.mock('../useAuth', () => ({
  useAuth: vi.fn()
}));

vi.mock('../useWebSocket', () => ({
  useWebSocket: vi.fn()
}));

// Mock fetch
global.fetch = vi.fn();

describe('useNotifications', () => {
  let queryClient: QueryClient;
  
  beforeEach(() => {
    queryClient = new QueryClient();
    
    // Mock auth hook with default session
    (useAuth as any).mockReturnValue({
      session: { access_token: 'test-token' },
      user: { id: 'test-user' }
    });
    
    // Mock useWebSocket hook
    (useWebSocket as any).mockReturnValue({
      isConnected: true,
      error: null,
      connectionStatus: 'connected'
    });
    
    // Mock fetch response
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        notifications: [
          {
            id: 'notif1',
            notification_type: 'info',
            severity: 'info',
            title: 'Test Notification',
            message: 'This is a test notification',
            created_at: new Date().toISOString()
          }
        ],
        total: 1,
        unread_count: 1
      })
    });
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn()
      },
      writable: true
    });
  });
  
  afterEach(() => {
    vi.clearAllMocks();
  });
  
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  
  it('should fetch notifications when session is available', async () => {
    const { result, waitFor } = renderHook(
      () => useNotifications(),
      { wrapper }
    );
    
    // Initial state
    expect(result.current.isLoading).toBe(true);
    
    // Wait for query to resolve
    await waitFor(() => !result.current.isLoading);
    
    expect(result.current.notifications).toHaveLength(1);
    expect(result.current.unreadCount).toBe(1);
    expect(result.current.isConnected).toBe(true);
  });
  
  it('should not fetch notifications without session', async () => {
    (useAuth as any).mockReturnValue({ session: null, user: null });
    
    const { result } = renderHook(
      () => useNotifications(),
      { wrapper }
    );
    
    expect(result.current.notifications).toHaveLength(0);
    expect(global.fetch).not.toHaveBeenCalled();
  });
  
  it('should handle mark as read mutation', async () => {
    const { result, waitFor } = renderHook(
      () => useNotifications(),
      { wrapper }
    );
    
    await waitFor(() => !result.current.isLoading);
    
    // Reset fetch mock to track the next call
    (global.fetch as any).mockClear();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ marked_read_count: 1 })
    });
    
    // Call markAsRead
    act(() => {
      result.current.markAsRead(['notif1']);
    });
    
    // Verify fetch was called with correct params
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/notifications/mark-read'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ notification_ids: ['notif1'] })
        })
      );
    });
  });
  
  it('should handle mark all as read mutation', async () => {
    const { result, waitFor } = renderHook(
      () => useNotifications(),
      { wrapper }
    );
    
    await waitFor(() => !result.current.isLoading);
    
    // Reset fetch mock to track the next call
    (global.fetch as any).mockClear();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ marked_read_count: 5 })
    });
    
    // Call markAllAsRead
    act(() => {
      result.current.markAllAsRead();
    });
    
    // Verify fetch was called with correct params
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/notifications/mark-all-read'),
        expect.objectContaining({
          method: 'POST'
        })
      );
    });
    
    // Verify localStorage was updated
    expect(localStorage.setItem).toHaveBeenCalledWith('unreadNotificationCount', '0');
  });
});